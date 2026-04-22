from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, select

from app.core.database import async_session_factory
from app.core.notify.service import NotificationService
from app.modules.qms.models import CAPA


async def check_overdue_capas() -> int:
    """Count overdue CAPAs and trigger rule-based notification."""
    now = datetime.now(timezone.utc)
    async with async_session_factory() as session:
        count_result = await session.execute(
            select(func.count()).select_from(CAPA).where(
                CAPA.target_completion_date.is_not(None),
                CAPA.target_completion_date < now,
                CAPA.current_status.notin_(["closed", "completed", "cancelled"]),
            )
        )
        overdue_count = int(count_result.scalar() or 0)
        if overdue_count > 0:
            await NotificationService.send_rule_based(
                session,
                "qms_capa_overdue",
                {"count": overdue_count},
            )
            await session.commit()
        return overdue_count
