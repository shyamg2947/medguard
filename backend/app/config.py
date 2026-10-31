"""
MedGuard Configuration Module.
Loads environment settings with strict safety defaults.
"""
from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Operational Mode
    MODE: str = "demo"  # demo | live
    FREE_TIER_MODE: bool = True
    CHANNEL: str = "simulator"  # simulator | whatsapp
    ALLOW_REAL_PATIENT_DATA: bool = False

    # LLM & AI Gateway
    GEMINI_API_KEY: str = ""
    LLM_PROVIDER: str = "gemini"  # gemini | stub
    LLM_MODEL: str = "gemini-2.5-flash"
    LLM_MAX_CALLS_PER_SESSION: int = 15
    LLM_MAX_CALLS_PER_DAY: int = 200
    LLM_RPM_LIMIT: int = 5
    PANEL_MODE: str = "single_call"  # single_call | multi_call
    REQUIRE_CLINICIAN_APPROVAL_FOR_AI_COMMENTARY: bool = True

    # Voice & Vision Providers
    STT_PROVIDER: str = "whisper"
    STT_MODEL_SIZE: str = "base"
    TTS_PROVIDER: str = "browser"
    OCR_PROVIDER: str = "tesseract"
    TRANSLATE_PROVIDER: str = "stub"

    # Languages
    SUPPORTED_LANGS: str = "en,hi,kn"
    DEFAULT_LANG: str = "en"

    # Database & Security
    DATABASE_URL: str = "sqlite:///./medguard.db"
    SECRET_KEY: str = "dev-secret-key-change-in-production-32-bytes-long!"
    VAULT_KEY: str = "u6fO7mZ8Z1WvL5K3d4R9Q2x8T1Y6P5m9J4w8C2k7L0g="

    # WhatsApp Cloud API
    WA_VERIFY_TOKEN: str = "medguard_verify_token"
    WA_APP_SECRET: str = "dev_wa_app_secret"
    WA_ACCESS_TOKEN: str = "dev_wa_access_token"
    WA_PHONE_NUMBER_ID: str = "1234567890"
    MEDIA_RETENTION_HOURS: int = 24

    # Matching & Review Thresholds
    MATCH_ACCEPT_THRESHOLD: float = 0.90
    MATCH_MARGIN_THRESHOLD: float = 0.10
    MATCH_CLARIFY_THRESHOLD: float = 0.65
    RULE_CHANGE_MIN_DECISIONS: int = 5
    RULE_CHANGE_REJECT_RATE: float = 0.60

    @property
    def supported_languages_list(self) -> List[str]:
        return [lang.strip() for lang in self.SUPPORTED_LANGS.split(",") if lang.strip()]


@lru_cache()
def get_settings() -> Settings:
    return Settings()

