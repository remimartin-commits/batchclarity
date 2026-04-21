"""
Equipment Management Module.
Covers: Equipment master data, calibration, IQ/OQ/PQ qualification, preventive maintenance.
"""
from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey, Integer, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.core.database import Base


class Equipment(Base):
    __tablename__ = "equipment"

    equipment_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    equipment_type: Mapped[str] = mapped_column(String(100), nullable=False)
    manufacturer: Mapped[str | None] = mapped_column(String(200), nullable=True)
    model: Mapped[str | None] = mapped_column(String(200), nullable=True)
    serial_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    location: Mapped[str | None] = mapped_column(String(200), nullable=True)
    site_id: Mapped[str] = mapped_column(String(36), ForeignKey("sites.id"), nullable=False)

    status: Mapped[str] = mapped_column(String(50), nullable=False, default="qualified")
    # Statuses: pre_qualification | qualified | out_of_service | retired | under_maintenance

    # Qualification status
    qualification_status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    # pending | iq_complete | oq_complete | pq_complete | qualified | requalification_due

    installation_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    commissioned_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    owner_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    is_gmp_critical: Mapped[bool] = mapped_column(Boolean, default=True)
    is_computerised_system: Mapped[bool] = mapped_column(Boolean, default=False)

    calibration_records: Mapped[list["CalibrationRecord"]] = relationship(
        "CalibrationRecord", back_populates="equipment"
    )
    qualification_records: Mapped[list["QualificationRecord"]] = relationship(
        "QualificationRecord", back_populates="equipment"
    )
    maintenance_records: Mapped[list["MaintenanceRecord"]] = relationship(
        "MaintenanceRecord", back_populates="equipment"
    )


class CalibrationRecord(Base):
    __tablename__ = "calibration_records"

    equipment_id: Mapped[str] = mapped_column(String(36), ForeignKey("equipment.id"), nullable=False, index=True)
    calibration_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    calibration_type: Mapped[str] = mapped_column(String(50), nullable=False)  # scheduled | unscheduled | post_repair
    performed_by_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    performed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    next_calibration_due: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    calibration_interval_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    result: Mapped[str] = mapped_column(String(50), nullable=False)  # pass | fail | conditional_pass
    certificate_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    certificate_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    as_found_condition: Mapped[str | None] = mapped_column(Text, nullable=True)
    as_left_condition: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_overdue: Mapped[bool] = mapped_column(Boolean, default=False)

    equipment: Mapped["Equipment"] = relationship("Equipment", back_populates="calibration_records")


class QualificationRecord(Base):
    __tablename__ = "qualification_records"

    equipment_id: Mapped[str] = mapped_column(String(36), ForeignKey("equipment.id"), nullable=False, index=True)
    qualification_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    qualification_type: Mapped[str] = mapped_column(String(10), nullable=False)  # IQ | OQ | PQ | DQ | PV
    protocol_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    report_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    performed_by_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    reviewed_by_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    approved_by_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    execution_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    execution_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    result: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    requalification_due: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deviations_count: Mapped[int] = mapped_column(Integer, default=0)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    equipment: Mapped["Equipment"] = relationship("Equipment", back_populates="qualification_records")


class MaintenanceRecord(Base):
    __tablename__ = "maintenance_records"

    equipment_id: Mapped[str] = mapped_column(String(36), ForeignKey("equipment.id"), nullable=False, index=True)
    maintenance_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    maintenance_type: Mapped[str] = mapped_column(String(50), nullable=False)  # preventive | corrective | emergency
    description: Mapped[str] = mapped_column(Text, nullable=False)
    performed_by_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    performed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    next_maintenance_due: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    equipment_downtime_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    parts_replaced: Mapped[str | None] = mapped_column(Text, nullable=True)
    requalification_required: Mapped[bool] = mapped_column(Boolean, default=False)
    result: Mapped[str] = mapped_column(String(50), nullable=False, default="completed")

    equipment: Mapped["Equipment"] = relationship("Equipment", back_populates="maintenance_records")
