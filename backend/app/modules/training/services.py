"""
Training module — curricula, bulk assignment, e-sig completion, overdue metrics.

E-signature is required for training completion (read-and-understood) per 21 CFR Part 11.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.audit.service import AuditService
from app.core.auth.models import User
from app.core.esig.service import ESignatureService
from app.modules.training.models import (
    CurriculumItem,
    TrainingAssignment,
    TrainingCompletion,
    TrainingCurriculum,
)
from app.modules.training.schemas import (
    CurriculumCreate,
    TrainingCompletionRequest,
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _clamp_page_size(page_size: int) -> int:
    return max(1, min(100, page_size))


def _offset(page: int, page_size: int) -> int:
    p = max(1, page)
    return (p - 1) * _clamp_page_size(page_size)


def _require_user_site_id(user: User) -> str:
    if not user.site_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not associated with a site_id.",
        )
    return str(user.site_id)


# ── Curricula ────────────────────────────────────────────────────────────────


async def create_curriculum(
    db: AsyncSession,
    data: CurriculumCreate,
    user: User,
    ip_address: Optional[str],
) -> TrainingCurriculum:
    existing = await db.execute(
        select(TrainingCurriculum).where(TrainingCurriculum.code == data.code)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Curriculum code '{data.code}' already exists.",
        )

    curriculum = TrainingCurriculum(
        name=data.name,
        code=data.code,
        description=data.description,
        target_roles=data.target_roles,
        target_departments=data.target_departments,
        is_gmp_mandatory=data.is_gmp_mandatory,
        site_id=data.site_id,
    )
    db.add(curriculum)
    await db.flush([curriculum])

    for item_data in data.items:
        item = CurriculumItem(
            curriculum_id=curriculum.id,
            **item_data.model_dump(),
        )
        db.add(item)

    await AuditService.log(
        db,
        action="CREATE",
        record_type="training_curriculum",
        record_id=curriculum.id,
        module="training",
        human_description=f"Training curriculum '{data.name}' ({data.code}) created",
        user_id=str(user.id),
        username=user.username,
        full_name=user.full_name,
        ip_address=ip_address,
        site_id=data.site_id,
    )
    await db.commit()
    await db.refresh(curriculum)
    return curriculum


# ── Assignments ──────────────────────────────────────────────────────────────


async def _get_curriculum_for_site(
    db: AsyncSession, curriculum_id: str, site_id: str
) -> TrainingCurriculum:
    result = await db.execute(
        select(TrainingCurriculum)
        .where(
            TrainingCurriculum.id == curriculum_id,
            TrainingCurriculum.site_id == site_id,
        )
        .options(selectinload(TrainingCurriculum.items))
    )
    curriculum = result.scalar_one_or_none()
    if not curriculum:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Curriculum not found for this site.",
        )
    return curriculum


async def assign_training(
    db: AsyncSession,
    curriculum_id: str,
    user_ids: list[str],
    due_date: Optional[datetime],
    user: User,
    ip_address: Optional[str],
) -> list[TrainingAssignment]:
    site_id = _require_user_site_id(user)
    curriculum = await _get_curriculum_for_site(db, curriculum_id, site_id)

    if not curriculum.items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Curriculum has no items to assign.",
        )

    unique_users = list(dict.fromkeys(user_ids))
    if not unique_users:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="user_ids must not be empty.",
        )

    created: list[TrainingAssignment] = []
    assigned_at = _utcnow()

    for item in sorted(curriculum.items, key=lambda i: (i.sequence, i.id)):
        for target_uid in unique_users:
            dupe = await db.execute(
                select(TrainingAssignment.id).where(
                    TrainingAssignment.user_id == target_uid,
                    TrainingAssignment.curriculum_item_id == item.id,
                )
            )
            if dupe.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        f"Assignment already exists for user {target_uid} "
                        f"and curriculum item {item.id}."
                    ),
                )
            a = TrainingAssignment(
                user_id=target_uid,
                curriculum_item_id=item.id,
                assigned_by_id=str(user.id),
                assigned_at=assigned_at,
                due_date=due_date,
                status="pending",
            )
            db.add(a)
            created.append(a)

    await db.flush()

    await AuditService.log(
        db,
        action="CREATE",
        record_type="training_curriculum",
        record_id=curriculum.id,
        module="training",
        human_description=(
            f"Bulk training assign: {len(created)} assignment(s) for curriculum {curriculum.code}"
        ),
        user_id=str(user.id),
        username=user.username,
        full_name=user.full_name,
        ip_address=ip_address,
        site_id=site_id,
        record_snapshot_after={
            "curriculum_id": curriculum_id,
            "user_count": len(unique_users),
            "assignments_created": len(created),
        },
    )
    await db.commit()
    for a in created:
        await db.refresh(a)
    return created


# ── Completion (e-sig) ───────────────────────────────────────────────────────


async def complete_training(
    db: AsyncSession,
    assignment_id: str,
    data: TrainingCompletionRequest,
    user: User,
    ip_address: Optional[str],
) -> TrainingCompletion:
    result = await db.execute(
        select(TrainingAssignment)
        .where(TrainingAssignment.id == assignment_id)
        .options(
            selectinload(TrainingAssignment.completion),
        )
    )
    assignment = result.scalar_one_or_none()
    if not assignment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found.")
    if assignment.user_id != str(user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only complete your own assignments.",
        )
    if assignment.completion is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assignment already completed.",
        )

    item_result = await db.execute(
        select(CurriculumItem).where(CurriculumItem.id == assignment.curriculum_item_id)
    )
    item = item_result.scalar_one_or_none()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Curriculum item for assignment is missing.",
        )

    now = _utcnow()
    expires: datetime | None = None
    if item.validity_period_months:
        expires = now + timedelta(days=item.validity_period_months * 30)

    ip = ip_address or "127.0.0.1"
    sig = await ESignatureService.sign(
        db,
        user_id=str(user.id),
        password=data.password,
        record_type="training_assignment",
        record_id=assignment_id,
        record_version="1.0",
        record_data={
            "assignment_id": assignment_id,
            "curriculum_item_id": assignment.curriculum_item_id,
            "completion_method": data.completion_method,
            "passed": data.passed,
        },
        meaning="read_and_understood",
        meaning_display="Read and Understood (training completed)",
        ip_address=ip,
        comments=data.notes,
    )

    cr_res = await db.execute(
        select(TrainingCurriculum).where(TrainingCurriculum.id == item.curriculum_id)
    )
    cur_for_site = cr_res.scalar_one_or_none()
    site_for_audit = cur_for_site.site_id if cur_for_site else None

    completion = TrainingCompletion(
        assignment_id=assignment_id,
        completed_at=now,
        completion_method=data.completion_method,
        assessment_score=data.assessment_score,
        passed=data.passed,
        expires_at=expires,
        signature_id=sig.id,
        notes=data.notes,
    )
    db.add(completion)
    assignment.status = "completed" if data.passed else "pending"

    await db.flush([completion])

    await AuditService.log(
        db,
        action="TRAINING_COMPLETED",
        record_type="training_assignment",
        record_id=assignment_id,
        module="training",
        human_description=(
            f"Training completed (read-and-understood) for assignment {assignment_id} — passed={data.passed}"
        ),
        user_id=str(user.id),
        username=user.username,
        full_name=user.full_name,
        ip_address=ip_address,
        site_id=site_for_audit,
        record_snapshot_after={
            "meaning": "read_and_understood",
            "passed": data.passed,
            "signature_id": str(sig.id),
        },
    )
    await db.commit()
    await db.refresh(completion)
    return completion


# ── Lists / reporting ────────────────────────────────────────────────────────


async def list_assignments(
    db: AsyncSession,
    site_id: str,
    user_id: Optional[str],
    status_filter: Optional[str],
    page: int = 1,
    page_size: int = 20,
) -> list[TrainingAssignment]:
    ps = _clamp_page_size(page_size)
    off = _offset(page, ps)
    q = (
        select(TrainingAssignment)
        .join(CurriculumItem, TrainingAssignment.curriculum_item_id == CurriculumItem.id)
        .join(TrainingCurriculum, CurriculumItem.curriculum_id == TrainingCurriculum.id)
        .where(TrainingCurriculum.site_id == site_id)
    )
    if user_id:
        q = q.where(TrainingAssignment.user_id == user_id)
    if status_filter:
        q = q.where(TrainingAssignment.status == status_filter)
    q = q.order_by(TrainingAssignment.due_date.asc().nulls_last()).offset(off).limit(ps)
    result = await db.execute(q)
    return list(result.scalars().all())


async def get_overdue_count(db: AsyncSession, site_id: str) -> int:
    now = _utcnow()
    q = (
        select(func.count())
        .select_from(TrainingAssignment)
        .join(CurriculumItem, TrainingAssignment.curriculum_item_id == CurriculumItem.id)
        .join(TrainingCurriculum, CurriculumItem.curriculum_id == TrainingCurriculum.id)
        .where(
            TrainingCurriculum.site_id == site_id,
            TrainingAssignment.status == "pending",
            TrainingAssignment.due_date.is_not(None),
            TrainingAssignment.due_date < now,
        )
    )
    c = await db.execute(q)
    return int(c.scalar() or 0)