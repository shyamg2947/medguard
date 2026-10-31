"""
Admin and Clinical Lead Governance Routes.
"""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.deps import get_current_user, get_db, require_role
from backend.app.models.db import RuleChangeProposal, RuleVersion, User, generate_uuid, utc_now
from backend.app.models.schemas import RuleChangeProposalOut
from backend.app.privacy.llm_gateway import get_llm_usage_summary
from backend.app.rules.loader import load_rules

router = APIRouter(prefix="/admin", tags=["Admin & Governance"])


@router.get("/usage")
def get_usage(
    user: User = Depends(require_role(["admin", "clinician"])),
    db: Session = Depends(get_db),
):
    """Admin LLM usage meter showing daily quota, calls remaining, and cache stats."""
    return get_llm_usage_summary(db)


@router.get("/rule-proposals", response_model=List[RuleChangeProposalOut])
def get_rule_proposals(
    user: User = Depends(require_role(["admin", "clinician"])),
    db: Session = Depends(get_db),
):
    proposals = db.query(RuleChangeProposal).order_by(RuleChangeProposal.created_at.desc()).all()
    return [RuleChangeProposalOut.model_validate(p) for p in proposals]


@router.post("/rule-proposals/{proposal_id}/decide")
def decide_rule_proposal(
    proposal_id: str,
    action: str,  # accept | reject
    user: User = Depends(require_role(["admin"])),
    db: Session = Depends(get_db),
):
    proposal = db.query(RuleChangeProposal).filter(RuleChangeProposal.id == proposal_id).first()
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")

    proposal.status = "accepted" if action == "accept" else "rejected"
    proposal.reviewed_by = user.display_token
    proposal.updated_at = utc_now()

    # If accepted, create a new RuleVersion record
    if action == "accept":
        ver_record = RuleVersion(
            id=generate_uuid(),
            version=f"v1.{len(db.query(RuleVersion).all()) + 1}",
            file_hashes_json="{}",
            released_at=utc_now(),
            released_by=user.display_token,
            changelog=f"Accepted proposal {proposal_id}: {proposal.proposed_change}",
        )
        db.add(ver_record)

    db.commit()
    return {"message": f"Proposal marked {proposal.status}", "proposal_id": proposal.id}


@router.get("/rules")
def get_all_rules(user: User = Depends(require_role(["admin", "clinician"]))):
    rules = load_rules()
    return [r.model_dump() for r in rules]


@router.get("/rule-versions")
def get_rule_versions(
    user: User = Depends(require_role(["admin", "clinician"])),
    db: Session = Depends(get_db),
):
    return db.query(RuleVersion).order_by(RuleVersion.released_at.desc()).all()


@router.post("/rules/reload")
def reload_rules(user: User = Depends(require_role(["admin"]))):
    from backend.app.rules.engine import ClinicalRulesEngine
    engine = ClinicalRulesEngine()
    return {"message": "Rules reloaded successfully", "count": len(engine.rules)}

