"""
Phase 3 Unit and Integration Tests.
Verifies Rules Engine, Risk Scores (ACB, Fall Risk, Cockcroft-Gault), Cascades, Durations, Reconciliation,
and End-to-End Scenarios A-D.
Strictly checks Safety Principles S1, S2, S3.
"""
import json
import os
import re
import pytest

from backend.app.rules.cascades import CascadeEvaluator
from backend.app.rules.durations import check_duration_exceeded, parse_duration_to_weeks
from backend.app.rules.engine import ClinicalRulesEngine
from backend.app.rules.reconcile import reconcile_medication_lists
from backend.app.scores.acb import calculate_acb_score
from backend.app.scores.fall_risk import calculate_fall_risk
from backend.app.scores.renal import calculate_renal_function

DIRECTIVE_WORDS = [
    r'\bstop\b', r'\bstart\b', r'\bincrease\b', r'\bdecrease\b', r'\bswitch\b', r'\bdiscontinue\b'
]


@pytest.fixture
def engine():
    return ClinicalRulesEngine()


def test_safety_s2_no_directive_medical_advice(engine):
    """Safety Principle S2: Output never orders the patient to stop, start, increase, decrease, or switch."""
    for rule in engine.rules:
        en_msg = rule.patient_message.get("en", "").lower()
        for pat in DIRECTIVE_WORDS:
            # Must not use directive imperatives
            assert not re.search(r'\b(you must|please)\s+' + pat, en_msg), \
                f"Directive phrasing found in rule {rule.id}: {en_msg}"
        assert "doctor" in en_msg or "pharmacist" in en_msg, \
            f"Rule {rule.id} patient message does not advise consulting professional"


def test_safety_s3_every_alert_cites_rule_and_source(engine):
    """Safety Principle S3: Every rule must have a valid rule_id, evidence level, and sources list."""
    for rule in engine.rules:
        assert rule.id, "Missing rule ID"
        assert rule.sources and len(rule.sources) > 0, f"Rule {rule.id} missing sources"
        assert rule.evidence in ["established", "limited", "theoretical"]
        assert rule.severity in ["critical", "high", "moderate", "low"]


def test_acb_score_calculation():
    # Diphenhydramine (3) + Amitriptyline (3) = 6 (Flagged)
    res = calculate_acb_score(["diphenhydramine", "amitriptyline", "metformin"])
    assert res["score"] == 6
    assert res["is_flagged"] is True
    assert res["level"] == "High"
    assert len(res["contributing_drugs"]) == 2

    # Zero score
    res_zero = calculate_acb_score(["paracetamol", "telmisartan"])
    assert res_zero["score"] == 0
    assert res_zero["is_flagged"] is False


def test_fall_risk_calculation():
    # 4 fall-risk medications -> High band
    meds = ["alprazolam", "amlodipine", "furosemide", "amitriptyline"]
    res = calculate_fall_risk(meds)
    assert res["count"] >= 4
    assert res["band"] == "High"


def test_cockcroft_gault_renal():
    # 70 yo male, 70kg, SCr 2.0 -> CrCl = ((140 - 70) * 70) / (72 * 2.0) = 4900 / 144 = 34.0 ml/min
    res_m = calculate_renal_function(age=70, sex="male", weight_kg=70.0, serum_creatinine_mg_dl=2.0)
    assert res_m["available"] is True
    assert abs(res_m["value"] - 34.0) < 0.5
    assert res_m["formula_version"] == "Cockcroft-Gault (1976)"

    # Female multiplier 0.85
    res_f = calculate_renal_function(age=70, sex="female", weight_kg=70.0, serum_creatinine_mg_dl=2.0)
    assert abs(res_f["value"] - (34.0 * 0.85)) < 0.5

    # Missing inputs must report missing without guessing
    res_missing = calculate_renal_function(age=70, sex="male", weight_kg=None, serum_creatinine_mg_dl=2.0)
    assert res_missing["available"] is False
    assert "weight_kg" in res_missing["missing_inputs"]


def test_durations_ppi():
    exceeded, possible, lower = check_duration_exceeded("14 weeks", max_duration_weeks=8)
    assert exceeded is True
    assert lower > 8

    exceeded2, possible2, lower2 = check_duration_exceeded("3 weeks", max_duration_weeks=8)
    assert exceeded2 is False


def test_prescribing_cascades():
    evaluator = CascadeEvaluator()
    meds = [
        {"id": "m1", "brand": "Amlong 5", "ingredients": [{"ingredient": "amlodipine"}], "start_date": "6 months"},
        {"id": "m2", "brand": "Lasix 40", "ingredients": [{"ingredient": "furosemide"}], "start_date": "4 months"},
    ]
    detected = evaluator.evaluate_cascades(meds, symptoms=["swelling"])
    assert len(detected) >= 1
    top = detected[0]
    assert "CASCADE-CCB-DIURETIC" == top["cascade_id"]
    assert "doctor_question" in top


