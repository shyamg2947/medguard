"""
Plain-Language Safety Report Builder.
Assembles the complete patient safety summary across languages with:
- 1. Summary headline
- 2. Top 1-3 expanded alerts (What was found, Why it matters, Question to ask)
- 3. Collapsed secondary alerts
- 4. Risk scores in simple bands
- 5. Data limitations
- 6. Standard clinical decision-support disclaimer
"""
from typing import Any, Dict, List, Optional
from backend.app.voice.translate import translate_with_drug_protection


def build_plain_language_report(
    analysis_data: Dict[str, Any],
    language: str = "en",
) -> Dict[str, Any]:
    all_alerts = analysis_data.get("all_alerts", [])
    top_alerts = analysis_data.get("top_alerts", all_alerts[:3])
    other_alerts = analysis_data.get("other_alerts", all_alerts[3:])
    risk_scores = analysis_data.get("risk_scores", {})
    limitations = analysis_data.get("data_limitations", [])

    # Format top alerts
    formatted_top = []
    for a in top_alerts:
        patient_msgs = a.get("patient_message", {})
        msg = patient_msgs.get(language) or patient_msgs.get("en", "")
        formatted_top.append({
            "rule_id": a["rule_id"],
            "severity": a["severity"],
            "what_was_found": a["type"].replace("_", " ").title(),
            "why_it_matters": a["mechanism_summary"],
            "patient_message": msg,
            "doctor_question": a["doctor_question"],
            "sources": a.get("sources", []),
        })

    formatted_other = []
    for a in other_alerts:
        patient_msgs = a.get("patient_message", {})
        msg = patient_msgs.get(language) or patient_msgs.get("en", "")
        formatted_other.append({
            "rule_id": a["rule_id"],
            "severity": a["severity"],
            "summary": msg,
            "doctor_question": a["doctor_question"],
        })

    # Risk scores formatted
    formatted_scores = {
        "acb": {
            "score": risk_scores.get("acb", {}).get("score", 0),
            "level": risk_scores.get("acb", {}).get("level", "None"),
            "is_flagged": risk_scores.get("acb", {}).get("is_flagged", False),
            "contributing_drugs": risk_scores.get("acb", {}).get("contributing_drugs", []),
        },
        "fall_risk": {
            "band": risk_scores.get("fall_risk", {}).get("band", "Low"),
            "count": risk_scores.get("fall_risk", {}).get("count", 0),
            "contributing_drugs": risk_scores.get("fall_risk", {}).get("contributing_drugs", []),
        },
        "renal": {
            "available": risk_scores.get("renal", {}).get("available", False),
            "crcl_value": risk_scores.get("renal", {}).get("value"),
            "stage": risk_scores.get("renal", {}).get("ckd_stage", "Unknown"),
        },
    }

    disclaimer = (
        "MedGuard एक निर्णय-सहायता उपकरण है। यह किसी डॉक्टर या फार्मासिस्ट की जगह नहीं लेता है। डॉक्टर से पूछे बिना कोई भी दवा शुरू, बंद या न बदलें।"
        if language == "hi"
        else "MedGuard is a decision-support tool. It does not replace a doctor or pharmacist. Do not start, stop, or change any medicine without talking to a qualified professional."
    )

    summary_sentence = analysis_data.get("summary_sentence", "")
    if language == "hi" and "items" in summary_sentence:
        summary_sentence = summary_sentence.replace("items worth discussing with your doctor or pharmacist soon.", "चीजें अपने डॉक्टर या फार्मासिस्ट से चर्चा करने योग्य हैं।")

    return {
        "summary_sentence": summary_sentence,
        "top_alerts": formatted_top,
        "other_alerts": formatted_other,
        "risk_scores": formatted_scores,
        "data_limitations": limitations,
        "disclaimer": disclaimer,
        "language": language,
    }

