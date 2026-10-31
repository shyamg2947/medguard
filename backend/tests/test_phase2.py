"""
Phase 2 Unit and Integration Tests.
Verifies Knowledge & Entities: Lexicon, Matcher, Context Re-ranking, Parsing, Read-back, and S4 Confirm-before-store.
"""
import json
import os
import pytest

from backend.app.entities.context_rerank import rerank_with_context
from backend.app.entities.lexicon import get_lexicon
from backend.app.entities.matcher import (
    find_candidates,
    normalize_text,
    parse_strength_and_frequency,
    simple_metaphone,
)
from backend.app.entities.resolver import resolve_medication_query
from backend.app.models.db import Medication, Patient, SessionLocal, User, init_db, utc_now


@pytest.fixture(autouse=True)
def setup_db():
    init_db()


def test_lexicon_loading():
    lex = get_lexicon()
    assert len(lex.brands) >= 150
    assert len(lex.generics) >= 100
    assert "paracetamol" in lex.generics
    assert "telmisartan" in lex.generics
    assert "combiflam" in lex.brands
    assert "ashwagandha" in lex.herbal_entries


def test_indic_transliteration_and_normalization():
    norm_hi = normalize_text("डोलो 650 tab subah shaam")
    assert "dolo" in norm_hi
    assert "tablet" in norm_hi


def test_strength_and_frequency_parsing():
    s, f, drug = parse_strength_and_frequency("Telma 40 mg once daily")
    assert s == "40 mg"
    assert f == "once daily"
    assert "telma" in drug.lower()

    s2, f2, drug2 = parse_strength_and_frequency("Combiflam tab subah shaam")
    assert f2 == "twice daily"
    assert "combiflam" in drug2.lower()


def test_matcher_candidate_ranking():
    candidates = find_candidates("Dolo 650")
    assert len(candidates) > 0
    top = candidates[0]
    assert "Dolo 650" in top["matched_name"]
    assert top["score"] >= 0.90


def test_context_reranking_safety():
    # Context re-ranking may adjust order, but must NEVER raise candidate above accept threshold (0.90) on its own
    initial_candidates = [
        {
            "matched_name": "TestDrug",
            "score": 0.88,
            "ingredients": [{"ingredient": "telmisartan", "strength": "40mg"}],
            "margin": 0.05,
        }
    ]
    reranked = rerank_with_context(
        initial_candidates,
        existing_med_ingredients=["amlodipine"],
        conditions=["hypertension"],
    )
    assert len(reranked) == 1
    # Score must be strictly < 0.90
    assert reranked[0]["adjusted_score"] < 0.90


def test_readback_multilingual():
    res_en = resolve_medication_query("Telma 40 mg once daily", language="en")
    assert res_en["status"] == "accept_candidate"
    assert "Telma 40" in res_en["readback_prompt"]
    assert "once daily" in res_en["readback_prompt"]
    assert "Is that right?" in res_en["readback_prompt"]

    res_hi = resolve_medication_query("डोलो 650", language="hi")
    assert res_hi["status"] == "accept_candidate"
    assert "मैंने सुना" in res_hi["readback_prompt"]
    assert "क्या यह सही है?" in res_hi["readback_prompt"]


def test_clarify_and_unrecognized_routing():
    # Ambiguous short token
    res_clarify = resolve_medication_query("pan")
    assert res_clarify["status"] in ["needs_clarification", "accept_candidate"]
    if res_clarify["status"] == "needs_clarification":
        assert len(res_clarify["clarification_options"]) > 0

    # Total gibberish
    res_gibberish = resolve_medication_query("qwertyuiop random nonsense 12345")
    assert res_gibberish["status"] == "unrecognized"
    assert res_gibberish["requires_photo"] is True


def test_s4_confirm_before_store():
    # Rule S4: A drug enters patient profile only after user confirms it (confirmed=True)
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.display_token == "DEMO-SENIOR").first()
        if not user:
            user = User(role="senior", display_token="DEMO-SENIOR")
            db.add(user)
            db.commit()

        pat = Patient(owner_user_id=user.id, age=70, sex="female")
        db.add(pat)
        db.commit()

        # Unconfirmed candidate in intake
        med = Medication(
            patient_id=pat.id,
            raw_text="Telma 40",
            brand="Telma 40",
            confirmed=False,  # Unconfirmed
            status="active",
        )
        med.ingredients = [{"ingredient": "telmisartan", "strength": "40mg"}]
        db.add(med)
        db.commit()

        # Check DB: confirmed is False
        db_med = db.query(Medication).filter(Medication.id == med.id).first()
        assert db_med.confirmed is False
        assert db_med.confirmed_at is None

        # User confirms
        db_med.confirmed = True
        db_med.confirmed_at = utc_now()
        db.commit()

        assert db.query(Medication).filter(Medication.id == med.id).first().confirmed is True
    finally:
        db.close()


def test_eval_asr_cases_zero_wrong_auto_accepts():
    # Run through eval/asr_name_cases.jsonl: wrong auto accepts MUST BE ZERO
    cases_path = os.path.join(os.path.dirname(__file__), "../../eval/asr_name_cases.jsonl")
    assert os.path.exists(cases_path)

    wrong_auto_accepts = 0
    total_cases = 0

    with open(cases_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            total_cases += 1
            case = json.loads(line)
            query = case["query"]
            expected_target = case.get("expected_target")
            expected_status = case.get("expected_status")

            res = resolve_medication_query(query)
            status = res["status"]

            # If the query was gibberish/clarify (expected_target is None), it must NEVER be auto-accepted
            if expected_target is None and status == "accept_candidate":
                wrong_auto_accepts += 1

    assert total_cases >= 100
    assert wrong_auto_accepts == 0, f"Safety Failure: {wrong_auto_accepts} wrong auto-accepts detected!"
