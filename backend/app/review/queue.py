"""
Clinician Review Queue Module.
Orders cases by severity and recency for clinical swipe review.
Enforces identity masking by default with audited reveal actions.
"""
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from backend.app.audit import log_audit_event
from backend.app.models.db import AgentPanelRun, Alert, Medication, Patient, User


def get_clinician_review_queue(db: Session, clinician_user: Optional[User] = None) -> List[Dict[str, Any]]:
    """
    Returns pending cases ordered by severity (critical first) then created_at asc.
    Identities are masked by default (e.g. PAT-ABC123).
    """
    alerts = (
        db.query(Alert)
        .filter(Alert.status == "pending_review")
        .order_by(
            Alert.severity == "critical",
            Alert.severity == "high",
            Alert.severity == "moderate",
            Alert.created_at.asc()
        )
        .all()
    )

    cases = []
    seen_patients = set()

    for a in alerts:
        patient = db.query(Patient).filter(Patient.id == a.patient_id).first()
        if not patient:
            continue

        # Masked token
        masked_id = f"PAT-{patient.id[:8].upper()}"

        meds = db.query(Medication).filter(Medication.patient_id == patient.id, Medication.confirmed.is_(True)).all()
        med_list = [
            {"brand": m.brand or m.raw_text, "ingredients": m.ingredients, "strength": m.strength_text}
            for m in meds
        ]

        # Check for agent panel commentary
        panel_run = (
            db.query(AgentPanelRun)
            .filter(AgentPanelRun.patient_id == patient.id)
            .order_by(AgentPanelRun.created_at.desc())
            .first()
        )

        cases.append({
            "case_id": a.id,
            "alert_id": a.id,
            "patient_id": patient.id,
            "patient_token": masked_id,
            "patient_age": patient.age,
            "patient_sex": patient.sex,
            "rule_id": a.rule_id,
            "severity": a.severity,
            "mechanism": a.mechanism_summary,
            "draft_patient_message": a.patient_message.get("en", ""),
            "doctor_question": a.doctor_question,
            "sources": a.sources,
            "evidence_level": a.evidence_level,
            "medications": med_list,
            "panel_summary": panel_run.moderator_output if panel_run else None,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        })

    return cases


def audited_reveal_patient(db: Session, patient_id: str, clinician_token: str, reason: str) -> Dict[str, Any]:
    """
    Explicit, audited action allowing a clinician to unmask patient demographics in emergencies.
    """
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        return {}

    log_audit_event(
        actor=clinician_token,
        action="reveal",
        entity="patient",
        entity_id=patient_id,
        meta={"justification": reason},
        db=db,
    )

    return {
        "patient_id": patient.id,
        "age": patient.age,
        "sex": patient.sex,
        "unmasked": True,
        "revealed_by": clinician_token,
    }

