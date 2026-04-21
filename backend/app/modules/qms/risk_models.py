"""
QMS Risk Management Models
==========================
ALCOA+ compliant SQLAlchemy models for risk assessment workflows.

Supports FMEA, ICH Q9 and other GMP risk methodologies.

Tables
------
- risk_assessments      : Header record per risk exercise
- risk_items            : Individual hazard/risk entries with RPN scoring
- risk_reviews          : Periodic review audit trail
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


class RiskMethodology(str, enum.Enum):
    FMEA = "FMEA"
    FMECA = "FMECA"
    ICH_Q9 = "ICH_Q9"
    HAZOP = "HAZOP"
    PHA = "PHA"
    OTHER = "OTHER"


class RiskAssessmentStatus(str, enum.Enum):
    DRAFT = "draft"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    OBSOLETE = "obsolete"


class RiskLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskItemStatus(str, enum.Enum):
    OPEN = "open"
    MITIGATED = "mitigated"
    ACCEPTED = "accepted"
    CLOSED = "closed"


class RiskReviewOutcome(str, enum.Enum):
    NO_CHANGE = "no_change"
    UPDATED = "updated"
    ESCALATED = "escalated"
    CLOSED = "closed"


# ---------------------------------------------------------------------------
# RiskAssessment
# ---------------------------------------------------------------------------


class RiskAssessment(Base):
    """
    Header record for a single risk assessment exercise.

    A RiskAssessment groups one or more RiskItems and tracks the overall
    lifecycle (draft → approved) of the risk evaluation.  It can be linked
    to any resource in the platform (deviation, change control, equipment,
    etc.) via the generic linked_resource_type / linked_resource_id pair.
    """

    __tablename__ = "risk_assessments"

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
    # Core fields
    # ------------------------------------------------------------------
    title = Column(
        String(255),
        nullable=False,
        comment="Short descriptive title of the risk assessment",
    )
    scope = Column(
        Text,
        nullable=True,
        comment="Scope and objectives of the assessment",
    )
    methodology = Column(
        Enum(RiskMethodology, name="risk_methodology_enum"),
        nullable=False,
        default=RiskMethodology.FMEA,
        comment="Risk methodology applied (FMEA, ICH Q9, HAZOP …)",
    )
    status = Column(
        Enum(RiskAssessmentStatus, name="risk_assessment_status_enum"),
        nullable=False,
        default=RiskAssessmentStatus.DRAFT,
        comment="Lifecycle status of the assessment",
    )

    # ------------------------------------------------------------------
    # Generic polymorphic link to any platform resource
    # ------------------------------------------------------------------
    linked_resource_type = Column(
        String(100),
        nullable=True,
        comment="Type of linked resource (e.g. 'deviation', 'change_control', 'equipment')",
    )
    linked_resource_id = Column(
        UUID(as_uuid=False),
        nullable=True,
        comment="UUID of the linked resource",
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
        comment="Site UUID (optional for org-wide assessments)",
    )

    # ------------------------------------------------------------------
    # Personnel
    # ------------------------------------------------------------------
    created_by_id = Column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        comment="User who created this assessment",
    )
    approved_by_id = Column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
        comment="User who approved this assessment",
    )
    approved_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="UTC timestamp of approval (populated on approval)",
    )

    # ------------------------------------------------------------------
    # Additional metadata (flexible JSONB store)
    # ------------------------------------------------------------------
    metadata_ = Column(
        "metadata",
        JSONB,
        nullable=True,
        default=dict,
        comment="Arbitrary key-value metadata (team members, revision history, etc.)",
    )

    # ------------------------------------------------------------------
    # ALCOA+ audit timestamps
    # ------------------------------------------------------------------
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        comment="Record creation timestamp (UTC)",
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        onupdate=utcnow,
        comment="Last modification timestamp (UTC)",
    )
    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        comment="Soft-delete flag; False = logically deleted",
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------
    items = relationship(
        "RiskItem",
        back_populates="assessment",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="RiskItem.created_at",
    )
    reviews = relationship(
        "RiskReview",
        back_populates="assessment",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="RiskReview.review_date",
    )

    # ------------------------------------------------------------------
    # Constraints & indexes
    # ------------------------------------------------------------------
    __table_args__ = (
        Index("ix_risk_assessments_org_status", "organisation_id", "status"),
        Index(
            "ix_risk_assessments_linked_resource",
            "linked_resource_type",
            "linked_resource_id",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<RiskAssessment id={self.id!r} title={self.title!r} "
            f"status={self.status!r}>"
        )


# ---------------------------------------------------------------------------
# RiskItem
# ---------------------------------------------------------------------------


class RiskItem(Base):
    """
    Individual hazard / risk entry within a RiskAssessment.

    Stores the full FMEA-style scoring:
      - Initial: probability × severity × detectability → RPN
      - Residual: scores after mitigation controls are applied

    The rpn and residual_rpn columns are *computed on write* by the
    application layer (or via a DB trigger) rather than being true
    generated columns, to remain compatible with all PostgreSQL versions.
    """

    __tablename__ = "risk_items"

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
    risk_assessment_id = Column(
        UUID(as_uuid=False),
        ForeignKey("risk_assessments.id", ondelete="CASCADE"),
        nullable=False,
        comment="Parent risk assessment",
    )

    # ------------------------------------------------------------------
    # Hazard description fields
    # ------------------------------------------------------------------
    hazard = Column(
        String(500),
        nullable=False,
        comment="Source of potential harm (the hazard)",
    )
    harm = Column(
        String(500),
        nullable=False,
        comment="Potential adverse outcome / harm",
    )
    hazardous_situation = Column(
        Text,
        nullable=True,
        comment="Circumstances in which exposure to the hazard leads to harm",
    )

    # ------------------------------------------------------------------
    # Initial risk scoring (1-5 scale)
    # ------------------------------------------------------------------
    probability_score = Column(
        Integer,
        nullable=False,
        comment="Likelihood of occurrence (1 = very unlikely … 5 = almost certain)",
    )
    severity_score = Column(
        Integer,
        nullable=False,
        comment="Severity of harm (1 = negligible … 5 = catastrophic)",
    )
    detectability_score = Column(
        Integer,
        nullable=False,
        comment="Ability to detect failure before harm (1 = easily detected … 5 = undetectable)",
    )
    rpn = Column(
        Integer,
        nullable=False,
        comment="Risk Priority Number = probability × severity × detectability (max 125)",
    )
    initial_risk_level = Column(
        Enum(RiskLevel, name="risk_level_enum"),
        nullable=False,
        comment="Categorical risk level derived from initial RPN",
    )

    # ------------------------------------------------------------------
    # Mitigation
    # ------------------------------------------------------------------
    mitigation_description = Column(
        Text,
        nullable=True,
        comment="Description of control measures / mitigations applied",
    )

    # ------------------------------------------------------------------
    # Residual risk scoring (post-mitigation)
    # ------------------------------------------------------------------
    residual_probability = Column(
        Integer,
        nullable=True,
        comment="Post-mitigation probability score (1-5)",
    )
    residual_severity = Column(
        Integer,
        nullable=True,
        comment="Post-mitigation severity score (1-5)",
    )
    residual_detectability = Column(
        Integer,
        nullable=True,
        comment="Post-mitigation detectability score (1-5)",
    )
    residual_rpn = Column(
        Integer,
        nullable=True,
        comment="Post-mitigation RPN",
    )
    residual_risk_level = Column(
        Enum(RiskLevel, name="risk_level_enum"),
        nullable=True,
        comment="Categorical risk level after mitigation",
    )

    # ------------------------------------------------------------------
    # Action tracking
    # ------------------------------------------------------------------
    responsible_user_id = Column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="User responsible for implementing mitigations",
    )
    due_date = Column(
        Date,
        nullable=True,
        comment="Target completion date for mitigation actions",
    )
    status = Column(
        Enum(RiskItemStatus, name="risk_item_status_enum"),
        nullable=False,
        default=RiskItemStatus.OPEN,
        comment="Current status of this risk item",
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
    assessment = relationship("RiskAssessment", back_populates="items")

    # ------------------------------------------------------------------
    # Constraints & indexes
    # ------------------------------------------------------------------
    __table_args__ = (
        CheckConstraint(
            "probability_score BETWEEN 1 AND 5",
            name="ck_risk_items_probability_range",
        ),
        CheckConstraint(
            "severity_score BETWEEN 1 AND 5",
            name="ck_risk_items_severity_range",
        ),
        CheckConstraint(
            "detectability_score BETWEEN 1 AND 5",
            name="ck_risk_items_detectability_range",
        ),
        CheckConstraint(
            "rpn = probability_score * severity_score * detectability_score",
            name="ck_risk_items_rpn_computed",
        ),
        Index("ix_risk_items_assessment_status", "risk_assessment_id", "status"),
    )

    def __repr__(self) -> str:
        return (
f"<RiskItem id={self.id!r} hazard={self.hazard!r} "
            f"rpn={self.rpn!r} status={self.status!r}>"
        )


# ---------------------------------------------------------------------------
# RiskReview
# ---------------------------------------------------------------------------


class RiskReview(Base):
    """
    Periodic review record for a RiskAssessment.

    GMP regulations (e.g. ICH Q9, EU GMP Annex 20) require that risk
    assessments are periodically reviewed and the review outcome documented.
    Each row represents one completed review cycle.
    """

    __tablename__ = "risk_reviews"

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
    risk_assessment_id = Column(
        UUID(as_uuid=False),
        ForeignKey("risk_assessments.id", ondelete="CASCADE"),
        nullable=False,
        comment="Parent risk assessment being reviewed",
    )

    # ------------------------------------------------------------------
    # Review details
    # ------------------------------------------------------------------
    review_date = Column(
        Date,
        nullable=False,
        comment="Date on which the review was conducted",
    )
    reviewed_by_id = Column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        comment="User who conducted the review",
    )
    outcome = Column(
        Enum(RiskReviewOutcome, name="risk_review_outcome_enum"),
        nullable=False,
        comment="Summary outcome of the review",
    )
    comments = Column(
        Text,
        nullable=True,
        comment="Narrative comments and findings from the review",
    )
    next_review_date = Column(
        Date,
        nullable=True,
        comment="Scheduled date for the next periodic review",
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
    assessment = relationship("RiskAssessment", back_populates="reviews")

    # ------------------------------------------------------------------
    # Indexes
    # ------------------------------------------------------------------
    __table_args__ = (
        Index(
            "ix_risk_reviews_assessment_date",
            "risk_assessment_id",
            "review_date",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<RiskReview id={self.id!r} assessment_id={self.risk_assessment_id!r} "
            f"date={self.review_date!r} outcome={self.outcome!r}>"
        )
