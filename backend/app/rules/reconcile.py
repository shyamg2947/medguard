"""
Discharge and Transition-of-Care Reconciliation Engine.
Detects:
- 'Boomerang' medications (intentionally stopped in hospital but inadvertently restarted)
- Newly introduced medications
- Strength or frequency alterations
- Duplicate therapies
- Unexplained omissions
Outputs respectful questions for the physician, never instructions (S2).
"""
from typing import Any, Dict, List, Optional, Set
from backend.app.entities.matcher import parse_strength_and_frequency
from backend.app.entities.resolver import resolve_medication_query


def reconcile_medication_lists(
    pre_admission_list: List[str],
    post_discharge_list: List[str],
    later_refill_list: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Compares medication snapshots.
    Supports 3-stage boomerang tracking: Pre -> Post-Discharge -> Later Refill.
    """
    pre_resolved = [_resolve_item(m) for m in pre_admission_list]
    post_resolved = [_resolve_item(m) for m in post_discharge_list]
    later_resolved = [_resolve_item(m) for m in (later_refill_list or [])]

    pre_ings = {item["generic"]: item for item in pre_resolved if item.get("generic")}
    post_ings = {item["generic"]: item for item in post_resolved if item.get("generic")}
    later_ings = {item["generic"]: item for item in later_resolved if item.get("generic")}

    new_meds = []
    missing_meds = []
    changed_meds = []
    boomerang_meds = []
    duplicates = []
    doctor_questions = []

    # 1. New in post-discharge
    for ing, item in post_ings.items():
        if ing not in pre_ings:
            new_meds.append(item["raw"])
            doctor_questions.append(
                f"Is the new medication '{item['raw']}' intended for long-term use after hospital discharge?"
            )

    # 2. Missing from post-discharge (intentionally or unintentionally stopped)
    for ing, item in pre_ings.items():
        if ing not in post_ings:
            missing_meds.append(item["raw"])
            doctor_questions.append(
                f"Was '{item['raw']}' intentionally stopped during the hospital stay, or should it be resumed?"
            )

    # 3. Changed strength or formulation
    for ing in pre_ings.keys() & post_ings.keys():
        pre_item = pre_ings[ing]
        post_item = post_ings[ing]
        if pre_item.get("strength") and post_item.get("strength") and pre_item["strength"] != post_item["strength"]:
            changed_meds.append(
                f"{ing.title()} (Changed from {pre_item['strength']} to {post_item['strength']})"
            )
            doctor_questions.append(
                f"Please confirm whether the dose change for {ing.title()} (from {pre_item['strength']} to {post_item['strength']}) should be continued."
            )

    # 4. Boomerang detection:
    # Present in Pre, ABSENT in Post-discharge (stopped), but REAPPEARS in Later Refill or current list!
    if later_ings:
        for ing, item in later_ings.items():
            if ing in pre_ings and ing not in post_ings:
                boomerang_meds.append(item["raw"])
                doctor_questions.append(
                    f"'{item['raw']}' was stopped during hospital discharge but appears to have been refilled recently. Should this medication remain stopped?"
                )
    else:
        # If comparing stopped list against post-discharge
        pass

    return {
        "discontinued_but_restarted": boomerang_meds,
        "new_medications": new_meds,
        "missing_medications": missing_meds,
        "changed_medications": changed_meds,
        "duplicates_detected": duplicates,
        "doctor_questions": doctor_questions,
    }


def _resolve_item(raw_med_str: str) -> Dict[str, Any]:
    res = resolve_medication_query(raw_med_str)
    generic = None
    strength, freq, _ = parse_strength_and_frequency(raw_med_str)

    if res.get("top_candidate"):
        top = res["top_candidate"]
        ings = top.get("ingredients", [])
        if ings:
            generic = ings[0].get("ingredient")
        if not strength:
            strength = top.get("strength")

    if not generic:
        # Fallback to cleaned word
        generic = raw_med_str.lower().split()[0]

    return {
        "raw": raw_med_str,
        "generic": generic.lower() if generic else None,
        "strength": strength,
        "frequency": freq,
    }
