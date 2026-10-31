"""
Phase 4 Unit and Integration Tests.
Verifies Privacy, Consent, Full Purge, PII Leak Prevention (50 inputs), RAG Ingest, Hybrid Retrieval,
Citation Enforcement, and Refusal Behavior.
Strictly checks Safety Principle S7.
"""
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.models.db import Alert, Medication, Patient, PiiVaultEntry, SessionLocal, User, init_db
from backend.app.privacy.consent import export_patient_data, purge_patient_completely, record_consent, revoke_consent
from backend.app.privacy.llm_gateway import PiiViolationException, execute_llm_call
from backend.app.privacy.pii import has_pii, mask_pii
from backend.app.privacy.vault import get_vault_map_for_patient, store_vault_token
from backend.app.rag.citations import enforce_citations
from backend.app.rag.ingest import ingest_all_guidelines
from backend.app.rag.retriever import RAGRetriever

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    init_db()


def test_pii_50_inputs_leak_test():
    """
    Safety Principle S7: Run 50 diverse PII-bearing inputs (names, phones, emails, Aadhaar, PAN, PIN codes)
    and assert that has_pii correctly flags them and execute_llm_call strictly blocks unmasked transmission.
    """
    pii_samples = [
        f"Patient Ramesh Kumar {i} phone +91 98765432{i:02d} taking medication"
        for i in range(15)
    ] + [
        f"Contact Dr. Sharma {i} at doctor{i}@hospital.org for review"
        for i in range(10)
    ] + [
        f"Patient Aadhaar number 2345 6789 {i:04d} resident of Delhi"
        for i in range(15)
    ] + [
        f"Tax ID PAN ABCDE{i:04d}F and pincode 1100{i:02d}"
        for i in range(10)
    ]

    assert len(pii_samples) == 50

    for sample in pii_samples:
        # Must detect unmasked PII
        assert has_pii(sample) is True, f"Failed to detect PII in: {sample}"

        # LLM Gateway must raise PiiViolationException
        with pytest.raises(PiiViolationException):
            execute_llm_call(prompt=sample, is_synthetic=True)

        # Masking must strip the raw identifiers
        masked, token_map = mask_pii(sample)
        assert not has_pii(masked), f"PII remained after masking: {masked}"


def test_rag_ingestion_and_chunking():
    chunks = ingest_all_guidelines()
    assert len(chunks) >= 15
    for c in chunks:
        assert c["chunk_id"]
        assert c["document_id"]
        assert c["text"]
        assert c["token_estimate"] > 10


def test_rag_retrieval_and_refusal():
    retriever = RAGRetriever.get_instance()

    # Grounded query
    results = retriever.retrieve("anticoagulant bleeding nsaid", top_k=3)
    assert len(results) > 0
    assert any("bleeding" in r["text"].lower() for r in results)

    # Refusal query (totally unrelated query)
    refusal_res = retriever.get_grounded_answer_or_refuse("how to bake chocolate fudge cake")
    assert refusal_res["grounded"] is False
    assert "I do not have reliable information on that" in refusal_res["answer"]


def test_citation_enforcement():
    valid_ids = ["DOC-BEERS-2023-BENZODIAZEPINE", "DDI-WARFARIN-NSAID"]
    fallback = "Fallback message from verified rule."

    # 1. Properly cited clinical text
    cited_text = (
        "Older adults have increased sensitivity to sedatives [DOC-BEERS-2023-BENZODIAZEPINE]. "
        "Please talk to your doctor."
    )
    cleaned, found, ok = enforce_citations(cited_text, valid_ids, fallback)
    assert ok is True
    assert "DOC-BEERS-2023-BENZODIAZEPINE" in found
    assert "Older adults have increased sensitivity" in cleaned

    # 2. Fabricated or uncited clinical claim -> must be pruned
    uncited_text = "You should stop taking your sleeping pills immediately. It is dangerous."
    cleaned_uncited, found_uncited, ok_uncited = enforce_citations(uncited_text, valid_ids, fallback)
    assert ok_uncited is False
    assert cleaned_uncited == fallback


def test_consent_export_and_full_purge_lifecycle():
    db = SessionLocal()
    try:
        import uuid
        u_token = f"SENIOR-{uuid.uuid4().hex[:8]}"
        user = User(role="senior", display_token=u_token)
        db.add(user)
        db.commit()

        pat = Patient(owner_user_id=user.id, age=73, sex="female")
        db.add(pat)
        db.commit()

        # Add vault token
        store_vault_token(db, pat.id, "[PERSON_1]", "Shri Harish Chandra")

        # Add consent
        c = record_consent(db, pat.id, version="v1.0")
        assert c.id is not None

        # Add confirmed medication
        med = Medication(patient_id=pat.id, raw_text="Telma 40", brand="Telma 40", confirmed=True)
        med.ingredients = [{"ingredient": "telmisartan", "strength": "40mg"}]
        db.add(med)
        db.commit()

        # Export data
        export_data = export_patient_data(db, pat.id)
        assert export_data["patient"]["id"] == pat.id
        assert len(export_data["medications"]) == 1

        # Revoke consent
        c_rev = revoke_consent(db, pat.id)
        assert c_rev.revoked_at is not None

        # Full purge
        purged = purge_patient_completely(db, pat.id)
        assert purged is True

        # Assert zero data remains in DB
        assert db.query(Patient).filter(Patient.id == pat.id).first() is None
        assert db.query(Medication).filter(Medication.patient_id == pat.id).first() is None
        assert db.query(PiiVaultEntry).filter(PiiVaultEntry.patient_id == pat.id).first() is None
    finally:
        db.close()


def test_patient_api_endpoints_integration():
    # Login
    login_resp = client.post("/auth/login", json={"phone_or_token": "DEMO-SENIOR", "password_or_otp": "p"})
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create patient
    p_resp = client.post("/patients", json={"age": 75, "sex": "male", "is_synthetic": True}, headers=headers)
    assert p_resp.status_code == 200
    pat_id = p_resp.json()["id"]

    # Intake medication
    intake_resp = client.post(f"/patients/{pat_id}/medications/intake?query_text=Telma 40 mg once daily", headers=headers)
    assert intake_resp.status_code == 200
    assert intake_resp.json()["status"] == "accept_candidate"

    # Confirm medication
    cand = intake_resp.json()["top_candidate"]
    conf_resp = client.post(
        f"/patients/{pat_id}/medications/confirm",
        json={
            "raw_text": "Telma 40",
            "brand": cand["matched_name"],
            "ingredients": cand["ingredients"],
            "strength_text": cand["strength"],
            "frequency_text": cand["frequency"],
            "confirmed": True,
        },
        headers=headers,
    )
    assert conf_resp.status_code == 200
    assert conf_resp.json()["confirmed"] is True

    # Run Analysis
    an_resp = client.post(f"/patients/{pat_id}/analyze", headers=headers)
    assert an_resp.status_code == 200
    an_data = an_resp.json()
    assert "risk_scores" in an_data

    # Cleanup with delete full purge
    del_resp = client.delete(f"/patients/{pat_id}", headers=headers)
    assert del_resp.status_code == 200
