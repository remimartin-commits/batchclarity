from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, Any
from enum import Enum


class RiskLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class CAPAType(str, Enum):
    corrective = "corrective"
    preventive = "preventive"
    corrective_and_preventive = "corrective_and_preventive"


class CAPAStatus(str, Enum):
    open = "open"
    investigation = "investigation"
    action_plan_approved = "action_plan_approved"
    in_progress = "in_progress"
    effectiveness_check = "effectiveness_check"
    closed = "closed"


class CAPASourceType(str, Enum):
    deviation = "deviation"
    audit_finding = "audit_finding"
    customer_complaint = "customer_complaint"
    oos = "oos"
    self_inspection = "self_inspection"
    risk_assessment = "risk_assessment"
    other = "other"


class GMPClassification(str, Enum):
    critical = "critical"
    major = "major"
    minor = "minor"
    observation = "observation"


class RootCauseCategory(str, Enum):
    human_error = "human_error"
    equipment = "equipment"
    process = "process"
    material = "material"
    environment = "environment"
    documentation = "documentation"
    software_it = "software_it"
    unknown = "unknown"


class CAPAActionStatus(str, Enum):
    pending = "pending"
    in_progress = "in_progress"
    complete = "complete"


class EffectivenessResult(str, Enum):
    pass_check = "pass"
    fail_check = "fail"


# ── CAPA Schemas ──────────────────────────────────────────────────────────────

class CAPAActionCreate(BaseModel):
    description: str
    action_type: str = "corrective"
    assignee_id: str
    due_date: Optional[datetime] = None
    status: CAPAActionStatus = CAPAActionStatus.pending
    completion_evidence: Optional[str] = None


class CAPACreate(BaseModel):
    title: str = Field(..., min_length=5, max_length=500)
    capa_type: CAPAType
    source: CAPASourceType
    product_material_affected: Optional[str] = None
    batch_lot_number: Optional[str] = None
    gmp_classification: GMPClassification = GMPClassification.minor
    source_record_id: Optional[str] = None
    risk_level: RiskLevel = RiskLevel.medium
    product_impact: bool = False
    patient_safety_impact: bool = False
    regulatory_reportable: bool = False
    regulatory_reporting_justification: Optional[str] = None
    problem_description: str = Field(..., min_length=20)
    immediate_actions: Optional[str] = None
    root_cause_category: Optional[RootCauseCategory] = None
    root_cause: Optional[str] = None
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
    completion_evidence: Optional[str]
    is_frozen: bool
    freeze_reason: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class CAPAActionUpdate(BaseModel):
    description: Optional[str] = None
    assignee_id: Optional[str] = None
    due_date: Optional[datetime] = None
    status: Optional[CAPAActionStatus] = None
    completion_evidence: Optional[str] = None


class CAPAOut(BaseModel):
    id: str
    capa_number: str
    title: str
    capa_type: str
    source: str
    product_material_affected: Optional[str]
    batch_lot_number: Optional[str]
    gmp_classification: str
    source_record_id: Optional[str]
    risk_level: str
    product_impact: bool
    patient_safety_impact: bool
    regulatory_reportable: bool
    regulatory_reporting_justification: Optional[str]
    problem_description: str
    immediate_actions: Optional[str]
    root_cause: Optional[str]
    root_cause_category: Optional[str]
    root_cause_method: Optional[str]
    effectiveness_criteria: Optional[str]
    effectiveness_result: Optional[str]
    effectiveness_check_method: Optional[str]
    effectiveness_evidence_note: Optional[str]
    current_status: str
    department: str
    owner_id: str
    site_id: str
    identified_date: datetime
    target_completion_date: Optional[datetime]
    actual_completion_date: Optional[datetime]
    effectiveness_check_date: Optional[datetime]
    actions: list[CAPAActionOut] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CAPAUpdate(BaseModel):
    title: Optional[str] = None
    root_cause: Optional[str] = None
    root_cause_category: Optional[RootCauseCategory] = None
    root_cause_method: Optional[str] = None
    immediate_actions: Optional[str] = None
    target_completion_date: Optional[datetime] = None
    effectiveness_criteria: Optional[str] = None
    effectiveness_check_date: Optional[datetime] = None
    effectiveness_check_method: Optional[str] = None
    effectiveness_result: Optional[EffectivenessResult] = None
    effectiveness_notes: Optional[str] = None
    effectiveness_evidence_note: Optional[str] = None
    source: Optional[CAPASourceType] = None
    product_material_affected: Optional[str] = None
    batch_lot_number: Optional[str] = None
    gmp_classification: Optional[GMPClassification] = None
    regulatory_reportable: Optional[bool] = None
    regulatory_reporting_justification: Optional[str] = None


