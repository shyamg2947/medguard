"""
Pre-warms the LLM Gateway response cache for Demo Scenarios A, B, C, D.
Ensures zero-latency, 100% offline demonstration without hitting paid external API quotas.
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.config import get_settings
from backend.app.models.db import SessionLocal, LlmCallRecord, generate_uuid, utc_now
from backend.app.privacy.llm_gateway import compute_prompt_hash


PREWARM_PROMPTS = [
    {
        "prompt": "Explain the interaction between Warfarin, Aspirin, and Combiflam (Ibuprofen + Paracetamol) for an elderly patient.",
        "response": (
            "Taking Warfarin, Aspirin, and Combiflam together creates a significant risk of internal stomach bleeding. "
            "Warfarin and Aspirin stop blood from clotting normally, while Ibuprofen in Combiflam irritates the stomach lining. "
            "Ask your doctor whether a safer pain relief alternative, such as a topical gel or paracetamol alone, can be used instead."
        ),
    },
    {
        "prompt": "Evaluate the safety of Telmisartan, Furosemide, and Diclofenac taken concurrently.",
        "response": (
            "The combination of an ARB (Telmisartan), a diuretic (Furosemide), and an NSAID (Diclofenac) is clinically known as the 'Triple Whammy'. "
            "It sharply reduces blood flow to the kidneys and can precipitate acute kidney injury, especially in older adults. "
            "Ask your doctor whether oral Diclofenac can be stopped or substituted for joint pain."
        ),
    },
    {
        "prompt": "Analyze prescribing cascade for Amlodipine followed by Loop Diuretic, with Diphenhydramine and Alprazolam.",
        "response": (
            "Amlodipine frequently causes ankle swelling as a harmless side effect; adding a loop diuretic to treat this swelling is a recognized prescribing cascade. "
            "Furthermore, taking Diphenhydramine and Alprazolam produces high anticholinergic and sedative burden, substantially increasing the risk of falls and confusion. "
            "Ask your doctor to review whether the water pill is necessary and whether sleep aids can be safely tapered."
        ),
    },
    {
        "prompt": "Reconcile discharge medications where Brufen (Ibuprofen) was discontinued but later resumed by patient.",
        "response": (
            "Brufen was stopped at discharge from the hospital to protect your stomach and kidneys. Resuming it at home creates an unintentional duplicate or conflicting therapy. "
            "Ask your doctor whether restarting Brufen was intentional or if an alternative pain plan should be followed."
        ),
    },
]


def prewarm_cache():
    print("[*] Pre-warming MedGuard LLM Gateway Cache for Scenarios A-D...")
    settings = get_settings()
    model_name = settings.LLM_MODEL
    db = SessionLocal()
    prewarmed = 0

    try:
        for item in PREWARM_PROMPTS:
            p = item["prompt"]
            r = item["response"]
            p_hash = compute_prompt_hash("v1", model_name, p)

            existing = (
                db.query(LlmCallRecord)
                .filter(LlmCallRecord.prompt_hash == p_hash)
                .first()
            )
            if not existing:
                rec = LlmCallRecord(
                    id=generate_uuid(),
                    session_id="prewarm-session",
                    model=model_name,
                    prompt_hash=p_hash,
                    response_cached=False,
                    latency_ms=10,
                    response_text=r,
                    created_at=utc_now(),
                )
                db.add(rec)
                prewarmed += 1

        db.commit()
        print(f" -> Successfully cached {prewarmed} scenario explanations into database.")
    finally:
        db.close()


if __name__ == "__main__":
    prewarm_cache()
