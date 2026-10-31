"""
Medication Resolver & Read-back Generation.
Coordinates matching, threshold routing, and read-back confirmation strings.
Enforces S4: Confirm before storing (only confirmed items are written as confirmed=true).
"""
from typing import Any, Dict, List, Optional
from backend.app.config import get_settings
from backend.app.entities.context_rerank import rerank_with_context
from backend.app.entities.matcher import find_candidates
from backend.app.models.schemas import MedicationCandidate, MedicationIngredient


def resolve_medication_query(
    raw_text: str,
    asr_confidence: float = 1.0,
    existing_med_ingredients: Optional[List[str]] = None,
    patient_age: Optional[int] = None,
    conditions: Optional[List[str]] = None,
    language: str = "en",
) -> Dict[str, Any]:
    """
    Full resolution pipeline from raw input to Candidate / Clarification request.
    """
    settings = get_settings()

    # 1. Candidate generation
    raw_candidates = find_candidates(raw_text, asr_confidence=asr_confidence)

    # 2. Context re-ranking
    ranked = rerank_with_context(
        raw_candidates,
        existing_med_ingredients=existing_med_ingredients,
        patient_age=patient_age,
        conditions=conditions,
    )

    if not ranked:
        return {
            "status": "unrecognized",
            "message": _get_unrecognized_message(language),
            "candidates": [],
            "requires_photo": True,
        }

    top = ranked[0]
    score = top.get("adjusted_score", top["score"])
    margin = top.get("margin", 0.0)

    # 3. Decision by thresholds
    # Exact matches (score >= 1.0) or high-confidence with safe margin proceed to read-back confirmation (S4)
    if score >= 1.0 or (score >= settings.MATCH_ACCEPT_THRESHOLD and margin >= settings.MATCH_MARGIN_THRESHOLD):
        # High confidence -> Generate read-back prompt for user confirmation
        readback_prompt = _generate_readback_message(top, language)
        return {
            "status": "accept_candidate",
            "readback_prompt": readback_prompt,
            "top_candidate": {
                "matched_name": top["matched_name"],
                "ingredients": top["ingredients"],
                "strength": top.get("extracted_strength") or "",
                "frequency": top.get("extracted_frequency") or "",
                "category": top.get("category", "prescription"),
                "score": score,
                "margin": margin,
            },
            "requires_clarification": False,
            "clarification_options": [],
        }

    elif score >= settings.MATCH_CLARIFY_THRESHOLD:
        # Medium confidence or ambiguous margin -> Ask user to choose between top 2-3 options or send photo
        options = [c["matched_name"] for c in ranked[:3]]
        clarify_msg = _get_clarify_message(options, language)
        return {
            "status": "needs_clarification",
            "message": clarify_msg,
            "clarification_options": options,
            "requires_clarification": True,
            "requires_photo": True,
            "candidates": ranked[:3],
        }

    else:
        # Low confidence (< 0.65) -> Unrecognized
        return {
            "status": "unrecognized",
            "message": _get_unrecognized_message(language),
            "candidates": [],
            "requires_photo": True,
        }


def _generate_readback_message(candidate: Dict[str, Any], language: str) -> str:
    name = candidate["matched_name"]
    strength = candidate.get("extracted_strength") or ""
    freq = candidate.get("extracted_frequency") or "as directed"

    parts = [name]
    if strength and strength.lower() not in name.lower():
        parts.append(strength)
    elif not strength and candidate.get("extracted_strength"):
        parts.append(candidate["extracted_strength"])

    if freq:
        parts.append(f", {freq}")

    details = " ".join(parts).strip()
    import re
    details = re.sub(r'\s+,', ',', details)

    if language == "hi":
        return f"मैंने सुना: {details}। क्या यह सही है?"
    elif language == "kn":
        return f"ನಾನು ಕೇಳಿದ್ದು: {details}. ಇದು ಸರಿಯೇ?"
    return f"I heard {details}. Is that right?"


def _get_clarify_message(options: List[str], language: str) -> str:
    opts_str = ", ".join(options)
    if language == "hi":
        return f"क्या आपका मतलब {opts_str} में से कोई दवा था? या आप दवा की पट्टी (स्ट्रिप) का फोटो भेज सकते हैं।"
    elif language == "kn":
        return f"ನೀವು {opts_str} ಅನ್ನು ಉಲ್ಲೇಖಿಸುತ್ತಿದ್ದೀರಾ? ಅಥವಾ ಔಷಧಿ ಪಟ್ಟಿಯ ಫೋಟೋವನ್ನು ಕಳುಹಿಸಬಹುದು."
    return f"Did you mean one of: {opts_str}? Or you can take a clear photo of the medicine strip."


def _get_unrecognized_message(language: str) -> str:
    if language == "hi":
        return "मुझे दवा का नाम स्पष्ट रूप से समझ नहीं आया। कृपया दवा की पट्टी (स्ट्रिप) की एक साफ़ फोटो भेजें।"
    elif language == "kn":
        return "ಔಷಧಿಯ ಹೆಸರು ಸ್ಪಷ್ಟವಾಗಿ ಅರ್ಥವಾಗಲಿಲ್ಲ. ದಯವಿಟ್ಟು ಔಷಧಿಯ ಪಟ್ಟಿಯ ಫೋಟೋವನ್ನು ಕಳುಹಿಸಿ."
    return "I could not recognize that medicine name. Please send a clear photo of the medicine strip or bottle."
