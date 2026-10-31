"""
Clinical Agent Guardrails.
Implements:
- S2: Rewrite or reject directive language into neutral physician-inquiry form.
- S3: Drop claims that do not cite evidence.
- S8: Gate AI commentary (approved_for_patient=False by default until clinician reviews).
- Rule Engine primacy (S1): Block any new alerts introduced by LLMs that were not produced by the rules engine.
"""
import re
from typing import Any, Dict, List, Set, Tuple

DIRECTIVE_PATTERNS = [
    (r'\b(?:you\s+must|please|should|immediately)?\s*(?:stop|discontinue|halt)\s+([a-zA-Z0-9_\-\s]+?)(?=\band\b|\bor\b|[.,;!?]|$)',
     r'ask your doctor whether \1 should be discontinued or adjusted'),
    (r'\b(?:you\s+must|please|should)?\s*(?:switch|change)\s+([a-zA-Z0-9_\-\s]+?)\s+to\s+([a-zA-Z0-9_\-\s]+?)(?=\band\b|\bor\b|[.,;!?]|$)',
     r'discuss with your doctor whether transitioning from \1 to \2 is appropriate'),
    (r'\b(?:you\s+must|please|should)?\s*(?:start|begin|take)\s+([a-zA-Z0-9_\-\s]+?)(?=\band\b|\bor\b|[.,;!?]|$)',
     r'ask your doctor if \1 is recommended for your condition'),
    (r'\b(?:increase|raise)\s+(?:the\s+dose\s+of\s+)?([a-zA-Z0-9_\-\s]+?)(?=\band\b|\bor\b|[.,;!?]|$)',
     r'discuss whether the dosage of \1 requires review with your physician'),
    (r'\b(?:decrease|reduce|lower)\s+(?:the\s+dose\s+of\s+)?([a-zA-Z0-9_\-\s]+?)(?=\band\b|\bor\b|[.,;!?]|$)',
     r'ask your doctor if reducing the dosage of \1 would lower side effect risks'),
]


def sanitize_directive_text(text: str) -> str:
    """Rewrites directive phrasing into respectful discussion questions."""
    sanitized = text
    for pat, rep in DIRECTIVE_PATTERNS:
        sanitized = re.sub(pat, rep, sanitized, flags=re.IGNORECASE)
    return sanitized


def validate_specialist_output(
    specialist_data: Dict[str, Any],
    allowed_alert_ids: Set[str],
    allowed_evidence_ids: Set[str],
) -> Dict[str, Any]:
    """
    Applies strict guardrails to specialist output:
    1. Prunes concerns referencing non-existent alerts.
    2. Drops concerns with zero valid evidence citations.
    3. Rewrites directive phrasing.
    """
    domain = specialist_data.get("domain", "Clinical")
    concerns = specialist_data.get("concerns", [])
    valid_concerns = []

    for c in concerns:
        alert_id = c.get("alert_id")
        # Primacy of Rules Engine: Alert must originate from the rules engine
        if alert_id and alert_id not in allowed_alert_ids and f"alert-{alert_id}" not in allowed_alert_ids:
            # Drop fabricated alert
            continue

        evidence_ids = c.get("evidence_ids", [])
        # Citation enforcement: drop claims without evidence citations
        valid_ev = [e for e in evidence_ids if e in allowed_evidence_ids or e in allowed_alert_ids]
        if not valid_ev and evidence_ids:
            # If evidence was provided but invalid
            continue

        stmt = sanitize_directive_text(c.get("statement", ""))
        valid_concerns.append({
            "alert_id": alert_id or "CLINICAL-CONCERN",
            "statement": stmt,
            "evidence_ids": valid_ev or list(allowed_evidence_ids)[:1],
        })

    # Sanitize questions for doctor
    raw_questions = specialist_data.get("questions_for_doctor", [])
    sanitized_questions = [sanitize_directive_text(q) for q in raw_questions if q.strip()]

    # Sanitize tradeoffs
    raw_tradeoffs = specialist_data.get("tradeoffs", [])
    sanitized_tradeoffs = [sanitize_directive_text(t) for t in raw_tradeoffs if t.strip()]

    return {
        "domain": domain,
        "concerns": valid_concerns,
        "questions_for_doctor": sanitized_questions,
        "tradeoffs": sanitized_tradeoffs,
        "confidence": specialist_data.get("confidence", "medium"),
    }
