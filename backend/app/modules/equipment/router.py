"""Equipment Management API — Equipment, Calibration, Qualification, Maintenance."""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timezone
from app.core.database import get_db
from app.core.auth.dependencies import get_current_user, get_client_ip
from app.core.auth.models import User
from app.core.audit.service import AuditService
from app.modules.equipment.models import Equipment, CalibrationRecord, QualificationRecord, MaintenanceRecord
from app.modules.equipment.schemas import (
    EquipmentCreate, EquipmentOut, EquipmentStatusUpdate,
    CalibrationCreate, CalibrationOut,
    QualificationCreate, QualificationOut,
    MaintenanceCreate, MaintenanceOut,
)

router = APIRouter(prefix="/equipment", tags=["Equipment Management"])

ALLOWED_STATUS_TRANSITIONS: dict[str, set[str]] = {
    "pre_qualification": {"qualified", "out_of_service", "retired"},
    "qualified": {"under_maintenance", "out_of_service", "retired"},
    "under_maintenance": {"qualified", "out_of_service", "retired"},
    "out_of_service": {"under_maintenance", "qualified", "retired"},
    "retired": set(),
}


# ── Equipment Master ──────────────────────────────────────────────────────────

@router.post("", response_model=EquipmentOut, status_code=201)
async def create_equipment(
    body: EquipmentCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(
        select(Equipment).where(Equipment.equipment_id == body.equipment_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"Equipment ID '{body.equipment_id}' already exists.")

    eq = Equipment(**body.model_dump(), owner_id=current_user.id)
    db.add(eq)
    await db.flush([eq])

    await AuditService.log(
        db, action="CREATE", record_type="equipment", record_id=eq.id,
        module="equipment",
        human_description=f"Equipment {body.equipment_id} '{body.name}' registered",
        user_id=current_user.id, username=current_user.username,
        full_name=current_user.full_name, ip_address=get_client_ip(request),
    )
    await db.refresh(eq)
    return eq


@router.get("", response_model=list[EquipmentOut])
async def list_equipment(
    site_id: str | None = None,
    status_filter: str | None = None,
    skip: int = 0, limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Equipment)
    if site_id:
        query = query.where(Equipment.site_id == site_id)
    if status_filter:
        query = query.where(Equipment.status == status_filter)
    result = await db.execute(
        query.order_by(Equipment.equipment_id).offset(skip).limit(limit)
    )
    return result.scalars().all()


@router.get("/{eq_id}", response_model=EquipmentOut)
async def get_equipment(
    eq_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Equipment).where(Equipment.id == eq_id))
    eq = result.scalar_one_or_none()
    if not eq:
        raise HTTPException(status_code=404, detail="Equipment not found.")
    return eq


@router.patch("/{eq_id}/status")
async def update_equipment_status(
    eq_id: str,
    body: EquipmentStatusUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Equipment).where(Equipment.id == eq_id))
    eq = result.scalar_one_or_none()
    if not eq:
        raise HTTPException(status_code=404, detail="Equipment not found.")

    old_status = eq.status
    allowed = ALLOWED_STATUS_TRANSITIONS.get(old_status, set())
    if body.status not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status transition: {old_status} -> {body.status}",
        )
    eq.status = body.status

    await AuditService.log_field_change(
        db, record_type="equipment", record_id=eq_id, module="equipment",
        field_name="status", old_value=old_status, new_value=body.status,
        user_id=current_user.id, username=current_user.username,
        full_name=current_user.full_name, ip_address=get_client_ip(request),
        reason=body.reason,
    )
    return {"status": eq.status}


# ── Calibration ───────────────────────────────────────────────────────────────

