from pydantic import BaseModel, Field, ConfigDict
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
    exceeds_alert_limit: bool = False
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


class MonitoringTrendCreate(BaseModel):
    parameter: str
    period_start: datetime
    period_end: datetime
    sample_count: int = Field(..., ge=0)
    alert_exceedances: int = 0
    action_exceedances: int = 0
    mean_value: Optional[float] = None
    max_value: Optional[float] = None
    trend_conclusion: Optional[str] = None
    linked_capa_id: Optional[str] = None


class MonitoringTrendReviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    password: str = Field(..., description="Re-auth for 21 CFR Part 11")
    trend_conclusion: str = Field(..., min_length=10, description="Signed trend conclusion / disposition")
