"""
Environmental monitoring — locations, results (ALCOA server time), trend review with e-sig.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit.service import AuditService
from app.core.auth.models import User
from app.core.esig.service import ESignatureService
from app.core.notify.service import NotificationService
from app.modules.env_monitoring.models import (
    AlertLimit,
    MonitoringLocation,
    MonitoringResult,
    MonitoringTrend,
)
from app.modules.env_monitoring.schemas import (
    MonitoringLocationCreate,
    MonitoringResultCreate,
    MonitoringTrendCreate,
    MonitoringTrendReviewRequest,
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


# ── Locations ────────────────────────────────────────────────────────────────


async def create_location(
    db: AsyncSession,
    data: MonitoringLocationCreate,
    user: User,
    ip_address: Optional[str],
) -> MonitoringLocation:
    if data.site_id != _require_user_site_id(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Location site_id must match the current user's site.",
        )

    existing = await db.execute(
        select(MonitoringLocation).where(MonitoringLocation.code == data.code)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Location code '{data.code}' already exists.",
        )

    loc = MonitoringLocation(**data.model_dump())
    db.add(loc)
    await db.flush([loc])
    await AuditService.log(
        db,
        action="CREATE",
        record_type="monitoring_location",
        record_id=loc.id,
        module="env_monitoring",
        human_description=(
            f"Monitoring location {data.code} '{data.name}' (Grade {data.gmp_grade}) created"
        ),
        user_id=str(user.id),
        username=user.username,
        full_name=user.full_name,
        ip_address=ip_address,
        site_id=data.site_id,
    )
    await db.commit()
    await db.refresh(loc)
    return loc


async def _get_location_for_site(
    db: AsyncSession, location_id: str, site_id: str
) -> MonitoringLocation:
    res = await db.execute(
        select(MonitoringLocation).where(
            MonitoringLocation.id == location_id,
            MonitoringLocation.site_id == site_id,
        )
    )
    loc = res.scalar_one_or_none()
    if not loc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Monitoring location not found for this site.",
        )
    return loc


# ── Results ───────────────────────────────────────────────────────────────────


async def record_result(
    db: AsyncSession,
    location_id: str,
    data: MonitoringResultCreate,
    user: User,
    ip_address: Optional[str],
) -> MonitoringResult:
    site_id = _require_user_site_id(user)
    loc = await _get_location_for_site(db, location_id, site_id)

    count_result = await db.execute(select(func.count()).select_from(MonitoringResult))
    count = (count_result.scalar() or 0) + 1
    result_number = f"EM-{_utcnow().year}-{count:05d}"

    limits_result = await db.execute(
        select(AlertLimit).where(
            AlertLimit.location_id == location_id,
            AlertLimit.parameter == data.parameter,
            AlertLimit.is_active == True,  # noqa: E712
        )
    )
    limit = limits_result.scalar_one_or_none()

    al_val = float(limit.alert_limit) if limit and limit.alert_limit is not None else None
    acl_val = float(limit.action_limit) if limit and limit.action_limit is not None else None

    em_status = "within_limits"
    if acl_val is not None and data.result_value > acl_val:
        em_status = "action"
    elif al_val is not None and data.result_value > al_val:
        em_status = "alert"

    investigation_required = em_status == "action"
    exceeds = al_val is not None and data.result_value > al_val
    linked_dev: str | None = None
    if exceeds:
        linked_dev = str(uuid.uuid4())

    now = _utcnow()
    em_result = MonitoringResult(
        result_number=result_number,
        location_id=location_id,
        parameter=data.parameter,
        sampling_method=data.sampling_method,
        sampled_at=now,
        sampled_by_id=str(user.id),
        batch_reference=data.batch_reference,
        result_value=data.result_value,
        unit=data.unit,
        result_entered_at=now,
        result_entered_by_id=str(user.id),
        status=em_status,
        alert_limit_at_time=al_val,
        action_limit_at_time=acl_val,
        investigation_required=investigation_required,
        exceeds_alert_limit=exceeds,
        linked_deviation_id=linked_dev,
        comments=data.comments,
    )
    db.add(em_result)
    await db.flush([em_result])

    await AuditService.log(
        db,
        action="CREATE",
        record_type="monitoring_result",
        record_id=em_result.id,
        module="env_monitoring",
        human_description=(
            f"EM result {result_number}: {data.parameter}={data.result_value} {data.unit} "
            f"at {loc.code} — status: {em_status}"
        ),
        user_id=str(user.id),
        username=user.username,
        full_name=user.full_name,
        ip_address=ip_address,
        site_id=loc.site_id,
    )

    if exceeds and linked_dev:
        await NotificationService.send_event(
            db,
            event_type="env_monitoring.alert_exceeded",
            record_type="monitoring_result",
            record_id=em_result.id,
            variables={
                "location_code": loc.code,
                "parameter": data.parameter,
                "value": str(data.result_value),
                "unit": data.unit,
                "alert_limit": str(al_val) if al_val is not None else "",
                "site_id": loc.site_id,
            },
            site_id=loc.site_id,
        )
        await AuditService.log(
            db,
            action="ALERT_LIMIT_EXCEEDED",
            record_type="monitoring_result",
            record_id=em_result.id,
            module="env_monitoring",
            human_description=(
                f"EM result {result_number} exceeded alert limit; loose deviation ref {linked_dev}"
            ),
            user_id=str(user.id),
            username=user.username,
            full_name=user.full_name,
            ip_address=ip_address,
            site_id=loc.site_id,
            record_snapshot_after={
                "exceeds_alert_limit": True,
                "linked_deviation_id": linked_dev,
            },
        )

    await db.commit()
    await db.refresh(em_result)
    return em_result


async def list_results(
    db: AsyncSession,
    location_id: str,
    site_id: str,
    page: int = 1,
    page_size: int = 20,
) -> list[MonitoringResult]:
    await _get_location_for_site(db, location_id, site_id)
    ps = _clamp_page_size(page_size)
    off = _offset(page, ps)
    result = await db.execute(
        select(MonitoringResult)
        .where(MonitoringResult.location_id == location_id)
        .order_by(MonitoringResult.sampled_at.desc())
        .offset(off)
        .limit(ps)
    )
    return list(result.scalars().all())


# ── Trends ───────────────────────────────────────────────────────────────────


async def create_trend(
    db: AsyncSession,
    location_id: str,
    data: MonitoringTrendCreate,
    user: User,
    ip_address: Optional[str],
) -> MonitoringTrend:
    site_id = _require_user_site_id(user)
    loc = await _get_location_for_site(db, location_id, site_id)

    trend = MonitoringTrend(
        location_id=location_id,
        status="pending",
        **data.model_dump(),
    )
    db.add(trend)
    await db.flush([trend])
    await AuditService.log(
        db,
        action="CREATE",
        record_type="monitoring_trend",
        record_id=trend.id,
        module="env_monitoring",
        human_description=f"Monitoring trend for {loc.code} / {data.parameter} ({data.period_start}–{data.period_end})",
        user_id=str(user.id),
        username=user.username,
        full_name=user.full_name,
        ip_address=ip_address,
        site_id=loc.site_id,
    )
    await db.commit()
    await db.refresh(trend)
    return trend


async def review_trend(
    db: AsyncSession,
    trend_id: str,
    data: MonitoringTrendReviewRequest,
    user: User,
    ip_address: Optional[str],
) -> MonitoringTrend:
    site_id = _require_user_site_id(user)
    tr_row = await db.execute(
        select(MonitoringTrend)
        .join(MonitoringLocation, MonitoringTrend.location_id == MonitoringLocation.id)
        .where(
            MonitoringTrend.id == trend_id,
            MonitoringLocation.site_id == site_id,
        )
    )
    trend = tr_row.scalar_one_or_none()
    if not trend:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Monitoring trend not found.",
        )
    if trend.status == "reviewed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This trend is already reviewed.",
        )

    loc = await _get_location_for_site(db, trend.location_id, site_id)

    ip = ip_address or "127.0.0.1"
    await ESignatureService.sign(
        db,
        user_id=str(user.id),
        password=data.password,
        record_type="monitoring_trend",
        record_id=trend_id,
        record_version="1.0",
        record_data={
            "trend_id": trend_id,
            "conclusion": data.trend_conclusion,
        },
        meaning="trend_reviewed",
        meaning_display="EM trend review",
        ip_address=ip,
        comments=data.trend_conclusion,
    )

    tr_now = _utcnow()
    trend.trend_conclusion = data.trend_conclusion
    trend.reviewed_by_id = str(user.id)
    trend.reviewed_at = tr_now
    trend.status = "reviewed"

    await AuditService.log(
        db,
        action="REVIEW",
        record_type="monitoring_trend",
        record_id=trend_id,
        module="env_monitoring",
        human_description=f"EM trend {trend_id} reviewed and signed (location {loc.code})",
        user_id=str(user.id),
        username=user.username,
        full_name=user.full_name,
        ip_address=ip_address,
        site_id=loc.site_id,
    )
    await db.commit()
    await db.refresh(trend)
    return trend
