"""
Phase 7 Unit and Integration Tests.
Verifies Plain-Language Safety Report, Doctor Discussion Guide PDF (ReportLab + QR),
Emergency Medication Card PDF, and Expiring Signed Share Links.
"""
import pytest
from fastapi.testclient import TestClient

from backend.app.api.routes_reports import generate_share_token, verify_share_token
from backend.app.main import app
from backend.app.models.db import Medication, Patient, SessionLocal, User, init_db
from backend.app.reports.builder import build_plain_language_report
from backend.app.reports.emergency_card import generate_emergency_card_pdf
from backend.app.reports.guide_pdf import generate_doctor_guide_pdf

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    init_db()


def test_plain_language_report_builder():
    mock_analysis = {
        "all_alerts": [
            {
                "rule_id": "DDI-WARFARIN-NSAID",
                "severity": "critical",
                "type": "interaction_pair",
                "mechanism_summary": "High bleeding risk with blood thinner and painkiller.",
                "doctor_question": "Can we switch to paracetamol?",
                "patient_message": {
                    "en": "Two of your medicines can cause severe bleeding.",
                    "hi": "आपकी दो दवाएं गंभीर रक्तस्राव का कारण बन सकती हैं।",
                },
                "sources": ["FDA Label: Warfarin"],
            }
        ],
        "top_alerts": [
            {
                "rule_id": "DDI-WARFARIN-NSAID",
                "severity": "critical",
                "type": "interaction_pair",
                "mechanism_summary": "High bleeding risk with blood thinner and painkiller.",
                "doctor_question": "Can we switch to paracetamol?",
                "patient_message": {
                    "en": "Two of your medicines can cause severe bleeding.",
                    "hi": "आपकी दो दवाएं गंभीर रक्तस्राव का कारण बन सकती हैं।",
                },
                "sources": ["FDA Label: Warfarin"],
            }
        ],
        "other_alerts": [],
        "risk_scores": {"acb": {"score": 0}, "fall_risk": {"band": "Low"}, "renal": {"available": False}},
        "summary_sentence": "1 item worth discussing with your doctor or pharmacist soon.",
        "data_limitations": ["No kidney lab provided"],
    }

    report_en = build_plain_language_report(mock_analysis, language="en")
    assert "1 item worth discussing" in report_en["summary_sentence"]
    assert len(report_en["top_alerts"]) == 1
    assert "Two of your medicines" in report_en["top_alerts"][0]["patient_message"]
    assert "decision-support" in report_en["disclaimer"]

    report_hi = build_plain_language_report(mock_analysis, language="hi")
    assert "आपकी दो दवाएं" in report_hi["top_alerts"][0]["patient_message"]
    assert "निर्णय-सहायता" in report_hi["disclaimer"]


def test_doctor_discussion_guide_pdf_generation():
    patient_info = {"display_token": "PAT-DEMO74", "age": 74, "sex": "female", "date": "2026-10-31"}
    meds = [
        {"brand": "Warf 5", "ingredients": [{"ingredient": "warfarin"}], "strength": "5mg", "start_date": "2024-01-01"},
        {"brand": "Combiflam", "ingredients": [{"ingredient": "ibuprofen"}, {"ingredient": "paracetamol"}], "strength": "400mg", "start_date": "2024-10-01"},
    ]
    alerts = [
        {
            "severity": "critical",
            "type": "interaction_pair",
            "mechanism_summary": "Elevated bleeding risk",
            "doctor_question": "Is paracetamol an acceptable substitute?",
        }
    ]
    risk_scores = {
        "acb": {"score": 1, "level": "Low"},
        "fall_risk": {"band": "Medium", "count": 2},
        "renal": {"available": True, "value": 52.0},
    }

    pdf_bytes = generate_doctor_guide_pdf(
        patient_info=patient_info,
        medications=meds,
        alerts=alerts,
        risk_scores=risk_scores,
        share_url="http://localhost:8000/share/test-guide-token",
    )

    assert pdf_bytes is not None
    assert len(pdf_bytes) > 2000
    assert pdf_bytes.startswith(b"%PDF-"), "Generated file does not have valid PDF header"


def test_emergency_card_pdf_generation():
    patient_info = {"display_token": "PAT-EMERG", "age": 74, "sex": "female"}
    meds = [
        {"brand": "Warf 5", "ingredients": [{"ingredient": "warfarin"}], "strength": "5mg"},
        {"brand": "Telma 40", "ingredients": [{"ingredient": "telmisartan"}], "strength": "40mg"},
    ]
    flags = ["ON BLOOD THINNER", "HIGH FALL RISK"]

    card_bytes = generate_emergency_card_pdf(
        patient_info=patient_info,
        medications=meds,
        critical_flags=flags,
        share_url="http://localhost:8000/share/test-emerg-token",
    )

    assert card_bytes is not None
    assert len(card_bytes) > 1000
    assert card_bytes.startswith(b"%PDF-")


def test_signed_expiring_share_links():
    patient_id = "test-patient-share-123"

    # 1. Generate valid token
    token = generate_share_token(patient_id, days_valid=7)
    assert token is not None

    # 2. Verify valid token
    resolved_id = verify_share_token(token)
    assert resolved_id == patient_id

    # 3. Tampered token must fail
    tampered = token[:-4] + "ffff"
    assert verify_share_token(tampered) is None

    # 4. Expired token must fail
    expired_token = generate_share_token(patient_id, days_valid=-1)
    assert verify_share_token(expired_token) is None


def test_pdf_download_endpoints():
    db = SessionLocal()
    import uuid
    u_token = f"SENIOR-PDF-{uuid.uuid4().hex[:6]}"
    user = User(role="senior", display_token=u_token)
    db.add(user)
    db.commit()

    pat = Patient(owner_user_id=user.id, age=76, sex="male", is_synthetic=True)
    db.add(pat)
    db.commit()

    med = Medication(patient_id=pat.id, raw_text="Dolo 650", brand="Dolo 650", confirmed=True)
    med.ingredients = [{"ingredient": "paracetamol", "strength": "650mg"}]
    db.add(med)
    db.commit()

    headers = {"Authorization": f"Bearer {user.id}"}

    # Guide PDF
    resp_guide = client.get(f"/patients/{pat.id}/guide.pdf", headers=headers)
    assert resp_guide.status_code == 200
    assert resp_guide.headers["content-type"] == "application/pdf"
    assert resp_guide.content.startswith(b"%PDF-")

    # Emergency Card PDF
    resp_card = client.get(f"/patients/{pat.id}/emergency-card.pdf", headers=headers)
    assert resp_card.status_code == 200
    assert resp_card.headers["content-type"] == "application/pdf"
    assert resp_card.content.startswith(b"%PDF-")
    db.close()

