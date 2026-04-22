from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select

from app.core.database import async_session_factory
from app.core.notify.service import NotificationService
from app.modules.qms.models import CAPA

_RULE_QMS_CAPA = "qms_capa_overdue"


async def check_overdue_capas() -> dict[str, int]:
    """Count CAPAs past target completion date and not closed; notify when count > 0."""
    now = datetime.now(timezone.utc)
    async with async_session_factory() as session:
        result = await session.execute(
            select(CAPA).where(
                CAPA.target_completion_date.is_not(None),
                CAPA.target_completion_date < now,
                CAPA.current_status.notin_(["closed", "completed", "cancelled"]),
            )
        )
        overdue = len(result.scalars().all())

        notified = 0
        if overdue > 0:
            notified = await NotificationService.send_rule_based(
                session,
                _RULE_QMS_CAPA,
                {
                    "count": overdue,
                    "site_id": "aggregated (all sites)",
                },
            )
        await session.commit()
    return {"overdue": overdue, "notified": notified}