@router.post("/{eq_id}/calibrations", response_model=CalibrationOut, status_code=201)
async def add_calibration(
    eq_id: str,
    body: CalibrationCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    eq_result = await db.execute(select(Equipment).where(Equipment.id == eq_id))
    eq = eq_result.scalar_one_or_none()
    if not eq:
        raise HTTPException(status_code=404, detail="Equipment not found.")

    count_result = await db.execute(select(func.count()).select_from(CalibrationRecord))
    count = (count_result.scalar() or 0) + 1
    cal_number = f"CAL-{datetime.now(timezone.utc).year}-{count:04d}"

    from datetime import timedelta
    next_due = None
    if body.calibration_interval_days:
        next_due = body.performed_at + timedelta(days=body.calibration_interval_days)

    cal = CalibrationRecord(
        equipment_id=eq_id,
        calibration_number=cal_number,
        calibration_type=body.calibration_type,
        performed_by_id=current_user.id,
        performed_at=body.performed_at,
        next_calibration_due=next_due,
        calibration_interval_days=body.calibration_interval_days,
        result=body.result,
        certificate_number=body.certificate_number,
        as_found_condition=body.as_found_condition,
        as_left_condition=body.as_left_condition,
        notes=body.notes,
    )
    db.add(cal)
    await db.flush([cal])

    await AuditService.log(
        db, action="CREATE", record_type="calibration_record", record_id=cal.id,
        module="equipment",
        human_description=f"Calibration {cal_number} ({body.result}) recorded for equipment {eq.equipment_id}",
        user_id=current_user.id, username=current_user.username,
        full_name=current_user.full_name, ip_address=get_client_ip(request),
    )
    await db.refresh(cal)
    return cal


@router.get("/{eq_id}/calibrations", response_model=list[CalibrationOut])
async def list_calibrations(
    eq_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CalibrationRecord).where(CalibrationRecord.equipment_id == eq_id)
        .order_by(CalibrationRecord.performed_at.desc())
    )
    return result.scalars().all()


# ── Qualification (IQ/OQ/PQ) ──────────────────────────────────────────────────

@router.post("/{eq_id}/qualifications", response_model=QualificationOut, status_code=201)
async def add_qualification(
    eq_id: str,
    body: QualificationCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    eq_result = await db.execute(select(Equipment).where(Equipment.id == eq_id))
    if not eq_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Equipment not found.")

    count_result = await db.execute(select(func.count()).select_from(QualificationRecord))
    count = (count_result.scalar() or 0) + 1
    qual_number = f"{body.qualification_type}-{datetime.now(timezone.utc).year}-{count:04d}"

    qual = QualificationRecord(
        equipment_id=eq_id,
        qualification_number=qual_number,
        performed_by_id=current_user.id,
        **body.model_dump(),
    )
    db.add(qual)
    await db.flush([qual])

    await AuditService.log(
        db, action="CREATE", record_type="qualification_record", record_id=qual.id,
        module="equipment",
        human_description=f"{body.qualification_type} qualification {qual_number} recorded",
        user_id=current_user.id, username=current_user.username,
        full_name=current_user.full_name, ip_address=get_client_ip(request),
    )
    await db.refresh(qual)
    return qual


@router.get("/{eq_id}/qualifications", response_model=list[QualificationOut])
async def list_qualifications(
    eq_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(QualificationRecord).where(QualificationRecord.equipment_id == eq_id)
        .order_by(QualificationRecord.created_at.desc())
    )
    return result.scalars().all()


# ── Maintenance ────────────────────────────────────────────────────────────────

@router.post("/{eq_id}/maintenance", response_model=MaintenanceOut, status_code=201)
async def add_maintenance(
    eq_id: str,
    body: MaintenanceCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    eq_result = await db.execute(select(Equipment).where(Equipment.id == eq_id))
    if not eq_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Equipment not found.")

    count_result = await db.execute(select(func.count()).select_from(MaintenanceRecord))
    count = (count_result.scalar() or 0) + 1
    maint_number = f"MAINT-{datetime.now(timezone.utc).year}-{count:04d}"

    maint = MaintenanceRecord(
        equipment_id=eq_id,
        maintenance_number=maint_number,
        performed_by_id=current_user.id,
        **body.model_dump(),
    )
    db.add(maint)
    await db.flush([maint])

    await AuditService.log(
        db, action="CREATE", record_type="maintenance_record", record_id=maint.id,
        module="equipment",
        human_description=f"Maintenance {maint_number} ({body.maintenance_type}) recorded",
        user_id=current_user.id, username=current_user.username,
        full_name=current_user.full_name, ip_address=get_client_ip(request),
    )
    await db.refresh(maint)
    return maint


@router.get("/{eq_id}/maintenance", response_model=list[MaintenanceOut])
async def list_maintenance(
    eq_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(MaintenanceRecord).where(MaintenanceRecord.equipment_id == eq_id)
        .order_by(MaintenanceRecord.performed_at.desc())
    )
    return result.scalars().all()
