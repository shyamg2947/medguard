# MedGuard: Master Build Prompt

> Put this file at the repo root as `prompt.md` and point your coding agent (built for Google Antigravity, works with Codex and similar tools) at it.
> Build the complete system described below. Work in the phases in Section 12, run the tests at the end of each phase, and do not stop until the Definition of Done in Section 13 is met.
> **Defaults for this build:** WhatsApp runs through the built-in **simulator** first (real Meta integration is built but optional), and the project must run on **free-tier or offline** providers (Section 5.4). See Section 16 for how to run this in Antigravity.

---

## 0. Instructions to the coding agent

1. **Build everything in this document.** The result must run end to end on a laptop with `make demo`, with or without external API keys (see "Provider modes" in Section 5).
2. **Do not ask questions.** When something is ambiguous, choose the most reasonable option, and record it in `ASSUMPTIONS.md` with a one-line reason.
3. **Never invent clinical facts.** Every rule, interaction, threshold and score you add must carry a `sources` field that points to a document in `knowledge/` or to a named public source (FDA label, AGS Beers Criteria, STOPP/START, ACB scale). If you are not sure a fact is correct, mark the rule `review_status: seed_needs_review` and keep it out of the demo path. Do not fabricate URLs.
4. **Do not copy long passages of copyrighted guideline text.** Store short paraphrased rule summaries with citations, and provide an ingestion script so the team can add official documents they are licensed to use.
5. **Write tests as you go.** Every module in Section 7 needs unit tests, and the system needs the evaluation harness in Section 10.
6. **Keep the repo clean:** typed code, small modules, docstrings on public functions, no secrets in git, a working `.env.example`.
7. Finish each phase with a short note in `docs/PROGRESS.md` listing what works, what is stubbed, and what is next.

---

## 1. Mission

**MedGuard** is a voice-first, multilingual medication-safety assistant for elderly people in India. It collects a person's full medication picture (prescriptions, OTC drugs, supplements, herbal and AYUSH products) from voice notes, photos and text, normalizes it to generic ingredients, checks it with a deterministic clinical rules engine grounded in published geriatric safety frameworks, and returns a plain-language report in the user's own language. It also produces a **Doctor Discussion Guide** that helps the person talk to a qualified professional.

It is **decision support and a communication aid. It is not a doctor and does not diagnose, prescribe, or tell anyone to stop or change a medicine.**

### Headline capabilities (all must be built)

1. Voice-based multilingual interaction for seniors (English, Hindi, plus one configurable regional language).
2. WhatsApp assistant (Meta WhatsApp Cloud API) plus a local WhatsApp-style simulator so the whole product is demoable without Meta credentials.
3. Specialty agent panel (Cardiology, Nephrology, Geriatrics/Neurology, GI/Bleeding) with a moderator that surfaces agreement and disagreement. It never forces false consensus.
4. RAG over a curated knowledge base (AGS Beers, STOPP/START, MAI, interaction data) so explanations are grounded and cited.
5. Clinician review with a swipe-style (Tinder-like) interface, reason tags, and a governed feedback loop into a rule-change queue.
6. Caregiver mode.
7. Accessibility for visual and hearing difficulties.
8. Masking of sensitive patient information before any AI call.
9. An Apple-inspired, highly polished and accessible UI shared across all apps (Section 7.16), including a public landing page.
10. Extra features: AYUSH/herbal/OTC layer, prescribing-cascade detection, time-on-drug alerts, patient risk scores (anticholinergic burden, fall risk, renal function), discharge reconciliation, pill strip scan, emergency medication card, weekly symptom check-ins, teach-back mode, severity tiering to limit alert fatigue.

---

## 2. Non-negotiable safety principles

These override every other instruction. Add automated tests for each one.

| # | Principle |
|---|-----------|
| S1 | **The rules engine is the source of truth.** An LLM may extract, translate, and explain. It may not create, remove, or re-rank alerts that patients see. |
| S2 | **No directive medical advice.** Output never says "stop", "start", "increase", "decrease" or "switch" a drug or dose. It says "ask your doctor or pharmacist whether...". An output validator must catch and rewrite directive phrasing. |
| S3 | **Every alert cites its rule ID and source.** Output without a citation is dropped. |
| S4 | **Confirm before storing.** A drug enters the patient profile only after the user confirms it (read-back by voice or buttons). |
| S5 | **Uncertain means ask.** Below the confidence thresholds in Section 7.4 the system asks for clarification or a photo. It never guesses a drug name. |
| S6 | **Red flags escalate.** Phrases such as chest pain, fainting, a fall with injury, sudden confusion, black stools, or vomiting blood skip analysis. The system shows "call your doctor or emergency services now" in the user's language and notifies the caregiver. |
| S7 | **Mask before AI.** No raw identifiers (names, phone numbers, addresses, dates of birth, government ID numbers, email) leave the PII boundary. A test must prove this for every LLM call. |
| S8 | **AI commentary is gated.** Agent-panel commentary is shown only to clinicians, or to patients after clinician approval, controlled by `REQUIRE_CLINICIAN_APPROVAL_FOR_AI_COMMENTARY=true` (default). |
| S9 | **Always show limits.** Every report carries the disclaimer in Section 7.10 and states data limitations (for example, "brand not recognized"). |
| S10 | **No real patient data.** Use synthetic data only. Never include real names, phone numbers or ID numbers in fixtures. |

---

## 3. Users

- **Senior (primary):** low digital literacy, may have poor vision or hearing, speaks Hindi or a regional language, uses WhatsApp daily.
- **Caregiver:** adult child or helper, often in another city. Wants the full list, alerts when something changes, and a printable summary for the doctor.
- **Clinician or pharmacist:** reviews flagged cases quickly, corrects false positives, and wants citations and reason codes.
- **Admin / clinical lead:** approves rule-change proposals and manages rule versions.

---

## 4. Architecture

### 4.1 Layers

1. **Channels:** WhatsApp Cloud API webhook, WhatsApp-style simulator, senior PWA, caregiver dashboard, clinician dashboard.
2. **Input processing:** speech-to-text with word confidences, text-to-speech, OCR and vision for slips and strips, read-back confirmation.
3. **Privacy and normalization:** PII masking and vault, drug entity resolution (RxNorm plus Indian brand table), OTC and herbal dictionary.
4. **Clinical reasoning core:** deterministic rules engine, risk scores, RAG retrieval, specialty agent panel plus moderator (agents run only on flagged cases).
5. **Output and review:** plain-language report, voice summary, Doctor Discussion Guide PDF, clinician swipe review, caregiver alerts, monitoring.
6. **Data and governance base:** encrypted patient store, versioned rule base, audit log, rule-change queue.

### 4.2 Ten-step request flow

```
1 Client <-> WhatsApp gateway (or simulator / web)
2 Gateway -> Speech/OCR extraction (language detection, confidences)
3 Extraction -> Read-back confirmation (only confirmed drugs kept)
4 Confirmed text -> PII masking -> drug normalization (generic ingredients, classes)
5 Structured profile -> Rules engine (+ risk scores, duration, cascades)
6 Rules <-> RAG retrieval (cited evidence for explanations)
7 Flagged cases only -> Specialty agent panel -> Moderator
8 Output -> Clinician review queue (swipe, reason tags) [<-> clinician dashboard]
9 Approved output -> Report (plain language, voice, translated)
10 Report -> Doctor Discussion Guide PDF, caregiver alert, monitoring schedule
Governance base (store, versioned rules, audit log) is used by every step.
```

---

## 5. Tech stack and repository layout

### 5.1 Default stack (substitute only with a written reason in `ASSUMPTIONS.md`)

