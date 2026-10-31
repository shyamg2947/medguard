"""
Rule Definition Schema.
Validates YAML rule specifications loaded by the clinical rules engine.
"""
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, ConfigDict, Field


class RuleTarget(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    ingredient: Optional[Union[str, List[str]]] = None
    class_name: Optional[Union[str, List[str]]] = Field(default=None, alias="class")
    category: Optional[str] = None


class RuleDefinition(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: str
    type: str  # duplicate_ingredient | duplicate_class | interaction_pair | interaction_combo | beers_pim | duration_exceeded | renal_threshold | cascade | herbal_interaction | drug_condition
    version: int = 1
    severity: str  # critical | high | moderate | low
    evidence: str = "established"  # established | limited | theoretical
    domain: str = "General"  # Cardiology | Nephrology | Geriatrics/Neurology | GI/Bleeding | General
    a: Optional[RuleTarget] = None
    b: Optional[RuleTarget] = None
    combo: Optional[List[RuleTarget]] = None
    condition: Optional[str] = None
    min_age: Optional[int] = None
    max_duration_weeks: Optional[int] = None
    crcl_threshold_ml_min: Optional[float] = None
    egfr_threshold_ml_min: Optional[float] = None
    mechanism: str
    patient_message: Dict[str, str]  # {"en": "...", "hi": "..."}
    doctor_question: str
    sources: List[str]
    review_status: str = "seed_needs_review"  # seed_needs_review | clinician_approved
