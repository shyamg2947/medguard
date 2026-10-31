"""
WhatsApp Simulator Channel.
Allows full end-to-end testing and interactive live demo of MedGuard without Meta API credentials.
Maintains chat history per session for the frontend simulator UI.
"""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.app.channels.handlers import handle_inbound_message
from backend.app.vision.slip_parser import analyze_prescription_image

router = APIRouter(prefix="/simulator", tags=["Simulator"])

_chat_histories: Dict[str, List[Dict[str, Any]]] = {}


class SimulatorMessageRequest(BaseModel):
    session_id: str = "sim-demo-user"
    sender_phone: Optional[str] = None
    message_type: str = "text"  # text | audio | image | interactive
    content: Optional[str] = None
    text: Optional[str] = None
    media_url: Optional[str] = None
    image_url: Optional[str] = None
    language: Optional[str] = "en"


@router.post("/message")
def post_simulator_message(req: SimulatorMessageRequest) -> Dict[str, Any]:
    """
    Submits a user message to the simulator session and returns the bot's response turn.
    """
    if req.session_id not in _chat_histories:
        _chat_histories[req.session_id] = []

    msg_content = req.content or req.text or req.media_url or req.image_url or ""
    
    # Record user message in history
    _chat_histories[req.session_id].append({
        "sender": "user",
        "type": req.message_type,
        "content": msg_content,
        "media_url": req.media_url or req.image_url,
    })

    # If it is an image / prescription photo, run prescription vision & safety analysis
    if req.message_type == "image":
        rx_res = analyze_prescription_image(
            image_input=msg_content or req.media_url or req.image_url,
            language=req.language or "en",
        )
        
        reply_lines = [
            f"📋 **Prescription Analysis Complete**",
            f"**Detected Medicines:** {', '.join(rx_res['medicine_names'])}",
            "",
        ]
        if rx_res["alerts"]:
            reply_lines.append(f"⚠️ **Clinical Safety Alerts ({len(rx_res['alerts'])})**:")
            for a in rx_res["alerts"]:
                reply_lines.append(f"• **{a.get('severity', 'Alert').upper()}:** {a.get('title', a.get('rule_id'))}")
                if a.get("doctor_question"):
                    reply_lines.append(f"  *Question for Doctor:* \"{a['doctor_question']}\"")
                reply_lines.append("")
        else:
            reply_lines.append("✅ No high-risk guideline interactions detected for this prescription.")
        
        reply_text = "\n".join(reply_lines)
        
        bot_msg = {
            "sender": "bot",
            "type": "prescription_result",
            "content": reply_text,
            "speech_text": rx_res["speech_text"],
            "detected_medicines": rx_res["detected_medicines"],
            "alerts": rx_res["alerts"],
            "buttons": ["Add to My List", "Download Doctor Guide (PDF)", "Ask a Question"],
            "emergency": False,
        }
        _chat_histories[req.session_id].append(bot_msg)

        return {
            "reply": reply_text,
            "body": reply_text,
            "speech_text": rx_res["speech_text"],
            "detected_medicines": rx_res["detected_medicines"],
            "alerts": rx_res["alerts"],
            "buttons": bot_msg["buttons"],
            "quick_replies": bot_msg["buttons"],
            "type": "prescription_result",
            "emergency": False,
            "history": _chat_histories[req.session_id],
        }

    # Dispatch normal message to state machine
    resp = handle_inbound_message(
        session_id=req.session_id,
        message_type=req.message_type,
        content=msg_content,
    )

    # Record assistant reply in history
    bot_msg = {
        "sender": "bot",
        "type": "text",
        "content": resp.get("reply", ""),
        "buttons": resp.get("buttons", []),
        "emergency": resp.get("emergency", False),
        "state": resp.get("state"),
        "report": resp.get("report"),
    }
    _chat_histories[req.session_id].append(bot_msg)

    return {
        "reply": resp.get("reply"),
        "body": resp.get("reply"),
        "buttons": resp.get("buttons", []),
        "quick_replies": resp.get("buttons", []),
        "state": resp.get("state"),
        "emergency": resp.get("emergency", False),
        "history": _chat_histories[req.session_id],
    }


@router.post("/prescription/analyze")
def analyze_prescription(req: SimulatorMessageRequest) -> Dict[str, Any]:
    """
    Direct endpoint for analyzing prescription photos with senior speech output.
    """
    img_data = req.content or req.media_url or req.image_url or "prescription_sample.jpg"
    res = analyze_prescription_image(img_data, language=req.language or "en")
    return res


@router.get("/session/{session_id}")
def get_simulator_history(session_id: str) -> Dict[str, Any]:
    history = _chat_histories.get(session_id, [])
    return {"session_id": session_id, "messages": history}


@router.post("/session/{session_id}/reset")
def reset_simulator_session(session_id: str) -> Dict[str, Any]:
    from backend.app.channels.handlers import _active_sessions
    _chat_histories[session_id] = []
    if session_id in _active_sessions:
        del _active_sessions[session_id]
    return {"message": "Session reset"}

