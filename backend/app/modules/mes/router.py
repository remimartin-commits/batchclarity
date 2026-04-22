"""MES API — delegates to app.modules.mes.services."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.auth.dependencies import get_current_user, get_client_ip
from app.core.auth.models import User
from app.modules.mes import services as mes_services
from app.modules.mes.schemas import (
    ProductCreate,
    ProductOut,
    MBRCreate,
    MBROut,
    MBRSignRequest,
    BatchRecordCreate,
    BatchRecordOut,
    BatchRecordStepExecute,
    BatchRecordStepOut,
    BatchReleaseRequest,
)

router = APIRouter(prefix="/mes", tags=["MES"])


@router.post("/products", response_model=ProductOut, status_code=201)
async def create_product(
    body: ProductCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await mes_services.create_product(
        db, body, current_user, get_client_ip(request)
    )


@router.get("/products", response_model=list[ProductOut])
async def list_products(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await mes_services.list_products(
        db, active_only=True, skip=skip, limit=limit
    )


@router.post("/mbrs", response_model=MBROut, status_code=201)
async def create_mbr(
    body: MBRCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await mes_services.create_mbr(db, body, current_user, get_client_ip(request))


@router.get("/mbrs", response_model=list[MBROut])
async def list_mbrs(
    product_id: str | None = None,
    status_filter: str | None = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await mes_services.list_mbrs(
        db, product_id=product_id, status_filter=status_filter, skip=skip, limit=limit
    )


@router.get("/mbrs/{mbr_id}", response_model=MBROut)
async def get_mbr(
    mbr_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await mes_services.get_mbr_or_404(db, mbr_id)


@router.post("/mbrs/{mbr_id}/sign")
async def sign_mbr(
    mbr_id: str,
    body: MBRSignRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await mes_services.sign_mbr(
        db, mbr_id, body, current_user, get_client_ip(request)
    )


@router.post("/batch-records", response_model=BatchRecordOut, status_code=201)
async def create_batch_record(
    body: BatchRecordCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await mes_services.create_batch_record(
        db, body, current_user, get_client_ip(request)
    )


@router.get("/batch-records", response_model=list[BatchRecordOut])
async def list_batch_records(
    status_filter: str | None = None,
    product_id: str | None = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await mes_services.list_batch_records(
        db, status_filter=status_filter, product_id=product_id, skip=skip, limit=limit
    )


@router.get("/batch-records/{br_id}", response_model=BatchRecordOut)
async def get_batch_record(
    br_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await mes_services.get_batch_record_or_404(db, br_id)


@router.patch(
    "/batch-records/{br_id}/steps/{step_id}", response_model=BatchRecordStepOut
)
async def execute_step(
    br_id: str,
    step_id: str,
    body: BatchRecordStepExecute,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await mes_services.execute_step(
        db, br_id, step_id, body, current_user, get_client_ip(request)
    )


@router.post("/batch-records/{br_id}/release")
async def release_batch(
    br_id: str,
    body: BatchReleaseRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await mes_services.release_batch(
        db, br_id, body, current_user, get_client_ip(request)
    )
