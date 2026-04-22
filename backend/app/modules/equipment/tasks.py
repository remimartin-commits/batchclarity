from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select, update

from app.core.database import async_session_factory
from app.core.notify.service import NotificationService
from app.modules.equipment.models import CalibrationRecord

_RULE_CALIBRATION = "equipment_calibration_overdue"


async def check_calibration_due() -> dict[str, int]:
    """Count due-soon / overdue calibrations; set is_overdue flags; notify on overdue batch."""
    now = datetime.now(timezone.utc)
    soon = now + timedelta(days=30)

    async with async_session_factory() as session:
        overdue = int(
            await session.scalar(
                select(func.count(CalibrationRecord.id)).where(
                    CalibrationRecord.next_calibration_due.is_not(None),
                    CalibrationRecord.next_calibration_due < now,
                )
            )
            or 0
        )
        due_soon = int(
            await session.scalar(
                select(func.count(CalibrationRecord.id)).where(
                    CalibrationRecord.next_calibration_due.is_not(None),
                    CalibrationRecord.next_calibration_due >= now,
                    CalibrationRecord.next_calibration_due <= soon,
                )
            )
            or 0
        )

        await session.execute(
            update(CalibrationRecord)
            .where(
                CalibrationRecord.next_calibration_due.is_not(None),
                CalibrationRecord.next_calibration_due < now,
                CalibrationRecord.is_overdue == False,  # noqa: E712
            )
            .values(is_overdue=True, updated_at=now)
        )
        await session.execute(
            update(CalibrationRecord)
            .where(
                CalibrationRecord.next_calibration_due.is_not(None),
                CalibrationRecord.next_calibration_due >= now,
                CalibrationRecord.is_overdue == True,  # noqa: E712
            )
            .values(is_overdue=False, updated_at=now)
        )

        notified = 0
        if overdue > 0:
            notified = await NotificationService.send_rule_based(
                session,
                _RULE_CALIBRATION,
                {
                    "count": overdue,
                    "site_id": "aggregated (all sites)",
                },
            )
        await session.commit()
    return {"overdue": overdue, "due_soon": due_soon, "notified": notified}
