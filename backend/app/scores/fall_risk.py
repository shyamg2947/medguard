"""
Geriatric Fall-Risk Drug Calculator.
Evaluates medications predisposing seniors to orthostatic hypotension, sedation, ataxia, and falls.
Categories: sedatives, antihypertensives, diuretics, opioids, antipsychotics, antidepressants, anticholinergics.
"""
from typing import Any, Dict, List
from backend.app.entities.lexicon import get_lexicon

FALL_RISK_CLASSES = {
    "sedative": ["benzodiazepine", "sedative_hypnotic"],
    "antihypertensive": ["calcium_channel_blocker", "beta_blocker", "ace_inhibitor", "arb"],
    "diuretic": ["loop_diuretic", "thiazide_diuretic", "potassium_sparing_diuretic", "diuretic"],
    "antipsychotic": ["antipsychotic"],
    "antidepressant": ["tca", "ssri", "snri"],
    "anticholinergic": ["first_gen_antihistamine", "anticholinergic_antiparkinson", "anticholinergic_bladder"],
    "opioid": ["opioid"],
}


def calculate_fall_risk(ingredients: List[str]) -> Dict[str, Any]:
    """
    Counts distinct fall-risk medications.
    Bands:
    - Low (0 - 1)
    - Medium (2 - 3)
    - High (>= 4)
    """
    lexicon = get_lexicon()
    contributing_drugs = []
    seen_drugs = set()

    for ing in ingredients:
        ing_lower = ing.lower().strip()
        classes = lexicon.get_classes_for_ingredient(ing_lower)

        matched_categories = []
        for cat_name, class_list in FALL_RISK_CLASSES.items():
            if any(cls in class_list for cls in classes):
                matched_categories.append(cat_name)

        if matched_categories and ing_lower not in seen_drugs:
            seen_drugs.add(ing_lower)
            contributing_drugs.append({
                "ingredient": ing_lower,
                "categories": matched_categories,
            })

    count = len(contributing_drugs)
    if count <= 1:
        band = "Low"
    elif count <= 3:
        band = "Medium"
    else:
        band = "High"

    return {
        "count": count,
        "band": band,
        "contributing_drugs": contributing_drugs,
        "source": "CDC STEADI (Stopping Elderly Accidents, Deaths, & Injuries) / AGS Beers Fall-Risk Guidance",
    }

