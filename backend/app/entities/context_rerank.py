"""
Context Re-ranking for Medication Matching.
Applies clinical priors based on:
- Existing patient medications (concordant therapeutic classes)
- Patient age (geriatric vs young)
- Documented conditions (hypertension, diabetes, arthralgia, etc.)
Safety rule: The prior may reorder close candidates but may NEVER raise a candidate above the acceptance threshold on its own.
"""
from typing import Any, Dict, List, Optional
from backend.app.config import get_settings
from backend.app.entities.lexicon import get_lexicon


def rerank_with_context(
    candidates: List[Dict[str, Any]],
    existing_med_ingredients: Optional[List[str]] = None,
    patient_age: Optional[int] = None,
    conditions: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """
    Adjusts candidate ranks using contextual priors.
    Max prior adjustment is capped at 0.08 to prevent artificial threshold inflation.
    """
    if not candidates:
        return candidates

    settings = get_settings()
    lexicon = get_lexicon()
    existing_ings = [i.lower() for i in (existing_med_ingredients or [])]
    conds = [c.lower() for c in (conditions or [])]

    # Gather existing classes
    existing_classes = set()
    for ing in existing_ings:
        for cls_name in lexicon.get_classes_for_ingredient(ing):
            existing_classes.add(cls_name)

    reranked = []
    for c in candidates:
        prior_boost = 0.0
        # Inspect ingredients of candidate
        cand_ings = [i["ingredient"].lower() for i in c.get("ingredients", [])]

        # 1. Class concordance (e.g. cardiovascular regimen)
        cand_classes = set()
        for ing in cand_ings:
            for cls_name in lexicon.get_classes_for_ingredient(ing):
                cand_classes.add(cls_name)

        if cand_classes.intersection(existing_classes):
            prior_boost += 0.03

        # 2. Condition concordance
        if any("hypertension" in cond or "bp" in cond for cond in conds):
            if any(cls in cand_classes for cls in ["arb", "ace_inhibitor", "calcium_channel_blocker", "beta_blocker"]):
                prior_boost += 0.03
        if any("diabetes" in cond or "sugar" in cond for cond in conds):
            if any(cls in cand_classes for cls in ["biguanide", "sulfonylurea"]):
                prior_boost += 0.03

        # Cap prior boost
        prior_boost = min(0.06, prior_boost)

        # Safety Guard: If raw score was below ACCEPT threshold, ensure boost does not push it over
        raw_score = c["score"]
        adjusted_score = raw_score + prior_boost
        if raw_score < settings.MATCH_ACCEPT_THRESHOLD and adjusted_score >= settings.MATCH_ACCEPT_THRESHOLD:
            adjusted_score = settings.MATCH_ACCEPT_THRESHOLD - 0.001

        candidate_copy = dict(c)
        candidate_copy["context_boost"] = round(prior_boost, 4)
        candidate_copy["adjusted_score"] = round(adjusted_score, 4)
        reranked.append(candidate_copy)

    # Sort by adjusted_score descending
    reranked.sort(key=lambda x: x["adjusted_score"], reverse=True)

    # Recompute margins based on adjusted score
    for i, c in enumerate(reranked):
        next_score = reranked[i + 1]["adjusted_score"] if i + 1 < len(reranked) else 0.0
        c["margin"] = round(c["adjusted_score"] - next_score, 4)

    return reranked

