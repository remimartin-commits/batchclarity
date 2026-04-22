"""
LIMS Certificate of Analysis (CoA) Models
==========================================
ALCOA+ compliant SQLAlchemy models for generating, managing, and
releasing Certificates of Analysis for pharmaceutical batches.

A CoA is the formal document that attests a batch meets its specification
before release to market or transfer to the next manufacturing step.

Tables
------
- certificates_of_analysis   : CoA header (batch identity, release status)
- coa_test_lines             : Individual test result lines on the CoA
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


class ReleaseStatus(str, enum.Enum):
    PENDING = "pending"
    RELEASED = "released"
    REJECTED = "rejected"
    QUARANTINE = "quarantine"
    RECALLED = "recalled"


class CoAPassFail(str, enum.Enum):
    PASS = "pass"
    FAIL = "fail"
    PENDING = "pending"


# ---------------------------------------------------------------------------
# CertificateOfAnalysis
# ---------------------------------------------------------------------------


class CertificateOfAnalysis(Base):
    """
    Header record for a batch Certificate of Analysis.

    The CoA summarises the results of all quality control tests performed
    on a batch, and is the primary document used for batch release decisions
    by the Qualified Person (QP) or authorised releaser.

    ``coa_number`` is unique within an organisation and follows the site's
    document numbering convention (e.g. "COA-2026-00123").

    Workflow:
      PENDING → review test lines → RELEASED or REJECTED
    """

    __tablename__ = "certificates_of_analysis"

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
    # Document identification
    # ------------------------------------------------------------------
    coa_number = Column(
        String(100),
        nullable=False,
        comment="Unique CoA reference number within the organisation",
    )

    # ------------------------------------------------------------------
    # Batch identity
    # ------------------------------------------------------------------
    batch_number = Column(
        String(100),
        nullable=False,
        comment="Manufacturing batch / lot number",
    )
    product_name = Column(
        String(255),
        nullable=False,
        comment="Full product name as registered",
    )
    product_code = Column(
        String(100),
        nullable=False,
        comment="Internal product code or SKU",
    )

    # ------------------------------------------------------------------
    # Batch dates
    # ------------------------------------------------------------------
    manufacturing_date = Column(
        Date,
        nullable=False,
        comment="Date of manufacture (start of manufacture or batch start date)",
    )
    expiry_date = Column(
        Date,
        nullable=False,
        comment="Expiry / use-by date assigned to this batch",
    )
    retest_date = Column(
        Date,
        nullable=True,
        comment="Retest date (where applicable instead of expiry)",
    )

    # ------------------------------------------------------------------
    # Storage & handling
    # ------------------------------------------------------------------
    storage_conditions = Column(
        String(255),
        nullable=True,
        comment="Approved storage conditions (e.g. 'Store below 25°C, protect from light')",
    )

    # ------------------------------------------------------------------
    # Release decision
    # ------------------------------------------------------------------
    release_status = Column(
        Enum(ReleaseStatus, name="coa_release_status_enum"),
        nullable=False,
        default=ReleaseStatus.PENDING,
        comment="Current release status of the batch",
    )
    released_by_id = Column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
        comment="Qualified Person or authorised user who released this batch",
    )
    released_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="UTC timestamp of the release decision",
    )
    rejection_reason = Column(
        Text,
        nullable=True,
        comment="Reason for rejection (populated when release_status = rejected)",
    )

    # ------------------------------------------------------------------
    # Electronic signature / attestation statement
    # ------------------------------------------------------------------
    attestation_statement = Column(
        Text,
        nullable=True,
        comment="Text of the QP attestation / declaration of conformity",
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
        comment="Manufacturing site UUID",
    )

    # ------------------------------------------------------------------
    # Document storage
    # ------------------------------------------------------------------
    signed_document_path = Column(
        String(1024),
        nullable=True,
        comment="Path or object key for the signed/finalised CoA PDF",
    )

    # ------------------------------------------------------------------
    # Personnel
    # ------------------------------------------------------------------
    created_by_id = Column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        comment="User who created this CoA record",
    )

    # ------------------------------------------------------------------
    # Flexible metadata store
    # ------------------------------------------------------------------
    metadata_ = Column(
        "metadata",
        JSONB,
        nullable=True,
        default=dict,
        comment="Arbitrary key-value metadata (customer references, customs data, etc.)",
    )

    # ------------------------------------------------------------------
    # ALCOA+ audit timestamps
    # ------------------------------------------------------------------
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        comment="UTC timestamp of record creation",
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        onupdate=utcnow,
        comment="UTC timestamp of last modification",
    )
    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        comment="Soft-delete flag",
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------
    test_lines = relationship(
        "CoATestLine",
        back_populates="coa",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="CoATestLine.sort_order, CoATestLine.test_name",
    )

    # ------------------------------------------------------------------
    # Constraints & indexes
    # ------------------------------------------------------------------
    __table_args__ = (
        UniqueConstraint(
            "organisation_id",
            "coa_number",
            name="uq_coa_org_number",
        ),
        CheckConstraint(
            "expiry_date > manufacturing_date",
            name="ck_coa_date_order",
        ),
        Index("ix_coa_org_status", "organisation_id", "release_status"),
        Index("ix_coa_batch_product", "batch_number", "product_code"),
        Index("ix_coa_expiry", "expiry_date"),
    )

    def __repr__(self) -> str:
        return (
            f"<CertificateOfAnalysis id={self.id!r} "
            f"coa_number={self.coa_number!r} "
            f"batch={self.batch_number!r} status={self.release_status!r}>"
        )


# ---------------------------------------------------------------------------
# CoATestLine
# ---------------------------------------------------------------------------


class CoATestLine(Base):
    """
    Individual test result line item on a Certificate of Analysis.

    Each CoATestLine corresponds to a single analytical test listed on the
    CoA (e.g. Assay, pH, Particle Size, Microbial Limits).

    The ``sort_order`` field controls the display sequence of tests on the
    printed / exported CoA document.

    Notes on ``result`` field:
      - Stored as String to accommodate ranges (e.g. '98.5 – 101.2 %'),
        qualitative values ('Complies', 'White crystalline powder'), and
        numeric values with units.
      - ``numeric_result`` is the parsed float value for data trending.
    """

    __tablename__ = "coa_test_lines"

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
    coa_id = Column(
        UUID(as_uuid=False),
        ForeignKey("certificates_of_analysis.id", ondelete="CASCADE"),
        nullable=False,
        comment="Parent Certificate of Analysis",
    )

    # ------------------------------------------------------------------
    # Test identification
    # ------------------------------------------------------------------
    test_name = Column(
        String(200),
        nullable=False,
        comment="Name of the test (e.g. 'Assay by HPLC', 'Identification', 'pH')",
    )
    method_reference = Column(
        String(150),
        nullable=True,
        comment="Analytical method reference (e.g. 'Ph.Eur. 2.2.3', 'STP-ASSAY-001')",
    )
    specification = Column(
        String(255),
        nullable=False,
        comment="Acceptance criterion (e.g. '98.0 – 102.0 %', 'NMT 0.5 %')",
    )
    test_category = Column(
        String(100),
        nullable=True,
        comment="Grouping category for the test (e.g. 'Physical', 'Chemical', 'Microbiological')",
    )

    # ------------------------------------------------------------------
    # Result
    # ------------------------------------------------------------------
    result = Column(
        String(255),
        nullable=False,
        comment="Reported result as it appears on the CoA document",
    )
    numeric_result = Column(
        Float,
        nullable=True,
        comment="Numeric value of the result (for trending and statistical use)",
    )
    unit = Column(
        String(50),
        nullable=True,
        comment="Unit of measurement",
    )
    pass_fail = Column(
        Enum(CoAPassFail, name="coa_pass_fail_enum"),
        nullable=False,
        default=CoAPassFail.PENDING,
        comment="Compliance determination against specification",
    )

    # ------------------------------------------------------------------
    # Linked LIMS data
    # ------------------------------------------------------------------
    lims_sample_id = Column(
        UUID(as_uuid=False),
        nullable=True,
        comment="FK to the LIMS Sample record that generated this result",
    )
    lims_test_result_id = Column(
        UUID(as_uuid=False),
        nullable=True,
        comment="FK to the specific LIMS TestResult record",
    )

    # ------------------------------------------------------------------
    # Attribution
    # ------------------------------------------------------------------
    analyst_id = Column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        comment="Analyst who performed the test",
    )
    analysed_at = Column(
DateTime(timezone=True),
        nullable=False,
        comment="UTC timestamp when the test was completed",
    )
    reviewed_by_id = Column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
        comment="Second reviewer (peer check) for this test line",
    )
    reviewed_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="UTC timestamp of the second review",
    )

    # ------------------------------------------------------------------
    # Display ordering
    # ------------------------------------------------------------------
    sort_order = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Display sequence on the printed CoA (lower number = higher position)",
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
    coa = relationship("CertificateOfAnalysis", back_populates="test_lines")

    # ------------------------------------------------------------------
    # Indexes
    # ------------------------------------------------------------------
    __table_args__ = (
        Index("ix_coa_test_lines_coa_id", "coa_id"),
        Index("ix_coa_test_lines_pass_fail", "coa_id", "pass_fail"),
    )

    def __repr__(self) -> str:
        return (
            f"<CoATestLine id={self.id!r} test={self.test_name!r} "
            f"result={self.result!r} pass_fail={self.pass_fail!r}>"
        )
