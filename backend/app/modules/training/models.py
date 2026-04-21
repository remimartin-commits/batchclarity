"""
Training Management Module.
Covers: Training curricula, assignments, completion tracking, competency assessments,
        SOP read-and-understood sign-off, training matrices.

GMP requirement: Personnel must be trained and competent before performing GMP activities.
New document versions automatically trigger retraining assignments.
"""
from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.core.database import Base


class TrainingCurriculum(Base):
    __tablename__ = "training_curricula"

    name: Mapped[str] = mapped_column(String(300), nullable=False)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    target_roles: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    target_departments: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    is_gmp_mandatory: Mapped[bool] = mapped_column(Boolean, default=True)
    site_id: Mapped[str] = mapped_column(String(36), ForeignKey("sites.id"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    items: Mapped[list["CurriculumItem"]] = relationship("CurriculumItem", back_populates="curriculum")


class CurriculumItem(Base):
    __tablename__ = "curriculum_items"

    curriculum_id: Mapped[str] = mapped_column(String(36), ForeignKey("training_curricula.id"), nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    item_type: Mapped[str] = mapped_column(String(50), nullable=False)  # document | assessment | on_job | video
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    document_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=True)
    requires_assessment: Mapped[bool] = mapped_column(Boolean, default=False)
    minimum_score: Mapped[int | None] = mapped_column(Integer, nullable=True)  # % pass mark
    validity_period_months: Mapped[int | None] = mapped_column(Integer, nullable=True)  # None = no expiry

    curriculum: Mapped["TrainingCurriculum"] = relationship("TrainingCurriculum", back_populates="items")


class TrainingAssignment(Base):
    __tablename__ = "training_assignments"

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    curriculum_item_id: Mapped[str] = mapped_column(String(36), ForeignKey("curriculum_items.id"), nullable=False)
    assigned_by_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    # Statuses: pending | in_progress | completed | overdue | waived

    # Triggered by document version change?
    triggered_by_document_version_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    completion: Mapped["TrainingCompletion | None"] = relationship(
        "TrainingCompletion", back_populates="assignment", uselist=False
    )


class TrainingCompletion(Base):
    __tablename__ = "training_completions"

    assignment_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("training_assignments.id"), unique=True, nullable=False
    )
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completion_method: Mapped[str] = mapped_column(String(50), nullable=False)  # self_study | classroom | on_job
    assessment_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Read & Understood — electronic signature
    signature_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("electronic_signatures.id"), nullable=True)
    trainer_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    assignment: Mapped["TrainingAssignment"] = relationship("TrainingAssignment", back_populates="completion")
