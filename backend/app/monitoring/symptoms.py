"""
Symptom Monitoring and Drug Linking Module.
Maps reported symptoms to potential causal drug classes.
Bypasses routine flow on emergency red flags (Rule S6).
"""
import re
from typing import Any, Dict, List, Optional, Tuple
from backend.app.channels.conversation import detect_red_flag
from backend.app.entities.lexicon import get_lexicon

SYMPTOM_CLASS_MAP: Dict[str, List[str]] = {
    "dizziness": ["antihypertensive", "calcium_channel_blocker", "beta_blocker", "ace_inhibitor", "arb", "diuretic", "benzodiazepine"],
    "fall": ["benzodiazepine", "sedative_hypnotic", "first_gen_antihistamine", "diuretic", "antihypertensive"],
    "confusion": ["first_gen_antihistamine", "benzodiazepine", "tca", "anticholinergic_antiparkinson", "anticholinergic_bladder"],
    "constipation": ["first_gen_antihistamine", "tca", "calcium_channel_blocker", "opioid"],
    "swelling": ["calcium_channel_blocker"],
    "cough": ["ace_inhibitor"],
    "drowsiness": ["benzodiazepine", "sedative_hypnotic", "first_gen_antihistamine"],
    "nausea": ["biguanide", "nsaid"],
    "bleeding": ["anticoagulant", "antiplatelet", "nsaid"],
}

# Multilingual symptom synonyms
SYMPTOM_SYNONYMS: Dict[str, str] = {
    "chakkar": "dizziness",
    "giddiness": "dizziness",
    "lightheaded": "dizziness",
    "gir gaya": "fall",
    "fell": "fall",
    "bhoolna": "confusion",
    "delirium": "confusion",
    "kabz": "constipation",
    "sujan": "swelling",
    "edema": "swelling",
    "khasi": "cough",
    "khoon": "bleeding",
    "neend": "drowsiness",
    "ulti": "nausea",
}


def analyze_symptom(
    raw_text: str,
    active_medications: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Parses reported symptom, checks red-flag emergency status, and links to suspect medications.
    """
    # 1. Emergency Red Flag check
    red_flag = detect_red_flag(raw_text)
    if red_flag:
        return {
            "controlled_symptom": "EMERGENCY_RED_FLAG",
            "is_red_flag": True,
            "suspect_med_ids": [],
            "doctor_question": "Immediate emergency evaluation required.",
            "emergency_guidance": "Please call emergency services (112/108) or go to the emergency room immediately.",
        }

    # 2. Match controlled symptom
    lower = raw_text.lower()
    matched_term = None
    for sym_key in SYMPTOM_CLASS_MAP.keys():
        if sym_key in lower:
            matched_term = sym_key
            break

    if not matched_term:
        for syn, canonical in SYMPTOM_SYNONYMS.items():
            if syn in lower:
                matched_term = canonical
                break

    if not matched_term:
        matched_term = "other_symptom"

    # 3. Link suspect medications
    lexicon = get_lexicon()
    suspect_meds = []
    causal_classes = set(SYMPTOM_CLASS_MAP.get(matched_term, []))

    for med in active_medications:
        med_id = med.get("id") or med.get("brand")
        brand = med.get("brand") or "Medication"
        for ing_obj in med.get("ingredients", []):
            ing = ing_obj.get("ingredient", "").lower()
            classes = set(lexicon.get_classes_for_ingredient(ing))
            if classes.intersection(causal_classes):
                suspect_meds.append({
                    "med_id": med_id,
                    "brand": brand,
                    "ingredient": ing,
                    "matched_class": list(classes.intersection(causal_classes))[0],
                })
                break

    question = (
        f"Could my {matched_term} be an adverse reaction related to {', '.join([m['brand'] for m in suspect_meds])}?"
        if suspect_meds
        else f"I have been noticing {matched_term}; should we investigate this symptom?"
    )

    return {
        "controlled_symptom": matched_term,
        "is_red_flag": False,
        "suspect_meds": suspect_meds,
        "suspect_med_ids": [m["med_id"] for m in suspect_meds],
        "doctor_question": question,
    }

