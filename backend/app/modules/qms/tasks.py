from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select

from app.core.database import async_session_factory
from app.modules.qms.models import CAPA


async def check_overdue_capas() -> int:
    """Count CAPAs past target completion date and not closed."""
    now = datetime.now(timezone.utc)
    async with async_session_factory() as session:
        result = await session.execute(
            select(CAPA).where(
                CAPA.target_completion_date.is_not(None),
                CAPA.target_completion_date < now,
                CAPA.current_status.notin_(["closed", "completed", "cancelled"]),
            )
        )
        return len(result.scalars().all())
