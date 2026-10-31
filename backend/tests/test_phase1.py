"""
Phase 1 Unit and Integration Tests.
Verifies Foundations: Healthz, Auth/Roles, Audit Logging, Fernet Vault, LLM Gateway, Rate Limits, Fallback.
"""
import pytest
from fastapi.testclient import TestClient

from backend.app.audit import log_audit_event
from backend.app.config import get_settings
from backend.app.main import app
from backend.app.models.db import AuditLog, Patient, SessionLocal, User, init_db, utc_now
from backend.app.privacy.llm_gateway import (
    NonSyntheticDataBlockedException,
    PiiViolationException,
    execute_llm_call,
    get_llm_usage_summary,
)
from backend.app.privacy.pii import has_pii, mask_pii, restore_pii
from backend.app.privacy.vault import (
    decrypt_value,
    encrypt_value,
    get_vault_map_for_patient,
    purge_vault_for_patient,
    store_vault_token,
)

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    init_db()


def test_healthz_and_readyz():
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"

    resp = client.get("/readyz")
    assert resp.status_code == 200
    assert resp.json()["ready"] is True


def test_auth_and_roles():
    # Login as DEMO-SENIOR
    resp = client.post("/auth/login", json={"phone_or_token": "DEMO-SENIOR", "password_or_otp": "pass"})
    assert resp.status_code == 200
    senior_data = resp.json()
    assert senior_data["user"]["role"] == "senior"
    token = senior_data["access_token"]

    # Access /auth/me with bearer
    resp = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["display_token"] == "DEMO-SENIOR"


def test_audit_logging():
    db = SessionLocal()
    try:
        entry = log_audit_event(
            actor="test-clinician",
            action="reveal",
            entity="patient",
            entity_id="pat-123",
            meta={"reason": "emergency care"},
            db=db,
        )
        assert entry.id is not None
        assert entry.action == "reveal"
        assert entry.meta["reason"] == "emergency care"

        # Query audit log
        saved = db.query(AuditLog).filter(AuditLog.id == entry.id).first()
        assert saved is not None
        assert saved.actor == "test-clinician"
    finally:
        db.close()


def test_fernet_vault():
    db = SessionLocal()
    try:
        pat_id = "test-patient-vault"
        orig_name = "Ramesh Kumar"
        token = "[PERSON_1]"

        store_vault_token(db, pat_id, token, orig_name)
        vmap = get_vault_map_for_patient(db, pat_id)
        assert vmap.get(token) == orig_name

        # Purge vault
        count = purge_vault_for_patient(db, pat_id)
        assert count >= 1
        assert len(get_vault_map_for_patient(db, pat_id)) == 0
    finally:
        db.close()


def test_pii_masking_and_restoration():
    raw = "Patient Ramesh Kumar with phone 9876543210 and Aadhaar 2345 6789 0123 has fever."
    masked, t_map = mask_pii(raw)
    assert "9876543210" not in masked
    assert "2345 6789 0123" not in masked
    assert "[PHONE_1]" in masked
    assert "[GOV_ID_1]" in masked

    restored = restore_pii(masked, t_map)
    assert "9876543210" in restored
    assert "2345 6789 0123" in restored


def test_llm_gateway_pii_safety_s7():
    # Attempting to send unmasked PII must raise PiiViolationException
    raw_prompt = "Hello my phone number is 9876543210 please prescribe medicine."
    with pytest.raises(PiiViolationException):
        execute_llm_call(prompt=raw_prompt, is_synthetic=True)


def test_llm_gateway_non_synthetic_guard_in_free_tier():
    # Non-synthetic data without ALLOW_REAL_PATIENT_DATA must be blocked
    masked_prompt = "Patient [PERSON_1] taking [DRUG_1]."
    with pytest.raises(NonSyntheticDataBlockedException):
        execute_llm_call(prompt=masked_prompt, is_synthetic=False)


def test_llm_gateway_persistent_cache_and_fallback():
    db = SessionLocal()
    try:
        import uuid
        unique_token = str(uuid.uuid4())
        prompt = f"Explain [DRUG_{unique_token[:8]}] interaction in plain language."
        # First call: executes or uses stub
        res1, cached1, badge1 = execute_llm_call(prompt=prompt, template_version="test-v1", db=db)
        assert res1 is not None
        assert cached1 is False

        # Second call with identical template, model, and prompt: must hit persistent cache with zero cost
        res2, cached2, badge2 = execute_llm_call(prompt=prompt, template_version="test-v1", db=db)
        assert res2 == res1
        assert cached2 is True

        usage = get_llm_usage_summary(db)
        assert usage["daily_calls_remaining"] >= 0
    finally:
        db.close()
