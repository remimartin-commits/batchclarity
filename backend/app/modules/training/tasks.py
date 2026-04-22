from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select, update

from app.core.database import async_session_factory
from app.core.notify.service import NotificationService
from app.modules.training.models import TrainingAssignment

_RULE_TRAINING = "training_assignment_overdue"


async def check_overdue_training() -> dict[str, int]:
    """Count reminder/overdue training; set status=overdue for pending past due; notify batch."""
    now = datetime.now(timezone.utc)
    reminder_window = now + timedelta(days=7)
    async with async_session_factory() as session:
        overdue = int(
            await session.scalar(
                select(func.count(TrainingAssignment.id)).where(
                    TrainingAssignment.due_date.is_not(None),
                    TrainingAssignment.status.notin_(["completed", "waived"]),
                    TrainingAssignment.due_date < now,
                )
            )
            or 0
        )
        reminders = int(
            await session.scalar(
                select(func.count(TrainingAssignment.id)).where(
                    TrainingAssignment.due_date.is_not(None),
                    TrainingAssignment.status.notin_(["completed", "waived"]),
                    TrainingAssignment.due_date >= now,
                    TrainingAssignment.due_date <= reminder_window,
                )
            )
            or 0
        )

        await session.execute(
            update(TrainingAssignment)
            .where(
                TrainingAssignment.due_date.is_not(None),
                TrainingAssignment.due_date < now,
                TrainingAssignment.status == "pending",
            )
            .values(status="overdue", updated_at=now)
        )

        notified = 0
        if overdue > 0:
            notified = await NotificationService.send_rule_based(
                session,
                _RULE_TRAINING,
                {
                    "count": overdue,
                    "site_id": "aggregated (all sites)",
                },
            )
        await session.commit()
    return {"overdue": overdue, "reminders": reminders, "notified": notified}
