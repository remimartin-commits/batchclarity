"""Scheduled environmental monitoring checks — overdue trend reviews, notifications."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, select

from app.core.database import async_session_factory
from app.core.notify.service import NotificationService
from app.modules.env_monitoring.models import MonitoringTrend

_RULE_ENV_REVIEW = "env_monitoring_review_overdue"


async def check_overdue_monitoring_reviews() -> dict[str, int]:
    """
    Count monitoring trend records past period end but not reviewed; notify when count > 0.
    """
    now = datetime.now(timezone.utc)
    async with async_session_factory() as session:
        overdue = int(
            await session.scalar(
                select(func.count(MonitoringTrend.id)).where(
                    MonitoringTrend.reviewed_at.is_(None),
                    MonitoringTrend.period_end < now,
                )
            )
            or 0
        )
        notified = 0
        if overdue > 0:
            notified = await NotificationService.send_rule_based(
                session,
                _RULE_ENV_REVIEW,
                {
                    "count": overdue,
                    "site_id": "aggregated (all sites)",
                },
            )
        await session.commit()
    return {"overdue": overdue, "notified": notified}
