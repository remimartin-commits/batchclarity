"""
Equipment module — business logic (calibration, qualification, listings).

Routers should delegate here; all writes log AuditEvent in the same transaction.
performed_at for calibrations is server-set (ALCOA Contemporaneous) — do not trust client timestamps.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit.service import AuditService
from app.core.auth.models import User
from app.core.esig.service import ESignatureService
from app.modules.equipment.models import (
    Equipment,
    CalibrationRecord,
    MaintenanceRecord,
    QualificationRecord,
)
from app.modules.equipment.schemas import (
    CalibrationCreate,
    EquipmentCreate,
    EquipmentStatusUpdate,
    MaintenanceCreate,
    QualificationCreate,
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _clamp_page_size(page_size: int) -> int:
    return max(1, min(100, page_size))


def _offset(page: int, page_size: int) -> int:
    p = max(1, page)
    return (p - 1) * _clamp_page_size(page_size)


def _require_user_site_id(user: User) -> str:
    if not user.site_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not associated with a site_id.",
        )
    return str(user.site_id)


# ── Equipment master ─────────────────────────────────────────────────────────


async def create_equipment(
    db: AsyncSession,
    data: EquipmentCreate,
    user: User,
    ip_address: Optional[str],
) -> Equipment:
    existing = await db.execute(
        select(Equipment).where(Equipment.equipment_id == data.equipment_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Equipment ID '{data.equipment_id}' already exists.",
        )

    eq = Equipment(
        **data.model_dump(),
        owner_id=str(user.id),
    )
    db.add(eq)
    await db.flush([eq])

    await AuditService.log(
        db,
        action="CREATE",
        record_type="equipment",
        record_id=eq.id,
        module="equipment",
        human_description=f"Equipment {data.equipment_id} '{data.name}' registered",
        user_id=str(user.id),
        username=user.username,
        full_name=user.full_name or user.username,
        ip_address=ip_address,
        site_id=data.site_id,
    )
    await db.commit()
    await db.refresh(eq)
    return eq


async def list_equipment(
    db: AsyncSession,
    *,
    site_id: str | None = None,
    status_filter: str | None = None,
    skip: int = 0,
    limit: int = 50,
) -> list[Equipment]:
    query = select(Equipment)
    if site_id:
        query = query.where(Equipment.site_id == site_id)
    if status_filter:
        query = query.where(Equipment.status == status_filter)
    query = query.order_by(Equipment.equipment_id).offset(max(0, skip)).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_equipment_or_404(
    db: AsyncSession, equipment_id: str, site_id: str | None = None
) -> Equipment:
    q = select(Equipment).where(Equipment.id == equipment_id)
    if site_id is not None:
        q = q.where(Equipment.site_id == site_id)
    result = await db.execute(q)
    eq = result.scalar_one_or_none()
    if not eq:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Equipment not found.")
    return eq


# ── Calibration ──────────────────────────────────────────────────────────────


async def record_calibration(
    db: AsyncSession,
    equipment_id: str,
    data: CalibrationCreate,
    user: User,
    ip_address: Optional[str],
) -> CalibrationRecord:
    site_id = _require_user_site_id(user)
    eq = await get_equipment_or_404(db, equipment_id, site_id)

    count_result = await db.execute(select(func.count()).select_from(CalibrationRecord))
    count = (count_result.scalar() or 0) + 1
    cal_number = f"CAL-{_utcnow().year}-{count:04d}"

    performed_at = _utcnow()
    interval_days = data.calibration_interval_days
    next_due: datetime | None = None
    if interval_days is not None and interval_days > 0:
        next_due = performed_at + timedelta(days=interval_days)

    cal = CalibrationRecord(
        equipment_id=eq.id,
        calibration_number=cal_number,
        calibration_type=data.calibration_type,
        performed_by_id=str(user.id),
        performed_at=performed_at,
        next_calibration_due=next_due,
        calibration_interval_days=interval_days,
        result=data.result,
        certificate_number=data.certificate_number,
        as_found_condition=data.as_found_condition,
        as_left_condition=data.as_left_condition,
        notes=data.notes,
        is_overdue=False,
    )
    db.add(cal)
    await db.flush([cal])

    # Clear scheduler overdue flags for this equipment when a new calibration is recorded.
    await db.execute(
        update(CalibrationRecord)
        .where(
            CalibrationRecord.equipment_id == eq.id,
            CalibrationRecord.is_overdue.is_(True),
        )
        .values(is_overdue=False)
    )

    await AuditService.log(
        db,
        action="CALIBRATION_RECORDED",
        record_type="calibration_record",
        record_id=cal.id,
        module="equipment",
        human_description=(
            f"Calibration {cal_number} ({data.result}) recorded for equipment {eq.equipment_id}"
        ),
        user_id=str(user.id),
        username=user.username,
        full_name=user.full_name or user.username,
        ip_address=ip_address,
        site_id=eq.site_id,
        record_snapshot_after={
            "calibration_number": cal_number,
            "performed_at": performed_at.isoformat(),
            "next_calibration_due": next_due.isoformat() if next_due else None,
        },
    )
    await db.commit()
    await db.refresh(cal)
    return cal


async def list_calibration_history(
    db: AsyncSession,
    equipment_id: str,
    site_id: str,
    page: int = 1,
    page_size: int = 20,
) -> list[CalibrationRecord]:
    await get_equipment_or_404(db, equipment_id, site_id)
    ps = _clamp_page_size(page_size)
    off = _offset(page, ps)
    result = await db.execute(
        select(CalibrationRecord)
        .where(CalibrationRecord.equipment_id == equipment_id)
        .order_by(CalibrationRecord.performed_at.desc())
        .offset(off)
        .limit(ps)
    )
    return list(result.scalars().all())


async def list_calibrations_for_user_site(
    db: AsyncSession, equipment_id: str, user: User
) -> list[CalibrationRecord]:
    """List calibration history for equipment, scoped to the user's site (up to 100 rows)."""
    site_id = _require_user_site_id(user)
    return await list_calibration_history(db, equipment_id, site_id, page=1, page_size=100)


