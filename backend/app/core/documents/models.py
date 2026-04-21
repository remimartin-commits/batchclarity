"""
Document Control — version-controlled, approval-gated GMP documents.

Covers: SOPs, Work Instructions, Forms, Specifications, Protocols, Policies.

Rules:
  - Every document has a major version (1.0, 2.0) and revision history
  - Only one version is 'effective' at a time
  - Superseded versions are archived, never deleted
  - Document changes require electronic signature approval
  - Effective date is set by QA approval, not by the author
  - Documents link to training (new version triggers retraining)
"""
from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.core.database import Base


class DocumentType(Base):
    __tablename__ = "document_types"

    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    prefix: Mapped[str] = mapped_column(String(10), nullable=False)  # e.g. SOP, WI, FORM, SPEC
    requires_periodic_review: Mapped[bool] = mapped_column(Boolean, default=True)
    review_period_months: Mapped[int] = mapped_column(Integer, default=24)
    requires_training: Mapped[bool] = mapped_column(Boolean, default=True)


class Document(Base):
    """The document master — one row per document number."""
    __tablename__ = "documents"

    document_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    document_type_id: Mapped[str] = mapped_column(String(36), ForeignKey("document_types.id"), nullable=False)
    department: Mapped[str] = mapped_column(String(100), nullable=True)
    site_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("sites.id"), nullable=True)
    owner_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    is_obsolete: Mapped[bool] = mapped_column(Boolean, default=False)
    current_version_id: Mapped[str | None] = mapped_column(String(36), nullable=True)  # FK set after insert

    document_type: Mapped["DocumentType"] = relationship("DocumentType")
    versions: Mapped[list["DocumentVersion"]] = relationship("DocumentVersion", back_populates="document")


class DocumentVersion(Base):
    """One row per version of a document. Version history is never deleted."""
    __tablename__ = "document_versions"

    document_id: Mapped[str] = mapped_column(String(36), ForeignKey("documents.id"), nullable=False, index=True)
    version_number: Mapped[str] = mapped_column(String(20), nullable=False)  # e.g. "1.0", "2.0", "2.1"
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="draft")
    # Statuses: draft | under_review | approved | effective | superseded | obsolete

    # Content
    content: Mapped[str] = mapped_column(Text, nullable=True)  # Rich text / markdown
    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)  # Stored file (PDF, DOCX)
    file_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)  # SHA-256 for integrity

    # Authorship
    authored_by_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    reviewed_by_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    approved_by_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)

    # Dates
    authored_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewed_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    effective_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    superseded_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_review_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Change details
    change_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    change_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    supersedes_version_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("document_versions.id"), nullable=True
    )

    document: Mapped["Document"] = relationship("Document", back_populates="versions")
