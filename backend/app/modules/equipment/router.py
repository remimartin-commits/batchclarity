"""Equipment API — delegates to app.modules.equipment.services."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.auth.dependencies import get_current_user, get_client_ip
from app.core.auth.models import User
from app.modules.equipment import services as equipment_services
from app.modules.equipment.schemas import (
    EquipmentCreate,
    EquipmentOut,
    EquipmentStatusUpdate,
    CalibrationCreate,
    CalibrationOut,
    QualificationCreate,
    QualificationOut,
    MaintenanceCreate,
    MaintenanceOut,
)

router = APIRouter(prefix="/equipment", tags=["Equipment Management"])


@router.post("", response_model=EquipmentOut, status_code=201)
async def create_equipment(
    body: EquipmentCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await equipment_services.create_equipment(
        db, body, current_user, get_client_ip(request)
    )


@router.get("", response_model=list[EquipmentOut])
async def list_equipment(
    site_id: str | None = None,
    status_filter: str | None = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await equipment_services.list_equipment(
        db,
        site_id=site_id,
        status_filter=status_filter,
        skip=skip,
        limit=limit,
    )


@router.get("/{eq_id}", response_model=EquipmentOut)
async def get_equipment(
    eq_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await equipment_services.get_equipment_or_404(db, eq_id, site_id=None)


@router.patch("/{eq_id}/status")
async def update_equipment_status(
    eq_id: str,
    body: EquipmentStatusUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await equipment_services.update_equipment_status(
        db, eq_id, body, current_user, get_client_ip(request)
    )


@router.post("/{eq_id}/calibrations", response_model=CalibrationOut, status_code=201)
async def add_calibration(
    eq_id: str,
    body: CalibrationCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await equipment_services.record_calibration(
        db, eq_id, body, current_user, get_client_ip(request)
    )


@router.get("/{eq_id}/calibrations", response_model=list[CalibrationOut])
async def list_calibrations(
    eq_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await equipment_services.list_calibrations_for_user_site(db, eq_id, current_user)


@router.post("/{eq_id}/qualifications", response_model=QualificationOut, status_code=201)
async def add_qualification(
    eq_id: str,
    body: QualificationCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await equipment_services.record_qualification(
        db, eq_id, body, current_user, get_client_ip(request)
    )


@router.get("/{eq_id}/qualifications", response_model=list[QualificationOut])
async def list_qualifications(
    eq_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await equipment_services.list_qualification_history(db, eq_id)


@router.post("/{eq_id}/maintenance", response_model=MaintenanceOut, status_code=201)
async def add_maintenance(
    eq_id: str,
    body: MaintenanceCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await equipment_services.record_maintenance(
        db, eq_id, body, current_user, get_client_ip(request)
    )


@router.get("/{eq_id}/maintenance", response_model=list[MaintenanceOut])
async def list_maintenance(
    eq_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await equipment_services.list_maintenance_history(db, eq_id)
