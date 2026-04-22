"""
Integration bus models — immutable feeds + operational event logs.

Aligns with handover: IntegrationConnector, IntegrationDataFeed, IntegrationEventLog.
PostgreSQL JSONB is used for connection_config (native indexing/query on Supabase).
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey, Integer, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class IntegrationConnector(Base):
    """Connection config for each external system (DeltaV, SAP, Empower, PI, etc.)."""

    __tablename__ = "integration_connectors"

    organisation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organisations.id"), nullable=False, index=True
    )
    site_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("sites.id"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    system_type: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    connection_config: Mapped[dict] = mapped_column(JSONB, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_ping_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_ping_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_by_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False, index=True
    )

    data_feeds: Mapped[list["IntegrationDataFeed"]] = relationship(
        "IntegrationDataFeed", back_populates="connector"
    )
    event_logs: Mapped[list["IntegrationEventLog"]] = relationship(
        "IntegrationEventLog", back_populates="connector"
    )


class IntegrationDataFeed(Base):
    """Immutable incoming data from an external instrument or system (ALCOA: Contemporaneous)."""

    __tablename__ = "integration_data_feeds"

    connector_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("integration_connectors.id"), nullable=False, index=True
    )
    organisation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organisations.id"), nullable=False, index=True
    )
    feed_type: Mapped[str] = mapped_column(String(100), nullable=False)
    tag_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    raw_value: Mapped[str] = mapped_column(Text, nullable=False)
    unit: Mapped[str | None] = mapped_column(String(50), nullable=True)
    quality_flag: Mapped[str | None] = mapped_column(String(50), nullable=True)
    source_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )
    batch_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    equipment_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)

    connector: Mapped["IntegrationConnector"] = relationship(
        "IntegrationConnector", back_populates="data_feeds"
    )

    __table_args__ = (
        Index("ix_feed_connector_time", "connector_id", "received_at"),
        Index("ix_feed_batch", "batch_id"),
    )


class IntegrationEventLog(Base):
    """Log of every sync / push / pull operation with full status."""

    __tablename__ = "integration_event_logs"

    connector_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("integration_connectors.id"), nullable=False, index=True
    )
    organisation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organisations.id"), nullable=False, index=True
    )
    operation: Mapped[str] = mapped_column(String(100), nullable=False)
    direction: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    records_processed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    connector: Mapped["IntegrationConnector"] = relationship(
        "IntegrationConnector", back_populates="event_logs"
    )

    __table_args__ = (Index("ix_integ_event_connector", "connector_id", "started_at"),)
