"""
Deterministic Clinical Rules Engine.
Implements Rule S1: The rules engine is the source of truth.
Evaluates confirmed medications against verified guideline rules, cascades, durations, and risk scores.
Strictly adheres to S2: Never generates directive medical advice.
Strictly adheres to S3: Every alert cites rule ID, sources, and evidence level.
"""
from typing import Any, Dict, List, Optional, Set
from backend.app.entities.lexicon import get_lexicon
from backend.app.rules.cascades import CascadeEvaluator
from backend.app.rules.durations import check_duration_exceeded
from backend.app.rules.loader import load_rules
from backend.app.rules.schema import RuleDefinition
from backend.app.scores.acb import calculate_acb_score
from backend.app.scores.fall_risk import calculate_fall_risk
from backend.app.scores.renal import calculate_renal_function

SEVERITY_WEIGHTS = {
    "critical": 4,
    "high": 3,
    "moderate": 2,
    "low": 1,
}

EVIDENCE_WEIGHTS = {
    "established": 3,
    "limited": 2,
    "theoretical": 1,
}


class ClinicalRulesEngine:
    def __init__(self, rules_file: Optional[str] = None):
        self.rules: List[RuleDefinition] = load_rules(rules_file)
        self.cascade_evaluator = CascadeEvaluator()

    def evaluate(
        self,
        medications: List[Dict[str, Any]],
        age: Optional[int] = None,
        sex: Optional[str] = None,
        weight_kg: Optional[float] = None,
        serum_creatinine: Optional[float] = None,
        egfr: Optional[float] = None,
        conditions: Optional[List[str]] = None,
        symptoms: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Executes full deterministic safety evaluation.
        """
        lexicon = get_lexicon()
        cond_set = {c.lower().strip() for c in (conditions or [])}
        alerts: List[Dict[str, Any]] = []

        # 1. Index medications by ingredient and class
        ing_to_meds: Dict[str, List[Dict[str, Any]]] = {}
        class_to_meds: Dict[str, List[Dict[str, Any]]] = {}
        all_ingredients: List[str] = []

        for med in medications:
            med_id = med.get("id") or med.get("brand") or "med"
            brand = med.get("brand") or "Medication"
            for ing_obj in med.get("ingredients", []):
                ing = ing_obj["ingredient"].lower().strip()
                all_ingredients.append(ing)

                if ing not in ing_to_meds:
                    ing_to_meds[ing] = []
                ing_to_meds[ing].append(med)

                classes = lexicon.get_classes_for_ingredient(ing)
                for cls_name in classes:
                    if cls_name not in class_to_meds:
                        class_to_meds[cls_name] = []
                    class_to_meds[cls_name].append(med)

        # 2. Calculate Risk Scores
        acb_res = calculate_acb_score(all_ingredients)
        fall_res = calculate_fall_risk(all_ingredients)
        renal_res = calculate_renal_function(
            age=age,
            sex=sex,
            weight_kg=weight_kg,
            serum_creatinine_mg_dl=serum_creatinine,
            direct_egfr=egfr,
        )

        # 3. Rule Evaluation
        for rule in self.rules:
            # Type: duplicate_ingredient
            if rule.type == "duplicate_ingredient":
                ing_target = rule.a.ingredient if rule.a else None
                if ing_target and ing_target in ing_to_meds:
                    matching_meds = ing_to_meds[ing_target]
                    if len(matching_meds) >= 2:
                        med_ids = [m.get("id", m.get("brand")) for m in matching_meds]
                        alerts.append(self._build_alert(rule, med_ids, matching_meds))

            # Type: duplicate_class
            elif rule.type == "duplicate_class":
                cls_target = rule.a.class_name if rule.a else None
                if cls_target and cls_target in class_to_meds:
                    matching_meds = class_to_meds[cls_target]
                    # Filter distinct medications
                    distinct_meds = {m.get("id", m.get("brand")): m for m in matching_meds}.values()
                    if len(distinct_meds) >= 2:
                        med_ids = [m.get("id", m.get("brand")) for m in distinct_meds]
                        alerts.append(self._build_alert(rule, med_ids, list(distinct_meds)))

            # Type: interaction_pair
            elif rule.type == "interaction_pair":
                meds_a = self._resolve_target(rule.a, ing_to_meds, class_to_meds)
                meds_b = self._resolve_target(rule.b, ing_to_meds, class_to_meds)
                if meds_a and meds_b:
                    # Ensure not the exact same single medication
                    combined = {m.get("id", m.get("brand")): m for m in (meds_a + meds_b)}.values()
                    if len(combined) >= 2:
                        med_ids = [m.get("id", m.get("brand")) for m in combined]
                        alerts.append(self._build_alert(rule, med_ids, list(combined)))

            # Type: interaction_combo (Triple Whammy)
            elif rule.type == "interaction_combo" and rule.combo:
                matched_all = True
                combo_meds = []
                for tgt in rule.combo:
                    matched = self._resolve_target(tgt, ing_to_meds, class_to_meds)
                    if not matched:
                        matched_all = False
                        break
                    combo_meds.extend(matched)

                if matched_all:
                    distinct = {m.get("id", m.get("brand")): m for m in combo_meds}.values()
                    if len(distinct) >= len(rule.combo):
                        med_ids = [m.get("id", m.get("brand")) for m in distinct]
                        alerts.append(self._build_alert(rule, med_ids, list(distinct)))

            # Type: beers_pim
            elif rule.type == "beers_pim":
                if age is not None and rule.min_age is not None and age >= rule.min_age:
                    meds_target = self._resolve_target(rule.a, ing_to_meds, class_to_meds)
                    if meds_target:
                        med_ids = [m.get("id", m.get("brand")) for m in meds_target]
                        alerts.append(self._build_alert(rule, med_ids, meds_target))

            # Type: duration_exceeded
            elif rule.type == "duration_exceeded":
                meds_target = self._resolve_target(rule.a, ing_to_meds, class_to_meds)
                max_w = rule.max_duration_weeks or 8
                for m in meds_target:
                    exceeded, possible, lower_w = check_duration_exceeded(m.get("start_date"), max_w)
                    if exceeded or possible:
                        alerts.append(self._build_alert(rule, [m.get("id", m.get("brand"))], [m]))

            # Type: renal_threshold
            elif rule.type == "renal_threshold":
                if renal_res.get("available") and renal_res.get("value") is not None:
                    crcl_val = renal_res["value"]
                    thresh = rule.crcl_threshold_ml_min or rule.egfr_threshold_ml_min or 30.0
                    if crcl_val < thresh:
                        meds_target = self._resolve_target(rule.a, ing_to_meds, class_to_meds)
                        if meds_target:
                            med_ids = [m.get("id", m.get("brand")) for m in meds_target]
                            alerts.append(self._build_alert(rule, med_ids, meds_target))

            # Type: herbal_interaction
            elif rule.type == "herbal_interaction":
                meds_a = self._resolve_target(rule.a, ing_to_meds, class_to_meds)
                meds_b = self._resolve_target(rule.b, ing_to_meds, class_to_meds)
                if meds_a and meds_b:
                    combined = {m.get("id", m.get("brand")): m for m in (meds_a + meds_b)}.values()
                    med_ids = [m.get("id", m.get("brand")) for m in combined]
                    alerts.append(self._build_alert(rule, med_ids, list(combined)))

            # Type: drug_condition
            elif rule.type == "drug_condition":
                if rule.condition and rule.condition.lower() in cond_set:
                    meds_target = self._resolve_target(rule.a, ing_to_meds, class_to_meds)
                    if meds_target:
                        med_ids = [m.get("id", m.get("brand")) for m in meds_target]
                        alerts.append(self._build_alert(rule, med_ids, meds_target))

        # 4. Cascades Evaluation
        cascades_detected = self.cascade_evaluator.evaluate_cascades(medications, symptoms=symptoms)
        for casc in cascades_detected:
            casc_alert = {
                "id": casc["cascade_id"],
                "rule_id": casc["cascade_id"],
                "rule_version": 1,
                "severity": casc.get("severity", "moderate"),
                "type": "cascade",
                "involved_med_ids": [casc["initiator_med"], casc["secondary_med"]],
                "mechanism_summary": casc["mechanism"],
                "patient_message": casc["patient_message"],
                "doctor_question": casc["doctor_question"],
                "sources": casc["sources"],
                "evidence_level": "established",
                "status": "pending_review",
            }
            alerts.append(casc_alert)

        # 5. Deduplicate alerts by rule_id
        seen_rules = set()
        deduped_alerts = []
        for a in alerts:
            if a["rule_id"] not in seen_rules:
                seen_rules.add(a["rule_id"])
                deduped_alerts.append(a)

        # 6. Alert Ranking & Tiering (Section 7.6.1)
        # Sort by severity weight desc, then evidence weight desc
        deduped_alerts.sort(
            key=lambda x: (
                SEVERITY_WEIGHTS.get(x["severity"], 1),
                EVIDENCE_WEIGHTS.get(x["evidence_level"], 1)
            ),
            reverse=True
        )

        critical_alerts = [a for a in deduped_alerts if a["severity"] == "critical"]
        top_alerts = deduped_alerts[:3]
        other_alerts = deduped_alerts[3:]

        # Data limitations list
        data_limitations = []
        if not renal_res.get("available"):
            data_limitations.append("Kidney lab results (creatinine/eGFR) not provided; renal safety checks skipped.")

        # Summary sentence
        alert_count = len(deduped_alerts)
        if alert_count == 0:
            summary = "Your medication check found no major guideline conflicts. Keep taking as prescribed."
        elif alert_count == 1:
            summary = "1 item worth discussing with your doctor or pharmacist soon."
        else:
            summary = f"{alert_count} items worth discussing with your doctor or pharmacist soon."

        disclaimer = (
            "MedGuard is a decision-support tool. It does not replace a doctor or pharmacist. "
            "Do not start, stop, or change any medicine without talking to a qualified professional."
        )

        return {
            "all_alerts": deduped_alerts,
            "critical_alerts": critical_alerts,
            "top_alerts": top_alerts,
            "other_alerts": other_alerts,
            "cascades": cascades_detected,
            "risk_scores": {
                "acb": acb_res,
                "fall_risk": fall_res,
                "renal": renal_res,
            },
            "summary_sentence": summary,
            "data_limitations": data_limitations,
            "disclaimer": disclaimer,
        }

    def _resolve_target(
        self,
        target: Optional[Any],
        ing_to_meds: Dict[str, List[Dict[str, Any]]],
        class_to_meds: Dict[str, List[Dict[str, Any]]],
    ) -> List[Dict[str, Any]]:
        if not target:
            return []

        matched = []
        # Target can be single ingredient or list
        ing = getattr(target, "ingredient", None)
        if ing:
            if isinstance(ing, list):
                for i in ing:
                    matched.extend(ing_to_meds.get(i.lower().strip(), []))
            elif ing.lower().strip() in ing_to_meds:
                matched.extend(ing_to_meds[ing.lower().strip()])

        # Target can be single class or list of classes
        cls_name = getattr(target, "class_name", None)
        if cls_name:
            if isinstance(cls_name, list):
                for c in cls_name:
                    matched.extend(class_to_meds.get(c.lower().strip(), []))
            elif cls_name.lower().strip() in class_to_meds:
                matched.extend(class_to_meds[cls_name.lower().strip()])

        # Deduplicate
        return list({m.get("id", m.get("brand")): m for m in matched}.values())

    def _build_alert(
        self,
        rule: RuleDefinition,
        involved_ids: List[str],
        meds: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        return {
            "id": f"alert-{rule.id}",
            "rule_id": rule.id,
            "rule_version": rule.version,
            "severity": rule.severity,
            "type": rule.type,
            "domain": rule.domain,
            "involved_med_ids": involved_ids,
            "mechanism_summary": rule.mechanism,
            "patient_message": rule.patient_message,
            "doctor_question": rule.doctor_question,
            "sources": rule.sources,
            "evidence_level": rule.evidence,
            "status": "pending_review",
        }

