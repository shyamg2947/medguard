"""
Patient and Clinical Core Routes.
Implements patient management, medication intake/confirmation, safety analysis, and export/purge.
"""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.agents.graph import run_specialty_agent_panel
from backend.app.audit import log_audit_event
from backend.app.deps import get_current_user, get_db
from backend.app.entities.resolver import resolve_medication_query
from backend.app.models.db import (
    AgentPanelRun,
    Alert,
    ConditionNote,
    LabValue,
    Medication,
    Patient,
    RiskScore,
    User,
    generate_uuid,
    utc_now,
)
from backend.app.models.schemas import (
    AnalysisResult,
    MedicationCandidate,
    MedicationConfirmRequest,
    MedicationOut,
    PatientCreate,
    PatientOut,
    ReconcileRequest,
    ReconcileResult,
)
from backend.app.privacy.consent import export_patient_data, purge_patient_completely, record_consent, revoke_consent
from backend.app.rules.engine import ClinicalRulesEngine
from backend.app.rules.reconcile import reconcile_medication_lists

router = APIRouter(prefix="/patients", tags=["Patients"])
rules_engine = ClinicalRulesEngine()


@router.post("", response_model=PatientOut)
def create_patient(
    req: PatientCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    owner_id = req.owner_user_id or user.id
    patient = Patient(
        id=generate_uuid(),
        owner_user_id=owner_id,
        is_synthetic=req.is_synthetic,
        age=req.age,
        sex=req.sex,
        weight_kg=req.weight_kg,
        height_cm=req.height_cm,
        language=req.language,
        consent_version="v1.0",
        created_at=utc_now(),
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)

    # Automatically record baseline consent
    record_consent(db, patient.id, version="v1.0", actor=user.display_token)
    return PatientOut.model_validate(patient)


@router.get("/{patient_id}", response_model=PatientOut)
def get_patient(
    patient_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return PatientOut.model_validate(patient)


@router.delete("/{patient_id}")
def delete_patient_full_purge(
    patient_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    purged = purge_patient_completely(db, patient_id, actor=user.display_token)
    if not purged:
        raise HTTPException(status_code=404, detail="Patient not found")
    return {"message": "Patient data purged completely from all systems", "patient_id": patient_id}


@router.get("/{patient_id}/export")
def export_data(
    patient_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data = export_patient_data(db, patient_id, actor=user.display_token)
    if not data:
        raise HTTPException(status_code=404, detail="Patient not found")
    return data


@router.post("/{patient_id}/consent")
def grant_consent_route(
    patient_id: str,
    version: str = "v1.0",
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    c = record_consent(db, patient_id, version=version, actor=user.display_token)
    return {"message": "Consent recorded", "consent_id": c.id}


@router.delete("/{patient_id}/consent")
def revoke_consent_route(
    patient_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    c = revoke_consent(db, patient_id, actor=user.display_token)
    if not c:
        raise HTTPException(status_code=404, detail="Active consent not found")
    return {"message": "Consent revoked"}


# Medications
@router.post("/{patient_id}/medications/intake")
def intake_medication(
    patient_id: str,
    query_text: str,
    asr_confidence: float = 1.0,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    existing_meds = db.query(Medication).filter(Medication.patient_id == patient_id, Medication.confirmed.is_(True)).all()
    existing_ings = []
    for m in existing_meds:
        for ing in m.ingredients:
            existing_ings.append(ing.get("ingredient"))

    conds = [c.controlled_term for c in patient.conditions]

    res = resolve_medication_query(
        raw_text=query_text,
        asr_confidence=asr_confidence,
        existing_med_ingredients=existing_ings,
        patient_age=patient.age,
        conditions=conds,
        language=patient.language,
    )
    return res


@router.post("/{patient_id}/medications/confirm", response_model=MedicationOut)
def confirm_medication(
    patient_id: str,
    req: MedicationConfirmRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    med = Medication(
        id=generate_uuid(),
        patient_id=patient_id,
        raw_text=req.raw_text,
        brand=req.brand,
        strength_text=req.strength_text,
        frequency_text=req.frequency_text,
        category=req.category,
        source=req.source,
        confidence=1.0,
        confirmed=req.confirmed,
        confirmed_at=utc_now() if req.confirmed else None,
        start_date=req.start_date,
        status="active",
        created_at=utc_now(),
    )
    med.ingredients = [i.model_dump() for i in req.ingredients]
    db.add(med)
    db.commit()
    db.refresh(med)

    log_audit_event(
        actor=user.display_token,
        action="confirm_medication",
        entity="medication",
        entity_id=med.id,
        meta={"brand": med.brand, "ingredients": med.ingredients_json},
        db=db,
    )
    return MedicationOut.model_validate(med)


@router.get("/{patient_id}/medications", response_model=List[MedicationOut])
def list_medications(
    patient_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    meds = db.query(Medication).filter(Medication.patient_id == patient_id).all()
    return [MedicationOut.model_validate(m) for m in meds]


@router.delete("/{patient_id}/medications/{med_id}")
def delete_medication(
    patient_id: str,
    med_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    med = db.query(Medication).filter(Medication.id == med_id, Medication.patient_id == patient_id).first()
    if not med:
        raise HTTPException(status_code=404, detail="Medication not found")
    db.delete(med)
    db.commit()
    return {"message": "Medication removed", "id": med_id}


# Labs & Conditions
@router.post("/{patient_id}/labs")
def add_lab_value(
    patient_id: str,
    kind: str,
    value: float,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    lab = LabValue(
        id=generate_uuid(),
        patient_id=patient_id,
        kind=kind,
        value=value,
        measured_at=utc_now(),
    )
    db.add(lab)
    db.commit()
    return {"message": "Lab value added", "id": lab.id}


@router.post("/{patient_id}/conditions")
def add_condition(
    patient_id: str,
    controlled_term: str,
    free_text: Optional[str] = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cond = ConditionNote(
        id=generate_uuid(),
        patient_id=patient_id,
        controlled_term=controlled_term,
        free_text=free_text,
    )
    db.add(cond)
    db.commit()
    return {"message": "Condition added", "id": cond.id}


# Safety Analysis
@router.post("/{patient_id}/analyze", response_model=AnalysisResult)
def analyze_patient_safety(
    patient_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    confirmed_meds = db.query(Medication).filter(
        Medication.patient_id == patient_id,
        Medication.confirmed.is_(True),
        Medication.status == "active",
    ).all()

    med_dicts = []
    for m in confirmed_meds:
        med_dicts.append({
            "id": m.id,
            "brand": m.brand or m.raw_text,
            "ingredients": m.ingredients,
            "start_date": m.start_date,
            "category": m.category,
        })

    # Fetch labs
    scr = None
    egfr = None
    for lab in patient.labs:
        if "creatinine" in lab.kind:
            scr = lab.value
        elif "egfr" in lab.kind:
            egfr = lab.value

    conditions = [c.controlled_term for c in patient.conditions]

    res = rules_engine.evaluate(
        medications=med_dicts,
        age=patient.age,
        sex=patient.sex,
        weight_kg=patient.weight_kg,
        serum_creatinine=scr,
        egfr=egfr,
        conditions=conditions,
    )

    # Persist alerts to DB
    for a in res["all_alerts"]:
        existing = db.query(Alert).filter(Alert.patient_id == patient_id, Alert.rule_id == a["rule_id"]).first()
        if not existing:
            alert_db = Alert(
                id=generate_uuid(),
                patient_id=patient_id,
                rule_id=a["rule_id"],
                rule_version=a.get("rule_version", 1),
                severity=a["severity"],
                type=a["type"],
                mechanism_summary=a["mechanism_summary"],
                doctor_question=a["doctor_question"],
                evidence_level=a["evidence_level"],
                status="pending_review" if a["severity"] != "critical" else "released",
                created_at=utc_now(),
            )
            alert_db.involved_med_ids = a.get("involved_med_ids", [])
            alert_db.patient_message = a.get("patient_message", {})
            alert_db.sources = a.get("sources", [])
            db.add(alert_db)

    # Persist risk scores
    for kind, score_obj in res["risk_scores"].items():
        if score_obj.get("available", True):
            val = score_obj.get("value") or score_obj.get("score") or score_obj.get("count") or 0.0
            r_db = RiskScore(
                id=generate_uuid(),
                patient_id=patient_id,
                kind=kind,
                value=float(val),
                computed_at=utc_now(),
            )
            r_db.detail = score_obj
            db.add(r_db)

    # Agent Panel Deliberation (Runs only on moderate+ severity or multi-domain alerts)
    panel_run = None
    pat_profile = {
        "id": patient.id,
        "age": patient.age,
        "sex": patient.sex,
        "conditions": conditions,
        "is_synthetic": patient.is_synthetic,
    }
    panel_result = run_specialty_agent_panel(pat_profile, res["all_alerts"])
    if panel_result:
        panel_run_db = AgentPanelRun(
            id=generate_uuid(),
            patient_id=patient_id,
            alert_ids_json=str([a["rule_id"] for a in res["all_alerts"]]),
            approved_for_patient=False,  # S8 Gate
            created_at=utc_now(),
        )
        panel_run = panel_result

    db.commit()

    return AnalysisResult(
        patient_id=patient_id,
        critical_alerts=res["critical_alerts"],
        top_alerts=res["top_alerts"],
        other_alerts=res["other_alerts"],
        all_alerts=res["all_alerts"],
        risk_scores=res["risk_scores"],
        cascades=res["cascades"],
        panel_commentary=panel_run,
        ai_commentary_gated=True,
        ai_fallback_badge=panel_run.get("fallback_badge") if panel_run else None,
        summary_sentence=res["summary_sentence"],
        data_limitations=res["data_limitations"],
        disclaimer=res["disclaimer"],
    )


@router.post("/reconcile", response_model=ReconcileResult)
def reconcile_lists(req: ReconcileRequest):
    res = reconcile_medication_lists(
        pre_admission_list=req.pre_admission_meds,
        post_discharge_list=req.post_discharge_meds,
    )
    return ReconcileResult.model_validate(res)
