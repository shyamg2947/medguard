"""
Monitoring, Symptom Reporting, and Fast-Forward Demo Clock Routes.
"""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.deps import get_current_user, get_db
from backend.app.models.db import Medication, Patient, SymptomReport, User, generate_uuid, utc_now
from backend.app.models.schemas import SymptomReportCreate, SymptomReportOut
from backend.app.monitoring.checkins import cancel_patient_checkin, fast_forward_demo_clock, get_current_time, schedule_patient_checkin
from backend.app.monitoring.symptoms import analyze_symptom

router = APIRouter(tags=["Monitoring"])


class CheckinScheduleRequest(BaseModel):
    day_of_week: str = "Sunday"
    time_str: str = "10:00"
    channel: str = "simulator"


@router.post("/patients/{patient_id}/symptoms", response_model=SymptomReportOut)
def report_symptom(
    patient_id: str,
    req: SymptomReportCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    meds = db.query(Medication).filter(Medication.patient_id == patient_id, Medication.confirmed.is_(True)).all()
    med_dicts = [{"id": m.id, "brand": m.brand or m.raw_text, "ingredients": m.ingredients} for m in meds]

    symptom_text = req.raw_text or req.controlled_symptom
    analysis = analyze_symptom(symptom_text, med_dicts)

    report_db = SymptomReport(
        id=generate_uuid(),
        patient_id=patient_id,
        controlled_symptom=analysis["controlled_symptom"],
        severity=req.severity,
        raw_text=symptom_text,
        is_red_flag=analysis["is_red_flag"],
        reported_at=utc_now(),
    )
    report_db.suspect_med_ids = analysis["suspect_med_ids"]
    db.add(report_db)
    db.commit()
    db.refresh(report_db)

    return SymptomReportOut(
        id=report_db.id,
        patient_id=report_db.patient_id,
        controlled_symptom=report_db.controlled_symptom,
        severity=report_db.severity,
        suspect_med_ids=report_db.suspect_med_ids,
        is_red_flag=report_db.is_red_flag,
        reported_at=report_db.reported_at,
    )


@router.get("/patients/{patient_id}/checkins")
def list_symptom_checkins(
    patient_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    reports = (
        db.query(SymptomReport)
        .filter(SymptomReport.patient_id == patient_id)
        .order_by(SymptomReport.reported_at.desc())
        .all()
    )
    return [
        {
            "id": r.id,
            "controlled_symptom": r.controlled_symptom,
            "severity": r.severity,
            "raw_text": r.raw_text,
            "is_red_flag": r.is_red_flag,
            "suspect_med_ids": r.suspect_med_ids,
            "reported_at": r.reported_at.isoformat(),
        }
        for r in reports
    ]


@router.post("/patients/{patient_id}/checkins/schedule")
def schedule_checkin_route(
    patient_id: str,
    req: CheckinScheduleRequest,
    user: User = Depends(get_current_user),
):
    sched = schedule_patient_checkin(
        patient_id=patient_id,
        day_of_week=req.day_of_week,
        time_str=req.time_str,
        channel=req.channel,
    )
    return {"message": "Check-in scheduled", "schedule": sched}


@router.delete("/patients/{patient_id}/checkins/schedule")
def cancel_checkin_route(patient_id: str, user: User = Depends(get_current_user)):
    cancelled = cancel_patient_checkin(patient_id)
    return {"cancelled": cancelled}


@router.post("/demo/clock/fast-forward")
def fast_forward_clock_route(days: int = 7):
    """Demo helper: advances simulated clock to trigger scheduled check-ins."""
    new_time = fast_forward_demo_clock(days)
    return {"simulated_time": new_time.isoformat(), "offset_days_added": days}

