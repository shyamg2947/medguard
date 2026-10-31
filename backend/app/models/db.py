"""
SQLAlchemy Models for MedGuard.
Implements the comprehensive data model described in Section 6.
"""
from datetime import datetime, timezone
import json
import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from backend.app.config import get_settings

Base = declarative_base()


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    role = Column(String(32), nullable=False, default="senior")  # senior | caregiver | clinician | admin
    display_token = Column(String(64), unique=True, nullable=False)
    preferred_language = Column(String(16), default="en")
    phone_hash = Column(String(128), nullable=True)
    password_hash = Column(String(256), nullable=True)
    otp = Column(String(16), nullable=True)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)


class Patient(Base):
    __tablename__ = "patients"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    owner_user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    is_synthetic = Column(Boolean, default=True)  # S10 & Free tier safety guard
    age = Column(Integer, nullable=False)
    sex = Column(String(16), nullable=False)  # female | male | other
    weight_kg = Column(Float, nullable=True)
    height_cm = Column(Float, nullable=True)
    language = Column(String(16), default="en")
    consent_version = Column(String(32), default="v1.0")
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    medications = relationship("Medication", back_populates="patient", cascade="all, delete-orphan")
    labs = relationship("LabValue", back_populates="patient", cascade="all, delete-orphan")
    conditions = relationship("ConditionNote", back_populates="patient", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="patient", cascade="all, delete-orphan")
    risk_scores = relationship("RiskScore", back_populates="patient", cascade="all, delete-orphan")


class CaregiverLink(Base):
    __tablename__ = "caregiver_links"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    patient_id = Column(String(36), ForeignKey("patients.id"), nullable=False)
    caregiver_user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    permissions = Column(Text, default="read,write")  # comma-separated
    notify_on_json = Column(Text, default='["critical_alert", "red_flag", "missed_checkin"]')
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    @property
    def notify_on(self) -> List[str]:
        return json.loads(self.notify_on_json or "[]")

    @notify_on.setter
    def notify_on(self, val: List[str]):
        self.notify_on_json = json.dumps(val)


class Consent(Base):
    __tablename__ = "consents"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    patient_id = Column(String(36), ForeignKey("patients.id"), nullable=False)
    version = Column(String(32), default="v1.0")
    scopes_json = Column(Text, default='["safety_analysis", "voice_processing"]')
    granted_at = Column(DateTime, default=utc_now)
    revoked_at = Column(DateTime, nullable=True)

    @property
    def scopes(self) -> List[str]:
        return json.loads(self.scopes_json or "[]")

    @scopes.setter
    def scopes(self, val: List[str]):
        self.scopes_json = json.dumps(val)


class Medication(Base):
    __tablename__ = "medications"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    patient_id = Column(String(36), ForeignKey("patients.id"), nullable=False)
    raw_text = Column(String(256), nullable=False)
    brand = Column(String(128), nullable=True)
    ingredients_json = Column(Text, default="[]")  # List[{"ingredient": str, "strength": str}]
    strength_text = Column(String(64), nullable=True)
    frequency_text = Column(String(64), nullable=True)
    route = Column(String(32), default="oral")
    start_date = Column(String(32), nullable=True)  # YYYY-MM-DD or approximate
    end_date = Column(String(32), nullable=True)
    category = Column(String(32), default="prescription")  # prescription|otc|supplement|herbal|ayush
    source = Column(String(32), default="text")  # voice|photo|text|import
    confidence = Column(Float, default=1.0)
    confirmed = Column(Boolean, default=False)  # S4: Confirm before storing
    confirmed_at = Column(DateTime, nullable=True)
    status = Column(String(32), default="active")  # active|stopped|unknown
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    patient = relationship("Patient", back_populates="medications")

    @property
    def ingredients(self) -> List[Dict[str, Any]]:
        return json.loads(self.ingredients_json or "[]")

    @ingredients.setter
    def ingredients(self, val: List[Dict[str, Any]]):
        self.ingredients_json = json.dumps(val)


