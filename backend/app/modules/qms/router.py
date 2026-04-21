from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import get_db
from app.core.auth.dependencies import get_current_user
from app.core.auth.models import User
from app.core.auth.service import AuthService
from app.core.audit.service import AuditService
from app.core.esig.service import ESignatureService
from app.modules.qms.models import CAPA, CAPAAction, Deviation, ChangeControl
from app.modules.qms.schemas import (
    CAPACreate, CAPAOut, CAPAUpdate, CAPASignRequest,
    CAPAActionCreate,
    DeviationCreate, DeviationOut, DeviationUpdate,
    ChangeControlCreate, ChangeControlOut, ChangeControlUpdate,
)
from datetime import datetime, timezone

router = APIRouter(prefix="/qms", tags=["QMS"])


def _next_number(prefix: str, sequence: int) -> str:
    year = datetime.now(timezone.utc).year
    return f"{prefix}-{year}-{sequence:04d}"


async def _require_permission(db: AsyncSession, user: User, permission_code: str) -> None:
    allowed = await AuthService.has_permission(db, str(user.id), permission_code)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Missing permission: {permission_code}",
        )


def _apply_transition(current_status: str, action: str, allowed: dict[str, tuple[str, str]]) -> str:
    if action not in allowed:
        raise HTTPException(status_code=400, detail=f"Unsupported transition action '{action}'.")
    from_state, next_status = allowed[action]
    if current_status != from_state:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid transition: action '{action}' requires state '{from_state}', current is '{current_status}'.",
        )
    if current_status == next_status:
        raise HTTPException(status_code=400, detail=f"Record is already in '{next_status}' state.")
    return next_status


# ── CAPA endpoints ────────────────────────────────────────────────────────────

