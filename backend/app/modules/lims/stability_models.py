"""
LIMS Stability Study Models
============================
ALCOA+ compliant SQLAlchemy models for pharmaceutical stability programmes.

Supports ICH Q1A(R2) study types: real-time, accelerated, intermediate,
and stress testing.  Each study is decomposed into discrete timepoints,
with individual test results captured per timepoint.

Tables
------
- stability_studies       : Study header (protocol, conditions, lifecycle)
- stability_timepoints    : Scheduled pull-points within a study
- stability_results       : Individual analytical results per timepoint
"""

from sqlalchemy import (
    Column,
    String,
    DateTime,
    Boolean,
    Integer,
    Text,
    ForeignKey,
    Enum,
    Float,
    Date,
    CheckConstraint,
    UniqueConstraint,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, declarative_base
import enum
import uuid
from datetime import datetime, timezone

Base = declarative_base()


def utcnow() -> datetime:
    """Return current UTC datetime (timezone-aware)."""
    return datetime.now(timezone.utc)


def new_uuid() -> str:
    """Return a new UUID4 string."""
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class StudyType(str, enum.Enum):
    REAL_TIME = "real_time"
    ACCELERATED = "accelerated"
    INTERMEDIATE = "intermediate"
    STRESSED = "stressed"
    PHOTO_STABILITY = "photo_stability"


class StudyStatus(str, enum.Enum):
    PLANNED = "planned"
    ACTIVE = "active"
    COMPLETED = "completed"
    DISCONTINUED = "discontinued"
    ON_HOLD = "on_hold"


class TimepointStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    MISSED = "missed"
    CANCELLED = "cancelled"


class PassFail(str, enum.Enum):
    PASS = "pass"
    FAIL = "fail"
    PENDING = "pending"
    OUT_OF_SPECIFICATION = "out_of_specification"


# ---------------------------------------------------------------------------
# StabilityStudy
# ---------------------------------------------------------------------------


class StabilityStudy(Base):
    """
    Header record for a stability study programme.

    A StabilityStudy defines the product, batch, storage condition, and
    protocol for a stability programme.  The study is broken into a series
    of StabilityTimepoints (e.g. T=0, T=3M, T=6M …), each of which
    generates one or more StabilityResults.

    ``protocol_document_id`` is a nullable FK that references the document
    management module where the approved study protocol is stored.
    """

    __tablename__ = "stability_studies"

    # ------------------------------------------------------------------
    # Primary key
    # ------------------------------------------------------------------
    id = Column(
        UUID(as_uuid=False),
        primary_key=True,
        default=new_uuid,
        nullable=False,
        comment="Surrogate primary key (UUID4)",
    )

    # ------------------------------------------------------------------
    # Study identification
    # ------------------------------------------------------------------
    title = Column(
        String(300),
        nullable=False,
        comment="Descriptive title of the stability study",
    )
    study_number = Column(
        String(50),
        nullable=True,
        comment="Internal study reference number (auto-generated or manual)",
    )
    product_name = Column(
        String(255),
        nullable=False,
        comment="Name of the product / formulation under study",
    )
    product_code = Column(
        String(100),
        nullable=True,
        comment="Product code or SKU",
    )
    batch_number = Column(
        String(100),
        nullable=False,
        comment="Batch / lot number placed on stability",
    )

    # ------------------------------------------------------------------
    # Study design
    # ------------------------------------------------------------------
    study_type = Column(
        Enum(StudyType, name="stability_study_type_enum"),
        nullable=False,
        comment="ICH stability study type",
    )
    storage_condition = Column(
        String(150),
        nullable=False,
        comment="Storage condition label (e.g. '25°C/60%RH', '40°C/75%RH')",
    )
    container_closure = Column(
        String(255),
        nullable=True,
        comment="Container closure system description",
    )
    orientation = Column(
        String(50),
        nullable=True,
        comment="Storage orientation (upright, inverted, horizontal)",
    )

    # ------------------------------------------------------------------
    # Protocol link
    # ------------------------------------------------------------------
    protocol_document_id = Column(
        UUID(as_uuid=False),
        nullable=True,
        comment="FK to document management record containing the approved protocol",
    )

    # ------------------------------------------------------------------
    # Timeline
    # ------------------------------------------------------------------
    start_date = Column(
        Date,
        nullable=False,
        comment="Date the first samples were placed on stability (T=0)",
    )
    planned_end_date = Column(
        Date,
        nullable=False,
        comment="Planned last timepoint date based on study duration",
    )
    actual_end_date = Column(
        Date,
        nullable=True,
        comment="Actual completion or discontinuation date",
    )

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    status = Column(
        Enum(StudyStatus, name="stability_study_status_enum"),
        nullable=False,
        default=StudyStatus.PLANNED,
        comment="Current lifecycle status of the study",
    )
    discontinuation_reason = Column(
        Text,
        nullable=True,
        comment="Reason for discontinuation (populated only if status = discontinued)",
    )

    # ------------------------------------------------------------------
    # Organisational context
    # ------------------------------------------------------------------
    organisation_id = Column(
        UUID(as_uuid=False),
        nullable=False,
        comment="Owning organisation UUID",
    )
    site_id = Column(
        UUID(as_uuid=False),
        nullable=True,
        comment="Originating site UUID",
    )

    # ------------------------------------------------------------------
    # Personnel
    # ------------------------------------------------------------------
    created_by_id = Column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        comment="User who registered the study",
    )
    study_manager_id = Column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="User responsible for managing the ongoing study",
    )

    # ------------------------------------------------------------------
    # Flexible metadata store
    # ------------------------------------------------------------------
    metadata_ = Column(
        "metadata",
        JSONB,
        nullable=True,
        default=dict,
        comment="Arbitrary key-value metadata (regulatory submission refs, etc.)",
    )

    # ------------------------------------------------------------------
    # ALCOA+ audit timestamps
    # ------------------------------------------------------------------
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        onupdate=utcnow,
    )
    is_active = Column(Boolean, nullable=False, default=True)

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------
    timepoints = relationship(
        "StabilityTimepoint",
        back_populates="study",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="StabilityTimepoint.scheduled_date",
    )

    # ------------------------------------------------------------------
    # Constraints & indexes
    # ------------------------------------------------------------------
    __table_args__ = (
        CheckConstraint(
            "planned_end_date >= start_date",
            name="ck_stability_studies_date_order",
        ),
        Index("ix_stability_studies_org_status", "organisation_id", "status"),
        Index("ix_stability_studies_product_batch", "product_code", "batch_number"),
    )

    def __repr__(self) -> str:
        return (
            f"<StabilityStudy id={self.id!r} title={self.title!r} "
            f"batch={self.batch_number!r} status={self.status!r}>"
        )


