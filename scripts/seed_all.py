"""
Master Seeding Script for MedGuard.
Seeds database with synthetic scenarios, rules, RAG index, and demo users.
"""
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.models.db import (
    SessionLocal,
    Patient,
    Medication,
    User,
    CaregiverLink,
    init_db,
    utc_now,
    generate_uuid,
)
from backend.app.rag.ingest import ingest_all_guidelines
from backend.app.rules.engine import ClinicalRulesEngine


def seed_all():
    print("[1/4] Initializing Database Schema...")
    init_db()
    db = SessionLocal()

    print("[2/4] Running Clinical RAG Ingestion...")
    manifest_path = "knowledge/manifest.yaml"
    if os.path.exists(manifest_path):
        chunks = ingest_all_guidelines()
        print(f" -> RAG chunks ({len(chunks)}) and BM25 index built successfully.")

    print("[3/4] Ensuring Demo Accounts Exist...")
    roles = [
        ("DEMO-SENIOR", "senior"),
        ("DEMO-CAREGIVER", "caregiver"),
        ("DEMO-CLINICIAN", "clinician"),
        ("DEMO-ADMIN", "admin"),
    ]
    caregiver_user = None
    for token, role in roles:
        u = db.query(User).filter(User.display_token == token).first()
        if not u:
            u = User(
                id=f"user-{role}",
                role=role,
                display_token=token,
                preferred_language="en",
                active=True,
                created_at=utc_now(),
            )
            db.add(u)
            db.commit()
        if role == "caregiver":
            caregiver_user = u

    print("[4/4] Importing Synthetic Patients and Scenarios...")
    synth_path = "data/synthetic_patients.json"
    if os.path.exists(synth_path):
        with open(synth_path, "r", encoding="utf-8") as f:
            patients_data = json.load(f)

        engine = ClinicalRulesEngine()

        for p_data in patients_data:
            pid = p_data["id"]
            existing_p = db.query(Patient).filter(Patient.id == pid).first()
            if not existing_p:
                p = Patient(
                    id=pid,
                    owner_user_id="user-senior",
                    language=p_data.get("language", "en"),
                    age=p_data.get("age", 70),
                    sex=p_data.get("sex", "female"),
                    weight_kg=p_data.get("weight_kg"),
                    is_synthetic=True,
                    created_at=utc_now(),
                )
                db.add(p)
                db.commit()

                # Add medications
                med_inputs = []
                for m in p_data.get("medications", []):
                    brand = m.get("brand")
                    start_date = m.get("start_date")
                    ing_list = m.get("ingredients", [])
                    raw_text = brand or (ing_list[0]["ingredient"] if ing_list else "Unknown Medication")
                    med = Medication(
                        id=generate_uuid(),
                        patient_id=pid,
                        raw_text=raw_text,
                        brand=brand,
                        ingredients_json=json.dumps(ing_list),
                        start_date=start_date,
                        status="active",
                        confirmed=True,
                        confirmed_at=utc_now(),
                        created_at=utc_now(),
                    )
                    db.add(med)
                    for ing in ing_list:
                        med_inputs.append({
                            "id": med.id,
                            "generic": ing.get("ingredient"),
                            "brand": brand,
                            "strength": ing.get("strength"),
                            "start_date": start_date,
                        })
                db.commit()

                # Evaluate safety alerts & risk scores
                patient_ctx = {
                    "age": p_data.get("age", 70),
                    "sex": p_data.get("sex", "female"),
                    "weight_kg": p_data.get("weight_kg", 60.0),
                    "serum_creatinine": next((l["value"] for l in p_data.get("labs", []) if l.get("kind") == "serum_creatinine_mg_dl"), None),
                    "conditions": p_data.get("conditions", []),
                }
                eval_res = engine.evaluate(med_inputs, **patient_ctx)

                # Link caregiver if not already linked
                if caregiver_user:
                    link = db.query(CaregiverLink).filter(
                        CaregiverLink.caregiver_user_id == caregiver_user.id,
                        CaregiverLink.patient_id == pid,
                    ).first()
                    if not link:
                        db.add(CaregiverLink(
                            id=generate_uuid(),
                            caregiver_user_id=caregiver_user.id,
                            patient_id=pid,
                            permissions="read,write",
                            created_at=utc_now(),
                        ))
                        db.commit()

        print(f" -> Successfully seeded {len(patients_data)} synthetic patients with clinical profiles.")

    db.close()
    print("MedGuard Seeding Complete.")


if __name__ == "__main__":
    seed_all()
