"""
Report Generation and Digital Share Routes.
Implements:
- Plain-language multilingual report endpoint
- One-page Doctor Discussion Guide PDF endpoint
- Compact Emergency Medication Card PDF endpoint
- Signed, expiring share links (/share/{token})
"""
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import json
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from backend.app.config import get_settings
from backend.app.deps import get_current_user, get_db
from backend.app.models.db import Alert, Medication, Patient, Report, RiskScore, User, generate_uuid, utc_now
from backend.app.reports.builder import build_plain_language_report
from backend.app.reports.emergency_card import generate_emergency_card_pdf
from backend.app.reports.guide_pdf import generate_doctor_guide_pdf
from backend.app.rules.engine import ClinicalRulesEngine

router = APIRouter(tags=["Reports"])
rules_engine = ClinicalRulesEngine()


def generate_share_token(patient_id: str, days_valid: int = 7) -> str:
    settings = get_settings()
    expires_at = datetime.now(timezone.utc) + timedelta(days=days_valid)
    payload = f"{patient_id}:{int(expires_at.timestamp())}"
    signature = hmac.new(
        settings.SECRET_KEY.encode(),
        payload.encode(),
        hashlib.sha256,
    ).hexdigest()[:16]
    return f"{payload}:{signature}"


def verify_share_token(token: str) -> Optional[str]:
    """Returns patient_id if token is valid and not expired; else None."""
    settings = get_settings()
    try:
        parts = token.split(":")
        if len(parts) != 3:
            return None
        patient_id, exp_str, signature = parts
        exp_ts = int(exp_str)
        if datetime.now(timezone.utc).timestamp() > exp_ts:
            return None  # Expired

        payload = f"{patient_id}:{exp_str}"
        expected_sig = hmac.new(
            settings.SECRET_KEY.encode(),
            payload.encode(),
            hashlib.sha256,
        ).hexdigest()[:16]

        if hmac.compare_digest(signature, expected_sig):
            return patient_id
        return None
    except Exception:
        return None


@router.get("/patients/{patient_id}/report")
def get_patient_report(
    patient_id: str,
    lang: str = Query("en"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    meds = db.query(Medication).filter(Medication.patient_id == patient_id, Medication.confirmed.is_(True)).all()
    med_dicts = [{"brand": m.brand or m.raw_text, "ingredients": m.ingredients, "start_date": m.start_date} for m in meds]

    analysis = rules_engine.evaluate(
        medications=med_dicts,
        age=patient.age,
        sex=patient.sex,
        weight_kg=patient.weight_kg,
    )
    return build_plain_language_report(analysis, language=lang)


@router.get("/patients/{patient_id}/guide.pdf")
def get_doctor_guide_pdf_route(
    patient_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    meds = db.query(Medication).filter(Medication.patient_id == patient_id, Medication.confirmed.is_(True)).all()
    med_dicts = [
        {"brand": m.brand or m.raw_text, "ingredients": m.ingredients, "start_date": m.start_date, "strength": m.strength_text}
        for m in meds
    ]

    analysis = rules_engine.evaluate(
        medications=med_dicts,
        age=patient.age,
        sex=patient.sex,
        weight_kg=patient.weight_kg,
    )

    share_token = generate_share_token(patient_id, days_valid=7)
    share_url = f"http://localhost:8000/share/{share_token}"

    pdf_bytes = generate_doctor_guide_pdf(
        patient_info={
            "display_token": f"PAT-{patient_id[:8].upper()}",
            "age": patient.age,
            "sex": patient.sex,
            "date": utc_now().strftime("%Y-%m-%d"),
        },
        medications=med_dicts,
        alerts=analysis["all_alerts"],
        risk_scores=analysis["risk_scores"],
        share_url=share_url,
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=Doctor_Discussion_Guide_{patient_id[:8]}.pdf"},
    )


@router.get("/patients/{patient_id}/emergency-card.pdf")
def get_emergency_card_pdf_route(
    patient_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    meds = db.query(Medication).filter(Medication.patient_id == patient_id, Medication.confirmed.is_(True)).all()
    med_dicts = [
        {"brand": m.brand or m.raw_text, "ingredients": m.ingredients, "strength": m.strength_text}
        for m in meds
    ]

    analysis = rules_engine.evaluate(
        medications=med_dicts,
        age=patient.age,
        sex=patient.sex,
        weight_kg=patient.weight_kg,
    )

    # Detect critical flags
    critical_flags = []
    for a in analysis["all_alerts"]:
        if "warfarin" in a.get("rule_id", "").lower() or "anticoag" in a.get("rule_id", "").lower():
            critical_flags.append("ON BLOOD THINNER")
    if analysis["risk_scores"]["fall_risk"]["band"] == "High":
        critical_flags.append("HIGH FALL RISK")

    share_token = generate_share_token(patient_id, days_valid=14)
    share_url = f"http://localhost:8000/share/{share_token}"

    pdf_bytes = generate_emergency_card_pdf(
        patient_info={
            "display_token": f"PAT-{patient_id[:8].upper()}",
            "age": patient.age,
            "sex": patient.sex,
        },
        medications=med_dicts,
        critical_flags=critical_flags,
        share_url=share_url,
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=Emergency_Card_{patient_id[:8]}.pdf"},
    )


@router.get("/share/{token}")
def get_shared_report(token: str, db: Session = Depends(get_db)):
    """Public read-only view accessible via signed expiring token."""
    patient_id = verify_share_token(token)
    if not patient_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="This share link has expired or is invalid.",
        )

    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    meds = db.query(Medication).filter(Medication.patient_id == patient_id, Medication.confirmed.is_(True)).all()
    med_dicts = [{"brand": m.brand or m.raw_text, "ingredients": m.ingredients, "start_date": m.start_date} for m in meds]

    analysis = rules_engine.evaluate(
        medications=med_dicts,
        age=patient.age,
        sex=patient.sex,
        weight_kg=patient.weight_kg,
    )

    return {
        "status": "active_share",
        "patient_token": f"PAT-{patient_id[:8].upper()}",
        "age": patient.age,
        "sex": patient.sex,
        "medications": med_dicts,
        "safety_summary": analysis["summary_sentence"],
        "top_alerts": analysis["top_alerts"],
        "risk_scores": analysis["risk_scores"],
        "disclaimer": analysis["disclaimer"],
    }

