"""
Audit Logging Module for MedGuard.
Provides append-only recording of sensitive actions: view, export, reveal, decision, rule_change.
"""
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session
from backend.app.models.db import AuditLog, SessionLocal, generate_uuid, utc_now


def log_audit_event(
    actor: str,
    action: str,
    entity: str,
    entity_id: str,
    meta: Optional[Dict[str, Any]] = None,
    db: Optional[Session] = None,
) -> AuditLog:
    """
    Append an entry to the audit log.
    If db session is passed, uses it; otherwise opens and commits in a dedicated session.
    """
    close_after = False
    if db is None:
        db = SessionLocal()
        close_after = True

    try:
        entry = AuditLog(
            id=generate_uuid(),
            actor=actor,
            action=action,
            entity=entity,
            entity_id=entity_id,
            at=utc_now(),
        )
        entry.meta = meta or {}
        db.add(entry)
        db.commit()
        db.refresh(entry)
        return entry
    finally:
        if close_after:
            db.close()

