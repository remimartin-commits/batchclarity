"""Environmental monitoring API — delegates to app.modules.env_monitoring.services."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.auth.dependencies import get_current_user, get_client_ip
from app.core.auth.models import User
from app.modules.env_monitoring import services as env_services
from app.modules.env_monitoring.schemas import (
    MonitoringLocationCreate,
    MonitoringLocationOut,
    AlertLimitCreate,
    AlertLimitOut,
    MonitoringResultCreate,
    MonitoringResultOut,
)

router = APIRouter(prefix="/env-monitoring", tags=["Environmental Monitoring"])


@router.post("/locations", response_model=MonitoringLocationOut, status_code=201)
async def create_location(
    body: MonitoringLocationCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await env_services.create_location(
        db, body, current_user, get_client_ip(request)
    )


@router.get("/locations", response_model=list[MonitoringLocationOut])
async def list_locations(
    site_id: str | None = None,
    gmp_grade: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await env_services.list_monitoring_locations(
        db, site_id=site_id, gmp_grade=gmp_grade
    )


@router.post("/locations/{loc_id}/limits", response_model=AlertLimitOut, status_code=201)
async def set_alert_limit(
    loc_id: str,
    body: AlertLimitCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await env_services.set_alert_limit(
        db, loc_id, body, current_user, get_client_ip(request)
    )


@router.get("/locations/{loc_id}/limits", response_model=list[AlertLimitOut])
async def get_alert_limits(
    loc_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await env_services.get_active_alert_limits(db, loc_id)


@router.post("/locations/{loc_id}/results", response_model=MonitoringResultOut, status_code=201)
async def enter_result(
    loc_id: str,
    body: MonitoringResultCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await env_services.record_result(
        db, loc_id, body, current_user, get_client_ip(request)
    )


@router.get("/results", response_model=list[MonitoringResultOut])
async def list_results(
    location_id: str | None = None,
    status_filter: str | None = None,
    investigation_required: bool | None = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await env_services.list_monitoring_results_global(
        db,
        location_id=location_id,
        status_filter=status_filter,
        investigation_required=investigation_required,
        skip=skip,
        limit=limit,
    )
