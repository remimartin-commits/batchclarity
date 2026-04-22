"""
Environmental Monitoring Module.
Covers: sampling plans, results entry, trending, OOT/OOS alerts.
GMP requirement: Clean rooms and controlled environments must be monitored
for microbial and particulate contamination.
"""
from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey, Integer, Float, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.core.database import Base


class MonitoringLocation(Base):
    """A defined sampling point within a facility (e.g. Grade A filling zone)."""
    __tablename__ = "monitoring_locations"

    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    room: Mapped[str] = mapped_column(String(100), nullable=False)
    gmp_grade: Mapped[str] = mapped_column(String(10), nullable=False)  # A | B | C | D
    site_id: Mapped[str] = mapped_column(String(36), ForeignKey("sites.id"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    sampling_plans: Mapped[list["SamplingPlan"]] = relationship("SamplingPlan", back_populates="location")
    results: Mapped[list["MonitoringResult"]] = relationship("MonitoringResult", back_populates="location")


class AlertLimit(Base):
    """Alert (AL) and Action (ACL) limits per location and parameter."""
    __tablename__ = "alert_limits"

    location_id: Mapped[str] = mapped_column(String(36), ForeignKey("monitoring_locations.id"), nullable=False)
    parameter: Mapped[str] = mapped_column(String(100), nullable=False)
    # Parameters: total_viable_count | yeast_mould | gram_negative | particles_0_5um | particles_5um

    unit: Mapped[str] = mapped_column(String(50), nullable=False)  # cfu/m3 | cfu/plate | particles/m3
    alert_limit: Mapped[float | None] = mapped_column(Float, nullable=True)
    action_limit: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    effective_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    document_reference: Mapped[str | None] = mapped_column(String(200), nullable=True)


class SamplingPlan(Base):
    """Scheduled sampling events for a monitoring location."""
    __tablename__ = "sampling_plans"

    location_id: Mapped[str] = mapped_column(String(36), ForeignKey("monitoring_locations.id"), nullable=False)
    parameter: Mapped[str] = mapped_column(String(100), nullable=False)
    frequency: Mapped[str] = mapped_column(String(50), nullable=False)  # daily | weekly | monthly | per_batch
    sampling_method: Mapped[str] = mapped_column(String(100), nullable=False)  # active_air | settle_plate | contact_plate | surface_swab | particle_counter
    sample_volume_or_time: Mapped[str | None] = mapped_column(String(50), nullable=True)
    assigned_to_role: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    location: Mapped["MonitoringLocation"] = relationship("MonitoringLocation", back_populates="sampling_plans")


class MonitoringResult(Base):
    """
    A single environmental monitoring result.
    Results are entered at time of sampling or reading — ALCOA Contemporaneous.
    OOT/OOS status is calculated server-side against the limit table.
    """
    __tablename__ = "monitoring_results"

    result_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    location_id: Mapped[str] = mapped_column(String(36), ForeignKey("monitoring_locations.id"), nullable=False)
    parameter: Mapped[str] = mapped_column(String(100), nullable=False)
    sampling_method: Mapped[str] = mapped_column(String(100), nullable=False)

    # Sampling event
    sampled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    sampled_by_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    batch_reference: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Result
    result_value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(50), nullable=False)
    result_entered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    result_entered_by_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)

    # OOT / OOS classification (server-set)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="within_limits")
    # Statuses: within_limits | alert | action | oot | oos
    alert_limit_at_time: Mapped[float | None] = mapped_column(Float, nullable=True)
    action_limit_at_time: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Investigation
    investigation_required: Mapped[bool] = mapped_column(Boolean, default=False)
    linked_deviation_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    comments: Mapped[str | None] = mapped_column(Text, nullable=True)

    location: Mapped["MonitoringLocation"] = relationship("MonitoringLocation", back_populates="results")


class MonitoringTrend(Base):
    """
    Periodic trend analysis records — monthly/quarterly summaries.
    Linked to any CAPA raised as a result of adverse trends.
    """
    __tablename__ = "monitoring_trends"

    location_id: Mapped[str] = mapped_column(String(36), ForeignKey("monitoring_locations.id"), nullable=False)
    parameter: Mapped[str] = mapped_column(String(100), nullable=False)
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    sample_count: Mapped[int] = mapped_column(Integer, nullable=False)
    alert_exceedances: Mapped[int] = mapped_column(Integer, default=0)
    action_exceedances: Mapped[int] = mapped_column(Integer, default=0)
    mean_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    trend_conclusion: Mapped[str | None] = mapped_column(Text, nullable=True)
    linked_capa_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    reviewed_by_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
