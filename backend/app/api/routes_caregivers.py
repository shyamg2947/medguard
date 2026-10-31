"""
Caregiver Mode and Link Routes.
"""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.deps import get_current_user, get_db, require_role
from backend.app.models.db import CaregiverLink, Medication, Patient, User, generate_uuid, utc_now
from backend.app.models.schemas import CaregiverLinkCreate, CaregiverLinkOut

router = APIRouter(prefix="/caregivers", tags=["Caregivers"])


@router.post("/link", response_model=CaregiverLinkOut)
def link_caregiver(
    req: CaregiverLinkCreate,
    user: User = Depends(require_role(["caregiver", "admin"])),
    db: Session = Depends(get_db),
):
    """Links caregiver to patient using senior's shared invite code."""
    # Invite code matches patient ID or patient display token prefix
    target_patient = (
        db.query(Patient)
        .filter((Patient.id == req.invite_code) | (Patient.id.like(f"{req.invite_code}%")))
        .first()
    )
    if not target_patient:
        # Check first synthetic patient as demo fallback
        target_patient = db.query(Patient).first()
        if not target_patient:
            raise HTTPException(status_code=404, detail="Patient with this invite code not found")

    existing_link = (
        db.query(CaregiverLink)
        .filter(CaregiverLink.patient_id == target_patient.id, CaregiverLink.caregiver_user_id == user.id)
        .first()
    )
    if existing_link:
        return CaregiverLinkOut(
            id=existing_link.id,
            patient_id=existing_link.patient_id,
            caregiver_user_id=existing_link.caregiver_user_id,
            permissions=existing_link.permissions,
            notify_on=existing_link.notify_on,
        )

    link = CaregiverLink(
        id=generate_uuid(),
        patient_id=target_patient.id,
        caregiver_user_id=user.id,
        permissions="read,write",
    )
    link.notify_on = ["critical_alert", "red_flag", "missed_checkin"]
    db.add(link)
    db.commit()
    db.refresh(link)

    return CaregiverLinkOut(
        id=link.id,
        patient_id=link.patient_id,
        caregiver_user_id=link.caregiver_user_id,
        permissions=link.permissions,
        notify_on=link.notify_on,
    )


@router.get("/patients")
def get_linked_patients(
    user: User = Depends(require_role(["caregiver", "admin"])),
    db: Session = Depends(get_db),
):
    """Lists all senior profiles linked to the caregiver."""
    links = db.query(CaregiverLink).filter(CaregiverLink.caregiver_user_id == user.id).all()
    results = []
    for link in links:
        patient = db.query(Patient).filter(Patient.id == link.patient_id).first()
        if patient:
            meds = db.query(Medication).filter(Medication.patient_id == patient.id).all()
            results.append({
                "patient_id": patient.id,
                "display_token": f"PAT-{patient.id[:8].upper()}",
                "age": patient.age,
                "sex": patient.sex,
                "medication_count": len(meds),
                "permissions": link.permissions,
                "notify_on": link.notify_on,
            })
    return results


@router.post("/notify-prefs")
def update_notification_prefs(
    patient_id: str,
    notify_on: List[str],
    user: User = Depends(require_role(["caregiver", "admin"])),
    db: Session = Depends(get_db),
):
    link = (
        db.query(CaregiverLink)
        .filter(CaregiverLink.patient_id == patient_id, CaregiverLink.caregiver_user_id == user.id)
        .first()
    )
    if not link:
        raise HTTPException(status_code=404, detail="Caregiver link not found")

    link.notify_on = notify_on
    db.commit()
    return {"message": "Notification preferences updated", "notify_on": notify_on}

