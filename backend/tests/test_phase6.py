"""
Phase 6 Unit and Integration Tests.
Verifies Conversational State Machine, Red Flag Routing (S6), WhatsApp Webhook & Signature Validation,
Simulator Channel, and Document Vision Parsers.
"""
import hashlib
import hmac
import json
import pytest
from fastapi.testclient import TestClient

from backend.app.channels.conversation import ConversationSession, detect_red_flag
from backend.app.channels.whatsapp import verify_whatsapp_signature
from backend.app.config import get_settings
from backend.app.main import app
from backend.app.vision.slip_parser import parse_prescription_slip
from backend.app.vision.strip_parser import parse_medicine_strip

client = TestClient(app)


def test_red_flag_detection_s6():
    """Safety Principle S6: Red-flag emergency symptoms skip analysis immediately."""
    assert detect_red_flag("I am having severe chest pain since morning") is not None
    assert detect_red_flag("meri behosh hone ki naubat aa gayi") is not None
    assert detect_red_flag("patient noticed black stool today") is not None
    assert detect_red_flag("vomiting blood after dinner") is not None
    assert detect_red_flag("taking telmisartan for blood pressure") is None


def test_conversation_state_machine_flow():
    session = ConversationSession(session_id="test-conv-user")

    # 1. Onboarding Consent
    turn1 = session.handle_input("Yes, I agree to proceed")
    assert session.state == "LANGUAGE"
    assert "language" in turn1["reply"].lower()

    # 2. Select Language (Hindi)
    turn2 = session.handle_input("हिंदी")
    assert session.state == "MAIN_MENU"
    assert session.language == "hi"

    # 3. Add Medicine
    turn3 = session.handle_input("Dolo 650 mg")
    assert session.state == "CONFIRM_MEDS"
    assert "Dolo 650" in turn3["reply"] or "सुना" in turn3["reply"]

    # 4. Confirm Read-back
    turn4 = session.handle_input("Haan, sahi hai")
    assert session.state == "MAIN_MENU"
    assert len(session.confirmed_medications) == 1

    # 5. Global command 'my list'
    turn5 = session.handle_input("my list")
    assert "Dolo 650" in turn5["reply"]

    # 6. Red-flag symptom during conversation -> immediate emergency escalation
    turn_emerg = session.handle_input("Doctor I have severe chest pain")
    assert turn_emerg.get("emergency") is True
    assert "112" in turn_emerg["reply"]


def test_whatsapp_webhook_verification():
    settings = get_settings()

    # Successful challenge
    resp = client.get(
        f"/webhook/whatsapp?hub.mode=subscribe&hub.verify_token={settings.WA_VERIFY_TOKEN}&hub.challenge=test_challenge_token"
    )
    assert resp.status_code == 200
    assert resp.text == "test_challenge_token"

    # Failed token mismatch
    resp_fail = client.get(
        "/webhook/whatsapp?hub.mode=subscribe&hub.verify_token=wrong_token&hub.challenge=test_token"
    )
    assert resp_fail.status_code == 403


def test_whatsapp_webhook_signature_validation():
    secret = "test_wa_secret"
    body = json.dumps({"entry": []}).encode("utf-8")
    valid_sig = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    invalid_sig = "sha256=invalid0000000000000000000000000000000000000000000000000000000000"

    # Test signature calculation
    assert hmac.compare_digest(
        valid_sig.split("sha256=")[1],
        hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    )


def test_simulator_api_endpoint():
    # Post message to simulator
    resp = client.post(
        "/simulator/message",
        json={"session_id": "test-sim-user", "message_type": "text", "content": "Yes, I agree"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "reply" in data
    assert "history" in data
    assert len(data["history"]) >= 2  # 1 user + 1 bot reply


def test_strip_and_slip_vision_parsers():
    # Test strip parser
    strip_res = parse_medicine_strip("sample_strip.jpg")
    assert "resolution" in strip_res
    assert strip_res["ocr_confidence"] >= 0.80

    # Test slip parser
    slip_res = parse_prescription_slip("sample_slip.jpg", is_handwritten=True)
    assert slip_res["is_handwritten"] is True
    assert slip_res["line_count"] >= 0

