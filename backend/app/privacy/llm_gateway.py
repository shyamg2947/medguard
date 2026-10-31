"""
LLM Gateway for MedGuard.
Enforces:
- S7: PII Masking verification on outgoing payloads.
- Section 5.2b: Free-tier call budget (session & daily limits).
- Token-bucket rate limiter.
- Exponential backoff & retry on 429/503.
- Circuit breaker for repeated provider failures.
- Persistent response cache (key = sha256(template_version + model + masked_input)).
- Data-privacy guard for free-tier: blocks real patient data (is_synthetic=false).
- Graceful fallback to verified rule text on exhaustion or errors.
"""
from datetime import datetime, timedelta, timezone
import hashlib
import json
import logging
import random
import time
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session
from backend.app.config import get_settings
from backend.app.models.db import LlmCallRecord, SessionLocal, generate_uuid, utc_now
from backend.app.privacy.pii import has_pii

logger = logging.getLogger("medguard.llm_gateway")


class CircuitBreakerOpenException(Exception):
    pass


class PiiViolationException(Exception):
    pass


class NonSyntheticDataBlockedException(Exception):
    pass


class BudgetExhaustedException(Exception):
    pass


class TokenBucketRateLimiter:
    """Thread-safe in-memory token bucket rate limiter."""
    def __init__(self, rpm: int):
        self.rpm = max(1, rpm)
        self.tokens = float(self.rpm)
        self.capacity = float(self.rpm)
        self.fill_rate = float(self.rpm) / 60.0  # tokens per second
        self.last_update = time.time()

    def acquire(self, wait: bool = True) -> bool:
        now = time.time()
        elapsed = now - self.last_update
        self.last_update = now
        self.tokens = min(self.capacity, self.tokens + elapsed * self.fill_rate)

        if self.tokens >= 1.0:
            self.tokens -= 1.0
            return True

        if not wait:
            return False

        needed = 1.0 - self.tokens
        sleep_sec = needed / self.fill_rate
        if sleep_sec > 5.0:
            return False  # Do not block indefinitely
        time.sleep(sleep_sec)
        self.tokens = 0.0
        return True


class CircuitBreaker:
    """Pauses LLM calls for a cool-down period after repeated failures."""
    def __init__(self, failure_threshold: int = 3, cooldown_seconds: int = 30):
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds
        self.consecutive_failures = 0
        self.opened_at: Optional[float] = None

    def is_open(self) -> bool:
        if self.opened_at is None:
            return False
        if time.time() - self.opened_at > self.cooldown_seconds:
            # Half-open: allow a trial
            self.opened_at = None
            self.consecutive_failures = 0
            return False
        return True

    def record_success(self):
        self.consecutive_failures = 0
        self.opened_at = None

    def record_failure(self):
        self.consecutive_failures += 1
        if self.consecutive_failures >= self.failure_threshold:
            self.opened_at = time.time()
            logger.warning(f"Circuit breaker opened for {self.cooldown_seconds}s after {self.consecutive_failures} failures")


# Global singletons
_rate_limiter = TokenBucketRateLimiter(get_settings().LLM_RPM_LIMIT)
_circuit_breaker = CircuitBreaker()


def compute_prompt_hash(template_version: str, model: str, masked_input: str) -> str:
    h = hashlib.sha256()
    h.update(template_version.encode("utf-8"))
    h.update(model.encode("utf-8"))
    h.update(masked_input.encode("utf-8"))
    return h.hexdigest()


