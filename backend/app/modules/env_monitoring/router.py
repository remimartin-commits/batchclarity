"""Environmental Monitoring API — Locations, Alert Limits, Results, Trending."""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timezone
from app.core.database import get_db
from app.core.auth.dependencies import get_current_user, get_client_ip
from app.core.auth.models import User
from app.core.audit.service import AuditService
from app.modules.env_monitoring.models import (
    MonitoringLocation, AlertLimit, MonitoringResult, SamplingPlan,
)
from app.modules.env_monitoring.schemas import (
    MonitoringLocationCreate, MonitoringLocationOut,
    AlertLimitCreate, AlertLimitOut,
    MonitoringResultCreate, MonitoringResultOut,
    SamplingPlanCreate,
)

router = APIRouter(prefix="/env-monitoring", tags=["Environmental Monitoring"])


# ── Locations ─────────────────────────────────────────────────────────────────

@router.post("/locations", response_model=MonitoringLocationOut, status_code=201)
async def create_location(
    body: MonitoringLocationCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(
        select(MonitoringLocation).where(MonitoringLocation.code == body.code)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"Location code '{body.code}' already exists.")

    loc = MonitoringLocation(**body.model_dump())
    db.add(loc)
    await db.flush([loc])
    await AuditService.log(
        db, action="CREATE", record_type="monitoring_location", record_id=loc.id,
        module="env_monitoring",
        human_description=f"Monitoring location {body.code} '{body.name}' (Grade {body.gmp_grade}) created",
        user_id=current_user.id, username=current_user.username,
        full_name=current_user.full_name, ip_address=get_client_ip(request),
    )
    await db.refresh(loc)
    return loc


@router.get("/locations", response_model=list[MonitoringLocationOut])
async def list_locations(
    site_id: str | None = None,
    gmp_grade: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(MonitoringLocation).where(MonitoringLocation.is_active == True)
    if site_id:
        query = query.where(MonitoringLocation.site_id == site_id)
    if gmp_grade:
        query = query.where(MonitoringLocation.gmp_grade == gmp_grade)
    result = await db.execute(query.order_by(MonitoringLocation.code))
    return result.scalars().all()


# ── Alert Limits ──────────────────────────────────────────────────────────────

@router.post("/locations/{loc_id}/limits", response_model=AlertLimitOut, status_code=201)
async def set_alert_limit(
    loc_id: str,
    body: AlertLimitCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    loc_result = await db.execute(select(MonitoringLocation).where(MonitoringLocation.id == loc_id))
    if not loc_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Monitoring location not found.")

    limit = AlertLimit(location_id=loc_id, is_active=True, **body.model_dump())
    db.add(limit)
    await db.flush([limit])
    await AuditService.log(
        db, action="CREATE", record_type="alert_limit", record_id=limit.id,
        module="env_monitoring",
        human_description=f"Alert limit set for location {loc_id}: {body.parameter} AL={body.alert_limit} ACL={body.action_limit}",
        user_id=current_user.id, username=current_user.username,
        full_name=current_user.full_name, ip_address=get_client_ip(request),
    )
    await db.refresh(limit)
    return limit


@router.get("/locations/{loc_id}/limits", response_model=list[AlertLimitOut])
async def get_alert_limits(
    loc_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AlertLimit).where(
            AlertLimit.location_id == loc_id,
            AlertLimit.is_active == True,
        )
    )
    return result.scalars().all()


# ── Results Entry ─────────────────────────────────────────────────────────────

@router.post("/locations/{loc_id}/results", response_model=MonitoringResultOut, status_code=201)
async def enter_result(
    loc_id: str,
    body: MonitoringResultCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    loc_result = await db.execute(select(MonitoringLocation).where(MonitoringLocation.id == loc_id))
    loc = loc_result.scalar_one_or_none()
    if not loc:
        raise HTTPException(status_code=404, detail="Monitoring location not found.")

    count_result = await db.execute(select(func.count()).select_from(MonitoringResult))
    count = (count_result.scalar() or 0) + 1
    result_number = f"EM-{datetime.now(timezone.utc).year}-{count:05d}"

    # Get current limits to determine OOT/OOS status
    limits_result = await db.execute(
        select(AlertLimit).where(
            AlertLimit.location_id == loc_id,
            AlertLimit.parameter == body.parameter,
            AlertLimit.is_active == True,
        )
    )
    limit = limits_result.scalar_one_or_none()

    em_status = "within_limits"
    al_val = limit.alert_limit if limit else None
    acl_val = limit.action_limit if limit else None

    if acl_val is not None and body.result_value > acl_val:
        em_status = "action"
    elif al_val is not None and body.result_value > al_val:
        em_status = "alert"

    investigation_required = em_status == "action"

    now = datetime.now(timezone.utc)
    em_result = MonitoringResult(
        result_number=result_number,
        location_id=loc_id,
        parameter=body.parameter,
        sampling_method=body.sampling_method,
        sampled_at=body.sampled_at,
        sampled_by_id=current_user.id,
        batch_reference=body.batch_reference,
        result_value=body.result_value,
        unit=body.unit,
        result_entered_at=now,
        result_entered_by_id=current_user.id,
        status=em_status,
        alert_limit_at_time=al_val,
        action_limit_at_time=acl_val,
        investigation_required=investigation_required,
        comments=body.comments,
    )
    db.add(em_result)
    await db.flush([em_result])

    await AuditService.log(
        db, action="CREATE", record_type="monitoring_result", record_id=em_result.id,
        module="env_monitoring",
        human_description=(
            f"EM result {result_number}: {body.parameter}={body.result_value} {body.unit} "
            f"at {loc.code} — status: {em_status}"
        ),
        user_id=current_user.id, username=current_user.username,
        full_name=current_user.full_name, ip_address=get_client_ip(request),
    )
    await db.refresh(em_result)
    return em_result


@router.get("/results", response_model=list[MonitoringResultOut])
async def list_results(
    location_id: str | None = None,
    status_filter: str | None = None,
    investigation_required: bool | None = None,
    skip: int = 0, limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(MonitoringResult)
    if location_id:
        query = query.where(MonitoringResult.location_id == location_id)
    if status_filter:
        query = query.where(MonitoringResult.status == status_filter)
    if investigation_required is not None:
        query = query.where(MonitoringResult.investigation_required == investigation_required)
    result = await db.execute(
        query.order_by(MonitoringResult.sampled_at.desc()).offset(skip).limit(limit)
    )
    return result.scalars().all()