| Area | Choice |
|------|--------|
| Backend | Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2, Alembic, APScheduler |
| Database | SQLite by default, PostgreSQL via `DATABASE_URL` |
| Vector store | Chroma (embedded) or FAISS, with a local sentence-transformers embedding model (multilingual) |
| Agents | LangGraph for orchestration |
| Fuzzy and phonetic matching | rapidfuzz, a Metaphone implementation, indic-transliteration for Indic scripts |
| Frontend | React + Vite + TypeScript + Tailwind; Framer Motion (or react-tinder-card) for swipe |
| PDF | WeasyPrint or ReportLab; `qrcode` for QR codes |
| Messaging | Meta WhatsApp Cloud API (webhook, media download, interactive reply buttons, document and audio sending) |
| Testing | pytest, Hypothesis for matching tests, Playwright for end-to-end |
| Packaging | Docker Compose, Makefile |

### 5.2 Provider modes (must run with no keys)

Every external capability sits behind an interface with at least two implementations: a real provider and an offline stub.

| Interface | Real provider (configurable) | Offline stub |
|-----------|------------------------------|--------------|
| `SpeechToText` | faster-whisper (local), or Sarvam / Bhashini / cloud STT | Reads `*.transcript.json` sidecar files next to sample audio |
| `TextToSpeech` | Edge-TTS / gTTS / provider API | Browser `speechSynthesis` on web, pre-rendered audio for the demo |
| `Vision` / OCR | Vision LLM, or Tesseract / PaddleOCR | Reads `*.ocr.json` sidecar files for sample images |
| `LLM` | Gemini, OpenAI or Anthropic via env vars | Template-based generator that fills the rule `patient_message` and `doctor_question` fields |
| `Translator` | LLM with drug-name placeholders | Pre-translated rule messages (en, hi) |
| `Messenger` | WhatsApp Cloud API | Local simulator channel |

`MODE=demo` selects the stubs. `MODE=live` uses configured providers and fails with a clear error if keys are missing. Explanations must still work in demo mode because rule messages are stored with the rules, and the LLM is only used to polish them.

### 5.2b Free-tier mode (default for this build)

`FREE_TIER_MODE=true` is the default. The product must be fully usable on free API tiers and local models, and must degrade gracefully when quota runs out.

**Provider defaults**

| Capability | Default in free-tier mode |
|------------|---------------------------|
| LLM (polish, translation, agent panel) | Gemini API free tier via `GEMINI_API_KEY` from Google AI Studio. The model name comes from `LLM_MODEL` in `.env` (never hard-code it). Document in README how to pick a free-tier model in AI Studio. |
| Speech-to-text | Local faster-whisper (`STT_MODEL_SIZE=base`, configurable), no key |
| Text-to-speech | Browser speech synthesis on the web apps, local fallback voice for the simulator, no key |
| OCR | Tesseract locally first. Use LLM vision only when OCR confidence is low and call budget remains. |
| Embeddings and vector store | Local sentence-transformers and Chroma |
| WhatsApp | Simulator (primary). Real Meta Cloud API is optional (`CHANNEL=simulator` by default). |

**Call-budget controls (implement in `llm_gateway.py`)**
- `LLM_MAX_CALLS_PER_SESSION` (default 15) and `LLM_MAX_CALLS_PER_DAY` (default 200), tracked in the database, with an admin page showing calls used and remaining.
- A token-bucket rate limiter (`LLM_RPM_LIMIT`, default 5) so bursts never trip provider limits.
- Retry on HTTP 429/503 with exponential backoff and jitter (max 3 attempts), plus a circuit breaker that pauses LLM calls for a cool-down period after repeated failures.
- **Persistent response cache:** key = hash of (prompt template version, masked input, model). A repeat of the same request costs zero calls. `make demo-cache` pre-warms the cache for Scenarios A-D so the demo works with no quota and no network.
- **Call minimization:** polish only the top 3 alerts. Translate all messages for a report in one batched call. Run the agent panel only on flagged cases, with `PANEL_MODE=single_call` (all specialists in one structured call) as the free-tier default and `multi_call` as the option for paid keys.
- **Graceful fallback:** if the budget is exhausted, a call fails, or the circuit breaker is open, the system returns the complete rules-only report using the stored rule `patient_message` and `doctor_question` text. The UI shows a small badge "Verified rule text (AI polish unavailable)". The product must never show an error instead of a report.

**Data-privacy guard for free tiers**
Free API tiers may use submitted content to improve the provider's products. Therefore:
- Add `is_synthetic` (bool) to `Patient`. In free-tier mode the LLM gateway **refuses any payload for a patient where `is_synthetic=false`** unless `ALLOW_REAL_PATIENT_DATA=true` is set explicitly, and it logs the refusal.
- Show a visible banner in demo and admin UIs: "Free-tier mode: use synthetic data only."
- Masking (S7) still applies on top of this guard.

**Tests required:** simulated 429 triggers retry then fallback; budget exhaustion still yields a complete rules-only report; a cache hit makes zero provider calls; a non-synthetic patient is blocked in free-tier mode; `make demo` works with no network.

### 5.3 Repository layout

```
medguard/
  README.md  ASSUMPTIONS.md  prompt.md  Makefile  docker-compose.yml  .env.example
  docs/                  PROGRESS.md  ARCHITECTURE.md  SAFETY.md  API.md  DEMO.md
  backend/
    app/
      main.py  config.py  deps.py
      channels/          whatsapp.py  simulator.py  handlers.py  conversation.py
      voice/             stt.py  tts.py  language.py  translate.py
      vision/            ocr.py  strip_parser.py  slip_parser.py
      entities/          lexicon.py  matcher.py  resolver.py  context_rerank.py
      privacy/           pii.py  vault.py  consent.py  llm_gateway.py
      rules/             engine.py  schema.py  loader.py  durations.py  cascades.py  reconcile.py
      scores/            acb.py  fall_risk.py  renal.py
      rag/               ingest.py  retriever.py  citations.py
      agents/            graph.py  specialists.py  moderator.py  guardrails.py
      reports/           builder.py  guide_pdf.py  emergency_card.py  templates/
      review/            queue.py  decisions.py  rule_changes.py
      monitoring/        checkins.py  symptoms.py  scheduler.py
      models/            db.py  schemas.py
      api/               routes_*.py
      audit.py
    tests/
  rules/                 *.yaml  (versioned rule files)  classes.yaml  cascades.yaml  herbal.yaml
  knowledge/             guidelines/  (paraphrased summaries + user-supplied docs)  manifest.yaml
  data/                  lexicon_seed.csv  synthetic_patients.json  sample_audio/  sample_images/
  eval/                  cases.jsonl  asr_name_cases.jsonl  run_eval.py  report.md
  frontend/
    src/
      apps/landing/  apps/senior/  apps/caregiver/  apps/clinician/  apps/admin/  apps/simulator/
      components/  i18n/  api/  styles/ (tokens.css)
    e2e/
```

---

## 6. Data model (SQLAlchemy / Pydantic)

Implement these entities with migrations. All patient-linked tables carry `created_at`, `updated_at`, and are covered by the audit log.

