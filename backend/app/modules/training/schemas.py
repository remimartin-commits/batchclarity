from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional


class CurriculumItemCreate(BaseModel):
    sequence: int
    item_type: str  # document | assessment | on_job | video
    title: str = Field(..., min_length=3)
    document_id: Optional[str] = None
    is_mandatory: bool = True
    requires_assessment: bool = False
    minimum_score: Optional[int] = None
    validity_period_months: Optional[int] = None


class CurriculumCreate(BaseModel):
    name: str = Field(..., min_length=3)
    code: str = Field(..., min_length=2, max_length=50)
    description: Optional[str] = None
    target_roles: list[str] = []
    target_departments: list[str] = []
    is_gmp_mandatory: bool = True
    site_id: str
    items: list[CurriculumItemCreate] = []


class CurriculumOut(BaseModel):
    id: str
    name: str
    code: str
    description: Optional[str]
    target_roles: list
    target_departments: list
    is_gmp_mandatory: bool
    is_active: bool
    created_at: datetime
    class Config:
        from_attributes = True


class CurriculumItemOut(BaseModel):
    id: str
    sequence: int
    item_type: str
    title: str
    document_id: Optional[str]
    is_mandatory: bool
    requires_assessment: bool
    minimum_score: Optional[int]
    validity_period_months: Optional[int]

    class Config:
        from_attributes = True


class CurriculumDetailOut(CurriculumOut):
    items: list[CurriculumItemOut] = []


class TrainingAssignmentCreate(BaseModel):
    user_id: str
    curriculum_item_id: str
    due_date: Optional[datetime] = None


class TrainingAssignmentOut(BaseModel):
    id: str
    user_id: str
    curriculum_item_id: str
    assigned_at: datetime
    due_date: Optional[datetime]
    status: str
    created_at: datetime
    class Config:
        from_attributes = True


class TrainingCompletionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    completion_method: str  # self_study | classroom | on_job
    assessment_score: Optional[int] = None
    passed: bool
    notes: Optional[str] = None


class TrainingCompletionOut(BaseModel):
    id: str
    assignment_id: str
    completed_at: datetime
    completion_method: str
    assessment_score: Optional[int]
    passed: bool
    expires_at: Optional[datetime]
    class Config:
        from_attributes = True


class ReadAndUnderstoodRequest(BaseModel):
    """Electronic sign-off for SOP read & understood."""
    model_config = ConfigDict(extra="forbid")

    password: str = Field(..., description="Re-auth for 21 CFR Part 11")
    notes: Optional[str] = None


class TrainingMatrixRow(BaseModel):
    user_id: str
    full_name: str
    department: Optional[str]
    curriculum_item_id: str
    item_title: str
    status: str
    completed_at: Optional[datetime]
    expires_at: Optional[datetime]
    is_overdue: bool
