"""Training Management API — Curricula, Assignments, Completions, Read & Understood."""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone, timedelta
from app.core.database import get_db
from app.core.auth.dependencies import get_current_user, get_client_ip
from app.core.auth.models import User
from app.core.audit.service import AuditService
from app.core.esig.service import ESignatureService
from app.modules.training.models import (
    TrainingCurriculum, CurriculumItem, TrainingAssignment, TrainingCompletion,
)
from app.modules.training.schemas import (
    CurriculumCreate, CurriculumOut, CurriculumDetailOut,
    TrainingAssignmentCreate, TrainingAssignmentOut,
    TrainingCompletionCreate, TrainingCompletionOut,
    ReadAndUnderstoodRequest,
)

router = APIRouter(prefix="/training", tags=["Training Management"])


# ── Curricula ─────────────────────────────────────────────────────────────────

@router.post("/curricula", response_model=CurriculumOut, status_code=201)
async def create_curriculum(
    body: CurriculumCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(
        select(TrainingCurriculum).where(TrainingCurriculum.code == body.code)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"Curriculum code '{body.code}' already exists.")

    curriculum = TrainingCurriculum(
        name=body.name,
        code=body.code,
        description=body.description,
        target_roles=body.target_roles,
        target_departments=body.target_departments,
        is_gmp_mandatory=body.is_gmp_mandatory,
        site_id=body.site_id,
    )
    db.add(curriculum)
    await db.flush([curriculum])

    for item_data in body.items:
        item = CurriculumItem(curriculum_id=curriculum.id, **item_data.model_dump())
        db.add(item)

    await AuditService.log(
        db, action="CREATE", record_type="training_curriculum", record_id=curriculum.id,
        module="training",
        human_description=f"Training curriculum '{body.name}' ({body.code}) created",
        user_id=current_user.id, username=current_user.username,
        full_name=current_user.full_name, ip_address=get_client_ip(request),
    )
    await db.refresh(curriculum)
    return curriculum


@router.get("/curricula", response_model=list[CurriculumOut])
async def list_curricula(
    skip: int = 0, limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(TrainingCurriculum).where(TrainingCurriculum.is_active == True)
        .order_by(TrainingCurriculum.name).offset(skip).limit(limit)
    )
    return result.scalars().all()


@router.get("/curricula/{curriculum_id}", response_model=CurriculumDetailOut)
async def get_curriculum(
    curriculum_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(TrainingCurriculum).where(TrainingCurriculum.id == curriculum_id))
    curriculum = result.scalar_one_or_none()
    if not curriculum:
        raise HTTPException(status_code=404, detail="Curriculum not found.")
    return curriculum


# ── Assignments ───────────────────────────────────────────────────────────────

@router.post("/assignments", response_model=TrainingAssignmentOut, status_code=201)
async def create_assignment(
    body: TrainingAssignmentCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Check item exists
    item_result = await db.execute(
        select(CurriculumItem).where(CurriculumItem.id == body.curriculum_item_id)
    )
    if not item_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Curriculum item not found.")

    assignment = TrainingAssignment(
        user_id=body.user_id,
        curriculum_item_id=body.curriculum_item_id,
        assigned_by_id=current_user.id,
        assigned_at=datetime.now(timezone.utc),
        due_date=body.due_date,
        status="pending",
    )
    db.add(assignment)
    await db.flush([assignment])

    await AuditService.log(
        db, action="CREATE", record_type="training_assignment", record_id=assignment.id,
        module="training",
        human_description=f"Training assignment created for user {body.user_id}",
        user_id=current_user.id, username=current_user.username,
        full_name=current_user.full_name, ip_address=get_client_ip(request),
    )
    await db.refresh(assignment)
    return assignment


@router.get("/assignments/my", response_model=list[TrainingAssignmentOut])
async def my_assignments(
    status_filter: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Returns the current user's training assignments."""
    query = select(TrainingAssignment).where(TrainingAssignment.user_id == current_user.id)
    if status_filter:
        query = query.where(TrainingAssignment.status == status_filter)
    result = await db.execute(query.order_by(TrainingAssignment.due_date))
    return result.scalars().all()


@router.get("/assignments", response_model=list[TrainingAssignmentOut])
async def list_assignments(
    user_id: str | None = None,
    status_filter: str | None = None,
    skip: int = 0, limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(TrainingAssignment)
    if user_id:
        query = query.where(TrainingAssignment.user_id == user_id)
    if status_filter:
        query = query.where(TrainingAssignment.status == status_filter)
    result = await db.execute(query.order_by(TrainingAssignment.due_date).offset(skip).limit(limit))
    return result.scalars().all()


@router.get("/assignments/{assignment_id}", response_model=TrainingAssignmentOut)
async def get_assignment(
    assignment_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(TrainingAssignment).where(TrainingAssignment.id == assignment_id))
    assignment = result.scalar_one_or_none()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found.")
    return assignment


# ── Completion ────────────────────────────────────────────────────────────────

@router.post("/assignments/{assignment_id}/complete", response_model=TrainingCompletionOut)
async def complete_assignment(
    assignment_id: str,
    body: TrainingCompletionCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(TrainingAssignment).where(TrainingAssignment.id == assignment_id)
    )
    assignment = result.scalar_one_or_none()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found.")

    if assignment.completion:
        raise HTTPException(status_code=400, detail="Assignment already completed.")
    if assignment.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only complete your own assignments.")

    item_result = await db.execute(
        select(CurriculumItem).where(CurriculumItem.id == assignment.curriculum_item_id)
    )
    item = item_result.scalar_one_or_none()

    now = datetime.now(timezone.utc)
    expires = None
    if item and item.validity_period_months:
        expires = now + timedelta(days=item.validity_period_months * 30)

    completion = TrainingCompletion(
        assignment_id=assignment_id,
        completed_at=now,
        completion_method=body.completion_method,
        assessment_score=body.assessment_score,
        passed=body.passed,
        expires_at=expires,
        notes=body.notes,
    )
    db.add(completion)
    assignment.status = "completed" if body.passed else "pending"

    await AuditService.log(
        db, action="UPDATE", record_type="training_assignment", record_id=assignment_id,
        module="training",
        human_description=f"Training assignment completed by {current_user.full_name} — {'PASSED' if body.passed else 'FAILED'}",
        user_id=current_user.id, username=current_user.username,
        full_name=current_user.full_name, ip_address=get_client_ip(request),
    )
    await db.flush([completion])
    await db.refresh(completion)
    return completion


@router.post("/assignments/{assignment_id}/read-and-understood")
async def read_and_understood(
    assignment_id: str,
    body: ReadAndUnderstoodRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Electronic sign-off that a user has read and understood an SOP.
    Requires password re-entry (21 CFR Part 11).
    """
    result = await db.execute(
        select(TrainingAssignment).where(TrainingAssignment.id == assignment_id)
    )
    assignment = result.scalar_one_or_none()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found.")
    if assignment.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only acknowledge your own assignments.")
    if assignment.completion:
        raise HTTPException(status_code=400, detail="Assignment already completed.")

    sig = await ESignatureService.sign(
        db,
        user_id=current_user.id,
        password=body.password,
        record_type="training_assignment",
        record_id=assignment_id,
        record_version="1.0",
        record_data={"assignment_id": assignment_id},
        meaning="acknowledged",
        meaning_display="Read and Understood",
        ip_address=get_client_ip(request),
        comments=body.notes,
    )

    now = datetime.now(timezone.utc)
    completion = TrainingCompletion(
        assignment_id=assignment_id,
        completed_at=now,
        completion_method="self_study",
        passed=True,
        signature_id=sig.id,
        notes=body.notes,
    )
    db.add(completion)
    assignment.status = "completed"

    return {
        "signature_id": sig.id,
        "signed_at": sig.signed_at,
        "message": "Read & Understood recorded with electronic signature.",
    }
