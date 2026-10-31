"""
Clinician Review & Governance Routes.
"""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.deps import get_current_user, get_db, require_role
from backend.app.models.db import Alert, User
from backend.app.models.schemas import ReviewDecisionCreate
from backend.app.review.decisions import record_review_decision, undo_review_decision
from backend.app.review.queue import audited_reveal_patient, get_clinician_review_queue

router = APIRouter(prefix="/review", tags=["Clinician Review"])


@router.get("/queue")
def get_queue(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Fetches queue of pending cases sorted by clinical severity."""
    return get_clinician_review_queue(db, clinician_user=user)


@router.post("/{alert_id}/decision")
def post_decision(
    alert_id: str,
    req: ReviewDecisionCreate,
    user: User = Depends(require_role(["clinician", "admin"])),
    db: Session = Depends(get_db),
):
    """Submits a swipe decision: agree, reject, or needs_info with mandatory reason tag on reject."""
    if req.decision in ["reject", "needs_info"] and not req.reason_tag:
        raise HTTPException(
            status_code=400,
            detail="A reason_tag is mandatory when rejecting or requesting more info.",
        )

    res = record_review_decision(
        db=db,
        alert_id=alert_id,
        clinician_id=user.id,
        clinician_token=user.display_token,
        decision=req.decision,
        reason_tag=req.reason_tag,
        note=req.note,
        edited_message=req.edited_message,
    )
    if "error" in res:
        raise HTTPException(status_code=404, detail=res["error"])
    return res


@router.post("/{decision_id}/undo")
def undo_decision(
    decision_id: str,
    user: User = Depends(require_role(["clinician", "admin"])),
    db: Session = Depends(get_db),
):
    """Reverts a decision within the 10-second window."""
    ok = undo_review_decision(db, decision_id, clinician_token=user.display_token)
    if not ok:
        raise HTTPException(
            status_code=400,
            detail="Undo window expired (10s limit) or decision not found.",
        )
    return {"message": "Decision successfully undone"}


@router.post("/{patient_id}/reveal")
def reveal_patient_identity(
    patient_id: str,
    reason: str = Query(..., min_length=5),
    user: User = Depends(require_role(["clinician", "admin"])),
    db: Session = Depends(get_db),
):
    """Audited unmasking of patient identification."""
    res = audited_reveal_patient(db, patient_id, clinician_token=user.display_token, reason=reason)
    if not res:
        raise HTTPException(status_code=404, detail="Patient not found")
    return res

