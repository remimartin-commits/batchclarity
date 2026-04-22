from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.core.database import async_session_factory
from app.modules.equipment.models import CalibrationRecord


async def check_calibration_due() -> dict[str, int]:
    """Count overdue and due-soon calibration records."""
    now = datetime.now(timezone.utc)
    soon = now + timedelta(days=30)

    async with async_session_factory() as session:
        result = await session.execute(
            select(CalibrationRecord).where(CalibrationRecord.next_calibration_due.is_not(None))
        )
        rows = result.scalars().all()

    overdue = 0
    due_soon = 0
    for row in rows:
        due = row.next_calibration_due
        if due is None:
            continue
        if due < now:
            overdue += 1
        elif due <= soon:
            due_soon += 1
    return {"overdue": overdue, "due_soon": due_soon}
