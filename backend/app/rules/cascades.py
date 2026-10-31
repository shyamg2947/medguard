"""
Prescribing Cascades Evaluator.
Detects drug-symptom-drug sequence cascades (e.g., CCB -> ankle swelling -> loop diuretic).
Phrased as respectful inquiries for the doctor, never accusations or directives (S2).
"""
import os
from typing import Any, Dict, List, Optional
import yaml
from backend.app.entities.lexicon import get_lexicon
from backend.app.rules.durations import parse_duration_to_weeks


class CascadeEvaluator:
    def __init__(self):
        self.cascades: List[Dict[str, Any]] = []
        self._load_cascades()

    def _load_cascades(self):
        casc_path = os.path.join(os.path.dirname(__file__), "../../../rules/cascades.yaml")
        if os.path.exists(casc_path):
            with open(casc_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
                self.cascades = data.get("cascades", [])

    def evaluate_cascades(
        self,
        medications: List[Dict[str, Any]],
        symptoms: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Evaluates confirmed medications and optional symptoms for cascade patterns.
        Each medication should have: {id, brand, ingredients: [{"ingredient": ...}], start_date}
        """
        lexicon = get_lexicon()
        reported_symptoms = [s.lower().strip() for s in (symptoms or [])]
        detected = []

        # Map meds by class and duration
        med_class_map: Dict[str, List[Dict[str, Any]]] = {}
        for m in medications:
            s_weeks, _ = parse_duration_to_weeks(m.get("start_date"))
            for ing_obj in m.get("ingredients", []):
                ing = ing_obj["ingredient"].lower()
                classes = lexicon.get_classes_for_ingredient(ing)
                for c in classes:
                    if c not in med_class_map:
                        med_class_map[c] = []
                    med_class_map[c].append({
                        "med_id": m.get("id"),
                        "brand": m.get("brand") or ing,
                        "ingredient": ing,
                        "duration_weeks": s_weeks,
                        "raw_start": m.get("start_date"),
                    })

        for casc in self.cascades:
            init_class = casc["initiator"].get("class")
            sec_class = casc["secondary"].get("class")
            symptom_trigger = casc.get("symptom_trigger", "").lower()

            if init_class in med_class_map and sec_class in med_class_map:
                # Both initiator and secondary drug exist
                inits = med_class_map[init_class]
                secs = med_class_map[sec_class]

                for init_item in inits:
                    for sec_item in secs:
                        # Check timeline if available: Initiator started earlier than Secondary
                        # Higher weeks = started earlier
                        init_w = init_item["duration_weeks"]
                        sec_w = sec_item["duration_weeks"]

                        is_sequence = True
                        if init_w is not None and sec_w is not None:
                            is_sequence = (init_w >= sec_w)  # e.g. CCB 24 weeks ago, Diuretic 16 weeks ago

                        # Symptom match bonus/confirmation
                        symptom_present = symptom_trigger in reported_symptoms if symptom_trigger else True

                        if is_sequence:
                            detected.append({
                                "cascade_id": casc["id"],
                                "severity": casc.get("severity", "moderate"),
                                "domain": casc.get("domain", "General"),
                                "initiator_med": init_item["brand"],
                                "secondary_med": sec_item["brand"],
                                "symptom": symptom_trigger,
                                "mechanism": casc["mechanism"],
                                "doctor_question": casc["question"],
                                "patient_message": casc.get("patient_message", {}),
                                "sources": casc.get("sources", []),
                                "symptom_confirmed": symptom_present,
                            })

        return detected

