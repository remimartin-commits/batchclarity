"""
MES Background Tasks — APScheduler jobs.

Registered in app/core/scheduler.py (or main.py) via:
    scheduler.add_job(check_stale_batches, "interval", hours=1, id="mes_stale_batches")
    scheduler.add_job(daily_batch_summary, "cron", hour=6, id="mes_daily_summary")

All tasks use async_session_factory (not the request-scoped get_db).
All tasks write to the audit trail as system actions (is_system_action=True).
No task modifies data without a corresponding AuditEvent.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.core.audit.service import AuditService
from app.core.database import async_session_factory
from app.modules.mes.models import BatchRecord, BatchRecordStep

logger = logging.getLogger(__name__)

# Sentinel user info for system-initiated audit events
_SYSTEM_USER_ID = "system"
_SYSTEM_USERNAME = "system"
_SYSTEM_FULL_NAME = "MES Scheduler"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


async def check_stale_batches() -> None:
    """
    Flag batch records that have been 'in_progress' for more than 48 hours
    without any step activity. Writes an audit warning — does NOT auto-close.

    Runs every hour. Intent: alert QA that a batch may have been abandoned
    without a proper deviation or completion record.
    """
    cutoff = _utcnow() - timedelta(hours=48)

    async with async_session_factory() as session:
        try:
            result = await session.execute(
                select(BatchRecord).where(
                    BatchRecord.status == "in_progress",
                    BatchRecord.actual_start < cutoff,
                )
            )
            stale_batches = result.scalars().all()

            for br in stale_batches:
                # Check if any step was recorded recently (within 48h)
                recent_step = await session.execute(
                    select(BatchRecordStep).where(
                        BatchRecordStep.batch_record_id == br.id,
                        BatchRecordStep.performed_at >= cutoff,
                    )
                )
                if recent_step.scalar_one_or_none():
                    continue  # Active — skip

                logger.warning(
                    "Stale batch detected: %s (started %s, no activity since %s)",
                    br.batch_number,
                    br.actual_start,
                    cutoff,
                )

                await AuditService.log(
                    session,
                    action="WARNING",
                    record_type="batch_record",
                    record_id=br.id,
                    module="mes",
                    human_description=(
                        f"STALE BATCH WARNING: {br.batch_number} has been 'in_progress' "
                        f"for >48h with no step activity. QA review required."
                    ),
                    user_id=None,
                    username=_SYSTEM_USERNAME,
                    full_name=_SYSTEM_FULL_NAME,
                    ip_address=None,
                    is_system_action=True,
                )

            await session.commit()
            logger.info("check_stale_batches: checked %d stale batch(es).", len(stale_batches))

        except Exception as exc:
            await session.rollback()
            logger.error("check_stale_batches failed: %s", exc, exc_info=True)


async def flag_yield_outliers() -> None:
    """
    Scan completed batches (status='completed') where yield_percentage is
    outside the MBR acceptable range and no deviation has been linked.

    Runs daily at 07:00 UTC. Writes an audit warning if an outlier is detected
    without a linked deviation — prompts QA to investigate.

    Note: this is a DETECTION job only. It does NOT create deviations automatically
    (that requires a human decision per our constitutional layer). It flags for review.
    """
    from app.modules.mes.models import MasterBatchRecord

    async with async_session_factory() as session:
        try:
            result = await session.execute(
                select(BatchRecord).where(
                    BatchRecord.status == "completed",
                    BatchRecord.yield_percentage.is_not(None),
                )
            )
            completed = result.scalars().all()
            flagged = 0

            for br in completed:
                if br.has_deviations:
                    continue  # Already acknowledged

                mbr_result = await session.execute(
                    select(MasterBatchRecord).where(
                        MasterBatchRecord.id == br.master_batch_record_id
                    )
                )
                mbr = mbr_result.scalar_one_or_none()
                if not mbr:
                    continue

                out_of_range = False
                if (
                    mbr.acceptable_yield_min is not None
                    and br.yield_percentage < mbr.acceptable_yield_min
                ):
                    out_of_range = True
                if (
                    mbr.acceptable_yield_max is not None
                    and br.yield_percentage > mbr.acceptable_yield_max
                ):
                    out_of_range = True

                if not out_of_range:
                    continue

                flagged += 1
                logger.warning(
                    "Yield outlier: batch %s yield=%.1f%% (acceptable: %.1f–%.1f%%)",
                    br.batch_number,
                    br.yield_percentage,
                    mbr.acceptable_yield_min or 0,
                    mbr.acceptable_yield_max or 100,
                )

                await AuditService.log(
                    session,
                    action="WARNING",
                    record_type="batch_record",
                    record_id=br.id,
                    module="mes",
                    human_description=(
                        f"YIELD OUTLIER: Batch {br.batch_number} yield={br.yield_percentage:.1f}% "
                        f"is outside acceptable range "
                        f"[{mbr.acceptable_yield_min}–{mbr.acceptable_yield_max}%]. "
                        f"No deviation linked. QA investigation required."
                    ),
                    user_id=None,
                    username=_SYSTEM_USERNAME,
                    full_name=_SYSTEM_FULL_NAME,
                    ip_address=None,
                    is_system_action=True,
                )

            await session.commit()
            logger.info("flag_yield_outliers: %d outlier(s) flagged.", flagged)

        except Exception as exc:
            await session.rollback()
            logger.error("flag_yield_outliers failed: %s", exc, exc_info=True)


async def daily_batch_summary() -> None:
    """
    Generate a daily audit summary of batch activity for the previous 24 hours.
    Runs at 06:00 UTC daily.

    Writes one summary AuditEvent so the daily state is permanently recorded
    in the audit trail (supports ALCOA+ Enduring / Available).
    """
    start = _utcnow() - timedelta(hours=24)

    async with async_session_factory() as session:
        try:
            result = await session.execute(
                select(BatchRecord).where(BatchRecord.created_at >= start)
            )
            batches = result.scalars().all()

            started = sum(1 for b in batches if b.status == "in_progress")
            completed = sum(1 for b in batches if b.status == "completed")
            released = sum(1 for b in batches if b.status == "released")
            rejected = sum(1 for b in batches if b.status == "rejected")

            summary = (
                f"Daily MES summary ({start.date()} to {_utcnow().date()}): "
                f"started={started}, completed={completed}, "
                f"released={released}, rejected={rejected}, "
                f"total={len(batches)}"
            )
            logger.info(summary)

            if batches:
                await AuditService.log(
                    session,
                    action="SUMMARY",
                    record_type="batch_record",
                    record_id="system",
                    module="mes",
                    human_description=summary,
                    user_id=None,
                    username=_SYSTEM_USERNAME,
                    full_name=_SYSTEM_FULL_NAME,
                    ip_address=None,
                    is_system_action=True,
                )
                await session.commit()

        except Exception as exc:
            await session.rollback()
            logger.error("daily_batch_summary failed: %s", exc, exc_info=True)