# ---------------------------------------------------------------------------
# StabilityTimepoint
# ---------------------------------------------------------------------------


class StabilityTimepoint(Base):
    """
    A single scheduled pull-point / interval within a StabilityStudy.

    Examples of timepoint_label: 'T=0', 'T=3 months', 'T=6 months',
    'T=12 months', 'T=24 months', '1-week stressed'.

    When the actual sample pull date differs from the scheduled date the
    difference is recorded and may be subject to ICH-compliant tolerance
    checks by the application layer.
    """

    __tablename__ = "stability_timepoints"

    # ------------------------------------------------------------------
    # Primary key
    # ------------------------------------------------------------------
    id = Column(
        UUID(as_uuid=False),
        primary_key=True,
        default=new_uuid,
        nullable=False,
    )

    # ------------------------------------------------------------------
    # Foreign key
    # ------------------------------------------------------------------
    study_id = Column(
        UUID(as_uuid=False),
        ForeignKey("stability_studies.id", ondelete="CASCADE"),
        nullable=False,
        comment="Parent stability study",
    )

    # ------------------------------------------------------------------
    # Timepoint details
    # ------------------------------------------------------------------
    timepoint_label = Column(
        String(100),
        nullable=False,
        comment="Human-readable timepoint label (e.g. 'T=6 months')",
    )
    scheduled_date = Column(
        Date,
        nullable=False,
        comment="Protocol-specified date for this pull-point",
    )
    actual_date = Column(
        Date,
        nullable=True,
        comment="Actual date samples were pulled (may differ within ICH tolerance)",
    )
    status = Column(
        Enum(TimepointStatus, name="timepoint_status_enum"),
        nullable=False,
        default=TimepointStatus.PENDING,
        comment="Current status of this timepoint",
    )
    notes = Column(
        Text,
        nullable=True,
        comment="Any deviations or comments relating to this timepoint",
    )

    # ------------------------------------------------------------------
    # ALCOA+ audit timestamps
    # ------------------------------------------------------------------
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        onupdate=utcnow,
    )
    is_active = Column(Boolean, nullable=False, default=True)

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------
    study = relationship("StabilityStudy", back_populates="timepoints")
    results = relationship(
        "StabilityResult",
        back_populates="timepoint",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="StabilityResult.test_name",
    )

    # ------------------------------------------------------------------
    # Indexes
    # ------------------------------------------------------------------
    __table_args__ = (
        Index(
            "ix_stability_timepoints_study_date",
            "study_id",
            "scheduled_date",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<StabilityTimepoint id={self.id!r} "
            f"label={self.timepoint_label!r} status={self.status!r}>"
        )


# ---------------------------------------------------------------------------
# StabilityResult
# ---------------------------------------------------------------------------


class StabilityResult(Base):
    """
    Individual analytical test result captured at a stability timepoint.

    Each row represents a single test (e.g. assay, pH, moisture content,
    particulate count) performed on the samples from a given timepoint.

    ``oos_triggered`` is set to True by the application when a result_value
    falls outside the registered specification, triggering an OOS
    investigation workflow.
    """

    __tablename__ = "stability_results"

    # ------------------------------------------------------------------
    # Primary key
    # ------------------------------------------------------------------
    id = Column(
        UUID(as_uuid=False),
        primary_key=True,
        default=new_uuid,
        nullable=False,
    )

    # ------------------------------------------------------------------
    # Foreign key
    # ------------------------------------------------------------------
    timepoint_id = Column(
        UUID(as_uuid=False),
        ForeignKey("stability_timepoints.id", ondelete="CASCADE"),
        nullable=False,
        comment="Parent stability timepoint",
    )

    # ------------------------------------------------------------------
    # Test identification
    # ------------------------------------------------------------------
    test_name = Column(
        String(200),
        nullable=False,
        comment="Name of the analytical test (e.g. 'Assay by HPLC', 'Water content')",
    )
    method_reference = Column(
        String(150),
        nullable=True,
        comment="Analytical method reference (e.g. 'Ph.Eur. 2.5.12', 'STP-001')",
    )
    specification = Column(
        String(255),
        nullable=True,
        comment="Acceptance criterion as stated in the specification or protocol",
    )

    # ------------------------------------------------------------------
    # Result data
    # ------------------------------------------------------------------
    result_value = Column(
        String(100),
        nullable=False,
        comment="Reported result value (stored as string to accommodate ranges, <LOD, etc.)",
    )
    numeric_result = Column(
        Float,
        nullable=True,
        comment="Numeric form of the result for statistical calculations",
    )
    unit = Column(
        String(50),
        nullable=True,
        comment="Unit of measurement (e.g. '%', 'mg/mL', 'ppm')",
    )
    pass_fail = Column(
        Enum(PassFail, name="stability_pass_fail_enum"),
        nullable=False,
        default=PassFail.PENDING,
        comment="Compliance determination against specification",
    )

    # ------------------------------------------------------------------
    # OOS / OOT tracking
    # ------------------------------------------------------------------
    oos_triggered = Column(
        Boolean,
        nullable=False,
        default=False,
        comment="True if an Out-Of-Specification investigation has been triggered",
    )
    oot_triggered = Column(
        Boolean,
        nullable=False,
        default=False,
        comment="True if an Out-Of-Trend alert has been raised",
    )
    oos_investigation_id = Column(
        UUID(as_uuid=False),
        nullable=True,
        comment="FK to the linked OOS investigation record (if triggered)",
    )

    # ------------------------------------------------------------------
    # Attribution
    # ------------------------------------------------------------------
    analyst_id = Column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        comment="Analyst who performed and recorded the test",
    )
    analysed_at = Column(
        DateTime(timezone=True),
        nullable=False,
        comment="UTC timestamp when the analysis was completed and recorded",
    )
    reviewed_by_id = Column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
        comment="Second reviewer (peer check) for the result",
    )
    reviewed_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="UTC timestamp of second review",
    )

    # ------------------------------------------------------------------
    # ALCOA+ audit timestamps
    # ------------------------------------------------------------------
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        onupdate=utcnow,
    )
    is_active = Column(Boolean, nullable=False, default=True)

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------
    timepoint = relationship("StabilityTimepoint", back_populates="results")

    # ------------------------------------------------------------------
    # Indexes
    # ------------------------------------------------------------------
    __table_args__ = (
        Index(
            "ix_stability_results_timepoint_test",
            "timepoint_id",
            "test_name",
        ),
        Index("ix_stability_results_oos", "oos_triggered"),
    )

    def __repr__(self) -> str:
        return (
            f"<StabilityResult id={self.id!r} test={self.test_name!r} "
            f"value={self.result_value!r} pass_fail={self.pass_fail!r}>"
        )
