"""
MES Module — Master Batch Records, Electronic Batch Records, Production Execution.

This replaces Syncade / paper-based batch records.

Key GMP rules:
  - Master Batch Records (MBR) are version-controlled and approval-gated
  - Electronic Batch Records (EBR) are executed against a specific MBR version
  - Every step entry is timestamped server-side (ALCOA Contemporaneous)
  - Steps cannot be back-filled — they must be entered at time of execution
  - Deviations during execution are linked to the Deviation module automatically
  - Completed batch records require QA review and electronic signature before release
"""
from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey, Integer, Float, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.core.database import Base


class Product(Base):
    __tablename__ = "products"

    product_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    product_type: Mapped[str] = mapped_column(String(100), nullable=False)  # drug_substance|drug_product|intermediate
    unit_of_measure: Mapped[str] = mapped_column(String(20), nullable=False)
    shelf_life_months: Mapped[int | None] = mapped_column(Integer, nullable=True)
    storage_conditions: Mapped[str | None] = mapped_column(String(200), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    site_id: Mapped[str] = mapped_column(String(36), ForeignKey("sites.id"), nullable=False)

    master_batch_records: Mapped[list["MasterBatchRecord"]] = relationship(
        "MasterBatchRecord", back_populates="product"
    )


class MasterBatchRecord(Base):
    """
    The approved template for manufacturing a product.
    Replaces paper MBR / Syncade recipe.
    """
    __tablename__ = "master_batch_records"

    mbr_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    product_id: Mapped[str] = mapped_column(String(36), ForeignKey("products.id"), nullable=False)
    version: Mapped[str] = mapped_column(String(20), nullable=False, default="1.0")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="draft")
    # Statuses: draft | under_review | approved | effective | superseded | obsolete

    batch_size: Mapped[float] = mapped_column(Float, nullable=False)
    batch_size_unit: Mapped[str] = mapped_column(String(20), nullable=False)
    theoretical_yield: Mapped[float | None] = mapped_column(Float, nullable=True)
    yield_unit: Mapped[str | None] = mapped_column(String(20), nullable=True)
    acceptable_yield_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    acceptable_yield_max: Mapped[float | None] = mapped_column(Float, nullable=True)

    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    equipment_required: Mapped[list | None] = mapped_column(JSON, nullable=True)
    critical_process_parameters: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    authored_by_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    approved_by_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    effective_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    superseded_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Link to document control
    document_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("documents.id"), nullable=True)
    workflow_instance_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("workflow_instances.id"), nullable=True)

    product: Mapped["Product"] = relationship("Product", back_populates="master_batch_records")
    steps: Mapped[list["MBRStep"]] = relationship("MBRStep", back_populates="mbr", order_by="MBRStep.step_number")
    batch_records: Mapped[list["BatchRecord"]] = relationship("BatchRecord", back_populates="master_batch_record")


class MBRStep(Base):
    """One step in the master batch record template."""
    __tablename__ = "mbr_steps"

    mbr_id: Mapped[str] = mapped_column(String(36), ForeignKey("master_batch_records.id"), nullable=False)
    step_number: Mapped[int] = mapped_column(Integer, nullable=False)
    phase: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g. "Preparation", "Mixing", "Filling"
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    instructions: Mapped[str] = mapped_column(Text, nullable=False)
    step_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # Step types: action|check|measurement|weight|ipc|critical_step|signature_required

    # Expected values (for measurements/checks)
    expected_value: Mapped[str | None] = mapped_column(String(100), nullable=True)
    expected_unit: Mapped[str | None] = mapped_column(String(20), nullable=True)
    lower_limit: Mapped[float | None] = mapped_column(Float, nullable=True)
    upper_limit: Mapped[float | None] = mapped_column(Float, nullable=True)

    is_critical: Mapped[bool] = mapped_column(Boolean, default=False)
    requires_second_check: Mapped[bool] = mapped_column(Boolean, default=False)
    requires_signature: Mapped[bool] = mapped_column(Boolean, default=False)
    allow_na: Mapped[bool] = mapped_column(Boolean, default=False)

    mbr: Mapped["MasterBatchRecord"] = relationship("MasterBatchRecord", back_populates="steps")


class BatchRecord(Base):
    """
    A live execution of a MasterBatchRecord for a specific batch.
    One row per manufactured batch.
    """
    __tablename__ = "batch_records"

    batch_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    master_batch_record_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("master_batch_records.id"), nullable=False
    )
    product_id: Mapped[str] = mapped_column(String(36), ForeignKey("products.id"), nullable=False)
    site_id: Mapped[str] = mapped_column(String(36), ForeignKey("sites.id"), nullable=False)

    status: Mapped[str] = mapped_column(String(50), nullable=False, default="in_progress")
    # Statuses: in_progress | completed | qa_review | released | rejected | quarantine

    # Execution details
    planned_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_completion: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    executed_by_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)

    # Yield
    actual_yield: Mapped[float | None] = mapped_column(Float, nullable=True)
    yield_unit: Mapped[str | None] = mapped_column(String(20), nullable=True)
    yield_percentage: Mapped[float | None] = mapped_column(Float, nullable=True)

    # QA Review
    reviewed_by_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    release_decision: Mapped[str | None] = mapped_column(String(50), nullable=True)  # released|rejected
    release_comments: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Deviations during execution
    has_deviations: Mapped[bool] = mapped_column(Boolean, default=False)

    master_batch_record: Mapped["MasterBatchRecord"] = relationship("MasterBatchRecord", back_populates="batch_records")
    steps: Mapped[list["BatchRecordStep"]] = relationship(
        "BatchRecordStep", back_populates="batch_record", order_by="BatchRecordStep.step_number"
    )


class BatchRecordStep(Base):
    """
    Execution record for one step in a live batch record.
    Timestamps are server-set — cannot be back-filled (ALCOA Contemporaneous).
    """
    __tablename__ = "batch_record_steps"

    batch_record_id: Mapped[str] = mapped_column(String(36), ForeignKey("batch_records.id"), nullable=False)
    mbr_step_id: Mapped[str] = mapped_column(String(36), ForeignKey("mbr_steps.id"), nullable=False)
    step_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    # Statuses: pending | in_progress | completed | skipped | deviated

    # Recorded values
    recorded_value: Mapped[str | None] = mapped_column(String(200), nullable=True)
    is_within_limits: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    is_na: Mapped[bool] = mapped_column(Boolean, default=False)
    comments: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Who did it and when (server-set, immutable after entry)
    performed_by_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    performed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)  # Server UTC

    # Second check (if required)
    checked_by_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Loose cross-module reference to QMS deviation (no hard FK coupling).
    linked_deviation_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    # Signature (for critical steps)
    signature_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("electronic_signatures.id"), nullable=True)

    batch_record: Mapped["BatchRecord"] = relationship("BatchRecord", back_populates="steps")
