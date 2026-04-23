"""QMS API — CAPA, Deviations, Change Control. Delegates to services.py."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.auth.dependencies import get_current_user, get_client_ip
from app.core.auth.models import User
from app.modules.qms import services as qms_services
from app.modules.qms.schemas import (
    CAPACreate, CAPAOut, CAPAUpdate, CAPASignRequest,
    CAPAActionCreate, CAPAActionOut, CAPAActionUpdate, CAPAAuditEventOut,
    DeviationCreate, DeviationOut, DeviationUpdate, DeviationAuditEventOut,
    ChangeControlCreate, ChangeControlOut, ChangeControlUpdate,
)

router = APIRouter(prefix="/qms", tags=["QMS"])


# ── CAPA ────────────────────────────────────────────────────────────────────

@router.post("/capas", response_model=CAPAOut, status_code=201)
async def create_capa(
    body: CAPACreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await qms_services.create_capa(db, body, current_user, get_client_ip(request))


@router.get("/capas", response_model=list[CAPAOut])
async def list_capas(
    status_filter: str | None = None,
    risk_level: str | None = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await qms_services.list_capas(
        db, status_filter=status_filter, risk_level=risk_level, skip=skip, limit=limit
    )


@router.get("/capas/{capa_id}", response_model=CAPAOut)
async def get_capa(
    capa_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await qms_services.get_capa_or_404(db, capa_id)


@router.patch("/capas/{capa_id}", response_model=CAPAOut)
async def update_capa(
    capa_id: str,
    body: CAPAUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await qms_services.update_capa(
        db, capa_id, body, current_user, get_client_ip(request)
    )


@router.post("/capas/{capa_id}/sign")
async def sign_capa(
    capa_id: str,
    body: CAPASignRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await qms_services.sign_capa(
        db, capa_id, body, current_user, get_client_ip(request)
    )


@router.post("/capas/{capa_id}/actions", status_code=201)
async def add_capa_action(
    capa_id: str,
    body: CAPAActionCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await qms_services.add_capa_action(
        db, capa_id, body, current_user, get_client_ip(request)
    )


@router.patch("/capas/{capa_id}/actions/{action_id}", response_model=CAPAActionOut)
async def update_capa_action(
    capa_id: str,
    action_id: str,
    body: CAPAActionUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await qms_services.update_capa_action(
        db, capa_id, action_id, body.model_dump(exclude_none=True), current_user, get_client_ip(request)
    )


@router.get("/capas/{capa_id}/audit-trail", response_model=list[CAPAAuditEventOut])
async def list_capa_audit_trail(
    capa_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await qms_services.list_capa_audit_events(db, capa_id)


# ── Deviations ──────────────────────────────────────────────────────────────

@router.post("/deviations", response_model=DeviationOut, status_code=201)
async def create_deviation(
    body: DeviationCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await qms_services.create_deviation(
        db, body, current_user, get_client_ip(request)
    )


@router.get("/deviations", response_model=list[DeviationOut])
async def list_deviations(
    status_filter: str | None = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await qms_services.list_deviations(
        db, status_filter=status_filter, skip=skip, limit=limit
    )


@router.get("/deviations/{deviation_id}", response_model=DeviationOut)
async def get_deviation(
    deviation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await qms_services.get_deviation_or_404(db, deviation_id)


@router.patch("/deviations/{deviation_id}", response_model=DeviationOut)
async def update_deviation(
    deviation_id: str,
    body: DeviationUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await qms_services.update_deviation(
        db, deviation_id, body, current_user, get_client_ip(request)
    )


@router.post("/deviations/{deviation_id}/sign")
async def sign_deviation(
    deviation_id: str,
    body: CAPASignRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await qms_services.sign_deviation(
        db, deviation_id, body, current_user, get_client_ip(request)
    )


@router.post("/deviations/{deviation_id}/{action}", response_model=DeviationOut)
async def transition_deviation(
    deviation_id: str,
    action: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await qms_services.transition_deviation(
        db, deviation_id, action, current_user, get_client_ip(request)
    )


@router.get("/deviations/{deviation_id}/audit-trail", response_model=list[DeviationAuditEventOut])
async def list_deviation_audit_trail(
    deviation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await qms_services.list_deviation_audit_events(db, deviation_id)


# ── Change control ─────────────────────────────────────────────────────────

@router.post("/change-controls", response_model=ChangeControlOut, status_code=201)
async def create_change_control(
    body: ChangeControlCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await qms_services.create_change_control(
        db, body, current_user, get_client_ip(request)
    )


@router.get("/change-controls", response_model=list[ChangeControlOut])
async def list_change_controls(
    status_filter: str | None = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await qms_services.list_change_controls(
        db, status_filter=status_filter, skip=skip, limit=limit
    )


@router.get("/change-controls/{cc_id}", response_model=ChangeControlOut)
async def get_change_control(
    cc_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await qms_services.get_change_control_or_404(db, cc_id)


@router.patch("/change-controls/{cc_id}", response_model=ChangeControlOut)
async def update_change_control(
    cc_id: str,
    body: ChangeControlUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await qms_services.update_change_control(
        db, cc_id, body, current_user, get_client_ip(request)
    )


@router.post("/change-controls/{cc_id}/sign")
async def sign_change_control(
    cc_id: str,
    body: CAPASignRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await qms_services.sign_change_control(
        db, cc_id, body, current_user, get_client_ip(request)
    )


@router.post("/change-controls/{cc_id}/{action}", response_model=ChangeControlOut)
async def transition_change_control(
    cc_id: str,
    action: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await qms_services.transition_change_control(
        db, cc_id, action, current_user, get_client_ip(request)
    )
