from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional


class DocumentTypeOut(BaseModel):
    id: str
    code: str
    name: str
    prefix: str
    requires_periodic_review: bool
    review_period_months: int
    requires_training: bool
    class Config:
        from_attributes = True


class DocumentCreate(BaseModel):
    title: str = Field(..., min_length=5, max_length=500)
    document_type_id: str
    department: Optional[str] = None
    site_id: Optional[str] = None


class DocumentOut(BaseModel):
    id: str
    document_number: str
    title: str
    department: Optional[str]
    is_obsolete: bool
    created_at: datetime
    class Config:
        from_attributes = True


class DocumentVersionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version_number: str = Field(..., example="1.0")
    content: Optional[str] = None
    change_summary: Optional[str] = None
    change_reason: Optional[str] = None


class DocumentVersionOut(BaseModel):
    id: str
    document_id: str
    version_number: str
    status: str
    authored_by_id: str
    authored_date: Optional[datetime]
    approved_date: Optional[datetime]
    effective_date: Optional[datetime]
    next_review_date: Optional[datetime]
    change_summary: Optional[str]
    class Config:
        from_attributes = True


class DocumentVersionSignRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    password: str = Field(..., description="Re-authentication for 21 CFR Part 11")
    meaning: str = Field(..., description="reviewed | approved")
    comments: Optional[str] = None