@router.post("/capas", response_model=CAPAOut, status_code=status.HTTP_201_CREATED)
async def create_capa(
    body: CAPACreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    count_result = await db.execute(select(func.count()).select_from(CAPA))
    count = count_result.scalar() + 1

    capa = CAPA(
        capa_number=_next_number("CAPA", count),
        owner_id=str(current_user.id),
        site_id=str(current_user.site_id) if current_user.site_id else "default",
        **body.model_dump(exclude={"actions"}),
    )
    db.add(capa)
    await db.flush([capa])

    for i, action_data in enumerate(body.actions, start=1):
        action = CAPAAction(
            capa_id=capa.id,
            sequence_number=i,
            **action_data.model_dump(),
        )
        db.add(action)

    await AuditService.log(
        db,
        action="CREATE",
        record_type="capa",
        record_id=capa.id,
        module="qms",
        human_description=f"CAPA {capa.capa_number} created: {capa.title}",
        user_id=str(current_user.id),
        username=current_user.username,
        full_name=current_user.full_name,
        ip_address=request.client.host if request.client else None,
        record_snapshot_after={"capa_number": capa.capa_number, "title": capa.title},
    )

    await db.commit()
    await db.refresh(capa)
    return capa


@router.get("/capas", response_model=list[CAPAOut])
async def list_capas(
    status_filter: str | None = None,
    risk_level: str | None = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(CAPA)
    if status_filter:
        query = query.where(CAPA.current_status == status_filter)
    if risk_level:
        query = query.where(CAPA.risk_level == risk_level)
    query = query.order_by(CAPA.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/capas/{capa_id}", response_model=CAPAOut)
async def get_capa(
    capa_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(CAPA).where(CAPA.id == capa_id))
    capa = result.scalar_one_or_none()
    if not capa:
        raise HTTPException(status_code=404, detail="CAPA not found.")
    return capa


@router.patch("/capas/{capa_id}", response_model=CAPAOut)
async def update_capa(
    capa_id: str,
    body: CAPAUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(CAPA).where(CAPA.id == capa_id))
    capa = result.scalar_one_or_none()
    if not capa:
        raise HTTPException(status_code=404, detail="CAPA not found.")

    changes = body.model_dump(exclude_none=True)
    for field, new_val in changes.items():
        old_val = getattr(capa, field)
        setattr(capa, field, new_val)
        await AuditService.log_field_change(
            db,
            record_type="capa",
            record_id=capa_id,
            module="qms",
            field_name=field,
            old_value=str(old_val),
            new_value=str(new_val),
            user_id=str(current_user.id),
            username=current_user.username,
            full_name=current_user.full_name,
            ip_address=request.client.host if request.client else None,
        )

    await db.commit()
    await db.refresh(capa)
    return capa


@router.post("/capas/{capa_id}/sign")
async def sign_capa(
    capa_id: str,
    body: CAPASignRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(CAPA).where(CAPA.id == capa_id))
    capa = result.scalar_one_or_none()
    if not capa:
        raise HTTPException(status_code=404, detail="CAPA not found.")

    sig = await ESignatureService.sign(
        db,
        user_id=str(current_user.id),
        password=body.password,
        record_type="capa",
        record_id=capa_id,
        record_version="1.0",
        record_data={
            "id": str(capa.id),
            "capa_number": capa.capa_number,
            "status": capa.current_status,
        },
        meaning=body.meaning,
        meaning_display=body.meaning.replace("_", " ").title(),
        ip_address=request.client.host if request.client else "unknown",
        comments=body.comments,
    )

    status_map = {
        "reviewed": "under_review",
        "approved": "approved",
        "closed": "closed",
    }
    if body.meaning in status_map:
        capa.current_status = status_map[body.meaning]

    await db.commit()
    return {"signature_id": str(sig.id), "signed_at": sig.signed_at, "meaning": sig.meaning}


@router.post("/capas/{capa_id}/actions", status_code=201)
async def add_capa_action(
    capa_id: str,
    body: CAPAActionCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(CAPA).where(CAPA.id == capa_id))
    capa = result.scalar_one_or_none()
    if not capa:
        raise HTTPException(status_code=404, detail="CAPA not found.")

    count_result = await db.execute(
        select(func.count()).select_from(CAPAAction).where(CAPAAction.capa_id == capa_id)
    )
    next_seq = count_result.scalar() + 1

    action = CAPAAction(
        capa_id=capa_id,
        sequence_number=next_seq,
        **body.model_dump(),
    )
    db.add(action)

    await AuditService.log(
        db,
        action="CREATE",
        record_type="capa_action",
        record_id=capa_id,
        module="qms",
        human_description=f"Action #{next_seq} added to CAPA {capa.capa_number}: {body.description}",
        user_id=str(current_user.id),
        username=current_user.username,
        full_name=current_user.full_name,
        ip_address=request.client.host if request.client else None,
    )

    await db.commit()
    await db.refresh(action)
    return action


# ── Deviation endpoints ────────────────────────────────────────────────────────

@router.post("/deviations", response_model=DeviationOut, status_code=201)
async def create_deviation(
    body: DeviationCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    count_result = await db.execute(select(func.count()).select_from(Deviation))
    count = count_result.scalar() + 1

    deviation = Deviation(
        deviation_number=_next_number("DEV", count),
        detected_by_id=str(current_user.id),
        owner_id=str(current_user.id),
        site_id=str(current_user.site_id) if current_user.site_id else "default",
        **body.model_dump(),
    )
    db.add(deviation)
    await db.flush([deviation])

    await AuditService.log(
        db,
        action="CREATE",
        record_type="deviation",
        record_id=deviation.id,
        module="qms",
        human_description=f"Deviation {deviation.deviation_number} created",
        user_id=str(current_user.id),
        username=current_user.username,
        full_name=current_user.full_name,
        ip_address=request.client.host if request.client else None,
    )

    await db.commit()
    await db.refresh(deviation)
    return deviation


@router.get("/deviations", response_model=list[DeviationOut])
async def list_deviations(
    status_filter: str | None = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Deviation)
    if status_filter:
        query = query.where(Deviation.current_status == status_filter)
    query = query.order_by(Deviation.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/deviations/{deviation_id}", response_model=DeviationOut)
async def get_deviation(
    deviation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Deviation).where(Deviation.id == deviation_id))
    deviation = result.scalar_one_or_none()
    if not deviation:
        raise HTTPException(status_code=404, detail="Deviation not found.")
    return deviation


@router.patch("/deviations/{deviation_id}", response_model=DeviationOut)
async def update_deviation(
    deviation_id: str,
    body: DeviationUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Deviation).where(Deviation.id == deviation_id))
    deviation = result.scalar_one_or_none()
    if not deviation:
        raise HTTPException(status_code=404, detail="Deviation not found.")

    for field, new_val in body.model_dump(exclude_none=True).items():
        old_val = getattr(deviation, field, None)
        setattr(deviation, field, new_val)
        await AuditService.log_field_change(
            db,
            record_type="deviation",
            record_id=deviation_id,
            module="qms",
            field_name=field,
            old_value=str(old_val),
            new_value=str(new_val),
            user_id=str(current_user.id),
            username=current_user.username,
            full_name=current_user.full_name,
            ip_address=request.client.host if request.client else None,
        )

    await db.commit()
    await db.refresh(deviation)
    return deviation


@router.post("/deviations/{deviation_id}/sign")
async def sign_deviation(
    deviation_id: str,
    body: CAPASignRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Deviation).where(Deviation.id == deviation_id))
    deviation = result.scalar_one_or_none()
    if not deviation:
        raise HTTPException(status_code=404, detail="Deviation not found.")

    await _require_permission(db, current_user, "qms.deviations.sign")
    sig = await ESignatureService.sign(
        db,
        user_id=str(current_user.id),
        password=body.password,
        record_type="deviation",
        record_id=deviation_id,
        record_version="1.0",
        record_data={
            "id": str(deviation.id),
            "deviation_number": deviation.deviation_number,
            "status": deviation.current_status,
        },
        meaning=body.meaning,
        meaning_display=body.meaning.replace("_", " ").title(),
        ip_address=request.client.host if request.client else "unknown",
        comments=body.comments,
    )
    await db.commit()
    return {"signature_id": str(sig.id), "signed_at": sig.signed_at, "meaning": sig.meaning}


@router.post("/deviations/{deviation_id}/{action}")
async def transition_deviation(
    deviation_id: str,
    action: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    transitions = {
        "submit": ("qms.deviations.submit", "draft", "under_review"),
        "approve": ("qms.deviations.approve", "under_review", "approved"),
        "close": ("qms.deviations.close", "approved", "closed"),
    }
    if action not in transitions:
        raise HTTPException(status_code=404, detail="Transition action not found.")
    permission_code, from_state, next_state = transitions[action]
    await _require_permission(db, current_user, permission_code)

    result = await db.execute(select(Deviation).where(Deviation.id == deviation_id))
    deviation = result.scalar_one_or_none()
    if not deviation:
        raise HTTPException(status_code=404, detail="Deviation not found.")

    old_state = deviation.current_status
    deviation.current_status = _apply_transition(
        old_state,
        action,
        {k: (f, t) for k, (_p, f, t) in transitions.items()},
    )
    await AuditService.log(
        db,
        action="TRANSITION",
        record_type="deviation",
        record_id=deviation_id,
        module="qms",
        human_description=f"Deviation transitioned {old_state} -> {next_state} ({action})",
        user_id=str(current_user.id),
        username=current_user.username,
        full_name=current_user.full_name,
        ip_address=request.client.host if request.client else None,
        reason=f"action={action}",
    )
    await db.commit()
    await db.refresh(deviation)
    return deviation


# ── Change Control endpoints ──────────────────────────────────────────────────

@router.post("/change-controls", response_model=ChangeControlOut, status_code=201)
async def create_change_control(
    body: ChangeControlCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    count_result = await db.execute(select(func.count()).select_from(ChangeControl))
    count = count_result.scalar() + 1

    cc = ChangeControl(
        change_number=_next_number("CC", count),
        owner_id=str(current_user.id),
        site_id=str(current_user.site_id) if current_user.site_id else "default",
        **body.model_dump(),
    )
    db.add(cc)
    await db.flush([cc])

    await AuditService.log(
        db,
        action="CREATE",
        record_type="change_control",
        record_id=cc.id,
        module="qms",
        human_description=f"Change Control {cc.change_number} created: {cc.title}",
        user_id=str(current_user.id),
        username=current_user.username,
        full_name=current_user.full_name,
        ip_address=request.client.host if request.client else None,
    )

    await db.commit()
    await db.refresh(cc)
    return cc


@router.get("/change-controls", response_model=list[ChangeControlOut])
async def list_change_controls(
    status_filter: str | None = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(ChangeControl)
    if status_filter:
        query = query.where(ChangeControl.current_status == status_filter)
    query = query.order_by(ChangeControl.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/change-controls/{cc_id}", response_model=ChangeControlOut)
async def get_change_control(
    cc_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(ChangeControl).where(ChangeControl.id == cc_id))
    cc = result.scalar_one_or_none()
    if not cc:
        raise HTTPException(status_code=404, detail="Change control not found.")
    return cc


@router.patch("/change-controls/{cc_id}", response_model=ChangeControlOut)
async def update_change_control(
    cc_id: str,
    body: ChangeControlUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(ChangeControl).where(ChangeControl.id == cc_id))
    cc = result.scalar_one_or_none()
    if not cc:
        raise HTTPException(status_code=404, detail="Change control not found.")

    for field, new_val in body.model_dump(exclude_none=True).items():
        old_val = getattr(cc, field, None)
        setattr(cc, field, new_val)
        await AuditService.log_field_change(
            db,
            record_type="change_control",
            record_id=cc_id,
            module="qms",
            field_name=field,
            old_value=str(old_val),
            new_value=str(new_val),
            user_id=str(current_user.id),
            username=current_user.username,
            full_name=current_user.full_name,
            ip_address=request.client.host if request.client else None,
        )

    await db.commit()
    await db.refresh(cc)
    return cc


@router.post("/change-controls/{cc_id}/sign")
async def sign_change_control(
    cc_id: str,
    body: CAPASignRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(ChangeControl).where(ChangeControl.id == cc_id))
    cc = result.scalar_one_or_none()
    if not cc:
        raise HTTPException(status_code=404, detail="Change control not found.")

    await _require_permission(db, current_user, "qms.change_controls.sign")
    sig = await ESignatureService.sign(
        db,
        user_id=str(current_user.id),
        password=body.password,
        record_type="change_control",
        record_id=cc_id,
        record_version="1.0",
        record_data={
            "id": str(cc.id),
            "change_number": cc.change_number,
            "status": cc.current_status,
        },
        meaning=body.meaning,
        meaning_display=body.meaning.replace("_", " ").title(),
        ip_address=request.client.host if request.client else "unknown",
        comments=body.comments,
    )
    await db.commit()
    return {"signature_id": str(sig.id), "signed_at": sig.signed_at, "meaning": sig.meaning}


@router.post("/change-controls/{cc_id}/{action}")
async def transition_change_control(
    cc_id: str,
    action: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    transitions = {
        "submit": ("qms.change_controls.submit", "draft", "under_review"),
        "approve": ("qms.change_controls.approve", "under_review", "approved"),
        "implement": ("qms.change_controls.implement", "approved", "implementation"),
        "close": ("qms.change_controls.close", "implementation", "closed"),
    }
    if action not in transitions:
        raise HTTPException(status_code=404, detail="Transition action not found.")
    permission_code, from_state, next_state = transitions[action]
    await _require_permission(db, current_user, permission_code)

    result = await db.execute(select(ChangeControl).where(ChangeControl.id == cc_id))
    cc = result.scalar_one_or_none()
    if not cc:
        raise HTTPException(status_code=404, detail="Change control not found.")

    old_state = cc.current_status
    cc.current_status = _apply_transition(
        old_state,
        action,
        {k: (f, t) for k, (_p, f, t) in transitions.items()},
    )
    await AuditService.log(
        db,
        action="TRANSITION",
        record_type="change_control",
        record_id=cc_id,
        module="qms",
        human_description=f"Change control transitioned {old_state} -> {next_state} ({action})",
        user_id=str(current_user.id),
        username=current_user.username,
        full_name=current_user.full_name,
        ip_address=request.client.host if request.client else None,
        reason=f"action={action}",
    )
    await db.commit()
    await db.refresh(cc)
    return cc
