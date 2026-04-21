from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional


# ── Equipment ─────────────────────────────────────────────────────────────────

class EquipmentCreate(BaseModel):
    equipment_id: str = Field(..., description="Unique equipment tag/ID e.g. EQ-001")
    name: str = Field(..., min_length=2, max_length=300)
    description: Optional[str] = None
    equipment_type: str
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    location: Optional[str] = None
    site_id: str
    is_gmp_critical: bool = True
    is_computerised_system: bool = False
    installation_date: Optional[datetime] = None


class EquipmentOut(BaseModel):
    id: str
    equipment_id: str
    name: str
    equipment_type: str
    manufacturer: Optional[str]
    model: Optional[str]
    serial_number: Optional[str]
    location: Optional[str]
    status: str
    qualification_status: str
    is_gmp_critical: bool
    is_computerised_system: bool
    installation_date: Optional[datetime]
    created_at: datetime
    class Config:
        from_attributes = True


class EquipmentStatusUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str  # qualified | out_of_service | under_maintenance | retired
    reason: str = Field(..., min_length=5)


# ── Calibration ───────────────────────────────────────────────────────────────

class CalibrationCreate(BaseModel):
    calibration_type: str  # scheduled | unscheduled | post_repair
    performed_at: datetime
    calibration_interval_days: Optional[int] = None
    result: str  # pass | fail | conditional_pass
    certificate_number: Optional[str] = None
    as_found_condition: Optional[str] = None
    as_left_condition: Optional[str] = None
    notes: Optional[str] = None


class CalibrationOut(BaseModel):
    id: str
    equipment_id: str
    calibration_number: str
    calibration_type: str
    performed_at: datetime
    next_calibration_due: Optional[datetime]
    calibration_interval_days: Optional[int]
    result: str
    certificate_number: Optional[str]
    as_found_condition: Optional[str]
    as_left_condition: Optional[str]
    is_overdue: bool
    created_at: datetime
    class Config:
        from_attributes = True


# ── Qualification (IQ/OQ/PQ) ──────────────────────────────────────────────────

class QualificationCreate(BaseModel):
    qualification_type: str = Field(..., description="IQ | OQ | PQ | DQ | PV")
    execution_start: Optional[datetime] = None
    execution_end: Optional[datetime] = None
    result: str = "pending"  # pending | passed | failed | conditional
    requalification_due: Optional[datetime] = None
    deviations_count: int = 0
    summary: Optional[str] = None


class QualificationOut(BaseModel):
    id: str
    equipment_id: str
    qualification_number: str
    qualification_type: str
    result: str
    execution_start: Optional[datetime]
    execution_end: Optional[datetime]
    requalification_due: Optional[datetime]
    deviations_count: int
    summary: Optional[str]
    performed_by_id: str
    reviewed_by_id: Optional[str]
    approved_by_id: Optional[str]
    created_at: datetime
    class Config:
        from_attributes = True


# ── Maintenance ────────────────────────────────────────────────────────────────

class MaintenanceCreate(BaseModel):
    maintenance_type: str  # preventive | corrective | emergency
    description: str = Field(..., min_length=10)
    performed_at: datetime
    equipment_downtime_hours: Optional[float] = None
    parts_replaced: Optional[str] = None
    requalification_required: bool = False


class MaintenanceOut(BaseModel):
    id: str
    equipment_id: str
    maintenance_number: str
    maintenance_type: str
    description: str
    performed_at: datetime
    next_maintenance_due: Optional[datetime]
    equipment_downtime_hours: Optional[float]
    requalification_required: bool
    result: str
    created_at: datetime
    class Config:
        from_attributes = True
