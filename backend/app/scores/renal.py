"""
Renal Function Calculator (Cockcroft-Gault & eGFR).
Computes estimated Creatinine Clearance (CrCl) or utilizes documented eGFR.
Handles missing inputs transparently without fabricating clinical data.
"""
from typing import Any, Dict, Optional


def calculate_renal_function(
    age: Optional[int],
    sex: Optional[str],
    weight_kg: Optional[float],
    serum_creatinine_mg_dl: Optional[float] = None,
    direct_egfr: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Computes Cockcroft-Gault CrCl:
    CrCl = ((140 - age) * weight_kg) / (72 * SCr) * (0.85 if female else 1.0)
    """
    if direct_egfr is not None:
        stage = _get_ckd_stage(direct_egfr)
        return {
            "available": True,
            "kind": "egfr",
            "value": round(direct_egfr, 1),
            "unit": "mL/min/1.73m2",
            "ckd_stage": stage,
            "method": "Direct Laboratory eGFR",
            "formula_version": "CKD-EPI (Documented Lab)",
            "missing_inputs": [],
        }

    missing = []
    if age is None:
        missing.append("age")
    if sex is None:
        missing.append("sex")
    if weight_kg is None:
        missing.append("weight_kg")
    if serum_creatinine_mg_dl is None:
        missing.append("serum_creatinine_mg_dl")

    if missing:
        return {
            "available": False,
            "kind": "crcl",
            "value": None,
            "unit": "mL/min",
            "ckd_stage": "Unknown",
            "method": "Cockcroft-Gault",
            "formula_version": "Cockcroft-Gault (1976)",
            "missing_inputs": missing,
            "note": f"Renal clearance calculation skipped due to missing inputs: {', '.join(missing)}.",
        }

    # Safe calculation
    if serum_creatinine_mg_dl <= 0:
        return {
            "available": False,
            "kind": "crcl",
            "value": None,
            "unit": "mL/min",
            "ckd_stage": "Invalid",
            "method": "Cockcroft-Gault",
            "formula_version": "Cockcroft-Gault (1976)",
            "missing_inputs": ["valid_positive_serum_creatinine"],
            "note": "Serum creatinine must be positive.",
        }

    crcl = ((140.0 - float(age)) * float(weight_kg)) / (72.0 * float(serum_creatinine_mg_dl))
    is_female = sex.lower().startswith("f")
    if is_female:
        crcl *= 0.85

    stage = _get_ckd_stage(crcl)
    return {
        "available": True,
        "kind": "crcl",
        "value": round(crcl, 1),
        "unit": "mL/min",
        "ckd_stage": stage,
        "method": "Cockcroft-Gault",
        "formula_version": "Cockcroft-Gault (1976)",
        "missing_inputs": [],
    }


def _get_ckd_stage(val: float) -> str:
    if val >= 90:
        return "Normal / Stage 1 (>=90)"
    elif val >= 60:
        return "Mildly Reduced / Stage 2 (60-89)"
    elif val >= 30:
        return "Moderately Reduced / Stage 3 (30-59)"
    elif val >= 15:
        return "Severely Reduced / Stage 4 (15-29)"
    else:
        return "Kidney Failure / Stage 5 (<15)"

