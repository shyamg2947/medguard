"""
Specialist Panel Agents for Clinical Multi-Agent Deliberation.
Domains:
- Cardiology
- Nephrology
- Geriatrics/Neurology
- GI/Bleeding
Supports single_call (batched free-tier mode) and deterministic fallback.
"""
from typing import Any, Dict, List, Optional, Set
import json
import re
from backend.app.agents.guardrails import validate_specialist_output
from backend.app.privacy.llm_gateway import execute_llm_call

SPECIALIST_DOMAINS = [
    "Cardiology",
    "Nephrology",
    "Geriatrics/Neurology",
    "GI/Bleeding",
]


def run_single_call_specialist_panel(
    patient_profile: Dict[str, Any],
    alerts: List[Dict[str, Any]],
    evidence_chunks: List[Dict[str, Any]],
    session_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Executes all 4 specialists + moderator in ONE batched structured LLM call.
    Minimizes API calls to 1 in free-tier mode (Section 5.2b).
    """
    allowed_alert_ids = {a["rule_id"] for a in alerts} | {a.get("id", "") for a in alerts}
    allowed_evidence_ids = {c["chunk_id"] for c in evidence_chunks} | allowed_alert_ids

    prompt = _build_panel_prompt(patient_profile, alerts, evidence_chunks)

    resp_text, was_cached, fallback_badge = execute_llm_call(
        prompt=prompt,
        template_version="panel-single-call-v1",
        session_id=session_id,
        is_synthetic=patient_profile.get("is_synthetic", True),
    )

    try:
        # Attempt to parse structured JSON from LLM response
        parsed = _parse_llm_json(resp_text)
        specialists = []
        for s_raw in parsed.get("specialists", []):
            validated = validate_specialist_output(s_raw, allowed_alert_ids, allowed_evidence_ids)
            if validated["concerns"]:
                specialists.append(validated)

        if not specialists:
            return generate_deterministic_specialist_panel(alerts, evidence_chunks)

        moderator_data = parsed.get("moderator", {})
        moderator_res = {
            "agreements": moderator_data.get("agreements", []),
            "conflicts": moderator_data.get("conflicts", []),
            "human_decision_needed": bool(moderator_data.get("conflicts", [])) or bool(moderator_data.get("human_decision_needed", False)),
            "top_questions_for_doctor": moderator_data.get("top_questions_for_doctor", [])[:5],
        }

        return {
            "specialists": specialists,
            "moderator": moderator_res,
            "fallback_badge": fallback_badge,
            "was_cached": was_cached,
        }
    except Exception:
        # Graceful deterministic fallback
        return generate_deterministic_specialist_panel(alerts, evidence_chunks)


def generate_deterministic_specialist_panel(
    alerts: List[Dict[str, Any]],
    evidence_chunks: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Deterministic rules-grounded specialist panel when offline or on LLM fallback.
    """
    specialists = []
    chunk_ids = [c["chunk_id"] for c in evidence_chunks]

    for domain in SPECIALIST_DOMAINS:
        domain_alerts = [a for a in alerts if a.get("domain", "") == domain or domain in a.get("domain", "")]
        if not domain_alerts and not alerts:
            continue

        concerns = []
        questions = []
        tradeoffs = []

        for a in (domain_alerts or alerts[:2]):
            concerns.append({
                "alert_id": a["rule_id"],
                "statement": a["mechanism_summary"],
                "evidence_ids": chunk_ids[:2] or a.get("sources", [])[:1],
            })
            questions.append(a["doctor_question"])
            tradeoffs.append(f"Weighing benefits of {a.get('type')} against clinical risk.")

        specialists.append({
            "domain": domain,
            "concerns": concerns,
            "questions_for_doctor": questions[:2],
            "tradeoffs": tradeoffs[:2],
            "confidence": "high",
        })

    # Moderator logic
    conflicts = []
    agreements = []
    cardio_alerts = [a["rule_id"] for a in alerts if "Cardiology" in a.get("domain", "")]
    gi_alerts = [a["rule_id"] for a in alerts if "GI" in a.get("domain", "")]
    nephro_alerts = [a["rule_id"] for a in alerts if "Nephrology" in a.get("domain", "")]

    if cardio_alerts and gi_alerts:
        conflicts.append("Cardiology emphasizes stroke/thromboembolism prevention; GI flags gastrointestinal hemorrhage hazard.")
    if cardio_alerts and nephro_alerts:
        conflicts.append("Cardiology manages arterial pressure control; Nephrology cautions against acute reduction in renal perfusion pressure.")

    top_questions = list({a["doctor_question"] for a in alerts})[:5]

    return {
        "specialists": specialists,
        "moderator": {
            "agreements": ["All specialists agree that ongoing clinical supervision is essential."],
            "conflicts": conflicts,
            "human_decision_needed": bool(conflicts),
            "top_questions_for_doctor": top_questions,
        },
        "fallback_badge": "Verified rule text (AI polish unavailable)",
        "was_cached": False,
    }


def _build_panel_prompt(
    patient_profile: Dict[str, Any],
    alerts: List[Dict[str, Any]],
    evidence_chunks: List[Dict[str, Any]],
) -> str:
    alerts_summary = json.dumps([
        {
            "rule_id": a["rule_id"],
            "severity": a["severity"],
            "domain": a.get("domain"),
            "mechanism": a["mechanism_summary"],
            "sources": a.get("sources", []),
        }
        for a in alerts
    ], indent=2)

    evidence_summary = json.dumps([
        {"chunk_id": c["chunk_id"], "text": c["text"][:200]}
        for c in evidence_chunks[:4]
    ], indent=2)

    return f"""You are the MedGuard Specialty Clinical Deliberation Panel.
Analyze the following patient medication safety profile.
Never give directive advice (do not say stop, start, increase, or switch). Use 'ask your doctor whether'.
Output strict JSON with 'specialists' and 'moderator'.

PATIENT PROFILE:
Age: {patient_profile.get('age')}, Sex: {patient_profile.get('sex')}
Conditions: {patient_profile.get('conditions', [])}

VERIFIED CLINICAL ALERTS:
{alerts_summary}

RETRIEVED GUIDELINE EVIDENCE:
{evidence_summary}

Respond in strict JSON:
{{
  "specialists": [
    {{
      "domain": "Cardiology",
      "concerns": [{{"alert_id": "...", "statement": "...", "evidence_ids": ["..."]}}],
      "questions_for_doctor": ["..."],
      "tradeoffs": ["..."],
      "confidence": "high"
    }}
  ],
  "moderator": {{
    "agreements": ["..."],
    "conflicts": ["..."],
    "human_decision_needed": true,
    "top_questions_for_doctor": ["..."]
  }}
}}
"""


def _parse_llm_json(text: str) -> Dict[str, Any]:
    # Extract JSON between curly braces if surrounded by markdown fences
    m = re.search(r'\{.*\}', text, re.DOTALL)
    if m:
        return json.loads(m.group(0))
    return json.loads(text)
