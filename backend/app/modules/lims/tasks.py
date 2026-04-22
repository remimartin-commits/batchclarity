"""
LIMS background tasks — long-running OOS investigations (stale) notification.
Uses async_session_factory (not request get_db). Audits as system when notifying.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select

from app.core.audit.service import AuditService
from app.core.database import async_session_factory
from app.core.notify.service import NotificationService
from app.modules.lims.models import OOSInvestigation

logger = logging.getLogger(__name__)

_RULE_LIMS_OOS_STALE = "lims_oos_investigation_stale"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


async def check_open_oos_investigations() -> None:
    """
    Count OOS investigations not closed and older than 14 days; notify if any.
    """
    cutoff = _utcnow() - timedelta(days=14)

    async with async_session_factory() as session:
        n = int(
            await session.scalar(
                select(func.count(OOSInvestigation.id)).where(
                    OOSInvestigation.status != "closed",
                    OOSInvestigation.created_at < cutoff,
                )
            )
            or 0
        )
        if n > 0:
            await NotificationService.send_rule_based(
                session,
                _RULE_LIMS_OOS_STALE,
                {
                    "count": n,
                    "site_id": "all sites (aggregated)",
                },
            )
            await AuditService.log(
                session,
                action="WARNING",
                record_type="oos_investigation",
                record_id="scheduler",
                module="lims",
                human_description=(
                    f"Scheduler: {n} OOS investigation(s) open longer than 14 days — "
                    f"stale OOS check notification sent"
                ),
                user_id=None,
                username="system",
                full_name="LIMS Scheduler",
                ip_address="127.0.0.1",
                is_system_action=True,
            )
        await session.commit()
