"""
Phase 9 Unit and Integration Tests.
Verifies Clinician Review Queue, Swipe Decisions, Reason Tags, 10s Undo, Audited Reveal,
Governed Rule Change Feedback Loop, Caregiver Mode, Symptom Linking, and Fast-Forward Clock.
"""
import uuid
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.models.db import (
    Alert,
    CaregiverLink,
    Medication,
    Patient,
    ReviewDecision,
    RuleChangeProposal,
    SessionLocal,
    User,
    generate_uuid,
    init_db,
    utc_now,
)
from backend.app.monitoring.checkins import fast_forward_demo_clock, get_due_checkins, reset_demo_clock, schedule_patient_checkin
from backend.app.monitoring.symptoms import analyze_symptom
from backend.app.review.rule_changes import check_and_propose_rule_change

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    init_db()
    reset_demo_clock()


def test_symptom_to_drug_linking():
    meds = [
        {"id": "m1", "brand": "Amlong 5", "ingredients": [{"ingredient": "amlodipine"}]},
        {"id": "m2", "brand": "Telma 40", "ingredients": [{"ingredient": "telmisartan"}]},
    ]
    # 'swelling' linked to CCB (amlodipine)
    res = analyze_symptom("I have noticeable ankle swelling this week", meds)
    assert res["controlled_symptom"] == "swelling"
    assert res["is_red_flag"] is False
    assert len(res["suspect_meds"]) >= 1
    assert res["suspect_meds"][0]["ingredient"] == "amlodipine"
    assert "swelling" in res["doctor_question"]


def test_fast_forward_demo_clock_and_checkins():
    pid = "pat-clock-test-1"
    sched = schedule_patient_checkin(pid)
    assert sched["active"] is True

    # Initially not due
    assert len(get_due_checkins()) == 0

    # Fast forward by 8 days -> must become due
    fast_forward_demo_clock(days=8)
    due = get_due_checkins()
    assert len(due) >= 1
    assert due[0]["patient_id"] == pid


def test_clinician_swipe_queue_and_decisions():
    db = SessionLocal()
    clinician = db.query(User).filter(User.role == "clinician").first()
    if not clinician:
        clinician = User(role="clinician", display_token="CLINICIAN-P9")
        db.add(clinician)
        db.commit()

    headers = {"Authorization": f"Bearer {clinician.id}"}

    # Setup patient and pending alert
    pat = Patient(owner_user_id=clinician.id, age=71, sex="female", is_synthetic=True)
    db.add(pat)
    db.commit()

    alert = Alert(
        id=generate_uuid(),
        patient_id=pat.id,
        rule_id="DDI-WARFARIN-NSAID",
        rule_version=1,
        severity="critical",
        type="interaction_pair",
        mechanism_summary="Bleeding hazard",
        doctor_question="Is paracetamol appropriate?",
        patient_message_json='{"en": "Bleeding hazard"}',
        sources_json='["FDA Warfarin"]',
        status="pending_review",
        created_at=utc_now(),
    )
    db.add(alert)
    db.commit()

    # 1. Fetch queue
    q_resp = client.get("/review/queue", headers=headers)
    assert q_resp.status_code == 200
    queue = q_resp.json()
    assert len(queue) >= 1
    target_case = next((c for c in queue if c["alert_id"] == alert.id), None)
    assert target_case is not None
    assert target_case["patient_token"].startswith("PAT-")

    # 2. Reject without reason tag must fail
    rej_fail = client.post(
        f"/review/{alert.id}/decision",
        json={"decision": "reject"},
        headers=headers,
    )
    assert rej_fail.status_code == 400

    # 3. Agree decision releases alert
    dec_resp = client.post(
        f"/review/{alert.id}/decision",
        json={"decision": "agree", "edited_message": "Edited message for clarity"},
        headers=headers,
    )
    assert dec_resp.status_code == 200
    assert dec_resp.json()["status"] == "released"
    decision_id = dec_resp.json()["decision_id"]

    # 4. Undo decision within 10s
    undo_resp = client.post(f"/review/{decision_id}/undo", headers=headers)
    assert undo_resp.status_code == 200

    # Verify status reverted to pending_review
    db.refresh(alert)
    assert alert.status == "pending_review"

    # 5. Audited reveal action
    rev_resp = client.post(
        f"/review/{pat.id}/reveal?reason=AcuteEmergencyConsultation",
        headers=headers,
    )
    assert rev_resp.status_code == 200
    assert rev_resp.json()["unmasked"] is True

    db.close()


def test_governed_feedback_loop_proposals():
    db = SessionLocal()
    rule_id = f"TEST-RULE-{uuid.uuid4().hex[:6]}"
    clinician = db.query(User).filter(User.role == "clinician").first()
    if not clinician:
        clinician = User(id="clinician-test-p9", role="clinician", display_token="CLIN-TEST-P9")
        db.add(clinician)
        db.commit()

    # Create 5 reject decisions for this rule to meet the 60% threshold
    for i in range(5):
        d = ReviewDecision(
            id=generate_uuid(),
            alert_or_case_id=f"alert-{rule_id}-{i}",
            clinician_id=clinician.id,
            decision="reject",
            reason_tag="false_positive",
            note="Too sensitive in practice",
            created_at=utc_now(),
        )
        db.add(d)
    db.commit()

    # Trigger rule change checker
    proposal = check_and_propose_rule_change(db, rule_id)
    assert proposal is not None
    assert proposal.status == "open"
    assert "false_positive" in proposal.proposed_change

    # Admin decides proposal
    admin_user = db.query(User).filter(User.role == "admin").first()
    if not admin_user:
        admin_user = User(id="admin-test-p9", role="admin", display_token="ADM-TEST-P9")
        db.add(admin_user)
        db.commit()
    admin_headers = {"Authorization": f"Bearer {admin_user.id}"}

    dec_resp = client.post(
        f"/admin/rule-proposals/{proposal.id}/decide?action=accept",
        headers=admin_headers,
    )
    assert dec_resp.status_code == 200
    assert "accepted" in dec_resp.json()["message"]

    db.close()


def test_caregiver_link_and_patient_dashboard():
    db = SessionLocal()
    caregiver = db.query(User).filter(User.role == "caregiver").first()
    if not caregiver:
        caregiver = User(id="caregiver-test-p9", role="caregiver", display_token="CG-TEST-P9")
        db.add(caregiver)
        db.commit()
    patient = db.query(Patient).first()
    if not patient:
        patient = Patient(id="patient-test-p9", display_token="PT-P9", primary_language="en")
        db.add(patient)
        db.commit()
    headers = {"Authorization": f"Bearer {caregiver.id}"}

    # Link caregiver
    link_resp = client.post(
        "/caregivers/link",
        json={"invite_code": patient.id},
        headers=headers,
    )
    assert link_resp.status_code == 200

    # View linked patients
    patients_resp = client.get("/caregivers/patients", headers=headers)
    assert patients_resp.status_code == 200
    assert len(patients_resp.json()) >= 1
    db.close()