- **User**: `id, role (senior|caregiver|clinician|admin), display_token, preferred_language, phone_hash, password_hash|otp, active`
- **Patient**: `id, owner_user_id, is_synthetic, age, sex, weight_kg?, height_cm?, language, consent_version, created_at`
- **CaregiverLink**: `patient_id, caregiver_user_id, permissions, notify_on[]`
- **Consent**: `patient_id, version, scopes[], granted_at, revoked_at?`
- **Medication**: `id, patient_id, raw_text, brand?, ingredients[] (generic, with strength), strength_text?, frequency_text?, route?, start_date?, end_date?, category (prescription|otc|supplement|herbal|ayush), source (voice|photo|text|import), confidence, confirmed (bool), confirmed_at, status (active|stopped|unknown)`
- **LabValue**: `patient_id, kind (creatinine_mg_dl|egfr|weight_kg|...), value, measured_at`
- **ConditionNote**: `patient_id, controlled_term, free_text?` (conditions entered as controlled terms where possible, because rules such as renal checks need them)
- **Alert**: `id, patient_id, rule_id, rule_version, severity (critical|high|moderate|low), type, involved_med_ids[], mechanism_summary, patient_message{lang->text}, doctor_question, sources[], evidence_level, status (pending_review|released|dismissed), created_at`
- **RiskScore**: `patient_id, kind (acb|fall_risk|renal), value, detail, computed_at`
- **AgentPanelRun**: `alert_ids[], specialist_outputs[], moderator_output, guardrail_flags[], approved_for_patient (bool)`
- **ReviewDecision**: `alert_or_case_id, clinician_id, decision (agree|reject), reason_tag?, note?, created_at`
- **RuleChangeProposal**: `id, rule_id?, proposed_change, justification, source_decisions[], status (open|accepted|rejected), reviewed_by?, created_at`
- **RuleVersion**: `version, file_hashes, released_at, released_by, changelog`
- **SymptomReport**: `patient_id, controlled_symptom, severity?, raw_text, reported_at, suspect_med_ids[]`
- **Report**: `id, patient_id, kind (safety|guide|emergency_card), file_path, share_token, expires_at`
- **AuditLog**: `id, actor, action, entity, entity_id, at, meta` (append-only)
- **PiiVaultEntry**: `token, encrypted_value, patient_id, created_at` (Fernet-encrypted, key from env)

---

## 7. Module specifications

### 7.1 Channels

**WhatsApp Cloud API (`channels/whatsapp.py`)**
- `GET /webhook/whatsapp` verifies `hub.verify_token`. `POST /webhook/whatsapp` validates the `X-Hub-Signature-256` header with the app secret and rejects invalid signatures.
- Handle `text`, `audio` (voice notes), `image`, and `interactive` (button replies). Download media through the Graph API with the access token, and store it temporarily (auto-delete after processing, default 24 hours).
- Send: text, audio, document (PDF), and interactive reply buttons (Yes / No / Say again, translated).
- Respect the 24-hour customer-service window. Proactive messages (weekly check-ins, caregiver alerts) outside the window must use pre-approved template messages. Define the templates in `docs/WHATSAPP_TEMPLATES.md` and select them in code. In demo mode, log the template that would be sent.
- Idempotency: ignore duplicate webhook deliveries (store message IDs).

**Simulator (`apps/simulator`)**
- A WhatsApp-style chat page that talks to the same `handlers.py` through the `Messenger` interface. It supports typed text, microphone recording (MediaRecorder), image upload, and sample-file buttons ("Play sample voice note", "Upload sample strip photo"), so the entire product can be demonstrated without Meta credentials.

**Conversation state machine (`channels/conversation.py`)**
States: `ONBOARD_CONSENT -> LANGUAGE -> MAIN_MENU -> COLLECT_MEDS -> CONFIRM_MEDS -> (ASK_LABS?) -> ANALYZING -> REPORT_READY -> MONITORING`. Support commands in any state: "add medicine", "my list", "report", "help", "call my caregiver", and "delete my data". Every state must handle unexpected input with a gentle re-prompt in the user's language.

Onboarding must obtain explicit consent (short, plain language, read aloud on request), then ask for language. Age and sex are asked in plain language, with weight and kidney test result optional.

### 7.2 Voice and language

- `SpeechToText.transcribe(audio, lang_hint) -> {text, language, words:[{w, start, end, conf}], avg_conf}`.
- Language detection from audio (or text) with a configurable list `SUPPORTED_LANGS=en,hi,kn` (the third is configurable to any regional language the chosen STT supports).
- **Custom vocabulary biasing:** pass the drug lexicon (generic names and top brands) as a prompt or phrase hints to the STT provider when supported. For local Whisper, build an `initial_prompt` from the most likely drug names for this patient (existing list first).
- **Translation with drug-name protection:** before translating any text, replace confirmed drug names with placeholders (for example `{{DRUG_1}}`), translate, restore the names, and run a back-translation check on the confirmation message. If the check fails, fall back to the pre-translated template.
- **TTS:** every system message can be spoken. Speak slowly by default (configurable rate), and let the user replay with one tap or the word "repeat".
- **Teach-back mode:** after the report summary, ask the senior (by voice or buttons) to confirm the key point in their own words, such as "Which two medicines should you ask your doctor about?" Accept any response, record whether the key items were mentioned, and offer to repeat if not. Never grade or shame the user.

### 7.3 Document vision

- `strip_parser.py`: from a photo of a medicine strip or bottle, extract brand, ingredient text, strength, and expiry if visible. Pre-process (rotate, deskew, contrast) before OCR.
- `slip_parser.py`: from a prescription photo, extract a list of drug lines (name, strength, frequency, duration). Handwritten text is lower confidence by definition. Flag handwriting with confidence below threshold for confirmation, and never auto-accept it.
- Output: candidate medications with per-field confidence. Every candidate flows into the same confirmation step as voice input.

### 7.4 Medication entity resolution (`entities/`)

Goal: map messy spoken or OCR'd text to canonical **generic ingredients** and **classes**.

**Lexicon** (`lexicon.py`): load from `data/lexicon_seed.csv` plus any dataset the user imports (script `scripts/import_lexicon.py`, for example a public medicines-with-generic-names dataset). Columns: `brand, ingredients (pipe-separated with strengths), form, category, source`. Also load RxNorm-style generic names, a herbal/AYUSH dictionary (`rules/herbal.yaml`), and transliterations (Hindi and regional spellings) for the 300 most common names.

**Matching pipeline** (`matcher.py`):
1. Normalize text: lowercase, strip punctuation, expand common abbreviations ("tab", "cap", "syp", "mg"), convert Indic script to Latin via transliteration, and keep the original.
2. Candidate generation: exact, then fuzzy (rapidfuzz WRatio), then phonetic (Metaphone on tokens), then character n-gram retrieval.
3. Score each candidate: `0.5*string_sim + 0.3*phonetic_sim + 0.2*asr_word_confidence`.
4. **Context re-ranking** (`context_rerank.py`): add a prior using the patient's existing list, age, and known conditions (for example, a blood-pressure drug is more likely for a patient already on other blood-pressure drugs). The prior may reorder close candidates but may never raise a candidate above the threshold on its own.
5. **Thresholds** (config): `ACCEPT >= 0.90 and margin >= 0.10` goes to read-back. `0.65 <= score < 0.90` or `margin < 0.10` means ask the user to choose between the top 2-3 options, or to send a photo of the strip. `< 0.65` means "I could not recognize that" with a photo prompt. Never auto-confirm.
6. Strength and frequency parsing: handle "40 mg", "once daily", "OD/BD/TDS", "morning and night", Hindi phrases such as "subah shaam", and store the raw phrase as well.

**Read-back:** produce a short message such as "I heard Telmisartan 40 mg, once a day. Is that right?" with buttons or a voice yes/no in the user's language. On "no", ask for a correction and re-run matching. Only confirmed items are written as `confirmed=true`.

### 7.5 Privacy and security (`privacy/`)

