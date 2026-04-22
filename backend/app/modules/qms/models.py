"""
QMS Module — CAPA, Deviations, Change Control, Risk Management.
This is Phase 2 of the build — the first sellable module.
All records use the shared workflow engine and audit trail from the foundation.
"""
from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.core.database import Base


# ─── CAPA ────────────────────────────────────────────────────────────────────

class CAPA(Base):
    __tablename__ = "capas"

    # Identification
    capa_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    capa_type: Mapped[str] = mapped_column(String(50), nullable=False)  # corrective | preventive

    # Classification
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    # Sources: deviation, audit_finding, customer_complaint, oos_result, trend_analysis, self_inspection, other
    source_record_id: Mapped[str | None] = mapped_column(String(36), nullable=True)  # Link to source record
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False, default="medium")  # low|medium|high|critical
    product_impact: Mapped[bool] = mapped_column(Boolean, default=False)
    patient_safety_impact: Mapped[bool] = mapped_column(Boolean, default=False)
    regulatory_reportable: Mapped[bool] = mapped_column(Boolean, default=False)

    # Description
    problem_description: Mapped[str] = mapped_column(Text, nullable=False)
    immediate_actions: Mapped[str | None] = mapped_column(Text, nullable=True)
    root_cause: Mapped[str | None] = mapped_column(Text, nullable=True)
    root_cause_method: Mapped[str | None] = mapped_column(String(100), nullable=True)  # 5-why, fishbone, etc.

    # Effectiveness
    effectiveness_criteria: Mapped[str | None] = mapped_column(Text, nullable=True)
    effectiveness_check_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    effectiveness_result: Mapped[str | None] = mapped_column(String(50), nullable=True)  # effective|not_effective
    effectiveness_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Ownership
    site_id: Mapped[str] = mapped_column(String(36), ForeignKey("sites.id"), nullable=False)
    owner_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    department: Mapped[str] = mapped_column(String(100), nullable=False)

    # Dates
    identified_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    target_completion_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_completion_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Workflow (managed by workflow engine)
    workflow_instance_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("workflow_instances.id"), nullable=True)
    current_status: Mapped[str] = mapped_column(String(50), nullable=False, default="draft")

    actions: Mapped[list["CAPAAction"]] = relationship("CAPAAction", back_populates="capa")
    attachments: Mapped[list["CAPAAttachment"]] = relationship("CAPAAttachment", back_populates="capa")


class CAPAAction(Base):
    __tablename__ = "capa_actions"

    capa_id: Mapped[str] = mapped_column(String(36), ForeignKey("capas.id"), nullable=False, index=True)
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    action_type: Mapped[str] = mapped_column(String(50), nullable=False)  # corrective|preventive|verification
    assignee_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="open")
    completion_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_frozen: Mapped[bool] = mapped_column(Boolean, default=False)  # e.g. during system migration
    freeze_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    capa: Mapped["CAPA"] = relationship("CAPA", back_populates="actions")


class CAPAAttachment(Base):
    __tablename__ = "capa_attachments"

    capa_id: Mapped[str] = mapped_column(String(36), ForeignKey("capas.id"), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    uploaded_by_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    capa: Mapped["CAPA"] = relationship("CAPA", back_populates="attachments")


# ─── DEVIATION ────────────────────────────────────────────────────────────────

class Deviation(Base):
    __tablename__ = "deviations"

    deviation_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    deviation_type: Mapped[str] = mapped_column(String(50), nullable=False)  # planned|unplanned
    category: Mapped[str] = mapped_column(String(100), nullable=False)  # process|equipment|material|environmental
    description: Mapped[str] = mapped_column(Text, nullable=False)
    detected_during: Mapped[str] = mapped_column(String(100), nullable=False)
    detected_by_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    detection_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    batch_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    product_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False, default="medium")
    immediate_action: Mapped[str | None] = mapped_column(Text, nullable=True)
    root_cause: Mapped[str | None] = mapped_column(Text, nullable=True)
    batch_disposition: Mapped[str | None] = mapped_column(String(50), nullable=True)  # release|reject|pending
    linked_capa_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("capas.id"), nullable=True)
    site_id: Mapped[str] = mapped_column(String(36), ForeignKey("sites.id"), nullable=False)
    owner_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    current_status: Mapped[str] = mapped_column(String(50), nullable=False, default="draft")
    workflow_instance_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("workflow_instances.id"), nullable=True)


# ─── CHANGE CONTROL ──────────────────────────────────────────────────────────

class ChangeControl(Base):
    __tablename__ = "change_controls"

    change_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    change_type: Mapped[str] = mapped_column(String(100), nullable=False)  # process|equipment|material|software|facility
    change_category: Mapped[str] = mapped_column(String(50), nullable=False)  # minor|major|critical
    description: Mapped[str] = mapped_column(Text, nullable=False)
    justification: Mapped[str] = mapped_column(Text, nullable=False)
    risk_assessment: Mapped[str | None] = mapped_column(Text, nullable=True)
    impact_assessment: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    regulatory_impact: Mapped[bool] = mapped_column(Boolean, default=False)
    validation_required: Mapped[bool] = mapped_column(Boolean, default=False)
    proposed_implementation_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_implementation_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    site_id: Mapped[str] = mapped_column(String(36), ForeignKey("sites.id"), nullable=False)
    owner_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    current_status: Mapped[str] = mapped_column(String(50), nullable=False, default="draft")
    workflow_instance_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("workflow_instances.id"), nullable=True)
