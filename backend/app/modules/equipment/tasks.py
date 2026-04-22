from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.core.database import async_session_factory
from app.core.notify.service import NotificationService
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
        changed = False
        for row in rows:
            due = row.next_calibration_due
            if due is None:
                continue
            # SQLite often returns naive datetimes; normalize for stable comparisons.
            if due.tzinfo is None:
                due = due.replace(tzinfo=timezone.utc)
            if due < now:
                overdue += 1
                if not row.is_overdue:
                    row.is_overdue = True
                    changed = True
            else:
                if row.is_overdue:
                    row.is_overdue = False
                    changed = True
                if due <= soon:
                    due_soon += 1

        if overdue > 0 or due_soon > 0:
            await NotificationService.send_rule_based(
                session,
                "equipment_calibration_due",
                {"overdue": overdue, "due_soon": due_soon},
            )

        if changed or overdue > 0 or due_soon > 0:
            await session.commit()

    return {"overdue": overdue, "due_soon": due_soon}
