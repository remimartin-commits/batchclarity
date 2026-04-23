from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


# ── Product ───────────────────────────────────────────────────────────────────

class ProductCreate(BaseModel):
    product_code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=2, max_length=300)
    description: Optional[str] = None
    product_type: str  # drug_substance | drug_product | intermediate | raw_material
    unit_of_measure: str
    shelf_life_months: Optional[int] = None
    storage_conditions: Optional[str] = None
    site_id: str


class ProductOut(BaseModel):
    id: str
    product_code: str
    name: str
    product_type: str
    unit_of_measure: str
    shelf_life_months: Optional[int]
    storage_conditions: Optional[str]
    is_active: bool
    created_at: datetime
    class Config:
        from_attributes = True


# ── Master Batch Record ───────────────────────────────────────────────────────

class MBRStepCreate(BaseModel):
    step_number: int
    phase: str
    title: str = Field(..., min_length=3)
    instructions: str = Field(..., min_length=10)
    step_type: str  # action | check | measurement | weight | ipc | critical_step | signature_required
    expected_value: Optional[str] = None
    expected_unit: Optional[str] = None
    lower_limit: Optional[float] = None
    upper_limit: Optional[float] = None
    is_critical: bool = False
    requires_second_check: bool = False
    requires_signature: bool = False
    allow_na: bool = False


class MBRStepOut(BaseModel):
    id: str
    step_number: int
    phase: str
    title: str
    instructions: str
    step_type: str
    expected_value: Optional[str]
    expected_unit: Optional[str]
    lower_limit: Optional[float]
    upper_limit: Optional[float]
    is_critical: bool
    requires_second_check: bool
    requires_signature: bool
    class Config:
        from_attributes = True


class MBRCreate(BaseModel):
    product_id: str
    version: str = Field(default="1.0", example="1.0")
    batch_size: float
    batch_size_unit: str
    theoretical_yield: Optional[float] = None
    yield_unit: Optional[str] = None
    acceptable_yield_min: Optional[float] = None
    acceptable_yield_max: Optional[float] = None
    description: Optional[str] = None
    steps: list[MBRStepCreate] = []


class MBROut(BaseModel):
    id: str
    mbr_number: str
    product_id: str
    version: str
    status: str
    batch_size: float
    batch_size_unit: str
    theoretical_yield: Optional[float]
    acceptable_yield_min: Optional[float]
    acceptable_yield_max: Optional[float]
    authored_by_id: str
    approved_by_id: Optional[str]
    effective_date: Optional[datetime]
    steps: list[MBRStepOut] = []
    created_at: datetime
    class Config:
        from_attributes = True


class MBRSignRequest(BaseModel):
    password: str = Field(..., description="Re-auth for 21 CFR Part 11")
    meaning: str  # reviewed | approved
    comments: Optional[str] = None


# ── Batch Record (live execution) ─────────────────────────────────────────────

class BatchRecordCreate(BaseModel):
    master_batch_record_id: str
    batch_number: str = Field(..., min_length=3, max_length=100)
    planned_start: Optional[datetime] = None


class BatchRecordStepExecute(BaseModel):
    recorded_value: Optional[str] = None
    is_na: bool = False
    comments: Optional[str] = None
    password: str = Field(..., description="Re-auth for EBR step sign-off")


class BatchRecordStepOut(BaseModel):
    id: str
    step_number: int
    status: str
    recorded_value: Optional[str]
    is_within_limits: Optional[bool]
    is_na: bool
    comments: Optional[str]
    performed_by_id: Optional[str]
    performed_at: Optional[datetime]
    checked_by_id: Optional[str]
    checked_at: Optional[datetime]
    linked_deviation_id: Optional[str]
    class Config:
        from_attributes = True


class BatchRecordOut(BaseModel):
    id: str
    batch_number: str
    master_batch_record_id: str
    product_id: str
    status: str
    actual_start: Optional[datetime]
    actual_completion: Optional[datetime]
    actual_yield: Optional[float]
    yield_percentage: Optional[float]
    has_deviations: bool
    steps: list[BatchRecordStepOut] = []
    created_at: datetime
    class Config:
        from_attributes = True


class BatchReleaseRequest(BaseModel):
    password: str = Field(..., description="Re-auth for 21 CFR Part 11")
    decision: str  # released | rejected
    comments: Optional[str] = None