class CAPASignRequest(BaseModel):
    username: Optional[str] = Field(default=None, description="Username re-entry for modules requiring explicit user-id confirmation")
    password: str = Field(..., description="User password — required for re-authentication per 21 CFR Part 11")
    meaning: str = Field(..., description="open|investigation|action_plan_approved|in_progress|effectiveness_check|closed")
    comments: Optional[str] = None
    no_capa_needed_confirmed: Optional[bool] = None
    no_capa_needed_justification: Optional[str] = None


class CAPAAuditEventOut(BaseModel):
    user_full_name: str
    role_at_time: str
    action: str
    old_value: Optional[Any]
    new_value: Optional[Any]
    timestamp_utc: datetime
    ip_address: Optional[str]


# ── Deviation Schemas ─────────────────────────────────────────────────────────

class DeviationStatus(str, Enum):
    open = "open"
    under_investigation = "under_investigation"
    pending_approval = "pending_approval"
    closed = "closed"


class DeviationType(str, Enum):
    process = "process"
    equipment = "equipment"
    environmental = "environmental"
    material = "material"
    documentation = "documentation"
    personnel = "personnel"
    laboratory = "laboratory"
    other = "other"


class GMPImpactClassification(str, Enum):
    critical = "critical"
    major = "major"
    minor = "minor"

class DeviationCreate(BaseModel):
    title: str = Field(..., min_length=5)
    deviation_type: DeviationType
    gmp_impact_classification: GMPImpactClassification = GMPImpactClassification.major
    potential_patient_impact: bool = False
    potential_patient_impact_justification: Optional[str] = None
    batches_affected: list[str] = []
    product_affected: Optional[str] = None
    description: str = Field(..., min_length=20)
    detected_during: str
    detection_date: datetime
    batch_number: Optional[str] = None
    risk_level: RiskLevel = RiskLevel.medium
    immediate_action: Optional[str] = None
    immediate_containment_actions: str = Field(..., min_length=10)
    root_cause_category: Optional[RootCauseCategory] = None
    root_cause: Optional[str] = None
    linked_capa_id: Optional[str] = None
    requires_capa: bool = False
    regulatory_notification_required: bool = False
    regulatory_authority_name: Optional[str] = None
    regulatory_notification_deadline: Optional[datetime] = None


class DeviationOut(BaseModel):
    id: str
    deviation_number: str
    title: str
    deviation_type: str
    gmp_impact_classification: str
    potential_patient_impact: bool
    potential_patient_impact_justification: Optional[str]
    batches_affected: list[str] = []
    product_affected: Optional[str]
    description: str
    risk_level: str
    current_status: str
    detection_date: datetime
    batch_number: Optional[str]
    immediate_containment_actions: Optional[str]
    immediate_containment_actions_at: Optional[datetime]
    root_cause_category: Optional[str]
    root_cause: Optional[str]
    linked_capa_id: Optional[str]
    requires_capa: bool
    regulatory_notification_required: bool
    regulatory_authority_name: Optional[str]
    regulatory_notification_deadline: Optional[datetime]
    no_capa_needed_confirmed: bool
    no_capa_needed_justification: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class DeviationUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    description: Optional[str] = Field(default=None, min_length=20)
    gmp_impact_classification: Optional[GMPImpactClassification] = None
    potential_patient_impact: Optional[bool] = None
    potential_patient_impact_justification: Optional[str] = None
    batches_affected: Optional[list[str]] = None
    product_affected: Optional[str] = None
    risk_level: Optional[RiskLevel] = None
    immediate_action: Optional[str] = None
    immediate_containment_actions: Optional[str] = None
    root_cause_category: Optional[RootCauseCategory] = None
    root_cause: Optional[str] = None
    requires_capa: Optional[bool] = None
    current_status: Optional[str] = None
    linked_capa_id: Optional[str] = None
    regulatory_notification_required: Optional[bool] = None
    regulatory_authority_name: Optional[str] = None
    regulatory_notification_deadline: Optional[datetime] = None
    no_capa_needed_confirmed: Optional[bool] = None
    no_capa_needed_justification: Optional[str] = None


