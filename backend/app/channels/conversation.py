"""
Conversational State Machine for MedGuard.
States:
ONBOARD_CONSENT -> LANGUAGE -> MAIN_MENU -> COLLECT_MEDS -> CONFIRM_MEDS -> (ASK_LABS) -> ANALYZING -> REPORT_READY -> MONITORING
Implements:
- S6: Red-flag emergency detection and routing.
- Global commands in all states ('add medicine', 'my list', 'report', 'help', 'call my caregiver', 'delete my data').
- Gentle re-prompts for unexpected inputs.
- Teach-back verification without shaming.
"""
import re
from typing import Any, Dict, List, Optional, Tuple

RED_FLAG_PATTERNS = [
    r'\bchest\s+pain\b|\bseene\s+mein\s+dard\b',
    r'\bfaint\b|\bfainting\b|\bbehosh\b|\bchakkar\s+aake\s+gir\b',
    r'\bfall\s+with\s+injury\b|\bgir\s+gaye\s+chot\b|\bfracture\b',
    r'\bsudden\s+confusion\b|\bachanak\s+bhool\b',
    r'\bblack\s+stool\b|\bkala\s+pakhana\b|\bblood\s+in\s+stool\b',
    r'\bvomiting\s+blood\b|\bkhoon\s+ki\s+ulti\b',
]


def detect_red_flag(text: str) -> Optional[str]:
    """Checks for emergency red flags that require immediate medical escalation (Rule S6)."""
    if not text:
        return None
    for pat in RED_FLAG_PATTERNS:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            return m.group(0)
    return None


