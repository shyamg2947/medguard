"""
Pydantic Schemas for MedGuard API.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


# Auth & User
class UserBase(BaseModel):
    role: str = "senior"  # senior | caregiver | clinician | admin
    display_token: str
    preferred_language: str = "en"
    phone: Optional[str] = None


class UserCreate(UserBase):
    password: Optional[str] = None


class UserOut(UserBase):
    id: str
    active: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class LoginRequest(BaseModel):
    phone_or_token: str
    password_or_otp: str


class OtpRequest(BaseModel):
    phone: str


# Patient
class PatientBase(BaseModel):
    age: int
    sex: str
    weight_kg: Optional[float] = None
    height_cm: Optional[float] = None
    language: str = "en"
    is_synthetic: bool = True


class PatientCreate(PatientBase):
    owner_user_id: Optional[str] = None


class PatientOut(PatientBase):
    id: str
    owner_user_id: str
    consent_version: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


# Medication
class MedicationIngredient(BaseModel):
    ingredient: str
    strength: Optional[str] = None


class MedicationCandidate(BaseModel):
    raw_text: str
    brand: Optional[str] = None
    ingredients: List[MedicationIngredient] = []
    strength_text: Optional[str] = None
    frequency_text: Optional[str] = None
    category: str = "prescription"
    confidence: float = 1.0
    margin: float = 0.5
    requires_clarification: bool = False
    clarification_options: List[str] = []


class MedicationConfirmRequest(BaseModel):
    raw_text: str
    brand: Optional[str] = None
    ingredients: List[MedicationIngredient] = []
    strength_text: Optional[str] = None
    frequency_text: Optional[str] = None
    category: str = "prescription"
    source: str = "text"
    confirmed: bool = True
    start_date: Optional[str] = None


class MedicationOut(BaseModel):
    id: str
    patient_id: str
    raw_text: str
    brand: Optional[str] = None
    ingredients: List[Dict[str, Any]] = []
    strength_text: Optional[str] = None
    frequency_text: Optional[str] = None
    route: str = "oral"
    start_date: Optional[str] = None
    category: str
    source: str
    confidence: float
    confirmed: bool
    confirmed_at: Optional[datetime] = None
    status: str
    model_config = ConfigDict(from_attributes=True)


# Alert
class AlertOut(BaseModel):
    id: str
    patient_id: str
    rule_id: str
    rule_version: int
    severity: str  # critical | high | moderate | low
    type: str
    involved_med_ids: List[str] = []
    mechanism_summary: str
    patient_message: Dict[str, str] = {}
    doctor_question: str
    sources: List[str] = []
    evidence_level: str
    status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# Risk Score
class RiskScoreOut(BaseModel):
    kind: str
    value: float
    detail: Dict[str, Any] = {}
    computed_at: datetime
    model_config = ConfigDict(from_attributes=True)


# Analysis
class AnalysisResult(BaseModel):
    patient_id: str
    critical_alerts: List[AlertOut] = []
    top_alerts: List[AlertOut] = []
    other_alerts: List[AlertOut] = []
    all_alerts: List[AlertOut] = []
    risk_scores: Dict[str, Any] = {}
    cascades: List[Dict[str, Any]] = []
    panel_commentary: Optional[Dict[str, Any]] = None
    ai_commentary_gated: bool = True
    ai_fallback_badge: Optional[str] = None
    summary_sentence: str
    data_limitations: List[str] = []
    disclaimer: str


# Clinician Review
class ReviewDecisionCreate(BaseModel):
    decision: str  # agree | reject | needs_info
    reason_tag: Optional[str] = None  # false_positive | clinically_acceptable | ...
    note: Optional[str] = None
    edited_message: Optional[str] = None


class RuleChangeProposalOut(BaseModel):
    id: str
    rule_id: Optional[str] = None
    proposed_change: str
    justification: str
    source_decisions: List[str] = []
    status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# Reconciliation
class ReconcileRequest(BaseModel):
    pre_admission_meds: List[str]
    post_discharge_meds: List[str]


class ReconcileResult(BaseModel):
    discontinued_but_restarted: List[str]  # Boomerang
    new_medications: List[str]
    missing_medications: List[str]
    changed_medications: List[str]
    duplicates_detected: List[str]
    doctor_questions: List[str]


# Caregiver Link
class CaregiverLinkCreate(BaseModel):
    invite_code: str


class CaregiverLinkOut(BaseModel):
    id: str
    patient_id: str
    caregiver_user_id: str
    permissions: str
    notify_on: List[str]
    model_config = ConfigDict(from_attributes=True)


# Symptoms
class SymptomReportCreate(BaseModel):
    controlled_symptom: str
    raw_text: Optional[str] = None
    severity: str = "moderate"


class SymptomReportOut(BaseModel):
    id: str
    patient_id: str
    controlled_symptom: str
    severity: str
    suspect_med_ids: List[str] = []
    is_red_flag: bool = False
    reported_at: datetime
    model_config = ConfigDict(from_attributes=True)