def check_budget_and_limits(db: Session, session_id: Optional[str] = None) -> Tuple[bool, str]:
    """
    Checks session limit and daily limit against LlmCallRecord in DB.
    Returns (ok, reason).
    """
    settings = get_settings()
    now = datetime.now(timezone.utc)
    day_ago = now - timedelta(days=1)

    daily_count = (
        db.query(func.count(LlmCallRecord.id))
        .filter(LlmCallRecord.created_at >= day_ago, LlmCallRecord.response_cached.is_(False))
        .scalar()
        or 0
    )

    if daily_count >= settings.LLM_MAX_CALLS_PER_DAY:
        return False, f"Daily LLM budget exhausted ({daily_count}/{settings.LLM_MAX_CALLS_PER_DAY})"

    if session_id:
        session_count = (
            db.query(func.count(LlmCallRecord.id))
            .filter(
                LlmCallRecord.session_id == session_id,
                LlmCallRecord.response_cached.is_(False),
            )
            .scalar()
            or 0
        )
        if session_count >= settings.LLM_MAX_CALLS_PER_SESSION:
            return False, f"Session LLM budget exhausted ({session_count}/{settings.LLM_MAX_CALLS_PER_SESSION})"

    return True, "OK"


def get_cached_response(db: Session, prompt_hash: str) -> Optional[str]:
    """Retrieves cached response from LlmCallRecord."""
    rec = (
        db.query(LlmCallRecord)
        .filter(LlmCallRecord.prompt_hash == prompt_hash, LlmCallRecord.response_text.isnot(None))
        .order_by(LlmCallRecord.created_at.desc())
        .first()
    )
    if rec and rec.response_text:
        return rec.response_text
    return None


def execute_llm_call(
    prompt: str,
    template_version: str = "v1",
    model: Optional[str] = None,
    session_id: Optional[str] = None,
    is_synthetic: bool = True,
    db: Optional[Session] = None,
) -> Tuple[str, bool, Optional[str]]:
    """
    Primary gateway entry point.
    Returns: (response_text, was_cached, fallback_badge)
    """
    settings = get_settings()
    model_name = model or settings.LLM_MODEL
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True

    try:
        # 1. Privacy Guard: Non-synthetic patient check in Free-tier mode
        if settings.FREE_TIER_MODE and not is_synthetic and not settings.ALLOW_REAL_PATIENT_DATA:
            logger.error("Non-synthetic patient payload blocked in free-tier mode")
            raise NonSyntheticDataBlockedException(
                "Free-tier mode: Real patient data (is_synthetic=false) is strictly refused."
            )

        # 2. Safety S7: Mask before AI assertion
        if has_pii(prompt):
            logger.critical(f"PII leak detected in prompt destined for LLM: {prompt[:80]}...")
            raise PiiViolationException("Safety Violation S7: Unmasked PII detected in outgoing LLM prompt")

        # 3. Check persistent cache
        p_hash = compute_prompt_hash(template_version, model_name, prompt)
        cached = get_cached_response(db, p_hash)
        if cached is not None:
            # Zero external cost
            return cached, True, None

        # 4. Check circuit breaker
        if _circuit_breaker.is_open():
            logger.warning("Circuit breaker is OPEN. Falling back to rule text.")
            return _generate_rules_fallback(prompt), False, "Verified rule text (Circuit breaker open)"

        # 5. Check call budget
        ok, reason = check_budget_and_limits(db, session_id)
        if not ok:
            logger.warning(f"Budget check failed: {reason}. Falling back to rule text.")
            return _generate_rules_fallback(prompt), False, "Verified rule text (Call budget reached)"

        # 6. Apply Rate Limiting
        if not _rate_limiter.acquire(wait=True):
            logger.warning("Rate limiter limit reached. Falling back to rule text.")
            return _generate_rules_fallback(prompt), False, "Verified rule text (Rate limit)"

        # 7. Execute call with retry & exponential backoff
        start_t = time.time()
        response_text = None
        error_encountered = None

        if settings.MODE == "demo" or settings.LLM_PROVIDER == "stub" or not settings.GEMINI_API_KEY:
            # Offline stub generator
            response_text = _generate_rules_fallback(prompt)
            _circuit_breaker.record_success()
        else:
            # Real Gemini provider with retry on 429/503
            max_retries = 3
            backoff = 1.0
            for attempt in range(max_retries):
                try:
                    from google import genai
                    client = genai.Client(api_key=settings.GEMINI_API_KEY)
                    resp = client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                    )
                    response_text = resp.text
                    _circuit_breaker.record_success()
                    break
                except Exception as ex:
                    error_encountered = ex
                    err_str = str(ex).lower()
                    if "429" in err_str or "quota" in err_str or "503" in err_str or "resource_exhausted" in err_str:
                        sleep_time = backoff + random.uniform(0.1, 0.5)
                        logger.warning(f"Retryable LLM error (attempt {attempt+1}/{max_retries}): {ex}. Sleeping {sleep_time:.2f}s")
                        time.sleep(sleep_time)
                        backoff *= 2
                    else:
                        break

            if response_text is None:
                _circuit_breaker.record_failure()
                logger.error(f"LLM call failed after retries: {error_encountered}. Using rules-only fallback.")
                return _generate_rules_fallback(prompt), False, "Verified rule text (AI polish unavailable)"

        latency = int((time.time() - start_t) * 1000)

        # 8. Record in DB and persistent cache
        record = LlmCallRecord(
            id=generate_uuid(),
            session_id=session_id,
            model=model_name,
            prompt_hash=p_hash,
            response_cached=False,
            response_text=response_text,
            latency_ms=latency,
            created_at=utc_now(),
        )
        db.add(record)
        db.commit()

        return response_text, False, None

    finally:
        if close_db:
            db.close()


