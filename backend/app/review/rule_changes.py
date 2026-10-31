"""
Governed Feedback Loop for Rule Evolution.
Aggregates clinician review decisions per rule.
When a rule gets repeated rejections (default: 5 decisions, >= 60% rejected),
automatically creates a RuleChangeProposal for administrative and clinical lead governance.
CRITICAL: Nothing updates rules or models automatically without explicit human sign-off.
"""
from typing import Any, Dict, List, Optional
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.app.config import get_settings
from backend.app.models.db import ReviewDecision, RuleChangeProposal, generate_uuid, utc_now


def check_and_propose_rule_change(db: Session, rule_id: str) -> Optional[RuleChangeProposal]:
    """
    Evaluates historical clinician decisions for a given rule_id.
    Triggers proposal if >= RULE_CHANGE_MIN_DECISIONS and reject_rate >= RULE_CHANGE_REJECT_RATE.
    """
    settings = get_settings()
    min_decisions = settings.RULE_CHANGE_MIN_DECISIONS
    reject_threshold = settings.RULE_CHANGE_REJECT_RATE

    decisions = (
        db.query(ReviewDecision)
        .filter(ReviewDecision.alert_or_case_id.like(f"%{rule_id}%"))
        .all()
    )

    if len(decisions) < min_decisions:
        return None

    rejections = [d for d in decisions if d.decision == "reject"]
    reject_rate = len(rejections) / float(len(decisions))

    if reject_rate >= reject_threshold:
        # Check if an open proposal already exists
        existing = (
            db.query(RuleChangeProposal)
            .filter(RuleChangeProposal.rule_id == rule_id, RuleChangeProposal.status == "open")
            .first()
        )
        if existing:
            return existing

        # Aggregate reason tags
        reason_counts: Dict[str, int] = {}
        for r in rejections:
            tag = r.reason_tag or "unspecified"
            reason_counts[tag] = reason_counts.get(tag, 0) + 1

        top_reason = max(reason_counts.items(), key=lambda x: x[1])[0]

        proposal = RuleChangeProposal(
            id=generate_uuid(),
            rule_id=rule_id,
            proposed_change=f"Review rule thresholds or specificity for '{rule_id}' due to {reject_rate*100:.1f}% rejection rate. Top reason: {top_reason}.",
            justification=f"Clinicians rejected {len(rejections)} of {len(decisions)} reviews. Feedback reasons: {reason_counts}",
            status="open",
            created_at=utc_now(),
        )
        proposal.source_decisions = [d.id for d in rejections]
        db.add(proposal)
        db.commit()
        db.refresh(proposal)
        return proposal

    return None

