# MedGuard Demo Guide

This guide walks through all official demonstration scenarios included in MedGuard. The entire product runs locally and offline without external API keys or cloud credentials.

---

## 1. Quickstart

Run one command to initialize, seed synthetic profiles, prewarm offline caches, and launch the server:

```bash
make demo
```

Once running, navigate to:
- **Web Applications:** [http://localhost:8000](http://localhost:8000) (Interactive SPA serving Landing, Senior, Caregiver, Clinician, Admin, and Simulator)
- **API Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs) (Interactive OpenAPI Swagger UI)

---

## 2. Core Clinical Scenarios

### Scenario A: Bleeding Risk Matrix
- **Patient Profile:** Female, 74 years old.
- **Medications:**
  - `Warfarin 2mg` (Anticoagulant)
  - `Ecosprin 75mg` (Aspirin - Antiplatelet)
  - `Combiflam` (Ibuprofen + Paracetamol - NSAID) taken for knee osteoarthritis
  - `Ashwagandha Churna` (5g nightly Ayurvedic supplement)
  - `Pantocid 40mg` (Pantoprazole - PPI) taken continuously for 14 weeks
- **What to Observe:**
  1. **Dual Antithrombotic + NSAID Alert:** Fired by `DDI-WARFARIN-NSAID` and `DDI-ANTICOAG-ANTIPLATELET`.
  2. **Herbal Interaction:** Fired by `HERB-ASHWAGANDHA-INTERACTION` noting additive bleeding risk.
  3. **Duration Exceeded:** Fired by `DURATION-PPI-8WEEKS` noting that continuous PPI therapy beyond 8 weeks warrants deprescribing review.
  4. **Multi-Specialist Deliberation:** Cardiology and GI specialists recommend discussing topical pain relief alternatives with the prescribing physician.

### Scenario B: Kidney Risk / Triple Whammy
- **Patient Profile:** Male, 69 years old.
- **Medications & Labs:**
  - `Telma 40` (Telmisartan - ARB)
  - `Lasix 40` (Furosemide - Loop Diuretic)
  - `Voveran 50` (Diclofenac - NSAID)
  - `Glycomet 500` (Metformin)
  - *Serum Creatinine:* 2.4 mg/dL
- **What to Observe:**
  1. **Triple Whammy Critical Alert:** Fired by `COMBO-TRIPLE-WHAMMY` detecting the simultaneous hemodynamic assault on glomerular filtration.
  2. **Renal Function Calculator:** Computes Cockcroft-Gault estimated clearance (< 30 mL/min) and triggers `RENAL-NSAID` and `RENAL-METFORMIN`.
  3. **Nephrology Deliberation:** Flags acute risk of hospital admission for renal failure.

### Scenario C: Prescribing Cascade & Falls
- **Patient Profile:** Female, 80 years old.
- **Medications:**
  - `Amlong 5` (Amlodipine) started 6 months ago for hypertension
  - `Dytor 10` (Torsemide) added 4 months ago to treat ankle swelling
  - `Benadryl` (Diphenhydramine) taken OTC for sleep
  - `Alprax 0.5` (Alprazolam) taken for nighttime anxiety
- **What to Observe:**
  1. **Prescribing Cascade Alert:** Fired by `CASCADE-CCB-DIURETIC`, detecting that the loop diuretic was prescribed to treat harmless amlodipine-induced peripheral edema.
  2. **Beers PIM Alerts:** Fired by `BEERS-BENZODIAZEPINE` and `BEERS-FIRST-GEN-ANTIHISTAMINE`.
  3. **Anticholinergic Burden (ACB):** Total score &ge; 3 flagged with High Fall Risk band.

### Scenario D: Boomerang Post-Discharge Medication Reappearance
- **Scenario:** Patient was discharged from hospital with instructions to discontinue `Brufen` (Ibuprofen). 3 weeks later at home, patient resumes taking leftover Brufen for back stiffness.
- **What to Observe:** Discharge reconciliation detects the boomerang NSAID, alerting the caregiver and generating a neutral clarification prompt for the follow-up clinic appointment.

---

## 3. Interactive Walkthroughs

### Senior Voice Experience (`/` &rarr; Senior App)
1. Select **Senior** from the navigation bar.
2. Toggle the **Text Size** buttons (`A+` / `A-`) to demonstrate 200% scalable typography.
3. Toggle **High Contrast** to see pure WCAG AAA black/white mode.
4. Tap the **Tap to Speak** button:
   - MedGuard parses the voice input into candidate generic formulations.
   - Triggers the **Confirm-Before-Store** screen (*"Did we hear you correctly: Combiflam?"*).
   - Once confirmed, displays grounded questions to ask the doctor.
5. Tap **Read this to me** to experience the slower, measured text-to-speech cadence.
6. Observe the persistent **Call Caregiver** and **Call 112 (Emergency)** buttons.

### Clinician Swipe Queue (`/` &rarr; Clinician App)
1. Select **Clinician** from the top bar.
2. View the split-pane queue ranked by clinical severity.
3. Review patient alerts, mechanism explanations, and guidelines.
4. Test decision actions:
   - **Approve (Right Arrow):** Approves the alert and releases it to patient and caregiver.
   - **Reject (Left Arrow):** Opens modal requiring a **reason tag** (`false_positive`, `clinically_acceptable`, `missing_context`, `wrong_severity`, etc.).
   - **Undo:** An interactive 10-second toast allows instantaneous undo of decisions.
5. Test **Audited Reveal:** Click "Audited Reveal" and provide a clinical justification. The masked token (`PT-DEMO-A74`) reveals the full patient identity, and an immutable log entry is generated.

### Caregiver Dashboard (`/` &rarr; Caregiver App)
1. Select **Caregiver** from the top bar.
2. Inspect the linked senior profile, recent change log, active alerts, and full medication list.
3. Click **Download Doctor Guide (PDF)** to generate the 1-page A4 summary with clinical QR code.

### Administration & Feedback Loop (`/` &rarr; Admin App)
1. Select **Admin** from the top bar.
2. Inspect the real-time **LLM Gateway Telemetry** (Daily budget, Session rate limiter, Circuit breaker status, and Persistent cache hits).
3. Review the **Governed Feedback Loop**: inspect rule proposals generated from repeated clinician rejections. Accept or reject proposals with human sign-off.