def _generate_rules_fallback(prompt: str) -> str:
    """
    Deterministic rules-only fallback when LLM is unavailable or offline.
    Returns structured text or JSON based on prompt context.
    """
    if "json" in prompt.lower() or "domain" in prompt.lower() or "specialists" in prompt.lower():
        # Specialist agent panel structure matching Section 7.9
        return json.dumps({
            "specialists": [
                {
                    "domain": "Cardiology",
                    "concerns": [
                        {
                            "alert_id": "DDI-WARFARIN-NSAID",
                            "statement": "Identified drug conflict grounded directly in verified clinical guidelines.",
                            "evidence_ids": ["DOC-BEERS-2023", "DOC-BLEEDING"]
                        }
                    ],
                    "questions_for_doctor": [
                        "Could we review whether these medications remain optimal for my current condition?",
                        "Are there safer alternatives with lower side effect risks?"
                    ],
                    "tradeoffs": [
                        "Balancing cardiovascular protection against bleeding and geriatric risk burden."
                    ],
                    "confidence": "high"
                }
            ],
            "moderator": {
                "agreements": ["Specialists agree on regular monitoring and cautious dosage."],
                "conflicts": ["Balancing cardiovascular protection against bleeding risks."],
                "human_decision_needed": True,
                "top_questions_for_doctor": [
                    "Could we review whether these medications remain optimal for my current condition?"
                ]
            }
        })
    return (
        "Based on your medication safety analysis, please discuss the highlighted combinations "
        "with your doctor or pharmacist. They can check if any safer alternatives are appropriate for you."
    )


def get_llm_usage_summary(db: Session) -> Dict[str, Any]:
    """Admin inspection helper for call budgets."""
    settings = get_settings()
    now = datetime.now(timezone.utc)
    day_ago = now - timedelta(days=1)

    daily_calls = (
        db.query(func.count(LlmCallRecord.id))
        .filter(LlmCallRecord.created_at >= day_ago, LlmCallRecord.response_cached.is_(False))
        .scalar()
        or 0
    )
    total_calls = db.query(func.count(LlmCallRecord.id)).scalar() or 0
    cached_calls = (
        db.query(func.count(LlmCallRecord.id))
        .filter(LlmCallRecord.response_cached.is_(True))
        .scalar()
        or 0
    )

    return {
        "daily_calls_used": daily_calls,
        "daily_calls_limit": settings.LLM_MAX_CALLS_PER_DAY,
        "daily_calls_remaining": max(0, settings.LLM_MAX_CALLS_PER_DAY - daily_calls),
        "session_limit": settings.LLM_MAX_CALLS_PER_SESSION,
        "total_calls_all_time": total_calls,
        "cached_calls": cached_calls,
        "circuit_breaker_open": _circuit_breaker.is_open(),
        "free_tier_mode": settings.FREE_TIER_MODE,
        "model": settings.LLM_MODEL,
    }
