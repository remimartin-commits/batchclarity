"""Training API — delegates to app.modules.training.services."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.auth.dependencies import get_current_user, get_client_ip
from app.core.auth.models import User
from app.modules.training import services as training_services
from app.modules.training.schemas import (
    CurriculumCreate,
    CurriculumOut,
    CurriculumDetailOut,
    TrainingAssignmentCreate,
    TrainingAssignmentOut,
    TrainingCompletionCreate,
    TrainingCompletionOut,
    ReadAndUnderstoodRequest,
)

router = APIRouter(prefix="/training", tags=["Training Management"])


@router.post("/curricula", response_model=CurriculumOut, status_code=201)
async def create_curriculum(
    body: CurriculumCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await training_services.create_curriculum(
        db, body, current_user, get_client_ip(request)
    )


@router.get("/curricula", response_model=list[CurriculumOut])
async def list_curricula(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await training_services.list_curricula_public(db, skip=skip, limit=limit)


@router.get("/curricula/{curriculum_id}", response_model=CurriculumDetailOut)
async def get_curriculum(
    curriculum_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await training_services.get_curriculum_detail(db, curriculum_id)


@router.post("/assignments", response_model=TrainingAssignmentOut, status_code=201)
async def create_assignment(
    body: TrainingAssignmentCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await training_services.create_single_assignment(
        db, body, current_user, get_client_ip(request)
    )


@router.get("/assignments/my", response_model=list[TrainingAssignmentOut])
async def my_assignments(
    status_filter: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await training_services.list_my_assignments(
        db, str(current_user.id), status_filter
    )


@router.get("/assignments", response_model=list[TrainingAssignmentOut])
async def list_assignments(
    user_id: str | None = None,
    status_filter: str | None = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await training_services.list_assignments_unscoped(
        db,
        user_id=user_id,
        status_filter=status_filter,
        skip=skip,
        limit=limit,
    )


@router.get("/assignments/{assignment_id}", response_model=TrainingAssignmentOut)
async def get_assignment(
    assignment_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await training_services.get_assignment_by_id(db, assignment_id)


@router.post("/assignments/{assignment_id}/complete", response_model=TrainingCompletionOut)
async def complete_assignment(
    assignment_id: str,
    body: TrainingCompletionCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await training_services.complete_assignment_simple(
        db, assignment_id, body, current_user, get_client_ip(request)
    )


@router.post("/assignments/{assignment_id}/read-and-understood")
async def read_and_understood(
    assignment_id: str,
    body: ReadAndUnderstoodRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await training_services.read_and_understood_sign_off(
        db, assignment_id, body, current_user, get_client_ip(request)
    )
