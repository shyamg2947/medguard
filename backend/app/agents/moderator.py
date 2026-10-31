"""
Specialist Panel Moderator.
Merges specialist outputs into neutral agreement and conflict summaries.
Strictly forbidden from selecting a winner or recommending treatment (S2).
"""
from typing import Any, Dict, List, Set
from backend.app.agents.guardrails import sanitize_directive_text


class Moderator:
    def synthesize(
        self,
        specialist_outputs: List[Dict[str, Any]],
        alerts: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Synthesizes multiple specialist perspectives without forcing artificial consensus.
        """
        conflicts = []
        agreements = []
        all_questions = []

        domains_present = {s["domain"] for s in specialist_outputs}

        # Check domain tensions
        if "Cardiology" in domains_present and "GI/Bleeding" in domains_present:
            conflicts.append(
                "Cardiology prioritizes vascular thromboembolism prevention; "
                "GI/Bleeding emphasizes heightened gastric mucosal hemorrhage hazard."
            )
        if "Cardiology" in domains_present and "Nephrology" in domains_present:
            conflicts.append(
                "Cardiology focuses on blood pressure reduction; "
                "Nephrology cautions against excessive drops in renal perfusion."
            )
        if "Geriatrics/Neurology" in domains_present and len(domains_present) > 1:
            agreements.append(
                "All specialists agree that cognitive clarity and fall prevention are critical priorities for this patient."
            )

        # Collect and deduplicate questions
        for s in specialist_outputs:
            for q in s.get("questions_for_doctor", []):
                cleaned = sanitize_directive_text(q).strip()
                if cleaned and cleaned not in all_questions:
                    all_questions.append(cleaned)

        for a in alerts:
            q = sanitize_directive_text(a.get("doctor_question", "")).strip()
            if q and q not in all_questions:
                all_questions.append(q)

        human_decision_needed = bool(conflicts)

        return {
            "agreements": agreements or ["Specialists concur on the need for close regular clinical follow-up."],
            "conflicts": conflicts,
            "human_decision_needed": human_decision_needed,
            "top_questions_for_doctor": all_questions[:5],
        }