class DeviationAuditEventOut(BaseModel):
    user_full_name: str
    role_at_time: str
    action: str
    old_value: Optional[Any]
    new_value: Optional[Any]
    timestamp_utc: datetime
    ip_address: Optional[str]


# ── Change Control Schemas ────────────────────────────────────────────────────

class ChangeType(str, Enum):
    equipment = "equipment"
    process = "process"
    material = "material"
    software = "software"
    facility = "facility"
    documentation = "documentation"
    supplier = "supplier"
    regulatory = "regulatory"
    other = "other"


class ChangeClassification(str, Enum):
    major = "major"
    minor = "minor"
    emergency = "emergency"


class RegulatoryFilingType(str, Enum):
    cbe_30 = "cbe_30"
    pas = "pas"
    annual_report = "annual_report"
    variation = "variation"
    other = "other"


class ChecklistResult(str, Enum):
    yes = "yes"
    no = "no"
    na = "na"


class ChecklistItem(BaseModel):
    item: str
    result: ChecklistResult


class ChangeControlStatus(str, Enum):
    draft = "draft"
    under_review = "under_review"
    approved = "approved"
    in_implementation = "in_implementation"
    effectiveness_review = "effectiveness_review"
    closed = "closed"

class ChangeControlCreate(BaseModel):
    title: str = Field(..., min_length=5)
    change_type: ChangeType
    change_category: ChangeClassification
    description: str = Field(..., min_length=20)
    justification: str = Field(..., min_length=20)
    regulatory_impact: bool = False
    regulatory_filing_required: bool = False
    regulatory_filing_type: Optional[RegulatoryFilingType] = None
    validation_required: bool = False
    validation_qualification_required: bool = False
    validation_scope_description: Optional[str] = None
    affected_document_ids: list[str] = []
    affected_equipment_ids: list[str] = []
    affected_sop_document_ids: list[str] = []
    implementation_plan: str = Field(..., min_length=10)
    implementation_target_date: datetime
    pre_change_verification_checklist: list[ChecklistItem] = []
    proposed_implementation_date: Optional[datetime] = None


class ChangeControlOut(BaseModel):
    id: str
    change_number: str
    title: str
    change_type: str
    change_category: str
    description: str
    regulatory_impact: bool
    regulatory_filing_required: bool
    regulatory_filing_type: Optional[str]
    validation_required: bool
    validation_qualification_required: bool
    validation_scope_description: Optional[str]
    affected_document_ids: list[str] = []
    affected_equipment_ids: list[str] = []
    affected_sop_document_ids: list[str] = []
    implementation_plan: Optional[str]
    implementation_target_date: Optional[datetime]
    pre_change_verification_checklist: list[ChecklistItem] = []
    post_change_effectiveness_date: Optional[datetime]
    post_change_effectiveness_outcome: Optional[str]
    post_change_effectiveness_approver_id: Optional[str]
    approval_signature_roles: list[str] = []
    current_status: str
    proposed_implementation_date: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class ChangeControlUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: Optional[str] = Field(default=None, min_length=5)
    description: Optional[str] = Field(default=None, min_length=20)
    change_type: Optional[ChangeType] = None
    change_category: Optional[ChangeClassification] = None
    risk_assessment: Optional[str] = None
    regulatory_filing_required: Optional[bool] = None
    regulatory_filing_type: Optional[RegulatoryFilingType] = None
    affected_document_ids: Optional[list[str]] = None
    affected_equipment_ids: Optional[list[str]] = None
    affected_sop_document_ids: Optional[list[str]] = None
    implementation_plan: Optional[str] = None
    implementation_target_date: Optional[datetime] = None
    validation_qualification_required: Optional[bool] = None
    validation_scope_description: Optional[str] = None
    pre_change_verification_checklist: Optional[list[ChecklistItem]] = None
    post_change_effectiveness_date: Optional[datetime] = None
    post_change_effectiveness_outcome: Optional[str] = None
    post_change_effectiveness_approver_id: Optional[str] = None
    current_status: Optional[str] = None
    actual_implementation_date: Optional[datetime] = None


class ChangeControlAuditEventOut(BaseModel):
    user_full_name: str
    role_at_time: str
    action: str
    old_value: Optional[Any]
    new_value: Optional[Any]
    timestamp_utc: datetime
    ip_address: Optional[str]
