from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional
from enum import Enum


class RiskLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class CAPAType(str, Enum):
    corrective = "corrective"
    preventive = "preventive"


class CAPAStatus(str, Enum):
    draft = "draft"
    under_review = "under_review"
    approved = "approved"
    in_progress = "in_progress"
    effectiveness_check = "effectiveness_check"
    completed = "completed"
    closed = "closed"


# ── CAPA Schemas ──────────────────────────────────────────────────────────────

class CAPAActionCreate(BaseModel):
    description: str
    action_type: str
    assignee_id: str
    due_date: Optional[datetime] = None


class CAPACreate(BaseModel):
    title: str = Field(..., min_length=5, max_length=500)
    capa_type: CAPAType
    source: str
    source_record_id: Optional[str] = None
    risk_level: RiskLevel = RiskLevel.medium
    product_impact: bool = False
    patient_safety_impact: bool = False
    regulatory_reportable: bool = False
    problem_description: str = Field(..., min_length=20)
    immediate_actions: Optional[str] = None
    department: str
    identified_date: datetime
    target_completion_date: Optional[datetime] = None
    actions: list[CAPAActionCreate] = []


class CAPAActionOut(BaseModel):
    id: str
    sequence_number: int
    description: str
    action_type: str
    assignee_id: str
    due_date: Optional[datetime]
    status: str
    is_frozen: bool
    freeze_reason: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class CAPAOut(BaseModel):
    id: str
    capa_number: str
    title: str
    capa_type: str
    source: str
    risk_level: str
    product_impact: bool
    patient_safety_impact: bool
    regulatory_reportable: bool
    problem_description: str
    root_cause: Optional[str]
    current_status: str
    department: str
    identified_date: datetime
    target_completion_date: Optional[datetime]
    actual_completion_date: Optional[datetime]
    actions: list[CAPAActionOut] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CAPAUpdate(BaseModel):
    title: Optional[str] = None
    root_cause: Optional[str] = None
    root_cause_method: Optional[str] = None
    immediate_actions: Optional[str] = None
    target_completion_date: Optional[datetime] = None
    effectiveness_criteria: Optional[str] = None


class CAPASignRequest(BaseModel):
    password: str = Field(..., description="User password — required for re-authentication per 21 CFR Part 11")
    meaning: str = Field(..., description="e.g. 'approved', 'reviewed'")
    comments: Optional[str] = None


# ── Deviation Schemas ─────────────────────────────────────────────────────────

class DeviationCreate(BaseModel):
    title: str = Field(..., min_length=5)
    deviation_type: str  # planned | unplanned
    category: str
    description: str = Field(..., min_length=20)
    detected_during: str
    detection_date: datetime
    batch_number: Optional[str] = None
    risk_level: RiskLevel = RiskLevel.medium
    immediate_action: Optional[str] = None


class DeviationOut(BaseModel):
    id: str
    deviation_number: str
    title: str
    deviation_type: str
    category: str
    description: str
    risk_level: str
    current_status: str
    detection_date: datetime
    batch_number: Optional[str]
    linked_capa_id: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class DeviationUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    description: Optional[str] = Field(default=None, min_length=20)
    risk_level: Optional[RiskLevel] = None
    immediate_action: Optional[str] = None
    root_cause: Optional[str] = None
    current_status: Optional[str] = None
    linked_capa_id: Optional[str] = None


# ── Change Control Schemas ────────────────────────────────────────────────────

class ChangeControlCreate(BaseModel):
    title: str = Field(..., min_length=5)
    change_type: str
    change_category: str  # minor | major | critical
    description: str = Field(..., min_length=20)
    justification: str = Field(..., min_length=20)
    regulatory_impact: bool = False
    validation_required: bool = False
    proposed_implementation_date: Optional[datetime] = None


class ChangeControlOut(BaseModel):
    id: str
    change_number: str
    title: str
    change_type: str
    change_category: str
    description: str
    regulatory_impact: bool
    validation_required: bool
    current_status: str
    proposed_implementation_date: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class ChangeControlUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: Optional[str] = Field(default=None, min_length=5)
    description: Optional[str] = Field(default=None, min_length=20)
    change_type: Optional[str] = None
    risk_assessment: Optional[str] = None
    current_status: Optional[str] = None
    actual_implementation_date: Optional[datetime] = None
