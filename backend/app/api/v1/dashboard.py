"""Aggregated dashboard counts and action items."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.documents.models import DocumentVersion
from app.core.auth.dependencies import get_current_user
from app.core.auth.models import User
from app.core.database import get_db
from app.modules.equipment.models import CalibrationRecord, Equipment
from app.modules.lims.models import OOSInvestigation
from app.modules.mes.models import BatchRecord
from app.modules.qms.models import CAPA, ChangeControl, Deviation
from app.modules.training.models import TrainingAssignment

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

CLOSED_STATUSES = ("closed", "completed", "cancelled")
OPEN_CC_STATUSES = ("draft", "under_review", "approved", "approved_pending", "in_implementation", "effectiveness_review")


class DashboardActionItem(BaseModel):
    id: str
    type: str
    title: str
    due_date: datetime | None = None
    module: str
    record_id: str


class DashboardSummaryOut(BaseModel):
    open_capas: int = Field(ge=0)
    overdue_capas: int = Field(ge=0)
    open_deviations: int = Field(ge=0)
    overdue_deviations: int = Field(ge=0)
    pending_change_controls: int = Field(ge=0)
    calibrations_due_30_days: int = Field(ge=0)
    calibrations_overdue: int = Field(ge=0)
    open_oos_investigations: int = Field(ge=0)
    documents_expiring_60_days: int = Field(ge=0)
    training_overdue: int = Field(ge=0)
    pending_my_signatures: int = Field(ge=0)
    pending_my_actions: list[DashboardActionItem] = []


@router.get("/summary", response_model=DashboardSummaryOut)
async def get_dashboard_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DashboardSummaryOut:
    """
    Return site-scoped KPI counters and current-user actions.
    """
    now = datetime.now(timezone.utc)
    due_30 = now + timedelta(days=30)
    due_60 = now + timedelta(days=60)
    overdue_cutoff = now - timedelta(days=7)
    site_id = str(current_user.site_id) if current_user.site_id else "default"
    user_id = str(current_user.id)

    open_capas_q = select(func.count(CAPA.id)).where(
        CAPA.site_id == site_id,
        CAPA.current_status.notin_(CLOSED_STATUSES),
    )
    overdue_capas_q = select(func.count(CAPA.id)).where(
        CAPA.site_id == site_id,
        CAPA.target_completion_date.is_not(None),
        CAPA.target_completion_date < now,
        CAPA.current_status.notin_(CLOSED_STATUSES),
    )

    open_deviations_q = select(func.count(Deviation.id)).where(
        Deviation.site_id == site_id,
        Deviation.current_status.notin_(CLOSED_STATUSES),
    )
    overdue_deviations_q = select(func.count(Deviation.id)).where(
        Deviation.site_id == site_id,
        Deviation.current_status.notin_(CLOSED_STATUSES),
        Deviation.detection_date < overdue_cutoff,
    )

    pending_cc_q = select(func.count(ChangeControl.id)).where(
        ChangeControl.site_id == site_id,
        ChangeControl.current_status.in_(OPEN_CC_STATUSES),
    )

    calib_due_30_q = (
        select(func.count(CalibrationRecord.id))
        .select_from(CalibrationRecord)
        .join(Equipment, CalibrationRecord.equipment_id == Equipment.id)
        .where(
            Equipment.site_id == site_id,
            CalibrationRecord.next_calibration_due.is_not(None),
            CalibrationRecord.next_calibration_due >= now,
            CalibrationRecord.next_calibration_due <= due_30,
        )
    )
    calib_overdue_q = (
        select(func.count(CalibrationRecord.id))
        .select_from(CalibrationRecord)
        .join(Equipment, CalibrationRecord.equipment_id == Equipment.id)
        .where(
            Equipment.site_id == site_id,
            CalibrationRecord.next_calibration_due.is_not(None),
            CalibrationRecord.next_calibration_due < now,
        )
    )

    open_oos_q = select(func.count(OOSInvestigation.id)).where(
        OOSInvestigation.status.notin_(("closed", "disposed")),
    )

    docs_exp_60_q = (
        select(func.count(DocumentVersion.id))
        .select_from(DocumentVersion)
        .join(DocumentVersion.document)
        .where(
            DocumentVersion.status == "effective",
            DocumentVersion.next_review_date.is_not(None),
            DocumentVersion.next_review_date >= now,
            DocumentVersion.next_review_date <= due_60,
            DocumentVersion.document.has(site_id=site_id),
        )
    )

    training_overdue_q = select(func.count(TrainingAssignment.id)).where(
        TrainingAssignment.user_id == user_id,
        TrainingAssignment.status == "overdue",
    )

    pending_my_signatures_q = (
        select(func.count(CAPA.id))
        .where(CAPA.owner_id == user_id, CAPA.current_status == "effectiveness_check")
    )
    pending_my_signatures_q2 = (
        select(func.count(Deviation.id))
        .where(Deviation.owner_id == user_id, Deviation.current_status == "pending_approval")
    )
    pending_my_signatures_q3 = (
        select(func.count(ChangeControl.id))
        .where(
            ChangeControl.owner_id == user_id,
            ChangeControl.current_status.in_(("under_review", "effectiveness_review")),
        )
    )

    # Action panel rows
    my_capa_actions_q = (
        select(CAPA.id, CAPA.capa_number, CAPA.target_completion_date)
        .where(CAPA.owner_id == user_id, CAPA.current_status.notin_(CLOSED_STATUSES))
        .order_by(CAPA.target_completion_date.asc().nulls_last())
        .limit(4)
    )
    my_training_actions_q = (
        select(TrainingAssignment.id, TrainingAssignment.due_date)
        .where(TrainingAssignment.user_id == user_id, TrainingAssignment.status.in_(("pending", "overdue", "in_progress")))
        .order_by(TrainingAssignment.due_date.asc().nulls_last())
        .limit(4)
    )

    r_open_capas = await db.execute(open_capas_q)
    r_overdue_capas = await db.execute(overdue_capas_q)
    r_open_dev = await db.execute(open_deviations_q)
    r_overdue_dev = await db.execute(overdue_deviations_q)
    r_pending_cc = await db.execute(pending_cc_q)
    r_cal_due_30 = await db.execute(calib_due_30_q)
    r_cal_overdue = await db.execute(calib_overdue_q)
    r_oos = await db.execute(open_oos_q)
    r_doc_exp = await db.execute(docs_exp_60_q)
    r_training_overdue = await db.execute(training_overdue_q)
    r_sig_1 = await db.execute(pending_my_signatures_q)
    r_sig_2 = await db.execute(pending_my_signatures_q2)
    r_sig_3 = await db.execute(pending_my_signatures_q3)

    capa_actions = (await db.execute(my_capa_actions_q)).all()
    training_actions = (await db.execute(my_training_actions_q)).all()
    pending_actions: list[DashboardActionItem] = []
    for row in capa_actions:
        pending_actions.append(
            DashboardActionItem(
                id=f"capa-{row.id}",
                type="action",
                title=f"Review CAPA {row.capa_number}",
                due_date=row.target_completion_date,
                module="qms",
                record_id=row.id,
            )
        )
    for row in training_actions:
        pending_actions.append(
            DashboardActionItem(
                id=f"training-{row.id}",
                type="training",
                title="Complete training assignment",
                due_date=row.due_date,
                module="training",
                record_id=row.id,
            )
        )

    return DashboardSummaryOut(
        open_capas=int(r_open_capas.scalar() or 0),
        overdue_capas=int(r_overdue_capas.scalar() or 0),
        open_deviations=int(r_open_dev.scalar() or 0),
        overdue_deviations=int(r_overdue_dev.scalar() or 0),
        pending_change_controls=int(r_pending_cc.scalar() or 0),
        calibrations_due_30_days=int(r_cal_due_30.scalar() or 0),
        calibrations_overdue=int(r_cal_overdue.scalar() or 0),
        open_oos_investigations=int(r_oos.scalar() or 0),
        documents_expiring_60_days=int(r_doc_exp.scalar() or 0),
        training_overdue=int(r_training_overdue.scalar() or 0),
        pending_my_signatures=(
            int(r_sig_1.scalar() or 0)
            + int(r_sig_2.scalar() or 0)
            + int(r_sig_3.scalar() or 0)
        ),
        pending_my_actions=pending_actions,
    )