- **PII masking** (`pii.py`): detect person names (use Presidio or a rule-based approach plus a name list), phone numbers, email, addresses, dates of birth, government ID patterns (12-digit and PAN-style patterns), and pin codes. Replace with stable tokens such as `[PERSON_1]`. Keep the mapping in the encrypted vault (`vault.py`, Fernet, key in env), scoped to the patient.
- **LLM gateway** (`llm_gateway.py`): the only code path to any LLM. It accepts only masked text and structured data, logs hashes (not content) for audit, and raises if a PII detector flags the outgoing payload. Add a pytest that runs 50 PII-bearing inputs and asserts nothing sensitive reaches the (mocked) provider.
- **Restoring names:** only in the final patient-facing rendering, never inside prompts.
- **Consent and rights:** versioned consent records, an endpoint to export a patient's data, and an endpoint to delete it, which also purges vault entries, media, and reports.
- **Access control:** role-based; caregivers see only linked patients; clinicians see assigned or pooled cases with masked identifiers by default (an explicit, audited "reveal" action per case).
- **Transport and storage:** HTTPS expected in deployment; secrets only from env; passwords hashed (argon2/bcrypt); share links for reports use signed, expiring tokens.
- **Audit:** append-only log of every view, export, reveal, review decision, and rule change.

### 7.6 Rules engine (`rules/`)

Deterministic, versioned, fully unit-tested.

**Inputs:** the patient's confirmed `Medication` list (with ingredients, classes, start dates), age, sex, weight, labs, and condition terms.
**Outputs:** `Alert` objects, each with severity, mechanism summary, `patient_message` (per language), `doctor_question`, `sources`, `evidence_level`.

**Rule file schema** (`rules/schema.py`, validated at load):

```yaml
id: DDI-WARFARIN-NSAID
type: interaction_pair        # see rule types below
version: 1
a: {ingredient: warfarin}
b: {class: nsaid}
severity: high                # critical | high | moderate | low
evidence: established         # established | limited | theoretical
mechanism: "Higher bleeding risk when an anticoagulant is combined with an NSAID."
patient_message:
  en: "Two of your medicines can raise the chance of bleeding when taken together. Please ask your doctor or pharmacist about this combination."
  hi: "..."                   # pre-translated; mark needs native review
doctor_question: "Is the combination of warfarin and this pain reliever appropriate for me, and is there a safer option?"
sources: ["FDA label: warfarin", "AGS Beers Criteria (current)"]
review_status: seed_needs_review   # seed_needs_review | clinician_approved
```

**Rule types to implement:**

| Type | Meaning |
|------|---------|
| `duplicate_ingredient` | Same ingredient from two sources (for example two brands containing paracetamol). Include fixed-dose combination expansion. |
| `duplicate_class` | Two drugs of one class that should not be combined (for example two NSAIDs). |
| `interaction_pair` | Ingredient/class vs ingredient/class. |
| `interaction_combo` | Three or more items, such as the ACE inhibitor/ARB + diuretic + NSAID "triple whammy" for kidney injury. |
| `beers_pim` | Potentially inappropriate medication for age >= 65 (class or ingredient, with optional condition and duration modifiers). |
| `duration_exceeded` | Drug taken longer than a threshold (for example a proton pump inhibitor beyond 8 weeks, from `start_date`). |
| `renal_threshold` | Needs a creatinine clearance or eGFR threshold (see 7.7). |
| `cascade` | Drug A, then a symptom or Drug B within a time window suggests a prescribing cascade (see 7.6.2). |
| `herbal_interaction` | Herbal/AYUSH/supplement vs drug or class, always with an explicit evidence level. |
| `drug_condition` | Drug vs a controlled condition term. |

**Seed rules to include** (all marked `seed_needs_review` and traceable to a source; verify each against the real document before marking approved):
- Anticoagulant (warfarin, apixaban, rivaroxaban, dabigatran) + NSAID, + aspirin/antiplatelet (bleeding).
- ACE inhibitor or ARB + diuretic + NSAID (triple whammy, kidney injury).
- SSRI + NSAID (GI bleeding risk).
- Two NSAIDs (duplicate class). Paracetamol duplicated across products.
- Benzodiazepines and sedative-hypnotics in age >= 65 (Beers). First-generation antihistamines such as diphenhydramine, chlorpheniramine, hydroxyzine, promethazine in age >= 65 (Beers, anticholinergic).
- PPI beyond 8 weeks (Beers duration rule).
- Metformin with low eGFR (use label thresholds). NSAIDs with low creatinine clearance.
- Herbal: ginkgo, garlic supplements, turmeric/curcumin with anticoagulants or antiplatelets (bleeding; evidence usually `limited` or `theoretical`). Ashwagandha with sedatives and with thyroid medicines (evidence `limited`). Keep wording cautious and evidence-labeled.

#### 7.6.1 Alert ranking (alert fatigue)
Sort by `severity`, then `evidence`, then patient risk modifiers (age, renal function, anticoagulant). The patient report shows the **top 1 to 3** alerts expanded and collapses the rest under "Other things to mention". Clinician view shows everything with filters. Never hide a `critical` alert.

#### 7.6.2 Prescribing cascades (`cascades.py`, `rules/cascades.yaml`)
Use medication start dates and optional symptom reports. Seed with classic documented patterns:
- Calcium channel blocker (for example amlodipine), then ankle swelling, then a loop diuretic.
- NSAID, then raised blood pressure, then a new antihypertensive.
- ACE inhibitor, then cough, then a cough suppressant or antibiotic.
- Antipsychotic or metoclopramide, then parkinsonism symptoms, then an anticholinergic antiparkinson drug.
- Cholinesterase inhibitor, then urinary incontinence, then an anticholinergic bladder drug.
Cascade alerts are phrased as questions ("Could the swelling be related to the earlier medicine?"), never conclusions.

#### 7.6.3 Time on drug (`durations.py`)
Compute exposure from `start_date` (ask the user "about how long have you been taking this?" and accept ranges such as "about 3 months"). Store both the estimate and its uncertainty, and only fire duration rules when the lower bound exceeds the threshold, or label the alert as "possible" otherwise.

#### 7.6.4 Discharge reconciliation (`reconcile.py`)
Accept two lists (pre-admission and post-discharge, or any two snapshots). Report: drugs stopped but present again (the "boomerang" case), new drugs, changed strengths, duplicates introduced, and drugs missing without a recorded reason. Output as questions for the doctor, not as instructions.

### 7.7 Risk scores (`scores/`)

- **Anticholinergic burden (ACB scale):** table of drug to score (0-3) loaded from `knowledge/` (seed with a few well-known high-burden drugs such as diphenhydramine, amitriptyline, oxybutynin, promethazine, paroxetine at score 3; complete from the published scale). Total >= 3 is flagged. Show contributing drugs.
- **Fall-risk drugs:** count of sedatives, antihypertensives, diuretics, opioids, antipsychotics, antidepressants, and anticholinergics. Show a simple Low / Medium / High band with the contributing drugs.
- **Renal function:** Cockcroft-Gault creatinine clearance when age, weight, sex and serum creatinine are provided: `CrCl = ((140 - age) * weight_kg) / (72 * SCr_mg_dl)`, multiplied by 0.85 for females. Store the formula version. If an eGFR value is given directly, use it. If inputs are missing, say so and skip renal rules rather than guessing.

### 7.8 RAG (`rag/`)

- **Ingestion** (`ingest.py`): read Markdown/PDF/text from `knowledge/guidelines/`, chunk by heading (about 300 to 500 tokens, overlap 50), and store chunk text, source document, section, and a stable `chunk_id`. Document metadata comes from `knowledge/manifest.yaml` (title, publisher, year, license note).
- **Seed corpus:** ship short, original paraphrased summaries (written by you, not copied) for the frameworks in the briefing: AGS Beers Criteria, STOPP/START, Medication Appropriateness Index, and the main interaction topics. Each summary file ends with a "source" line naming the original publication.
- **Retrieval** (`retriever.py`): hybrid (BM25 plus embeddings), top-k with a score threshold. Retrieval is always keyed by the alert's rule ID and ingredients first, then by free text.
- **Citation enforcement** (`citations.py`): any generated explanation sentence that makes a clinical claim must reference at least one retrieved `chunk_id` or a rule ID. Unreferenced claims are removed, and if nothing remains, fall back to the stored rule `patient_message`.
- **Refusal behavior:** if retrieval finds nothing relevant, answer "I do not have reliable information on that. Please ask your pharmacist or doctor." Do not improvise.

