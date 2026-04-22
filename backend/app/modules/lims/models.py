"""
LIMS — Laboratory Information Management System.
Covers: samples, test methods, results, OOS investigations, CoA, stability studies.
"""
from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey, Integer, Float, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.core.database import Base


class TestMethod(Base):
    """Approved analytical test method. Version-controlled."""
    __tablename__ = "test_methods"

    method_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    method_type: Mapped[str] = mapped_column(String(100), nullable=False)
    # Types: identity | assay | impurity | microbial | dissolution | particle_size | viscosity | pH | other
    unit: Mapped[str] = mapped_column(String(50), nullable=False)
    version: Mapped[str] = mapped_column(String(20), nullable=False, default="1.0")
    document_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    is_compendial: Mapped[bool] = mapped_column(Boolean, default=False)  # USP/EP/JP method
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Specification(Base):
    """Product/material specification with acceptance criteria per test."""
    __tablename__ = "specifications"

    spec_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    material_type: Mapped[str] = mapped_column(String(50), nullable=False)  # product | raw_material | packaging
    product_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    version: Mapped[str] = mapped_column(String(20), nullable=False, default="1.0")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="draft")
    document_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    tests: Mapped[list["SpecificationTest"]] = relationship("SpecificationTest", back_populates="specification")


class SpecificationTest(Base):
    """One test within a specification — defines acceptance criteria."""
    __tablename__ = "specification_tests"

    specification_id: Mapped[str] = mapped_column(String(36), ForeignKey("specifications.id"), nullable=False)
    test_method_id: Mapped[str] = mapped_column(String(36), ForeignKey("test_methods.id"), nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=True)
    # Acceptance criteria
    acceptance_criteria: Mapped[str] = mapped_column(Text, nullable=False)  # e.g. "98.0% - 102.0%"
    lower_limit: Mapped[float | None] = mapped_column(Float, nullable=True)
    upper_limit: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit: Mapped[str | None] = mapped_column(String(50), nullable=True)

    specification: Mapped["Specification"] = relationship("Specification", back_populates="tests")


class Sample(Base):
    """A physical sample submitted for laboratory testing."""
    __tablename__ = "samples"

    sample_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    sample_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # Types: in_process | finished_product | raw_material | stability | environmental | water | reference

    # Source traceability
    batch_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    product_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    specification_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("specifications.id"), nullable=True)

    sampled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    sampled_by_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    received_by_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    storage_conditions: Mapped[str | None] = mapped_column(String(200), nullable=True)
    expiry_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    site_id: Mapped[str] = mapped_column(String(36), ForeignKey("sites.id"), nullable=False)

    status: Mapped[str] = mapped_column(String(50), nullable=False, default="received")
    # Statuses: received | in_testing | completed | released | rejected | discarded

    results: Mapped[list["TestResult"]] = relationship("TestResult", back_populates="sample")


class TestResult(Base):
    """
    A single test result for a sample.
    OOS status triggers automatic investigation workflow.
    Results are APPEND-ONLY — corrections require a new result with reference to the original.
    """
    __tablename__ = "test_results"

    sample_id: Mapped[str] = mapped_column(String(36), ForeignKey("samples.id"), nullable=False, index=True)
    test_method_id: Mapped[str] = mapped_column(String(36), ForeignKey("test_methods.id"), nullable=False)
    specification_test_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("specification_tests.id"), nullable=True
    )

    # Raw result
    result_value: Mapped[str] = mapped_column(String(200), nullable=False)  # String to support ranges, "complies"
    result_numeric: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Who and when (ALCOA)
    analyst_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    tested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    entered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Compliance (server-set against specification)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending_review")
    # Statuses: pending_review | pass | fail | oos | oot | invalidated

    acceptance_criteria_at_time: Mapped[str | None] = mapped_column(String(200), nullable=True)  # Snapshot
    reviewer_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    review_comments: Mapped[str | None] = mapped_column(Text, nullable=True)

    # OOS investigation linkage
    is_oos: Mapped[bool] = mapped_column(Boolean, default=False)
    linked_investigation_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("oos_investigations.id"), nullable=True
    )
    signature_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("electronic_signatures.id"), nullable=True
    )

    sample: Mapped["Sample"] = relationship("Sample", back_populates="results")


class OOSInvestigation(Base):
    """
    Out-of-Specification investigation record.
    Triggered automatically when a test result exceeds specification.
    """
    __tablename__ = "oos_investigations"

    investigation_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    sample_id: Mapped[str] = mapped_column(String(36), ForeignKey("samples.id"), nullable=False)
    initial_result_id: Mapped[str] = mapped_column(String(36), ForeignKey("test_results.id"), nullable=False)

    # Phase 1 — Lab investigation
    phase1_conclusion: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Conclusions: assignable_cause_found | no_assignable_cause
    phase1_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    phase1_completed_by_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)

    # Phase 2 — Full investigation (if no assignable cause in Phase 1)
    root_cause: Mapped[str | None] = mapped_column(Text, nullable=True)
    corrective_action: Mapped[str | None] = mapped_column(Text, nullable=True)
    linked_capa_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    # Disposition
    final_disposition: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # Dispositions: reject | retest | release_with_justification
    disposition_justification: Mapped[str | None] = mapped_column(Text, nullable=True)

    assigned_to_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="open")
    workflow_instance_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("workflow_instances.id"), nullable=True
    )
