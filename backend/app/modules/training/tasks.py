from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.core.database import async_session_factory
from app.modules.training.models import TrainingAssignment


async def check_overdue_training() -> dict[str, int]:
    """Count overdue assignments and due-within-7-days reminders."""
    now = datetime.now(timezone.utc)
    reminder_window = now + timedelta(days=7)
    async with async_session_factory() as session:
        result = await session.execute(
            select(TrainingAssignment).where(
                TrainingAssignment.due_date.is_not(None),
                TrainingAssignment.status.notin_(["completed", "waived"]),
            )
        )
        rows = result.scalars().all()

        overdue = 0
        reminders = 0
        changed = False
        for row in rows:
            due = row.due_date
            if due is None:
                continue
            # SQLite often returns naive datetimes; normalize for stable comparisons.
            if due.tzinfo is None:
                due = due.replace(tzinfo=timezone.utc)
            if due < now:
                overdue += 1
                if row.status != "overdue":
                    row.status = "overdue"
                    changed = True
            elif due <= reminder_window:
                reminders += 1

        if changed:
            await session.commit()

    return {"overdue": overdue, "reminders": reminders}