class LabValue(Base):
    __tablename__ = "lab_values"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    patient_id = Column(String(36), ForeignKey("patients.id"), nullable=False)
    kind = Column(String(64), nullable=False)  # creatinine_mg_dl | egfr | weight_kg | etc.
    value = Column(Float, nullable=False)
    measured_at = Column(DateTime, default=utc_now)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    patient = relationship("Patient", back_populates="labs")


class ConditionNote(Base):
    __tablename__ = "condition_notes"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    patient_id = Column(String(36), ForeignKey("patients.id"), nullable=False)
    controlled_term = Column(String(128), nullable=False)
    free_text = Column(String(256), nullable=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    patient = relationship("Patient", back_populates="conditions")


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    patient_id = Column(String(36), ForeignKey("patients.id"), nullable=False)
    rule_id = Column(String(128), nullable=False)
    rule_version = Column(Integer, default=1)
    severity = Column(String(32), nullable=False)  # critical | high | moderate | low
    type = Column(String(64), nullable=False)
    involved_med_ids_json = Column(Text, default="[]")
    mechanism_summary = Column(Text, nullable=False)
    patient_message_json = Column(Text, nullable=False)  # {"en": "...", "hi": "..."}
    doctor_question = Column(Text, nullable=False)
    sources_json = Column(Text, nullable=False)  # ["FDA label: ...", "AGS Beers Criteria"]
    evidence_level = Column(String(32), default="established")  # established | limited | theoretical
    status = Column(String(32), default="pending_review")  # pending_review | released | dismissed
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    patient = relationship("Patient", back_populates="alerts")

    @property
    def involved_med_ids(self) -> List[str]:
        return json.loads(self.involved_med_ids_json or "[]")

    @involved_med_ids.setter
    def involved_med_ids(self, val: List[str]):
        self.involved_med_ids_json = json.dumps(val)

    @property
    def patient_message(self) -> Dict[str, str]:
        return json.loads(self.patient_message_json or "{}")

    @patient_message.setter
    def patient_message(self, val: Dict[str, str]):
        self.patient_message_json = json.dumps(val)

    @property
    def sources(self) -> List[str]:
        return json.loads(self.sources_json or "[]")

    @sources.setter
    def sources(self, val: List[str]):
        self.sources_json = json.dumps(val)


class RiskScore(Base):
    __tablename__ = "risk_scores"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    patient_id = Column(String(36), ForeignKey("patients.id"), nullable=False)
    kind = Column(String(32), nullable=False)  # acb | fall_risk | renal
    value = Column(Float, nullable=False)
    detail_json = Column(Text, default="{}")
    computed_at = Column(DateTime, default=utc_now)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    patient = relationship("Patient", back_populates="risk_scores")

    @property
    def detail(self) -> Dict[str, Any]:
        return json.loads(self.detail_json or "{}")

    @detail.setter
    def detail(self, val: Dict[str, Any]):
        self.detail_json = json.dumps(val)


class AgentPanelRun(Base):
    __tablename__ = "agent_panel_runs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    patient_id = Column(String(36), ForeignKey("patients.id"), nullable=False)
    alert_ids_json = Column(Text, default="[]")
    specialist_outputs_json = Column(Text, default="[]")
    moderator_output_json = Column(Text, default="{}")
    guardrail_flags_json = Column(Text, default="[]")
    approved_for_patient = Column(Boolean, default=False)  # S8: AI commentary gated
    created_at = Column(DateTime, default=utc_now)

    @property
    def alert_ids(self) -> List[str]:
        return json.loads(self.alert_ids_json or "[]")

    @property
    def specialist_outputs(self) -> List[Dict[str, Any]]:
        return json.loads(self.specialist_outputs_json or "[]")

    @property
    def moderator_output(self) -> Dict[str, Any]:
        return json.loads(self.moderator_output_json or "{}")

    @property
    def guardrail_flags(self) -> List[str]:
        return json.loads(self.guardrail_flags_json or "[]")


class ReviewDecision(Base):
    __tablename__ = "review_decisions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    alert_or_case_id = Column(String(64), nullable=False)
    clinician_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    decision = Column(String(32), nullable=False)  # agree | reject | needs_info
    reason_tag = Column(String(64), nullable=True)  # false_positive | clinically_acceptable | ...
    note = Column(Text, nullable=True)
    edited_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)


