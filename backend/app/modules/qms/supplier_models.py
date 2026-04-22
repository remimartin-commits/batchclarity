"""
QMS Supplier Quality Management Models
=======================================
ALCOA+ compliant SQLAlchemy models for supplier qualification,
audit management, and certificate tracking.

Tables
------
- suppliers                : Approved supplier master records
- supplier_audits          : Audit event records (initial, surveillance, for-cause, remote)
- supplier_certificates    : Quality certificates with expiry tracking
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


class SupplierType(str, enum.Enum):
    RAW_MATERIAL = "raw_material"
    SERVICE = "service"
    EQUIPMENT = "equipment"
    CONTRACT_MANUFACTURER = "contract_manufacturer"
    PACKAGING = "packaging"
    LABORATORY = "laboratory"


class SupplierStatus(str, enum.Enum):
    APPROVED = "approved"
    CONDITIONAL = "conditional"
    SUSPENDED = "suspended"
    DISQUALIFIED = "disqualified"
    PENDING_APPROVAL = "pending_approval"


class RiskLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AuditType(str, enum.Enum):
    INITIAL = "initial"
    SURVEILLANCE = "surveillance"
    FOR_CAUSE = "for_cause"
    REMOTE = "remote"
    DESKTOP = "desktop"


class AuditStatus(str, enum.Enum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class AuditOutcome(str, enum.Enum):
    SATISFACTORY = "satisfactory"
    MINOR_FINDINGS = "minor_findings"
    MAJOR_FINDINGS = "major_findings"
    CRITICAL_FINDINGS = "critical_findings"


class CertificateStatus(str, enum.Enum):
    VALID = "valid"
    EXPIRED = "expired"
    REVOKED = "revoked"
    PENDING = "pending"


# ---------------------------------------------------------------------------
# Supplier
# ---------------------------------------------------------------------------


class Supplier(Base):
    """
    Master record for an approved (or in-qualification) supplier.

    The ``code`` field is unique within an organisation and acts as the
    human-readable identifier used on purchase orders and material labels.
    """

    __tablename__ = "suppliers"

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
    # Identification
    # ------------------------------------------------------------------
    name = Column(
        String(255),
        nullable=False,
        comment="Full legal / trading name of the supplier",
    )
    code = Column(
        String(50),
        nullable=False,
        comment="Short alphanumeric code; unique per organisation",
    )
    supplier_type = Column(
        Enum(SupplierType, name="supplier_type_enum"),
        nullable=False,
        comment="Category of goods or services supplied",
    )

    # ------------------------------------------------------------------
    # Qualification status
    # ------------------------------------------------------------------
    status = Column(
        Enum(SupplierStatus, name="supplier_status_enum"),
        nullable=False,
        default=SupplierStatus.PENDING_APPROVAL,
        comment="Qualification / approval status",
    )
    risk_level = Column(
        Enum(RiskLevel, name="supplier_risk_level_enum"),
        nullable=False,
        default=RiskLevel.MEDIUM,
        comment="Assessed supply-chain risk level",
    )

    # ------------------------------------------------------------------
    # Contact & address
    # ------------------------------------------------------------------
    address = Column(
        Text,
        nullable=True,
        comment="Full postal address of the supplier's primary site",
    )
    country = Column(
        String(100),
        nullable=True,
        comment="ISO country name or code",
    )
    primary_contact_name = Column(
        String(200),
        nullable=True,
        comment="Full name of the primary quality contact",
    )
    primary_contact_email = Column(
        String(254),
        nullable=True,
        comment="Email address of the primary quality contact",
    )

    # ------------------------------------------------------------------
    # Approval tracking
    # ------------------------------------------------------------------
    approved_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="UTC timestamp when supplier was first approved",
    )
    approved_by_id = Column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
        comment="User who granted initial approval",
    )
    next_audit_date = Column(
        Date,
        nullable=True,
        comment="Scheduled date of the next planned audit",
    )

    # ------------------------------------------------------------------
    # Organisational context
    # ------------------------------------------------------------------
    organisation_id = Column(
        UUID(as_uuid=False),
        nullable=False,
        comment="Owning organisation UUID",
    )

    # ------------------------------------------------------------------
    # Flexible metadata store
    # ------------------------------------------------------------------
    metadata_ = Column(
        "metadata",
        JSONB,
        nullable=True,
        default=dict,
        comment="Arbitrary key-value metadata (certifications held, GLN, etc.)",
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
    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        comment="Soft-delete flag",
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------
    audits = relationship(
        "SupplierAudit",
        back_populates="supplier",
cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="SupplierAudit.audit_date.desc()",
    )
    certificates = relationship(
        "SupplierCertificate",
        back_populates="supplier",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="SupplierCertificate.expiry_date",
    )

    # ------------------------------------------------------------------
    # Constraints & indexes
    # ------------------------------------------------------------------
    __table_args__ = (
        UniqueConstraint("organisation_id", "code", name="uq_suppliers_org_code"),
        Index("ix_suppliers_org_status", "organisation_id", "status"),
        Index("ix_suppliers_next_audit", "next_audit_date"),
    )

    def __repr__(self) -> str:
        return (
            f"<Supplier id={self.id!r} code={self.code!r} "
            f"name={self.name!r} status={self.status!r}>"
        )


# ---------------------------------------------------------------------------
# SupplierAudit
# ---------------------------------------------------------------------------


class SupplierAudit(Base):
    """
    Individual audit event conducted against a supplier.

    Covers initial qualification audits, periodic surveillance audits,
    for-cause audits triggered by quality failures, and remote/desktop audits.
    The ``report_storage_path`` field points to the document management system
    path (or cloud storage key) where the full audit report is stored.
    """

    __tablename__ = "supplier_audits"

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
    # Foreign keys
    # ------------------------------------------------------------------
    supplier_id = Column(
        UUID(as_uuid=False),
        ForeignKey("suppliers.id", ondelete="CASCADE"),
        nullable=False,
        comment="Supplier being audited",
    )
    organisation_id = Column(
        UUID(as_uuid=False),
        nullable=False,
        comment="Organisation conducting the audit",
    )

    # ------------------------------------------------------------------
    # Audit details
    # ------------------------------------------------------------------
    audit_type = Column(
        Enum(AuditType, name="audit_type_enum"),
        nullable=False,
        comment="Classification of the audit event",
    )
    audit_date = Column(
        Date,
        nullable=False,
        comment="Date on which the audit was / is scheduled to occur",
    )
    lead_auditor_id = Column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        comment="Lead auditor responsible for the audit",
    )
    status = Column(
        Enum(AuditStatus, name="audit_status_enum"),
        nullable=False,
        default=AuditStatus.PLANNED,
        comment="Current status of the audit",
    )
    outcome = Column(
        Enum(AuditOutcome, name="audit_outcome_enum"),
        nullable=True,
        comment="Outcome classification (populated on completion)",
    )

    # ------------------------------------------------------------------
    # Report & follow-up
    # ------------------------------------------------------------------
    report_storage_path = Column(
        String(1024),
        nullable=True,
        comment="Storage path or object key for the audit report document",
    )
    capa_required = Column(
        Boolean,
        nullable=False,
        default=False,
        comment="True if a CAPA must be raised as a result of this audit",
    )
    findings_summary = Column(
        Text,
        nullable=True,
        comment="Narrative summary of audit findings",
    )

    # ------------------------------------------------------------------
    # Personnel
    # ------------------------------------------------------------------
    created_by_id = Column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        comment="User who created this audit record",
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
    supplier = relationship("Supplier", back_populates="audits")

    # ------------------------------------------------------------------
    # Indexes
    # ------------------------------------------------------------------
    __table_args__ = (
        Index("ix_supplier_audits_supplier_date", "supplier_id", "audit_date"),
        Index("ix_supplier_audits_org_status", "organisation_id", "status"),
    )

    def __repr__(self) -> str:
        return (
            f"<SupplierAudit id={self.id!r} supplier_id={self.supplier_id!r} "
            f"date={self.audit_date!r} outcome={self.outcome!r}>"
        )


# ---------------------------------------------------------------------------
# SupplierCertificate
# ---------------------------------------------------------------------------


class SupplierCertificate(Base):
    """
    Quality or compliance certificate held by a supplier.

    Certificates are tracked with expiry dates so the platform can trigger
    renewal reminders and automatically flag expired certificates.

    Examples of certificate_type values:
      - "ISO 9001:2015"
      - "ISO 13485:2016"
      - "GMP Certificate"
      - "EU Qualified Person Declaration"
      - "FSSC 22000"
    """

    __tablename__ = "supplier_certificates"

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
    supplier_id = Column(
        UUID(as_uuid=False),
        ForeignKey("suppliers.id", ondelete="CASCADE"),
        nullable=False,
        comment="Supplier to which this certificate belongs",
    )

    # ------------------------------------------------------------------
    # Certificate details
    # ------------------------------------------------------------------
    certificate_type = Column(
        String(150),
        nullable=False,
        comment="Standard or scheme name (e.g. 'ISO 9001:2015', 'GMP Certificate')",
    )
    certificate_number = Column(
        String(100),
        nullable=True,
        comment="Certificate reference number issued by the certification body",
    )
    issued_by = Column(
        String(255),
        nullable=False,
        comment="Name of the certification or regulatory body",
    )
    issued_date = Column(
        Date,
        nullable=False,
        comment="Date the certificate was issued",
    )
    expiry_date = Column(
        Date,
        nullable=False,
        comment="Date on which the certificate expires",
    )
    storage_path = Column(
        String(1024),
        nullable=True,
        comment="Document management path or object key for the certificate file",
    )
    status = Column(
        Enum(CertificateStatus, name="certificate_status_enum"),
        nullable=False,
        default=CertificateStatus.VALID,
        comment="Currency status of the certificate",
    )

    # ------------------------------------------------------------------
    # Scope / notes
    # ------------------------------------------------------------------
    scope = Column(
        Text,
        nullable=True,
        comment="Scope statement as printed on the certificate",
    )

    # ------------------------------------------------------------------
    # Personnel
    # ------------------------------------------------------------------
    created_by_id = Column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        comment="User who uploaded / registered this certificate",
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
    supplier = relationship("Supplier", back_populates="certificates")

    # ------------------------------------------------------------------
    # Constraints & indexes
    # ------------------------------------------------------------------
    __table_args__ = (
        CheckConstraint(
            "expiry_date >= issued_date",
            name="ck_supplier_certificates_date_order",
        ),
        Index("ix_supplier_certificates_expiry", "expiry_date", "status"),
        Index("ix_supplier_certificates_supplier", "supplier_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<SupplierCertificate id={self.id!r} type={self.certificate_type!r} "
            f"expiry={self.expiry_date!r} status={self.status!r}>"
        )
