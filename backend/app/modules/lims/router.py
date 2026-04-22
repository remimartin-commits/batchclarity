"""LIMS API — delegates to app.modules.lims.services."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.auth.dependencies import get_current_user, get_client_ip
from app.core.auth.models import User
from app.modules.lims import services as lims_services
from app.modules.lims.schemas import (
    SampleCreate,
    SampleOut,
    TestResultCreate,
    TestResultOut,
    TestResultReviewRequest,
    OOSInvestigationOut,
    SpecificationCreate,
    SpecificationOut,
)

router = APIRouter(prefix="/lims", tags=["LIMS"])


@router.post("/specifications", response_model=SpecificationOut, status_code=201)
async def create_specification(
    body: SpecificationCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await lims_services.create_specification(
        db, body, current_user, get_client_ip(request)
    )


@router.get("/specifications", response_model=list[SpecificationOut])
async def list_specifications(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await lims_services.list_specifications(db, skip=skip, limit=limit)


@router.post("/samples", response_model=SampleOut, status_code=201)
async def create_sample(
    body: SampleCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await lims_services.create_sample(
        db, body, current_user, get_client_ip(request)
    )


@router.get("/samples", response_model=list[SampleOut])
async def list_samples(
    status_filter: str | None = None,
    sample_type: str | None = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await lims_services.list_samples(
        db,
        site_id=None,
        status_filter=status_filter,
        sample_type=sample_type,
        skip=skip,
        limit=limit,
    )


@router.get("/samples/{sample_id}", response_model=SampleOut)
async def get_sample(
    sample_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await lims_services.get_sample_or_404(db, sample_id)


@router.post("/samples/{sample_id}/results", response_model=TestResultOut, status_code=201)
async def enter_result(
    sample_id: str,
    body: TestResultCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await lims_services.record_test_result(
        db, sample_id, body, current_user, get_client_ip(request)
    )


@router.get("/samples/{sample_id}/results", response_model=list[TestResultOut])
async def list_results(
    sample_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await lims_services.list_test_results_for_sample(db, sample_id)


@router.post("/results/{result_id}/review")
async def review_result(
    result_id: str,
    body: TestResultReviewRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await lims_services.review_test_result(
        db, result_id, body, current_user, get_client_ip(request)
    )


@router.get("/oos-investigations", response_model=list[OOSInvestigationOut])
async def list_oos_investigations(
    status_filter: str | None = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await lims_services.list_oos_investigations(
        db, status_filter=status_filter, skip=skip, limit=limit
    )
