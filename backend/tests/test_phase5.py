"""
Phase 5 Unit and Integration Tests.
Verifies LangGraph Specialty Agent Panel, Moderator, Guardrails, Gated AI Commentary (S8),
Primacy of Rules Engine (S1), and Directive Language Rewriting (S2).
"""
import pytest

from backend.app.agents.graph import compute_panel_cache_key, run_specialty_agent_panel, should_trigger_panel
from backend.app.agents.guardrails import sanitize_directive_text, validate_specialist_output
from backend.app.agents.moderator import Moderator


def test_guardrails_sanitize_directive_phrasing_s2():
    """Rule S2: Output never orders a patient to stop, start, increase, or switch medications."""
    directive_input = "You must stop taking your painkiller immediately and switch ibuprofen to paracetamol."
    sanitized = sanitize_directive_text(directive_input)
    assert "stop" not in sanitized.lower() or "ask your doctor" in sanitized.lower()
    assert "switch" not in sanitized.lower() or "discuss" in sanitized.lower() or "transition" in sanitized.lower()


def test_guardrails_drop_fabricated_alerts_s1():
    """Rule S1: LLM agents may add commentary, NEVER new alerts."""
    allowed_alerts = {"DDI-WARFARIN-NSAID"}
    allowed_evidence = {"DOC-BEERS-2023"}

    raw_specialist_data = {
        "domain": "Cardiology",
        "concerns": [
            {
                "alert_id": "DDI-WARFARIN-NSAID",
                "statement": "Elevated hemorrhage risk with concurrent anticoagulant and NSAID.",
                "evidence_ids": ["DOC-BEERS-2023"],
            },
            {
                "alert_id": "FABRICATED-ALERT-HALLUCINATION",
                "statement": "This drug combination was invented by LLM.",
                "evidence_ids": ["DOC-BEERS-2023"],
            },
        ],
        "questions_for_doctor": ["Can we reconsider this regimen?"],
    }

    validated = validate_specialist_output(raw_specialist_data, allowed_alerts, allowed_evidence)
    alert_ids = [c["alert_id"] for c in validated["concerns"]]
    assert "DDI-WARFARIN-NSAID" in alert_ids
    assert "FABRICATED-ALERT-HALLUCINATION" not in alert_ids, "Hallucinated alert was not pruned!"


def test_guardrails_drop_uncited_claims_s3():
    """Rule S3: Claims lacking valid citations are dropped."""
    allowed_alerts = {"DDI-WARFARIN-NSAID"}
    allowed_evidence = {"DOC-BEERS-2023"}

    raw_specialist_data = {
        "domain": "Nephrology",
        "concerns": [
            {
                "alert_id": "DDI-WARFARIN-NSAID",
                "statement": "Unreferenced claim without evidence.",
                "evidence_ids": ["NON-EXISTENT-EVIDENCE-ID"],
            }
        ],
    }

    validated = validate_specialist_output(raw_specialist_data, allowed_alerts, allowed_evidence)
    # The invalid evidence ID must not be accepted
    assert len(validated["concerns"]) == 0 or validated["concerns"][0]["evidence_ids"] != ["NON-EXISTENT-EVIDENCE-ID"]


def test_panel_trigger_condition():
    # 1. Clean list or low severity single domain -> Should NOT trigger
    low_alerts = [{"rule_id": "LOW-ALERT", "severity": "low", "domain": "General"}]
    assert should_trigger_panel(low_alerts) is False

    # 2. Moderate or High severity -> MUST trigger
    mod_alerts = [{"rule_id": "MOD-ALERT", "severity": "moderate", "domain": "Cardiology"}]
    assert should_trigger_panel(mod_alerts) is True

    # 3. Two different domains -> MUST trigger
    multi_domain = [
        {"rule_id": "R1", "severity": "low", "domain": "Cardiology"},
        {"rule_id": "R2", "severity": "low", "domain": "Nephrology"},
    ]
    assert should_trigger_panel(multi_domain) is True


def test_moderator_neutrality_and_conflicts():
    moderator = Moderator()
    specialists = [
        {
            "domain": "Cardiology",
            "questions_for_doctor": ["Is anticoagulation intensity optimal?"],
        },
        {
            "domain": "GI/Bleeding",
            "questions_for_doctor": ["Should gastroprotection be added?"],
        },
    ]
    alerts = [{"rule_id": "DDI-WARFARIN-NSAID", "doctor_question": "Can we switch to paracetamol?"}]

    synthesis = moderator.synthesize(specialists, alerts)
    assert synthesis["human_decision_needed"] is True
    assert len(synthesis["conflicts"]) >= 1
    assert "Cardiology" in synthesis["conflicts"][0]
    assert "GI" in synthesis["conflicts"][0]
    # Deduplicated doctor questions capped at 5
    assert len(synthesis["top_questions_for_doctor"]) <= 5


def test_panel_run_gated_by_default_s8():
    """Rule S8: Panel commentary is strictly gated (approved_for_patient=False) by default."""
    pat_profile = {"id": "pat-test", "age": 75, "sex": "male", "is_synthetic": True}
    alerts = [
        {
            "rule_id": "DDI-WARFARIN-NSAID",
            "severity": "critical",
            "domain": "Cardiology",
            "mechanism_summary": "High bleeding risk with anticoagulant + NSAID",
            "doctor_question": "Can we discontinue the NSAID?",
            "sources": ["FDA Warfarin Label"],
        }
    ]

    result = run_specialty_agent_panel(pat_profile, alerts)
    assert result is not None
    assert result["approved_for_patient"] is False
    assert len(result["specialists"]) > 0
    assert result["moderator"]["human_decision_needed"] is True or len(result["moderator"]["top_questions_for_doctor"]) > 0

