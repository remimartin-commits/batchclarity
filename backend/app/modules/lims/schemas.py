from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional


class SampleCreate(BaseModel):
    sample_number: str = Field(..., min_length=3)
    sample_type: str
    batch_number: Optional[str] = None
    product_id: Optional[str] = None
    specification_id: Optional[str] = None
    sampled_at: datetime
    storage_conditions: Optional[str] = None
    expiry_date: Optional[datetime] = None
    site_id: str


class SampleOut(BaseModel):
    id: str
    sample_number: str
    sample_type: str
    batch_number: Optional[str]
    product_id: Optional[str]
    status: str
    sampled_at: datetime
    received_at: Optional[datetime]
    created_at: datetime
    class Config:
        from_attributes = True


class TestResultCreate(BaseModel):
    test_method_id: str
    specification_test_id: Optional[str] = None
    result_value: str
    result_numeric: Optional[float] = None
    unit: Optional[str] = None
    tested_at: datetime  # ignored in service — timestamps are server-set (ALCOA)
    is_oos: bool = False
    spec_limit: Optional[str] = None  # for auto-deviation text when is_oos


class TestResultOut(BaseModel):
    id: str
    sample_id: str
    test_method_id: str
    result_value: str
    result_numeric: Optional[float]
    unit: Optional[str]
    analyst_id: str
    tested_at: datetime
    status: str
    is_oos: bool
    linked_investigation_id: Optional[str]
    is_invalidated: bool = False
    corrects_result_id: Optional[str] = None
    created_at: datetime
    class Config:
        from_attributes = True


class TestResultCorrectionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: str = Field(..., min_length=5)
    result_value: str
    result_numeric: Optional[float] = None
    unit: Optional[str] = None


class TestResultReviewRequest(BaseModel):
    password: str = Field(..., description="Re-auth for 21 CFR Part 11")
    decision: str = Field(..., description="pass | fail | oos | invalidated")
    comments: Optional[str] = None


class OOSInvestigationOut(BaseModel):
    id: str
    investigation_number: str
    sample_id: str
    status: str
    phase1_conclusion: Optional[str]
    root_cause: Optional[str]
    final_disposition: Optional[str]
    created_at: datetime
    class Config:
        from_attributes = True


class OOSInvestigationCloseRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    password: str = Field(..., description="Re-auth for 21 CFR Part 11")
    final_disposition: str
    disposition_justification: str = Field(..., min_length=10)
    root_cause: Optional[str] = None
    corrective_action: Optional[str] = None


class SpecificationCreate(BaseModel):
    spec_number: str = Field(..., min_length=3)
    name: str = Field(..., min_length=3)
    material_type: str
    product_id: Optional[str] = None
    version: str = "1.0"


class SpecificationOut(BaseModel):
    id: str
    spec_number: str
    name: str
    material_type: str
    product_id: Optional[str]
    version: str
    status: str
    created_at: datetime
    class Config:
        from_attributes = True
