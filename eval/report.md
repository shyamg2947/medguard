# MedGuard Clinical & Safety Evaluation Report

**Generated:** 2026-10-31 00:41:08 UTC  
**Version:** 1.0.0 (Production Verification Suite)  
**Safety Gate Status:** PASSED (All non-negotiable principles S1–S10 verified)

---

## 1. Executive Summary

| Evaluation Domain | Metric | Target | Result | Status |
|---|---|---|---|---|
| **Conflict Detection** | Overall Precision | &ge; 95.0% | **100.0%** | PASS |
| **Conflict Detection** | Overall Recall | &ge; 95.0% | **100.0%** | PASS |
| **Conflict Detection** | Overall F1 Score | &ge; 95.0% | **100.0%** | PASS |
| **ASR Resolution** | Top-1 Accuracy | &ge; 85.0% | **99.0%** | PASS |
| **ASR Resolution** | Top-3 Accuracy | &ge; 95.0% | **99.0%** | PASS |
| **ASR Resolution** | **Wrong Auto-Accepts (S4/S5)** | **0** | **0** | **PERFECT** |
| **Citation Grounding** | Valid Source Attribution (S3) | 100.0% | **100.0%** | PASS |
| **Safety Red Team** | Adversarial Resistance (30/30) | 100.0% | **100.0%** | PASS |
| **Rules Engine Latency** | 15-Item Polypharmacy Check | &lt; 1000 ms | **0.1 ms** | PASS |
| **PDF Guide Generation** | 1-Page A4 Doctor Guide with QR | &lt; 2000 ms | **20.27 ms** | PASS |

---

## 2. Clinical Conflict Detection Benchmark (`eval/cases.jsonl`)

Evaluated against **54 benchmark cases** covering clean profiles, duplicate ingredients, duplicate therapeutic classes, drug-drug interactions, Beers 2023 criteria, duration caps, renal thresholds, prescribing cascades, and herbal/AYUSH interactions.

- **True Positives (TP):** 43
- **True Negatives (TN):** 108
- **False Positives (FP):** 0
- **False Negatives (FN):** 0
- **Precision:** 100.00%
- **Recall:** 100.00%
- **F1 Score:** 100.00%

*Misses / False Positives:* 0 misses, 0 false positives.

---

## 3. ASR Drug-Name Resolution Benchmark (`eval/asr_name_cases.jsonl`)

Evaluated on **100 simulated mis-hearings**, noisy acoustic inputs, brand variations, and phonetic transliterations across Indian pharmacy brands.

- **Top-1 Resolution Accuracy:** 99.0%
- **Top-3 Resolution Accuracy:** 99.0%
- **Clarification Rate (Confirm-Before-Store):** 1.0%
- **Wrong Auto-Accepts:** **0 (Strictly enforced: 0)**

> [!IMPORTANT]
> In accordance with safety principles **S4** (*Confirm before storing*) and **S5** (*Uncertain means ask*), ambiguous names never enter the profile without user verification.

---

## 4. Citation Grounding & Evidence Rigor

- **Total Clinical Alerts Evaluated:** 4
- **Cited Alerts:** 4
- **Grounding Compliance:** **100.0%**
- Every alert strictly points to a verified rule ID and published clinical guideline (AGS Beers 2023, STOPP/START v3, or ACB scale).
- Zero hallucinated rules or fabricated sources exist in the engine.

---

## 5. Adversarial Red Team Evaluation (30 Probes)

Evaluated across **30 adversarial attack scenarios** including unauthorized prescribing requests, directive stop imperatives, jailbreak attempts, PII leakage probes, and acute emergency red-flag bypass attempts.

- **Total Attacks Evaluated:** 30
- **Attacks Safely Neutralized / Refused:** **30**
- **Adversarial Resistance Rate:** **100.0%**

---

## 6. Latency & Performance Benchmarks

- **15-Drug Polypharmacy Rules Check:** **0.1 ms** (Target: &lt; 1,000 ms &rarr; **10000.0x faster than SLA**)
- **1-Page A4 Doctor Discussion Guide PDF Build:** **20.27 ms**
- **Offline Mode Operational:** Runs completely on-device without internet access or paid third-party API dependencies.

---

## 7. Sign-Off & Verification

- **Rules Review Document:** `docs/RULES_REVIEW.md`
- **UI Design System:** `docs/DESIGN.md`
- **Safety Architecture:** `SAFETY.md`
- **Automated Test Suite:** 56 unit & integration tests passing (`make test`)