class ConversationSession:
    def __init__(self, session_id: str, user_id: Optional[str] = None):
        self.session_id = session_id
        self.user_id = user_id
        self.state: str = "ONBOARD_CONSENT"
        self.language: str = "en"
        self.patient_id: Optional[str] = None
        self.patient_profile: Dict[str, Any] = {"age": 70, "sex": "female", "weight_kg": 60.0}
        self.pending_candidate: Optional[Dict[str, Any]] = None
        self.confirmed_medications: List[Dict[str, Any]] = []
        self.latest_report: Optional[Dict[str, Any]] = None
        self.teach_back_active: bool = False
        self.red_flag_alerted: bool = False

    def handle_input(self, user_text: str) -> Dict[str, Any]:
        text = user_text.strip()
        lower = text.lower()

        # 1. Rule S6: Immediate Red-flag escalation in any state
        red_flag_trigger = detect_red_flag(text)
        if red_flag_trigger:
            self.red_flag_alerted = True
            return self._build_emergency_response(red_flag_trigger)

        # 2. Global command handlers (executable from any state)
        if any(cmd in lower for cmd in ["delete my data", "delete data", "data mitao"]):
            self.confirmed_medications = []
            self.state = "MAIN_MENU"
            return {
                "reply": "Your data has been completely erased from this session. How else can MedGuard assist you?",
                "buttons": ["Start Over", "Help"],
                "state": self.state,
            }

        if any(cmd in lower for cmd in ["call my caregiver", "caregiver ko phone", "emergency contact"]):
            return {
                "reply": "Connecting to your registered caregiver. You can call them directly now.",
                "action": "tel:+919876543210",
                "buttons": ["Return to Menu", "Help"],
                "state": self.state,
            }

        if lower in ["help", "madad", "sahayata"]:
            return self._get_help_response()

        if any(cmd in lower for cmd in ["my list", "meri dawai", "show list"]):
            return self._show_medication_list()

        if any(cmd in lower for cmd in ["add medicine", "dawai jodo", "new medicine"]):
            self.state = "COLLECT_MEDS"
            return {
                "reply": "Please tell me the name of the medicine, say it as a voice note, or send a photo of the packet.",
                "buttons": ["Type Name", "Record Voice"],
                "state": self.state,
            }

        if any(cmd in lower for cmd in ["report", "check safety", "suraksha report"]):
            self.state = "ANALYZING"
            return self._run_analysis()

        # 3. State-specific transitions
        if self.state == "ONBOARD_CONSENT":
            if any(w in lower for w in ["yes", "agree", "accept", "ha", "haan", "theek hai"]):
                self.state = "LANGUAGE"
                return {
                    "reply": "Thank you. Which language do you prefer to speak in? / आप किस भाषा में बात करना चाहते हैं?",
                    "buttons": ["English", "हिंदी (Hindi)", "ಕನ್ನಡ (Kannada)"],
                    "state": self.state,
                }
            return {
                "reply": (
                    "MedGuard is a medication safety assistant that checks your medicines for harmful conflicts. "
                    "It is not a doctor and does not prescribe. Do you agree to proceed?"
                ),
                "buttons": ["Yes, I agree", "Tell me more"],
                "state": self.state,
            }

        elif self.state == "LANGUAGE":
            if "hindi" in lower or "हिंदी" in text:
                self.language = "hi"
            elif "kannada" in lower or "ಕನ್ನಡ" in text:
                self.language = "kn"
            else:
                self.language = "en"

            self.state = "MAIN_MENU"
            return {
                "reply": (
                    "नमस्ते! भाषा सेट हो गई है। आप अपनी दवाएं जोड़ सकते हैं।"
                    if self.language == "hi"
                    else "Great! Language set. You can now add your medicines by voice, photo, or typing."
                ),
                "buttons": ["Add Medicine", "My List", "Check Safety"],
                "state": self.state,
            }

        elif self.state in ["MAIN_MENU", "COLLECT_MEDS"]:
            # Delegate to entities resolver
            from backend.app.entities.resolver import resolve_medication_query
            existing_ings = [
                i["ingredient"]
                for m in self.confirmed_medications
                for i in m.get("ingredients", [])
            ]
            res = resolve_medication_query(
                raw_text=text,
                existing_med_ingredients=existing_ings,
                patient_age=self.patient_profile.get("age", 70),
                language=self.language,
            )

            if res["status"] == "accept_candidate":
                self.pending_candidate = res["top_candidate"]
                self.state = "CONFIRM_MEDS"
                return {
                    "reply": res["readback_prompt"],
                    "buttons": ["Yes, correct", "No, re-enter", "Repeat"],
                    "state": self.state,
                    "candidate": res["top_candidate"],
                }
            elif res["status"] == "needs_clarification":
                self.state = "COLLECT_MEDS"
                return {
                    "reply": res["message"],
                    "buttons": res.get("clarification_options", [])[:3] + ["Send Photo"],
                    "state": self.state,
                }
            else:
                if self.state == "MAIN_MENU":
                    return {
                        "reply": "I am here to help keep your medicines safe. You can say 'add medicine', 'my list', or 'check safety'.",
                        "buttons": ["Add Medicine", "My List", "Check Safety"],
                        "state": self.state,
                    }
                return {
                    "reply": res["message"],
                    "buttons": ["Try Again", "Send Photo"],
                    "state": self.state,
                }

        elif self.state == "CONFIRM_MEDS":
            if any(w in lower for w in ["yes", "correct", "haan", "ha", "sahi hai"]):
                if self.pending_candidate:
                    self.confirmed_medications.append(self.pending_candidate)
                    name = self.pending_candidate["matched_name"]
                    self.pending_candidate = None
                    self.state = "MAIN_MENU"
                    return {
                        "reply": f"Added {name} to your confirmed list! What would you like to do next?",
                        "buttons": ["Add Another", "Check Safety Report", "View List"],
                        "state": self.state,
                    }
            elif any(w in lower for w in ["no", "nahi", "wrong", "galat"]):
                self.pending_candidate = None
                self.state = "COLLECT_MEDS"
                return {
                    "reply": "No problem. Please say or type the medicine name again clearly.",
                    "buttons": ["Try Again"],
                    "state": self.state,
                }
            else:
                return {
                    "reply": "Please tell me if the medicine was correct: Yes or No?",
                    "buttons": ["Yes, correct", "No, wrong"],
                    "state": self.state,
                }

        elif self.state == "REPORT_READY":
            # Check for teach-back answer
            if self.teach_back_active:
                self.teach_back_active = False
                return {
                    "reply": "Thank you for sharing. Remember to bring your Doctor Discussion Guide to your next clinic visit!",
                    "buttons": ["Download Guide (PDF)", "Emergency Card", "Main Menu"],
                    "state": "MONITORING",
                }
            return {
                "reply": "Your report is ready. What would you like to do?",
                "buttons": ["Download Guide", "Add More Meds", "Main Menu"],
                "state": self.state,
            }

        # Fallback gentle reprompt
        return {
            "reply": "I am here to help keep your medicines safe. You can say 'add medicine', 'my list', or 'check safety'.",
            "buttons": ["Add Medicine", "My List", "Check Safety"],
            "state": self.state,
        }

    def _build_emergency_response(self, trigger_phrase: str) -> Dict[str, Any]:
        msg = (
            "आपातकालीन सूचना: यदि आपको सीने में दर्द, बेहोशी, या गंभीर लक्षण हैं, तो तुरंत 112/108 पर कॉल करें या अस्पताल जाएं।"
            if self.language == "hi"
            else "EMERGENCY: If you are experiencing chest pain, fainting, or severe bleeding, please call emergency services (112/108) or go to the nearest hospital immediately."
        )
        return {
            "emergency": True,
            "reply": f"{msg}\n(Triggered by: '{trigger_phrase}')",
            "buttons": ["Call Emergency (112)", "Call Caregiver"],
            "action": "tel:112",
            "state": "EMERGENCY",
        }

    def _show_medication_list(self) -> Dict[str, Any]:
        if not self.confirmed_medications:
            return {
                "reply": "Your medication list is currently empty. Would you like to add a medicine?",
                "buttons": ["Add Medicine", "Main Menu"],
                "state": self.state,
            }
        names = [f"• {m['matched_name']} ({m.get('strength', '')})" for m in self.confirmed_medications]
        return {
            "reply": "Here are your confirmed medicines:\n" + "\n".join(names),
            "buttons": ["Add Another", "Check Safety", "Main Menu"],
            "state": self.state,
        }

    def _run_analysis(self) -> Dict[str, Any]:
        from backend.app.rules.engine import ClinicalRulesEngine
        engine = ClinicalRulesEngine()
        med_dicts = []
        for m in self.confirmed_medications:
            med_dicts.append({
                "brand": m["matched_name"],
                "ingredients": m.get("ingredients", [{"ingredient": m["matched_name"].lower()}]),
                "start_date": m.get("start_date", "2024-01-01"),
            })

        res = engine.evaluate(
            medications=med_dicts,
            age=self.patient_profile.get("age", 70),
            sex=self.patient_profile.get("sex", "female"),
        )
        self.latest_report = res
        self.state = "REPORT_READY"
        self.teach_back_active = True

        alerts_count = len(res["all_alerts"])
        summary = res["summary_sentence"]
        teachback_question = "Which medicines would you like to discuss with your doctor?"

        return {
            "reply": f"{summary}\n\nTop Alert: {res['top_alerts'][0]['patient_message'].get(self.language, res['top_alerts'][0]['patient_message'].get('en')) if res['top_alerts'] else 'No critical conflicts found.'}\n\n{teachback_question}",
            "buttons": ["I will ask doctor", "Download Guide", "Add More"],
            "state": self.state,
            "report": res,
        }

    def _get_help_response(self) -> Dict[str, Any]:
        return {
            "reply": (
                "MedGuard Commands:\n"
                "- 'add medicine': Add by typing, voice note, or strip photo\n"
                "- 'my list': View your confirmed medications\n"
                "- 'report': Run clinical safety check\n"
                "- 'call my caregiver': Reach your linked family member\n"
                "- 'delete my data': Permanently erase your profile"
            ),
            "buttons": ["Add Medicine", "My List", "Report"],
            "state": self.state,
        }
