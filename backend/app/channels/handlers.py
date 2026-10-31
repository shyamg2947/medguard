"""
Unified Channel Message Handlers.
Routes inbound messages from WhatsApp or the Simulator through STT, OCR, and the Conversation State Machine.
"""
from abc import ABC, abstractmethod
import os
from typing import Any, Dict, List, Optional
from backend.app.channels.conversation import ConversationSession
from backend.app.voice.stt import get_stt_provider

# Active conversation sessions mapped by session_id (phone number or simulator token)
_active_sessions: Dict[str, ConversationSession] = {}


def get_or_create_session(session_id: str, user_id: Optional[str] = None) -> ConversationSession:
    if session_id not in _active_sessions:
        _active_sessions[session_id] = ConversationSession(session_id, user_id=user_id)
    return _active_sessions[session_id]


class Messenger(ABC):
    @abstractmethod
    def send_text(self, recipient: str, text: str, buttons: Optional[List[str]] = None) -> bool:
        pass

    @abstractmethod
    def send_document(self, recipient: str, file_path: str, caption: Optional[str] = None) -> bool:
        pass


def handle_inbound_message(
    session_id: str,
    message_type: str,  # text | audio | image | interactive
    content: Any,
    messenger: Optional[Messenger] = None,
) -> Dict[str, Any]:
    """
    Coordinates message intake:
    - Audio: transcribes via STT provider
    - Image: extracts via strip parser
    - Text / Interactive: feeds directly into state machine
    """
    session = get_or_create_session(session_id)
    user_text = ""

    if message_type == "text":
        user_text = str(content)

    elif message_type == "interactive":
        # Button reply id or title
        user_text = str(content)

    elif message_type == "audio":
        # Audio file path or bytes
        stt = get_stt_provider()
        res = stt.transcribe(content, lang_hint=session.language)
        user_text = res.get("text", "")

    elif message_type == "image":
        from backend.app.vision.strip_parser import parse_medicine_strip
        strip_res = parse_medicine_strip(content)
        user_text = strip_res.get("raw_ocr_text", "")

    # Execute conversation turn
    response = session.handle_input(user_text)

    # If a real messenger was provided (like WhatsApp sender), dispatch it
    if messenger:
        messenger.send_text(
            recipient=session_id,
            text=response.get("reply", ""),
            buttons=response.get("buttons", []),
        )

    return response