# ── Qualification ────────────────────────────────────────────────────────────


async def record_qualification(
    db: AsyncSession,
    equipment_id: str,
    data: QualificationCreate,
    user: User,
    ip_address: Optional[str],
) -> QualificationRecord:
    site_id = _require_user_site_id(user)
    eq = await get_equipment_or_404(db, equipment_id, site_id)

    count_result = await db.execute(select(func.count()).select_from(QualificationRecord))
    count = (count_result.scalar() or 0) + 1
    qual_number = f"{data.qualification_type}-{_utcnow().year}-{count:04d}"

    qual = QualificationRecord(
        equipment_id=eq.id,
        qualification_number=qual_number,
        performed_by_id=str(user.id),
        **data.model_dump(),
    )
    db.add(qual)
    await db.flush([qual])

    await AuditService.log(
        db,
        action="CREATE",
        record_type="qualification_record",
        record_id=qual.id,
        module="equipment",
        human_description=f"{data.qualification_type} qualification {qual_number} recorded for {eq.equipment_id}",
        user_id=str(user.id),
        username=user.username,
        full_name=user.full_name or user.username,
        ip_address=ip_address,
        site_id=eq.site_id,
    )
    await db.commit()
    await db.refresh(qual)
    return qual


ALLOWED_STATUS_TRANSITIONS: dict[str, set[str]] = {
    "pre_qualification": {"qualified", "out_of_service", "retired"},
    "qualified": {"under_maintenance", "out_of_service", "retired"},
    "under_maintenance": {"qualified", "out_of_service", "retired"},
    "out_of_service": {"under_maintenance", "qualified", "retired"},
    "retired": set(),
}


async def update_equipment_status(
    db: AsyncSession,
    equipment_id: str,
    data: EquipmentStatusUpdate,
    user: User,
    ip_address: str | None,
) -> dict:
    eq = await get_equipment_or_404(db, equipment_id, site_id=None)
    old_status = eq.status
    allowed = ALLOWED_STATUS_TRANSITIONS.get(old_status, set())
    if data.status not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status transition: {old_status} -> {data.status}",
        )
    await ESignatureService.sign(
        db,
        user_id=str(user.id),
        password=data.password,
        record_type="equipment",
        record_id=equipment_id,
        record_version="1.0",
        record_data={"equipment_id": eq.equipment_id, "status_before": old_status},
        meaning=data.status,
        meaning_display=f"Equipment status -> {data.status}",
        ip_address=ip_address or "127.0.0.1",
        comments=data.reason,
    )
    eq.status = data.status
    await AuditService.log_field_change(
        db,
        record_type="equipment",
        record_id=equipment_id,
        module="equipment",
        field_name="status",
        old_value=old_status,
        new_value=data.status,
        user_id=str(user.id),
        username=user.username,
        full_name=user.full_name or user.username,
        ip_address=ip_address,
        reason=data.reason,
    )
    await db.commit()
    return {"status": eq.status}


async def list_qualification_history(
    db: AsyncSession, equipment_id: str
) -> list[QualificationRecord]:
    await get_equipment_or_404(db, equipment_id, site_id=None)
    result = await db.execute(
        select(QualificationRecord)
        .where(QualificationRecord.equipment_id == equipment_id)
        .order_by(QualificationRecord.created_at.desc())
    )
    return list(result.scalars().all())


async def record_maintenance(
    db: AsyncSession,
    equipment_id: str,
    data: MaintenanceCreate,
    user: User,
    ip_address: str | None,
) -> MaintenanceRecord:
    eq = await get_equipment_or_404(db, equipment_id, site_id=None)

    count_result = await db.execute(select(func.count()).select_from(MaintenanceRecord))
    count = (count_result.scalar() or 0) + 1
    maint_number = f"MAINT-{_utcnow().year}-{count:04d}"

    maint = MaintenanceRecord(
        equipment_id=eq.id,
        maintenance_number=maint_number,
        performed_by_id=str(user.id),
        **data.model_dump(),
    )
    db.add(maint)
    await db.flush([maint])
    await AuditService.log(
        db,
        action="CREATE",
        record_type="maintenance_record",
        record_id=maint.id,
        module="equipment",
        human_description=f"Maintenance {maint_number} ({data.maintenance_type}) recorded",
        user_id=str(user.id),
        username=user.username,
        full_name=user.full_name or user.username,
        ip_address=ip_address,
        site_id=eq.site_id,
    )
    await db.commit()
    await db.refresh(maint)
    return maint


async def list_maintenance_history(
    db: AsyncSession, equipment_id: str
) -> list[MaintenanceRecord]:
    await get_equipment_or_404(db, equipment_id, site_id=None)
    result = await db.execute(
        select(MaintenanceRecord)
        .where(MaintenanceRecord.equipment_id == equipment_id)
        .order_by(MaintenanceRecord.performed_at.desc())
    )
    return list(result.scalars().all())