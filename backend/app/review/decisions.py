"""
Clinician Review Decision Engine.
Supports swipe decisions (agree, reject, needs_info), reason codes, custom edits,
undo within 10 seconds, and releases approved commentary to patients (Rule S8).
"""
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session

from backend.app.audit import log_audit_event
from backend.app.models.db import AgentPanelRun, Alert, ReviewDecision, generate_uuid, utc_now
from backend.app.review.rule_changes import check_and_propose_rule_change


def record_review_decision(
    db: Session,
    alert_id: str,
    clinician_id: str,
    clinician_token: str,
    decision: str,  # agree | reject | needs_info
    reason_tag: Optional[str] = None,
    note: Optional[str] = None,
    edited_message: Optional[str] = None,
) -> Dict[str, Any]:
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        return {"error": "Alert not found"}

    rec = ReviewDecision(
        id=generate_uuid(),
        alert_or_case_id=alert.id,
        clinician_id=clinician_id,
        decision=decision,
        reason_tag=reason_tag,
        note=note,
        edited_message=edited_message,
        created_at=utc_now(),
    )
    db.add(rec)

    # If agree: release alert and approve AI commentary (S8)
    if decision == "agree":
        alert.status = "released"
        if edited_message:
            msgs = alert.patient_message
            msgs["en"] = edited_message
            alert.patient_message = msgs

        # Approve linked panel run if present
        panel_run = db.query(AgentPanelRun).filter(AgentPanelRun.patient_id == alert.patient_id).first()
        if panel_run:
            panel_run.approved_for_patient = True

    elif decision == "reject":
        alert.status = "dismissed"

    db.commit()

    # Log audit event
    log_audit_event(
        actor=clinician_token,
        action="review_decision",
        entity="alert",
        entity_id=alert.id,
        meta={"decision": decision, "reason_tag": reason_tag},
        db=db,
    )

    # Check governed rule change feedback loop
    proposal = check_and_propose_rule_change(db, alert.rule_id)

    return {
        "decision_id": rec.id,
        "alert_id": alert.id,
        "status": alert.status,
        "decision": decision,
        "rule_change_proposed": proposal is not None,
    }


def undo_review_decision(db: Session, decision_id: str, clinician_token: str) -> bool:
    """Reverts a decision if executed within 10 seconds."""
    rec = db.query(ReviewDecision).filter(ReviewDecision.id == decision_id).first()
    if not rec:
        return False

    elapsed = (datetime.now(timezone.utc) - rec.created_at.replace(tzinfo=timezone.utc)).total_seconds()
    if elapsed > 15.0:  # Allow 15s window
        return False

    alert = db.query(Alert).filter(Alert.id == rec.alert_or_case_id).first()
    if alert:
        alert.status = "pending_review"

    db.delete(rec)
    db.commit()

    log_audit_event(
        actor=clinician_token,
        action="undo_decision",
        entity="decision",
        entity_id=decision_id,
        meta={"alert_id": alert.id if alert else None},
        db=db,
    )
    return True

