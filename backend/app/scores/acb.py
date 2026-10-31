"""
Anticholinergic Cognitive Burden (ACB) Scale Calculator.
Based on Boustani et al. (2008) and Campbell et al. (2013).
Total score >= 3 indicates clinically significant anticholinergic burden.
"""
from typing import Any, Dict, List, Tuple

ACB_DRUG_TABLE: Dict[str, int] = {
    # Score 3: Severe anticholinergic burden
    "amitriptyline": 3,
    "diphenhydramine": 3,
    "promethazine": 3,
    "hydroxyzine": 3,
    "chlorpheniramine": 3,
    "oxybutynin": 3,
    "paroxetine": 3,
    "trihexyphenidyl": 3,
    "nortriptyline": 3,
    "clomipramine": 3,
    "doxepin": 3,
    "imipramine": 3,
    "tolterodine": 3,

    # Score 2: Moderate anticholinergic burden
    "amantadine": 2,
    "carbamazepine": 2,
    "clozapine": 2,
    "cyclobenzaprine": 2,
    "oxcarbazepine": 2,

    # Score 1: Mild anticholinergic burden
    "alprazolam": 1,
    "atenolol": 1,
    "captopril": 1,
    "cetirizine": 1,
    "chlorthalidone": 1,
    "cimetidine": 1,
    "diazepam": 1,
    "digoxin": 1,
    "furosemide": 1,
    "haloperidol": 1,
    "hydrochlorothiazide": 1,
    "isosorbide": 1,
    "loratadine": 1,
    "metoprolol": 1,
    "prednisone": 1,
    "ranitidine": 1,
    "risperidone": 1,
    "theophylline": 1,
    "warfarin": 1,
}


def calculate_acb_score(ingredients: List[str]) -> Dict[str, Any]:
    """
    Computes total ACB score from list of active generic ingredients.
    Returns: {
        "score": int,
        "is_flagged": bool (score >= 3),
        "level": "low" | "moderate" | "high",
        "contributing_drugs": [{"ingredient": str, "score": int}],
        "source": "Anticholinergic Cognitive Burden Scale (Boustani et al.)"
    }
    """
    total = 0
    contributors = []

    for ing in ingredients:
        ing_lower = ing.lower().strip()
        if ing_lower in ACB_DRUG_TABLE:
            score = ACB_DRUG_TABLE[ing_lower]
            total += score
            contributors.append({"ingredient": ing_lower, "score": score})

    is_flagged = total >= 3
    if total == 0:
        level = "None"
    elif total <= 2:
        level = "Low"
    else:
        level = "High"

    return {
        "score": total,
        "is_flagged": is_flagged,
        "level": level,
        "contributing_drugs": contributors,
        "source": "Anticholinergic Cognitive Burden Scale (Boustani et al.)",
    }