### 7.9 Specialty agent panel (`agents/`)

Built with LangGraph. Runs **only when the rules engine produced at least one alert at severity `moderate` or above, or when rules from two or more domains fired.**

**Specialists:** Cardiology, Nephrology, Geriatrics/Neurology, GI/Bleeding. Each receives only (a) the masked, structured patient profile, (b) the alerts relevant to its domain (by a domain tag on each rule), and (c) retrieved evidence chunks for those alerts.

**Each specialist returns strict JSON:**
```json
{
  "domain": "nephrology",
  "concerns": [{"alert_id": "...", "statement": "...", "evidence_ids": ["chunk_id", "..."]}],
  "questions_for_doctor": ["..."],
  "tradeoffs": ["..."],
  "confidence": "low|medium|high"
}
```

**Moderator** (`moderator.py`) merges the outputs into:
- `agreements` (concerns shared by two or more specialists),
- `conflicts` (where one domain's concern pulls against another's, stated neutrally, for example "Cardiology prefers continuing X; Nephrology flags kidney risk with X"),
- `human_decision_needed` (always true when `conflicts` is non-empty),
- `top_questions_for_doctor` (deduplicated, at most 5).
The moderator must not choose a winner, produce a "consensus treatment", or recommend a dose or stop.

**Guardrails** (`guardrails.py`), applied to every agent output:
- Reject or rewrite directive phrases (stop, start, increase, decrease, switch, discontinue, take X mg) into "ask your doctor whether...".
- Drop claims with no `evidence_ids`.
- Block any new alert that is not in the rules engine output (agents may add commentary, never alerts).
- Cap output length and enforce JSON schema, with one retry then fallback to the rules-only report.
- Mark everything `approved_for_patient=false` until a clinician approves (S8).

**Cost control:** cache results by (rule set hash, profile hash). Limit to one panel run per profile change.

### 7.10 Reports (`reports/`)

**Plain-language safety report** (per patient, per language) contains:
1. A one-sentence summary ("2 things worth discussing with your doctor soon").
2. Top 1-3 alerts, each with: what was found, why it matters (one or two sentences), and the question to ask.
3. "Other things to mention" (collapsed lower-severity alerts).
4. Risk scores in simple bands, with contributing drugs.
5. Data limitations (unrecognized brands, missing labs, uncertain durations).
6. Disclaimer: "MedGuard is a decision-support tool. It does not replace a doctor or pharmacist. Do not start, stop, or change any medicine without talking to a qualified professional."
Delivered as text, as a voice message (TTS), and on the senior web app with large text.

**Doctor Discussion Guide PDF** (`guide_pdf.py`): one page, A4, large readable type:
- Header with masked identity (initials or token), age, date, language of origin.
- Current medication table (generic name, brand, strength, how long, source).
- Top conflicts ranked by severity, each with the question to ask.
- Risk score summary.
- Space for the doctor's notes.
- QR code to a signed, expiring read-only web view of the same content.
- Disclaimer.

### 7.11 Clinician review (swipe) (`review/`, `apps/clinician`)

- **Queue:** cases ordered by severity, then age of case. Each card shows the masked profile, the medication list, the alerts with citations, the agent panel summary (if any), and the draft patient message.
- **Swipe:** right = agree, left = disagree, up = needs more info (optional), plus keyboard arrows and buttons for accessibility. On left or up, a modal requires a **reason tag**: `false_positive | clinically_acceptable | missing_context | wrong_severity | unclear_wording | other`, plus an optional note. Undo within 10 seconds.
- **Edits:** the clinician can edit the patient message wording before approval (stored as a suggestion; original kept).
- **Release:** `agree` marks the alert and the AI commentary `approved_for_patient=true` and releases it to the senior and caregiver. Critical rule-engine alerts are released to the patient immediately with a "talk to your doctor soon" message, and clinician review then refines them.
- **Identity masking:** identifiers hidden by default, with an audited reveal.

**Governed feedback loop** (`rule_changes.py`): aggregate review decisions per rule. When a rule gets repeated rejections with the same reason (default: 5 decisions, at least 60% rejected), create a `RuleChangeProposal` with the evidence. Admins review proposals in `apps/admin`, accept or reject, and an accepted change creates a new `RuleVersion` after a clinician sign-off. **Nothing updates rules or models automatically.**

### 7.12 Caregiver mode

- Link flow: the senior shares a code on WhatsApp or in the app, and the caregiver accepts after consent.
- Dashboard: full medication list, latest report, active alerts, review status, symptom check-in history, refill and new-prescription notices.
- Notifications (WhatsApp templates or in-app): new medication added, new critical or high alert released, red-flag symptom reported, missed weekly check-in (two in a row).
- Caregiver can add or edit medicines on the senior's behalf, with the same confirm-before-store flow, and every edit is attributed in the audit log.
- Printable summary and the Doctor Discussion Guide download.

### 7.13 Senior accessibility (`apps/senior`)

- Large type (base 20px, scalable to 200%), high-contrast theme, big touch targets (>= 56px), simple one-action-per-screen layout.
- **Visual difficulty:** every screen is fully voice-operable and screen-reader friendly (semantic HTML, ARIA labels), with a "read this to me" button and auto-read option.
- **Hearing difficulty:** captions and large text for every voice message, visual alerts for notifications, adjustable TTS speed and volume, and a text-only mode.
- One-tap "Call my caregiver" (tel: link) and "Call emergency" shortcuts.
- Meet WCAG 2.2 AA, and add automated checks with axe in Playwright.
- Language switcher visible on every screen, with the chosen language remembered.

### 7.14 Monitoring and symptom check-ins (`monitoring/`)

- Weekly check-in (configurable day/time, user-chosen) by WhatsApp voice or text: "Any dizziness, falls, confusion, constipation, bleeding, or swelling this week?"
- **Controlled symptom vocabulary** with multilingual synonyms (for example dizziness, fall, confusion, constipation, nausea, bleeding, swelling, drowsiness). Map free speech to terms with the same matching approach as drugs, and ask a clarifying question when unsure.
- **Symptom-to-drug linking:** rules map symptoms to drug classes that commonly cause them (for example dizziness and falls to antihypertensives, sedatives, diuretics). Present as "this might be related to..." questions for the doctor.
- **Red flags** (S6) bypass everything. Store the event, notify the caregiver, and show emergency guidance.
- Re-run the rules engine when a new medication is added, when a start date changes, or when labs change.
- Reminder scheduling for check-ins is controlled by the user ("stop reminders" must work at any time).

### 7.15 Emergency medication card (`reports/emergency_card.py`)

A compact printable PDF and a PNG for the phone lock screen: masked name or initials, age, current medicines (generic names with strengths), key alert flags (such as "on a blood thinner"), and a QR link to the signed read-only view with a configurable expiry. Make it a one-tap action from WhatsApp ("emergency card").

### 7.16 UI design system (Apple-inspired)

All web apps (`landing`, `senior`, `caregiver`, `clinician`, `admin`, `simulator`) share one design system in `frontend/src/styles/tokens.css` and `frontend/src/components/`, documented in `docs/DESIGN.md`. The visual language is **inspired by Apple's website and apps**: calm, spacious, typographic, minimal color, soft depth. It is not a copy.

**Legal and brand rules**
- Do not use Apple logos, product photos, trademarked names, or the SF Pro font files. Use the system font stack so Apple devices render their own system font, with a self-hosted open fallback.
- Do not imply any affiliation with Apple. MedGuard gets its own simple wordmark and logo (an original SVG shield with a pulse line).

**Design tokens**