class RuleChangeProposal(Base):
    __tablename__ = "rule_change_proposals"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    rule_id = Column(String(128), nullable=True)
    proposed_change = Column(Text, nullable=False)
    justification = Column(Text, nullable=False)
    source_decisions_json = Column(Text, default="[]")
    status = Column(String(32), default="open")  # open | accepted | rejected
    reviewed_by = Column(String(36), nullable=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    @property
    def source_decisions(self) -> List[str]:
        return json.loads(self.source_decisions_json or "[]")

    @source_decisions.setter
    def source_decisions(self, val: List[str]):
        self.source_decisions_json = json.dumps(val)


class RuleVersion(Base):
    __tablename__ = "rule_versions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    version = Column(String(32), unique=True, nullable=False)
    file_hashes_json = Column(Text, default="{}")
    released_at = Column(DateTime, default=utc_now)
    released_by = Column(String(36), nullable=False)
    changelog = Column(Text, nullable=True)


class SymptomReport(Base):
    __tablename__ = "symptom_reports"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    patient_id = Column(String(36), ForeignKey("patients.id"), nullable=False)
    controlled_symptom = Column(String(128), nullable=False)
    severity = Column(String(32), default="moderate")
    raw_text = Column(String(256), nullable=True)
    reported_at = Column(DateTime, default=utc_now)
    suspect_med_ids_json = Column(Text, default="[]")
    is_red_flag = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    @property
    def suspect_med_ids(self) -> List[str]:
        return json.loads(self.suspect_med_ids_json or "[]")

    @suspect_med_ids.setter
    def suspect_med_ids(self, val: List[str]):
        self.suspect_med_ids_json = json.dumps(val)


class Report(Base):
    __tablename__ = "reports"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    patient_id = Column(String(36), ForeignKey("patients.id"), nullable=False)
    kind = Column(String(32), nullable=False)  # safety | guide | emergency_card
    file_path = Column(String(256), nullable=False)
    share_token = Column(String(128), unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=utc_now)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    actor = Column(String(128), nullable=False)
    action = Column(String(64), nullable=False)  # view | export | reveal | decision | rule_change
    entity = Column(String(64), nullable=False)
    entity_id = Column(String(64), nullable=False)
    at = Column(DateTime, default=utc_now)
    meta_json = Column(Text, default="{}")

    @property
    def meta(self) -> Dict[str, Any]:
        return json.loads(self.meta_json or "{}")

    @meta.setter
    def meta(self, val: Dict[str, Any]):
        self.meta_json = json.dumps(val)


class PiiVaultEntry(Base):
    __tablename__ = "pii_vault_entries"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    token = Column(String(64), nullable=False, index=True)
    encrypted_value = Column(String(512), nullable=False)
    patient_id = Column(String(36), ForeignKey("patients.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=utc_now)


class LlmCallRecord(Base):
    __tablename__ = "llm_call_records"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    session_id = Column(String(64), nullable=True)
    model = Column(String(64), nullable=False)
    prompt_hash = Column(String(64), nullable=False, index=True)
    response_cached = Column(Boolean, default=False)
    response_text = Column(Text, nullable=True)
    latency_ms = Column(Integer, default=0)
    created_at = Column(DateTime, default=utc_now)


# Engine & Session setup
settings = get_settings()
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    Base.metadata.create_all(bind=engine)

