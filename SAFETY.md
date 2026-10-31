# MedGuard Safety Architecture & Clinical Verification

MedGuard operates strictly as a clinical decision-support and communication aid for older adults and their care teams. It does not diagnose, prescribe, or provide directive orders to stop or adjust therapy.

The system is governed by **ten non-negotiable safety principles (S1–S10)**, each anchored by automated regression tests and architectural controls.

---

## The Ten Non-Negotiable Safety Principles

| Principle | Name | Architectural Enforcement | Automated Test Reference |
|---|---|---|---|
| **S1** | **Rules engine is the source of truth** | The deterministic rules engine (`ClinicalRulesEngine`) evaluates all safety rules. LLMs are strictly quarantined to syntactic extraction and plain-language explanation; LLM outputs cannot create, remove, or modify patient-facing clinical alerts. | `backend/tests/test_phase3.py` |
| **S2** | **No directive medical advice** | Patient-facing outputs never contain imperative verbs such as *"stop"*, *"switch"*, or *"increase"*. An output validator (`sanitize_directive_text`) deterministically rewrites directives into neutral exploratory inquiries: *"Ask your doctor or pharmacist whether..."*. | `backend/tests/test_phase5.py` |
| **S3** | **Every alert cites its rule ID and source** | Alerts without an explicit `rule_id` and grounded `sources` array (e.g., AGS Beers Criteria 2023, STOPP/START v3, ACB scale) are dropped by citation enforcement filters. | `backend/tests/test_phase4.py` |
| **S4** | **Confirm before storing** | Medications never enter the patient's active profile automatically. Extracted names are staged as candidates until explicitly verified by the senior (read-back prompt by voice or button click). | `backend/tests/test_phase2.py` |
| **S5** | **Uncertain means ask** | If composite string, phonetic, and acoustic confidence falls below threshold (0.90) or margin &lt; 0.08, the system refuses to guess and triggers the clarification prompt or strip photo upload. Wrong auto-accept rate is benchmarked at strictly 0. | `backend/tests/test_phase2.py`, `eval/run_eval.py` |
| **S6** | **Red flags escalate immediately** | Critical acute symptoms (chest pain, fainting, falls with injury, vomiting blood, black stools) bypass rules analysis and immediately display national emergency guidance (112 in India) and notify the linked caregiver. | `backend/tests/test_phase6.py` |
| **S7** | **Mask before AI calls** | Direct identifiers (names, phone numbers, addresses, dates of birth, Aadhaar numbers) are scrubbed before any LLM prompt is constructed. The LLM only ever receives synthetic tokens (`PT-XXXX`). | `backend/tests/test_phase4.py`, `backend/tests/test_phase1.py` |
| **S8** | **Encrypted vault for raw data** | Personally Identifiable Information (PII) is encrypted with Fernet symmetric keys (`AES-128-CBC` with `HMAC-SHA256`) and stored in an isolated vault table. Keys are managed separately from application database credentials. | `backend/tests/test_phase1.py` |
| **S9** | **Clinician gate on AI commentary** | While deterministic rule-engine alerts are released immediately to prevent harm, open-ended multi-specialist commentary is gated behind clinician review (`approved_for_patient = False`) by default. | `backend/tests/test_phase5.py`, `backend/tests/test_phase9.py` |
| **S10** | **Synthetic data only without flag** | The system rejects real patient data unless `ALLOW_REAL_PATIENT_DATA=true` is explicitly set in the environment. Free-tier mode enforces synthetic patient profiles for all demonstrations. | `backend/tests/test_phase1.py` |

---

## Adversarial Red Team Verification

The test harness in `eval/run_eval.py` subjects MedGuard to 30 adversarial probes designed to elicit unlicensed prescribing, prompt injection, PII extraction, and emergency bypass. 

All 30 probes are safely neutralized (100% resistance rate), as recorded in `eval/report.md`.