```css
:root {
  --font: -apple-system, BlinkMacSystemFont, "SF Pro Text", "SF Pro Display", "Inter",
          "Noto Sans", "Noto Sans Devanagari", "Noto Sans Kannada", system-ui, sans-serif;
  /* Light */
  --bg: #ffffff;  --bg-alt: #f5f5f7;  --surface: #ffffff;
  --text: #1d1d1f;  --text-secondary: #515154;   /* >= 7:1 on white for seniors */
  --accent: #0071e3;  --link: #0066cc;
  --hairline: rgba(0,0,0,0.12);
  --sev-critical: #d70015; --sev-high: #c93400; --sev-moderate: #8a5a00; --sev-low: #1d7d3f;
  --radius-card: 24px; --radius-input: 12px; --radius-pill: 980px;
  --shadow-card: 0 4px 24px rgba(0,0,0,0.08);
  --ease: cubic-bezier(0.28, 0.11, 0.32, 1);
}
@media (prefers-color-scheme: dark) {
  :root { --bg:#000000; --bg-alt:#1d1d1f; --surface:#1c1c1e; --text:#f5f5f7;
          --text-secondary:#a1a1a6; --accent:#2997ff; --link:#2997ff;
          --hairline: rgba(255,255,255,0.16); --shadow-card: none; }
}
```
Verify every text/background pair with an automated contrast test (>= 4.5:1, and >= 7:1 for body text in the senior app). Never rely on color alone: severity always pairs color with an icon and a text label.

**Typography**
- Hero headline: `clamp(40px, 7vw, 80px)`, weight 600, letter-spacing -0.02em, line-height 1.05.
- Section headline: `clamp(32px, 5vw, 56px)`, weight 600. Body 21px on landing and caregiver/clinician, **22px minimum in the senior app** (scalable to 200%).
- Self-host Inter plus Noto Sans for Devanagari and the chosen regional script, so Indic text renders cleanly everywhere. Test line-height for Indic scripts (they need more).

**Layout**
- Generous whitespace: section padding 96-160px desktop, 56-80px mobile. Content max width 980px (text) and 1200px (tile grids). Alternate section backgrounds between `--bg` and `--bg-alt`.
- Sticky translucent top bar, 48px high: `background: rgba(255,255,255,0.72); backdrop-filter: saturate(180%) blur(20px);` with a solid fallback when blur is unsupported or when `prefers-reduced-transparency` is set. Local sub-nav on the landing page (Overview, How it works, Safety, Caregivers, Clinicians).
- Responsive breakpoints: 320, 768, 1024, 1440. No horizontal scroll at any width.

**Components** (build once, reuse everywhere): pill buttons (filled primary, outlined secondary, and text links with a chevron such as "Learn more"), tile cards with 24px radius, bento grid, segmented control (language switcher, tabs), **inset grouped lists** in the style of Settings (medication list, alerts), toggles, bottom sheets on mobile and centered dialogs on desktop, toasts, skeleton loaders, and a generic rounded device frame (original CSS, not an Apple device lookalike) for embedding the simulator on the landing page. Icons: Lucide (open license). No emoji in the UI.

**Motion**
- Easing `--ease`, durations 300-600ms. Scroll-reveal fade-up (24px) for sections, spring physics for swipe cards, a soft pulse on the microphone button while listening.
- Respect `prefers-reduced-motion`: replace all movement with instant or opacity-only changes. No autoplaying video with sound, and any video has visible controls.

**Landing page (`apps/landing`)**
Sections: hero ("Medicine safety, in your language." with two buttons, "Try the demo" and "How it works"), bento tiles for the headline capabilities, a three-step scroll story (Say it, Check it, Share it), an embedded live simulator in the device frame, a privacy and safety section (masking, citations, clinician review), caregiver and clinician sections, and a footer with small-print disclaimers in the style of footnotes. Keep copy short and plain.

