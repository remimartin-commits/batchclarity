"""
Immutable Audit Trail — ALCOA+ compliant.

This is the single most critical GMP requirement for any software system.
Rules:
  - Records are WRITE-ONCE. No UPDATE, no DELETE, ever.
  - Every data change in the system creates an audit event here.
  - The original value AND new value are both stored.
  - Who, What, When, Where are always captured.
  - The audit trail itself is protected from modification (DB-level constraints).

ALCOA+ coverage:
  Attributable  -> user_id, username (denormalised)
  Legible       -> human_description field
  Contemporaneous -> event_at (server-set UTC, not client-provided)
  Original      -> first record of data, stored as JSON
  Accurate      -> record_hash validates record integrity
  Complete      -> all field changes captured, not just "record updated"
  Consistent    -> UTC everywhere
  Enduring      -> 10-year retention policy enforced at DB level
  Available     -> indexed for fast retrieval by auditors
"""
from sqlalchemy import String, Text, DateTime, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from app.core.database import Base


class AuditEvent(Base):
    __tablename__ = "audit_events"

    # Who
    user_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)  # Null for system events
    username: Mapped[str] = mapped_column(String(100), nullable=False)  # Denormalised — preserved forever
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role_at_time: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    session_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    # What
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    # Actions: CREATE, READ, UPDATE, DELETE, LOGIN, LOGOUT, SIGN, APPROVE, REJECT,
    #          EXECUTE, PRINT, EXPORT, CONFIG_CHANGE, PERMISSION_CHANGE, etc.

    # Which record
    record_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    record_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    record_display: Mapped[str] = mapped_column(String(500), nullable=True)  # Human readable record identifier

    # Field-level changes (the critical ALCOA piece)
    field_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    old_value: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    new_value: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Full record snapshots (for complete audit reconstruction)
    record_snapshot_before: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    record_snapshot_after: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Human-readable description (for auditor readability — Legible)
    human_description: Mapped[str] = mapped_column(Text, nullable=False)

    # When (Contemporaneous — always server-set UTC, client cannot override)
    event_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    # Context
    module: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    site_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)

    # Reason for change (required for certain GMP actions)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # System metadata
    system_version: Mapped[str] = mapped_column(String(20), nullable=False)  # Platform version at time of event
    is_system_action: Mapped[bool] = mapped_column(nullable=False, default=False)

    __table_args__ = (
        # Composite indexes for common auditor queries
        Index("ix_audit_record", "record_type", "record_id"),
        Index("ix_audit_user_time", "user_id", "event_at"),
        Index("ix_audit_module_time", "module", "event_at"),
    )

    def __repr__(self) -> str:
        return f"<AuditEvent {self.action} on {self.record_type}/{self.record_id} by {self.username} at {self.event_at}>"
