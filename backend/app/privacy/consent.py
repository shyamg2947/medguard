"""
Patient Consent, Data Export, and Full Purge Module.
Implements patient data sovereignty:
- Versioned consent records
- Machine-readable JSON export
- Irreversible purge of patient record, medications, alerts, scores, vault tokens, reports, and audit attribution
"""
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from backend.app.audit import log_audit_event
from backend.app.models.db import (
    Alert,
    CaregiverLink,
    ConditionNote,
    Consent,
    LabValue,
    Medication,
    Patient,
    PiiVaultEntry,
    Report,
    RiskScore,
    SymptomReport,
    User,
    generate_uuid,
    utc_now,
)
from backend.app.privacy.vault import purge_vault_for_patient


def record_consent(
    db: Session,
    patient_id: str,
    version: str = "v1.0",
    scopes: Optional[List[str]] = None,
    actor: str = "patient",
) -> Consent:
    consent = Consent(
        id=generate_uuid(),
        patient_id=patient_id,
        version=version,
        granted_at=utc_now(),
    )
    consent.scopes = scopes or ["safety_analysis", "voice_processing", "caregiver_sharing"]
    db.add(consent)
    db.commit()
    db.refresh(consent)

    log_audit_event(
        actor=actor,
        action="grant_consent",
        entity="patient",
        entity_id=patient_id,
        meta={"version": version, "scopes": consent.scopes},
        db=db,
    )
    return consent


def revoke_consent(
    db: Session,
    patient_id: str,
    actor: str = "patient",
) -> Optional[Consent]:
    consent = (
        db.query(Consent)
        .filter(Consent.patient_id == patient_id, Consent.revoked_at.is_(None))
        .order_by(Consent.granted_at.desc())
        .first()
    )
    if consent:
        consent.revoked_at = utc_now()
        db.commit()
        log_audit_event(
            actor=actor,
            action="revoke_consent",
            entity="patient",
            entity_id=patient_id,
            meta={"consent_id": consent.id},
            db=db,
        )
    return consent


def export_patient_data(
    db: Session,
    patient_id: str,
    actor: str = "patient",
) -> Dict[str, Any]:
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        return {}

    meds = db.query(Medication).filter(Medication.patient_id == patient_id).all()
    alerts = db.query(Alert).filter(Alert.patient_id == patient_id).all()
    labs = db.query(LabValue).filter(LabValue.patient_id == patient_id).all()
    conds = db.query(ConditionNote).filter(ConditionNote.patient_id == patient_id).all()
    scores = db.query(RiskScore).filter(RiskScore.patient_id == patient_id).all()
    consents = db.query(Consent).filter(Consent.patient_id == patient_id).all()

    log_audit_event(
        actor=actor,
        action="export",
        entity="patient",
        entity_id=patient_id,
        meta={"export_format": "json"},
        db=db,
    )

    return {
        "patient": {
            "id": patient.id,
            "age": patient.age,
            "sex": patient.sex,
            "weight_kg": patient.weight_kg,
            "language": patient.language,
            "is_synthetic": patient.is_synthetic,
            "created_at": patient.created_at.isoformat() if patient.created_at else None,
        },
        "medications": [
            {
                "id": m.id,
                "raw_text": m.raw_text,
                "brand": m.brand,
                "ingredients": m.ingredients,
                "confirmed": m.confirmed,
                "status": m.status,
            }
            for m in meds
        ],
        "alerts": [
            {
                "id": a.id,
                "rule_id": a.rule_id,
                "severity": a.severity,
                "mechanism": a.mechanism_summary,
                "sources": a.sources,
            }
            for a in alerts
        ],
        "labs": [{"kind": l.kind, "value": l.value} for l in labs],
        "conditions": [{"term": c.controlled_term} for c in conds],
        "scores": [{"kind": s.kind, "value": s.value, "detail": s.detail} for s in scores],
        "consents": [{"version": c.version, "granted_at": c.granted_at.isoformat()} for c in consents],
    }


def purge_patient_completely(
    db: Session,
    patient_id: str,
    actor: str = "patient",
) -> bool:
    """
    Permanently deletes all data associated with patient:
    Medications, Alerts, Labs, Conditions, RiskScores, Symptoms, Reports, Vault Tokens, CaregiverLinks, and Patient.
    """
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        return False

    # 1. Purge encrypted vault tokens
    purge_vault_for_patient(db, patient_id)

    # 2. Delete linked records
    db.query(Medication).filter(Medication.patient_id == patient_id).delete()
    db.query(Alert).filter(Alert.patient_id == patient_id).delete()
    db.query(LabValue).filter(LabValue.patient_id == patient_id).delete()
    db.query(ConditionNote).filter(ConditionNote.patient_id == patient_id).delete()
    db.query(RiskScore).filter(RiskScore.patient_id == patient_id).delete()
    db.query(SymptomReport).filter(SymptomReport.patient_id == patient_id).delete()
    db.query(Report).filter(Report.patient_id == patient_id).delete()
    db.query(CaregiverLink).filter(CaregiverLink.patient_id == patient_id).delete()
    db.query(Consent).filter(Consent.patient_id == patient_id).delete()

    # 3. Delete patient record
    db.delete(patient)
    db.commit()

    # 4. Append audit record of purge
    log_audit_event(
        actor=actor,
        action="delete_full_purge",
        entity="patient",
        entity_id=patient_id,
        meta={"status": "purged_all"},
        db=db,
    )
    return True