**Per-app guidance**
- **Senior (`apps/senior`):** one action per screen, a big circular microphone button, text and speech side by side, a visible text-size slider and high-contrast toggle, always-present "Call my caregiver". Calmer and larger than the other apps. Never use the translucent bar over body text in a way that reduces contrast.
- **Caregiver:** card-based dashboard with the medication list as an inset grouped list, a clear "What changed" section, and a one-tap guide download.
- **Clinician:** a split view on desktop (queue on the left, case detail on the right) like Apple Mail and Notes, a swipe card stack on mobile with spring physics and keyboard arrows, reason-tag sheet on reject, and dark mode that works for long reading sessions.
- **Admin:** inset grouped tables, with a rule-proposal diff view and the LLM usage meter.
- **Simulator:** looks like a clean messaging screen (generic, not a copy of WhatsApp's branding), with an inline voice-note player and quick-reply chips.

**Quality gates**
- Playwright visual snapshots for the landing page, senior home, clinician queue and one alert card in light and dark at 375, 768 and 1440 widths.
- axe accessibility checks pass on every screen. Lighthouse targets on the landing page: Accessibility >= 95, Performance >= 90, with optimized images, preloaded fonts and no layout shift.
- A reduced-motion test and a 200% zoom test pass.

---

## 8. API surface (FastAPI, documented in OpenAPI)

All endpoints require auth except webhooks and signed share links. Return typed JSON, and use consistent error shapes.

| Group | Endpoints |
|-------|-----------|
| Auth | `POST /auth/login`, `POST /auth/otp/request`, `POST /auth/otp/verify`, `POST /auth/logout` |
| Patients | `POST /patients`, `GET /patients/{id}`, `PATCH /patients/{id}`, `DELETE /patients/{id}` (full purge), `GET /patients/{id}/export` |
| Consent | `POST /patients/{id}/consent`, `DELETE /patients/{id}/consent` |
| Medications | `POST /patients/{id}/medications/intake` (text/audio/image, returns candidates), `POST /patients/{id}/medications/confirm`, `GET /patients/{id}/medications`, `PATCH`/`DELETE` per item |
| Labs/conditions | `POST /patients/{id}/labs`, `POST /patients/{id}/conditions` |
| Analysis | `POST /patients/{id}/analyze` (rules, scores, optional panel), `GET /patients/{id}/alerts`, `GET /patients/{id}/scores` |
| Reconciliation | `POST /patients/{id}/reconcile` (two list snapshots) |
| Reports | `GET /patients/{id}/report?lang=`, `GET /patients/{id}/guide.pdf`, `GET /patients/{id}/emergency-card.pdf`, `GET /share/{token}` (signed, expiring) |
| Review | `GET /review/queue`, `POST /review/{case_id}/decision`, `POST /review/{case_id}/undo`, `POST /review/{case_id}/reveal` (audited) |
| Governance | `GET /admin/rule-proposals`, `POST /admin/rule-proposals/{id}/decide`, `GET /admin/rules`, `GET /admin/rule-versions`, `POST /admin/rules/reload` |
| Caregiver | `POST /caregivers/link`, `GET /caregivers/patients`, `POST /caregivers/notify-prefs` |
| Monitoring | `POST /patients/{id}/symptoms`, `GET /patients/{id}/checkins`, `POST /patients/{id}/checkins/schedule` |
| Channels | `GET/POST /webhook/whatsapp`, `POST /simulator/message`, `GET /simulator/stream` (SSE or WebSocket) |
| Health | `GET /healthz`, `GET /readyz` |

Generate an OpenAPI schema and TypeScript client types (`frontend/src/api/`) from it so the frontend and backend stay in sync.

---

## 9. Seed data, synthetic patients, demo scenarios

### 9.1 Lexicon seed (`data/lexicon_seed.csv`)
Create about 150 rows covering common Indian brands and generics. Verify every brand to ingredient mapping against a public dataset before marking it trusted, and flag unverified rows. Starter examples to verify: Dolo 650 and Crocin (paracetamol), Combiflam (ibuprofen + paracetamol), Brufen (ibuprofen), Voveran (diclofenac), Ecosprin (aspirin), Telma (telmisartan), Amlong (amlodipine), Cardace (ramipril), Betaloc (metoprolol), Lasix (furosemide), Glycomet (metformin), Atorva (atorvastatin), Pan 40 (pantoprazole), Omez (omeprazole), Alprax (alprazolam), Benadryl (diphenhydramine-containing cough syrup). Include herbal items: ashwagandha, turmeric/curcumin, ginkgo biloba, garlic supplement, brahmi, triphala, giloy.

### 9.2 Synthetic patients (`data/synthetic_patients.json`)
At least 12 invented patients with realistic mixes, covering clean lists, single conflicts, multiple conflicts, and edge cases (missing labs, unknown brand, uncertain durations). Use obviously fake names and phone numbers.

### 9.3 Demo scenarios (must work end to end in `make demo`)
- **Scenario A, bleeding risk:** age 74 woman on warfarin, aspirin (low dose), Combiflam for knee pain, and an ashwagandha supplement, with a PPI taken for about 14 weeks. Expected: anticoagulant + NSAID alert, anticoagulant + antiplatelet alert, herbal alert with limited evidence, PPI duration alert, and a panel run with Cardiology and GI/Bleeding views.
- **Scenario B, kidney risk:** age 69 man on telmisartan, furosemide, and diclofenac, with creatinine supplied and metformin. Expected: triple-whammy combo alert, renal threshold checks (computed CrCl shown), and a Nephrology concern in the panel.
- **Scenario C, cascade and falls:** age 80 woman on amlodipine for 6 months, a loop diuretic started about 4 months ago after "ankle swelling", diphenhydramine as a sleep aid, and alprazolam. Expected: cascade question, two Beers alerts, ACB total flagged, high fall-risk band.
- **Scenario D, boomerang:** two snapshots (pre-admission and post-discharge, then a later pharmacy refill) in which an NSAID stopped at discharge reappears. Expected: reconciliation output as doctor questions.
- **Voice demo:** sample Hindi and English voice notes (with sidecar transcripts) naming drugs, including one deliberately ambiguous name that triggers the "which one did you mean" flow, and one red-flag phrase.

---

## 10. Evaluation and testing

### 10.1 Unit and integration tests
- Rules engine: at least one positive and one negative test per rule type and per seed rule.
- Matching: property tests with Hypothesis for typos, transliteration variants, and abbreviations.
- Safety tests for S1-S10: directive-language rewriting, citation enforcement, PII leak test across every LLM call, red-flag routing, confirm-before-store, gated AI commentary.
- API tests for auth and role boundaries (a caregiver must not see unlinked patients).

### 10.2 Evaluation harness (`eval/run_eval.py`, output to `eval/report.md`)
1. **Conflict detection:** `eval/cases.jsonl` with at least 50 cases (medication list, age, labs, expected alert rule IDs, expected absence). Report precision and recall per rule type and overall, plus a list of misses and false positives.
2. **ASR drug-name resolution:** `eval/asr_name_cases.jsonl` with at least 100 simulated mis-hearings and brand variants. Report top-1 and top-3 accuracy and the "asked for clarification" rate, with and without context re-ranking, and the rate of **wrong auto-accepts** (must be 0 in the committed run).
3. **Grounding:** sample of generated explanations, with the percentage of claims that carry a valid citation (target 100% after enforcement).
4. **Safety red team:** a set of 30 adversarial prompts (asking the assistant to prescribe, to stop a drug, to ignore rules, to reveal data) with an expected refusal or safe redirect.
5. **Latency:** rules check under 1 second for a 15-item list on a laptop, and full report with the panel under 30 seconds in live mode.
Commit the generated report so judges and clinicians can read the numbers.

### 10.3 End to end (Playwright)
- Simulator flow: consent, language, voice note, read-back, confirm, report, guide download.
- Clinician flow: open queue, swipe agree, swipe disagree with reason, undo, reveal audited.
- Caregiver flow: link, receive alert, view list.
- Accessibility: axe checks on every screen, keyboard-only navigation, 200% zoom.

---

## 11. Configuration and DevOps

`.env.example` must list: `MODE`, `FREE_TIER_MODE`, `CHANNEL`, `LLM_MODEL`, `LLM_MAX_CALLS_PER_SESSION`, `LLM_MAX_CALLS_PER_DAY`, `LLM_RPM_LIMIT`, `PANEL_MODE`, `STT_MODEL_SIZE`, `ALLOW_REAL_PATIENT_DATA`, `DATABASE_URL`, `SECRET_KEY`, `VAULT_KEY`, `SUPPORTED_LANGS`, `DEFAULT_LANG`, `REQUIRE_CLINICIAN_APPROVAL_FOR_AI_COMMENTARY`, provider selectors (`STT_PROVIDER`, `TTS_PROVIDER`, `OCR_PROVIDER`, `LLM_PROVIDER`, `TRANSLATE_PROVIDER`), provider keys, WhatsApp settings (`WA_VERIFY_TOKEN`, `WA_APP_SECRET`, `WA_ACCESS_TOKEN`, `WA_PHONE_NUMBER_ID`), media retention hours, matching thresholds, and review thresholds.

**Makefile targets:** `make setup`, `make dev` (api + web), `make seed` (lexicon, rules, knowledge ingest, synthetic patients), `make demo-cache` (pre-warm the LLM cache for Scenarios A-D), `make demo` (stubs or cache plus seeded scenarios and the simulator open), `make test`, `make e2e`, `make eval`, `make lint`, `make docker-up`.

**Docker Compose:** `api`, `web`, optional `db` (Postgres). One command brings up a working demo.

**Logging and observability:** structured JSON logs without PII, request IDs, basic metrics endpoint, and clear error messages when a provider is missing.

---

## 12. Build phases and acceptance criteria

Complete in order. Do not start a phase until the previous phase's tests pass.

| Phase | Build | Acceptance |
|-------|-------|-----------|
| 1 Foundations | Repo, config, DB models and migrations, auth and roles, audit log, provider interfaces and stubs, free-tier call budget, cache and fallback in the LLM gateway, Makefile, Docker | `make setup && make test` passes; `/healthz` ok; roles enforced |
| 2 Knowledge and entities | Lexicon import, matcher, context re-rank, strength/frequency parsing, herbal dictionary, read-back logic | ASR name eval runs; zero wrong auto-accepts; confirm-before-store test passes |
| 3 Rules and scores | Rule schema/loader, all rule types, seed rules, cascades, durations, risk scores, reconciliation, ranking | Scenarios A-D produce the expected alerts; per-rule tests pass |
| 4 Privacy and RAG | PII masking, vault, LLM gateway, consent/export/delete, RAG ingest/retrieve/citations | PII leak test passes; citation enforcement test passes; delete purges all data |
| 5 Agents | LangGraph panel, specialists, moderator, guardrails, caching, gating | Directive-language tests pass; panel runs only on flagged cases; AI commentary hidden until approved |
| 6 Channels and voice | WhatsApp webhook and sending, simulator, conversation state machine, STT/TTS, translation with drug protection, vision parsers, red-flag flow | Simulator end-to-end demo works in `MODE=demo`; webhook signature test passes |
| 7 Reports | Safety report, guide PDF with QR, emergency card, share links | PDF renders on one page with QR; signed link expires correctly |
| 8 Frontends | Design system (Section 7.16), landing page, senior PWA, caregiver dashboard, clinician swipe UI, admin rule-proposal UI, simulator polish, i18n | Playwright e2e, axe, contrast, reduced-motion and visual snapshot checks pass; keyboard-only review works; landing page meets Lighthouse targets |
| 9 Monitoring and governance | Weekly check-ins, symptom linking, notifications, rule-change proposals, rule versioning | Check-in cycle works in demo with fast-forward clock; proposal triggers after the threshold |
| 10 Evaluation and docs | Full harness and committed report, README, SAFETY.md, DEMO.md, ARCHITECTURE.md with diagrams | `make eval` produces `eval/report.md`; a new developer can run `make demo` from the README alone |

---

## 13. Definition of done

- [ ] `make demo` runs the whole product offline (stubs) and a person can complete Scenarios A-D from the simulator and the web apps.
- [ ] With a free Gemini API key set, `MODE=live` works for LLM polish, translation and the agent panel, with local Whisper, Tesseract and browser TTS, and the call-budget, cache and fallback behavior in Section 5.2b is tested.
- [ ] The WhatsApp simulator completes every flow. The real Meta WhatsApp webhook is implemented and tested with signed sample payloads, and works with Meta test credentials when supplied (optional for this build).
- [ ] All ten headline capabilities in Section 1 and every extra feature are implemented and reachable from the UI or WhatsApp.
- [ ] The UI follows the design system in Section 7.16 (tokens, components, light and dark mode, landing page) and passes the quality gates.
- [ ] Safety principles S1-S10 each have a passing automated test.
- [ ] `eval/report.md` is generated and committed, with precision/recall, ASR resolution, grounding, red-team and latency numbers.
- [ ] No real personal data in the repo; `.env.example` complete; no secrets committed.
- [ ] README, SAFETY.md, DEMO.md, ARCHITECTURE.md, ASSUMPTIONS.md and the OpenAPI docs are complete.
- [ ] Every seed rule is listed in `docs/RULES_REVIEW.md` with its source and review status, so a clinician can review them.

---

## 14. Known limitations to state honestly (put in README and SAFETY.md)

- MedGuard is not a certified medical device and has not been clinically validated. Do not use it for real treatment decisions. Before any clinical deployment, assess the applicable Indian regulatory requirements (software as a medical device) and data protection law.
- Seed rules and translations require clinician and native-speaker review.
- Indian brand coverage depends on the imported datasets and will be incomplete.
- Beers and STOPP/START come from US and European contexts, and local prescribing patterns differ.
- Speech and handwriting recognition are error-prone, which is why confirmation is mandatory.
- Herbal and AYUSH interaction evidence is often limited, and the system labels it that way.
- LLM output can still be wrong, so patient-facing content is rules-first, cited, and gated.

---

## 15. Optional work split when using two coding agents

Agree on contracts first (OpenAPI schema, Pydantic models, the medication profile JSON, and the alert JSON), then work in parallel in separate branches with one person merging.

- **Agent A (backend and clinical core):** Phases 1-5 and 7, plus the evaluation harness.
- **Agent B (channels and frontends):** Phase 6 channel code, Phase 8, and the simulator, against the contract and a mocked API.
- **Cross-review:** each agent reviews the other's pull request. A human verifies the safety-critical code (rules, guardrails, PII masking, citation enforcement) line by line against the sources.


---

## 16. Running this build in Google Antigravity

### 16.1 Setup
1. Create an empty Git repository, put this file at the root as `prompt.md`, and commit it. Open the folder in Antigravity.
2. Create `.env` from `.env.example` after Phase 1. Put your free Gemini API key from Google AI Studio in `GEMINI_API_KEY`. Do not commit `.env`.
3. Terminal safety: set the terminal policy so commands that install packages, delete files, or call the network need your review before running. Approve routine test and lint commands freely.
4. If your Antigravity version supports plan, task-list, and walkthrough artifacts, ask the agent to produce them for each phase and save a copy under `docs/`. Use the built-in browser agent to exercise the simulator and web apps, and save screenshots into `docs/screens/`.

### 16.2 How to run it
- **One conversation per phase** (Section 12). A single giant session loses context. Every new conversation starts with the kickoff prompt in 16.3, which makes the agent re-read `prompt.md` and `docs/PROGRESS.md`.
- **Parallel agents (optional):** after Phase 1 defines the API contract, run two agents. Agent A owns `backend/`, `rules/`, `knowledge/`, `eval/`. Agent B owns `frontend/`. Neither edits the other's directory. A human merges.
- **Stop at checkpoints:** after Phase 3 (rules) and Phase 5 (agents and guardrails), a human reviews `docs/RULES_REVIEW.md`, the guardrail tests, and a sample of generated reports before continuing.
- If an agent claims a phase is done, run `make test` yourself. Do not accept "done" without green tests.

### 16.3 Kickoff prompts (copy and paste, one per conversation)

**Master prompt (use at the start of every conversation):**
```
Read prompt.md in full, then read docs/PROGRESS.md and ASSUMPTIONS.md if they exist.
Execute ONLY Phase <N> from Section 12 of prompt.md, following every relevant module spec and safety principle (S1-S10).
Do not ask me questions; record assumptions in ASSUMPTIONS.md.
Never invent clinical facts; every rule needs a source and review_status as described.
Use FREE_TIER_MODE defaults and offline stubs so everything runs without paid keys.
When finished: run make test (and make eval if the phase touches rules, entities or RAG), fix failures, update docs/PROGRESS.md with what works, what is stubbed, and what is next, then stop and summarize.
```

**Phase-specific additions (append one line to the master prompt):**
1. `Phase 1: Foundations. Also implement the LLM gateway with budget, rate limit, retry, circuit breaker, cache and rules-only fallback from Section 5.2b.`
2. `Phase 2: Knowledge and entities. Build the lexicon import, matcher, context re-ranking and read-back logic, plus eval/asr_name_cases.jsonl with at least 100 cases.`
3. `Phase 3: Rules and scores. Implement all rule types, seed rules, cascades, durations, risk scores, reconciliation and alert ranking; make Scenarios A-D produce the expected alerts; create docs/RULES_REVIEW.md.`
4. `Phase 4: Privacy and RAG. Implement PII masking, vault, consent, export and delete, the is_synthetic guard, and RAG with citation enforcement.`
5. `Phase 5: Agents. Implement the LangGraph specialty panel (PANEL_MODE=single_call by default), moderator, guardrails, caching and the clinician-approval gate.`
6. `Phase 6: Channels and voice. Build the simulator channel first, then the conversation state machine, local Whisper STT, browser TTS, translation with drug-name protection, vision parsers, red-flag flow, and the real WhatsApp webhook tested with signed sample payloads.`
7. `Phase 7: Reports. Build the safety report, one-page Doctor Discussion Guide PDF with QR, emergency card and signed share links.`
8. `Phase 8: Frontends. First build the design system from Section 7.16 (tokens.css, shared components, docs/DESIGN.md), then the landing page, senior PWA, caregiver dashboard, clinician swipe UI, admin pages (including LLM usage meter and rule proposals) and i18n. Add Playwright, axe, contrast, reduced-motion and visual snapshot tests. Use the browser agent to review each screen against the design rules in light and dark mode and save screenshots.`
9. `Phase 9: Monitoring and governance. Build weekly check-ins with a fast-forward demo clock, symptom linking, notifications, rule-change proposals and rule versioning.`
10. `Phase 10: Evaluation and docs. Run make eval, commit eval/report.md, and complete README, SAFETY.md, DEMO.md and ARCHITECTURE.md so a new developer can run make demo from the README alone.`

### 16.4 If something goes wrong
- **Agent invents rules or sources:** open `rules/*.yaml`, delete anything without a real source, and re-run the Phase 3 prompt with "remove unsourced rules".
- **Context drift in a long phase:** start a new conversation with the master prompt, which re-reads `prompt.md` and `docs/PROGRESS.md`.
- **Quota errors from Gemini:** this is expected on free tiers. Confirm the fallback badge appears and the report is still complete, then run `make demo-cache` before presenting.
- **Dependency conflicts:** ask the agent to pin versions in `requirements.txt` and `package.json`, and to explain any new dependency it adds.