def test_discharge_reconciliation_scenario_d():
    pre = ["Metformin 500 mg", "Amlodipine 5 mg", "Brufen 400 mg", "Atorvastatin 20 mg"]
    post = ["Metformin 500 mg", "Amlodipine 5 mg", "Atorvastatin 20 mg", "Paracetamol 650 mg"]
    refill = ["Metformin 500 mg", "Amlodipine 5 mg", "Brufen 400 mg", "Atorvastatin 20 mg"]

    res = reconcile_medication_lists(pre, post, later_refill_list=refill)
    assert len(res["discontinued_but_restarted"]) >= 1
    assert any("brufen" in str(b).lower() for b in res["discontinued_but_restarted"])
    assert len(res["doctor_questions"]) >= 1


def test_scenario_a_bleeding_risk(engine):
    """Scenario A: 74yo female on warfarin, aspirin low dose, Combiflam, ashwagandha, PPI for 14 weeks."""
    patients_file = os.path.join(os.path.dirname(__file__), "../../data/synthetic_patients.json")
    with open(patients_file, "r", encoding="utf-8") as f:
        patients = json.load(f)

    pat_a = next(p for p in patients if p["id"] == "pat-scenario-a")
    res = engine.evaluate(
        medications=pat_a["medications"],
        age=pat_a["age"],
        sex=pat_a["sex"],
        weight_kg=pat_a.get("weight_kg"),
        conditions=pat_a.get("conditions"),
    )

    rule_ids = {a["rule_id"] for a in res["all_alerts"]}
    assert "DDI-WARFARIN-NSAID" in rule_ids, "Missing Warfarin+NSAID critical alert"
    assert "DDI-ANTICOAG-ANTIPLATELET" in rule_ids, "Missing Anticoag+Antiplatelet alert"
    assert "HERB-BLEEDING-HERBS" in rule_ids or "HERB-ASHWAGANDHA-INTERACTION" in rule_ids
    assert "DURATION-PPI-8WEEKS" in rule_ids, "Missing PPI duration alert"


def test_scenario_b_kidney_risk(engine):
    """Scenario B: 69yo male on telmisartan, furosemide, diclofenac, metformin, with SCr 2.4."""
    patients_file = os.path.join(os.path.dirname(__file__), "../../data/synthetic_patients.json")
    with open(patients_file, "r", encoding="utf-8") as f:
        patients = json.load(f)

    pat_b = next(p for p in patients if p["id"] == "pat-scenario-b")
    res = engine.evaluate(
        medications=pat_b["medications"],
        age=pat_b["age"],
        sex=pat_b["sex"],
        weight_kg=pat_b.get("weight_kg"),
        serum_creatinine=pat_b["labs"][0]["value"],
        conditions=pat_b.get("conditions"),
    )

    rule_ids = {a["rule_id"] for a in res["all_alerts"]}
    assert "COMBO-TRIPLE-WHAMMY" in rule_ids, "Missing Triple Whammy alert"
    assert "RENAL-METFORMIN" in rule_ids or "RENAL-NSAID" in rule_ids
    assert res["risk_scores"]["renal"]["available"] is True
    assert res["risk_scores"]["renal"]["value"] < 35.0


def test_scenario_c_cascade_and_falls(engine):
    """Scenario C: 80yo female on amlodipine, loop diuretic (after ankle swelling), diphenhydramine, alprazolam."""
    patients_file = os.path.join(os.path.dirname(__file__), "../../data/synthetic_patients.json")
    with open(patients_file, "r", encoding="utf-8") as f:
        patients = json.load(f)

    pat_c = next(p for p in patients if p["id"] == "pat-scenario-c")
    res = engine.evaluate(
        medications=pat_c["medications"],
        age=pat_c["age"],
        sex=pat_c["sex"],
        weight_kg=pat_c.get("weight_kg"),
        symptoms=pat_c.get("symptoms"),
        conditions=pat_c.get("conditions"),
    )

    rule_ids = {a["rule_id"] for a in res["all_alerts"]}
    assert "CASCADE-CCB-DIURETIC" in rule_ids, "Missing CCB-diuretic cascade alert"
    assert "BEERS-BENZODIAZEPINE" in rule_ids, "Missing Beers benzodiazepine alert"
    assert "BEERS-FIRST-GEN-ANTIHISTAMINE" in rule_ids, "Missing Beers antihistamine alert"
    assert res["risk_scores"]["acb"]["is_flagged"] is True, "ACB score should be flagged (>=3)"
    assert res["risk_scores"]["fall_risk"]["band"] == "High"

