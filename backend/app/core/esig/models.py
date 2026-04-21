"""
Electronic Signature models — 21 CFR Part 11 / EU Annex 11 compliant.

Every signature captures:
  - WHO signed (user identity, cannot be shared)
  - WHAT was signed (record type, record id, hash of record content)
  - WHY they signed (meaning — approve, review, execute, etc.)
  - WHEN (UTC timestamp, immutable)
  - Authentication method used (password re-entry required per Part 11)

Signatures are APPEND-ONLY. They can never be deleted or modified.
"""
from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.core.database import Base


class ElectronicSignature(Base):
    __tablename__ = "electronic_signatures"

    # Who signed
    signed_by_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False, index=True
    )
    signed_by_username: Mapped[str] = mapped_column(String(100), nullable=False)  # Denormalised — never changes
    signed_by_full_name: Mapped[str] = mapped_column(String(255), nullable=False)  # Denormalised

    # What was signed
    record_type: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g. "capa", "batch_record"
    record_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    record_version: Mapped[str] = mapped_column(String(20), nullable=False)
    record_hash: Mapped[str] = mapped_column(String(64), nullable=False)  # SHA-256 of record JSON at time of signing

    # Why (signature meaning)
    meaning: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g. "approved", "reviewed", "executed"
    meaning_display: Mapped[str] = mapped_column(String(255), nullable=False)  # Human-readable

    # When (immutable — set at creation, never updated)
    signed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # How (authentication method — Part 11 requires re-authentication)
    auth_method: Mapped[str] = mapped_column(String(50), nullable=False, default="password")
    auth_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Cryptographic proof
    signature_token: Mapped[str] = mapped_column(Text, nullable=False)  # JWT signed with platform RSA private key
    ip_address: Mapped[str] = mapped_column(String(45), nullable=True)

    # Notes
    comments: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship(  # noqa: F821
        "User", back_populates="electronic_signatures", foreign_keys=[signed_by_id]
    )

    def __repr__(self) -> str:
        return f"<ESig {self.meaning} on {self.record_type}/{self.record_id} by {self.signed_by_username}>"


class SignatureRequirement(Base):
    """
    Defines what signatures are required for a given record type and state transition.
    e.g. CAPA 'draft' -> 'approved' requires roles: ['qa_manager', 'department_head']
    """
    __tablename__ = "signature_requirements"

    record_type: Mapped[str] = mapped_column(String(100), nullable=False)
    from_state: Mapped[str] = mapped_column(String(100), nullable=False)
    to_state: Mapped[str] = mapped_column(String(100), nullable=False)
    meaning: Mapped[str] = mapped_column(String(100), nullable=False)
    required_role: Mapped[str] = mapped_column(String(100), nullable=False)
    min_signatories: Mapped[int] = mapped_column(nullable=False, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
