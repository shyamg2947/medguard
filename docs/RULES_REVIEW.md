# MedGuard Clinical Rules Review

This document catalogues all deterministic clinical safety rules in `rules/seed_rules.yaml` and `rules/cascades.yaml`.
Per Safety Principle S3, every rule cites its verified clinical source. All rules start as `seed_needs_review` until formally signed off by a licensed clinician.

| Rule ID | Type | Severity | Evidence | Target A | Target B / Modifiers | Sources | Review Status |
|---------|------|----------|----------|----------|----------------------|---------|---------------|
| `DUP-PARACETAMOL` | duplicate_ingredient | high | established | paracetamol | paracetamol (multi-source) | FDA Drug Safety Comm. (2014); Indian Pharmacopoeia | seed_needs_review |
| `DUP-NSAID` | duplicate_class | high | established | class: nsaid | class: nsaid (concurrent) | AGS Beers Criteria 2023; STOPP/START v3 Sec A | seed_needs_review |
| `DDI-WARFARIN-NSAID` | interaction_pair | critical | established | class: anticoagulant | class: nsaid | FDA Warfarin Prescribing Info; AGS Beers 2023 | seed_needs_review |
| `DDI-ANTICOAG-ANTIPLATELET` | interaction_pair | high | established | class: anticoagulant | class: antiplatelet | ACC/AHA Dual Antithrombotic Guidelines; STOPP v3 Sec B | seed_needs_review |
| `DDI-SSRI-NSAID` | interaction_pair | moderate | established | class: ssri | class: nsaid | de Abajo FJ, BMJ 1999; FDA Safety Alert | seed_needs_review |
| `COMBO-TRIPLE-WHAMMY` | interaction_combo | critical | established | class: ace_inhibitor / arb | diuretic + nsaid | Thomas MC, Med J Aust 2000; Loboz & Shenfield 2005 | seed_needs_review |
| `BEERS-BENZODIAZEPINE` | beers_pim | high | established | class: benzodiazepine / sedative_hypnotic | Age >= 65 | AGS Beers Criteria 2023 Update; STOPP v3 Sec D | seed_needs_review |
| `BEERS-FIRST-GEN-ANTIHISTAMINE` | beers_pim | high | established | class: first_gen_antihistamine | Age >= 65 | AGS Beers Criteria 2023 Update; ACB Scale | seed_needs_review |
| `DURATION-PPI-8WEEKS` | duration_exceeded | moderate | established | class: ppi | Duration > 8 weeks | AGS Beers Criteria 2023 Update; FDA Comm. 2011 | seed_needs_review |
| `RENAL-METFORMIN` | renal_threshold | high | established | metformin | CrCl / eGFR < 30 mL/min | FDA Metformin Warning 2016; KDIGO CKD Guidelines | seed_needs_review |
| `RENAL-NSAID` | renal_threshold | high | established | class: nsaid | CrCl / eGFR < 30 mL/min | KDIGO 2024 Guidelines; STOPP/START v3 Sec C | seed_needs_review |
| `HERB-ASHWAGANDHA-INTERACTION` | herbal_interaction | moderate | limited | ashwagandha | sedative / thyroid / antithrombotic | MSKCC Integrative Medicine; NIH NCCIH | seed_needs_review |
| `HERB-BLEEDING-HERBS` | herbal_interaction | moderate | limited | ginkgo, garlic, turmeric | anticoagulant / antiplatelet | NIH NCCIH Herbs at a Glance; FDA MedWatch | seed_needs_review |
| `COND-NSAID-PUD` | drug_condition | high | established | class: nsaid | condition: peptic_ulcer | ACG Ulcer Bleeding Guidelines; STOPP v3 Sec A | seed_needs_review |
| `CASCADE-CCB-DIURETIC` | cascade | moderate | established | class: calcium_channel_blocker | swelling -> loop_diuretic | Rochon PA & Gurwitz JH, BMJ 1997; Beers 2023 | seed_needs_review |
| `CASCADE-NSAID-ANTIHYPERTENSIVE` | cascade | moderate | established | class: nsaid | high BP -> antihypertensive | Johnson AG, Ann Intern Med 1994 | seed_needs_review |
| `CASCADE-ACEI-COUGH` | cascade | low | established | class: ace_inhibitor | cough -> suppressant | Dicpinigaitis PV, Chest 2006 | seed_needs_review |
| `CASCADE-DOPAMINE-ANTIPARKINSON` | cascade | high | established | dopamine antagonist | tremor -> anticholinergic | Thanvi B & Treadwell S, Postgrad Med J 2009 | seed_needs_review |
| `CASCADE-CHOLINESTERASE-BLADDER` | cascade | high | established | cholinesterase inhibitor | incontinence -> bladder anticholinergic | Gill SS et al., Lancet 2005 | seed_needs_review |
