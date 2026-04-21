from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class MonitoringLocationCreate(BaseModel):
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=3)
    description: Optional[str] = None
    room: str
    gmp_grade: str = Field(..., description="A | B | C | D")
    site_id: str


class MonitoringLocationOut(BaseModel):
    id: str
    code: str
    name: str
    room: str
    gmp_grade: str
    is_active: bool
    created_at: datetime
    class Config:
        from_attributes = True


class AlertLimitCreate(BaseModel):
    parameter: str
    unit: str
    alert_limit: Optional[float] = None
    action_limit: Optional[float] = None
    document_reference: Optional[str] = None


class AlertLimitOut(BaseModel):
    id: str
    location_id: str
    parameter: str
    unit: str
    alert_limit: Optional[float]
    action_limit: Optional[float]
    document_reference: Optional[str]
    class Config:
        from_attributes = True


class MonitoringResultCreate(BaseModel):
    parameter: str
    sampling_method: str
    sampled_at: datetime
    batch_reference: Optional[str] = None
    result_value: float
    unit: str
    comments: Optional[str] = None


class MonitoringResultOut(BaseModel):
    id: str
    result_number: str
    location_id: str
    parameter: str
    sampling_method: str
    sampled_at: datetime
    result_value: float
    unit: str
    status: str
    alert_limit_at_time: Optional[float]
    action_limit_at_time: Optional[float]
    investigation_required: bool
    linked_deviation_id: Optional[str]
    comments: Optional[str]
    created_at: datetime
    class Config:
        from_attributes = True


class SamplingPlanCreate(BaseModel):
    parameter: str
    frequency: str
    sampling_method: str
    sample_volume_or_time: Optional[str] = None
    assigned_to_role: Optional[str] = None
