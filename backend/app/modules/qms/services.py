"""
QMS Services — business logic layer.

All business rules live here, NOT in the router. The router handles only:
  - HTTP binding (path params, query params, request body parsing)
  - HTTP response codes
  - Calling the correct service function

This layer is also consumed by:
  - Background tasks (APScheduler / Celery jobs)
  - Test fixtures (no HTTP overhead)
  - Cross-module event hooks (e.g. LIMS OOS auto-trigger creates a Deviation)
  - Constitutional layer assertions

21 CFR Part 11 / EU Annex 11 guarantees enforced here:
  - Every state change produces an AuditEvent (ALCOA+ Contemporaneous)
  - Sign operations require password re-authentication (ESignatureService)
  - Records are never deleted — only transitioned to terminal states
  - auto_close_capa sets actual_completion_date at time of close (not editable)
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.audit.service import AuditService
from app.core.auth.models import User
from app.core.auth.service import AuthService
from app.core.esig.service import ESignatureService
from app.modules.qms.models import CAPA, CAPAAction, ChangeControl, Deviation
from app.modules.qms.schemas import (
    CAPAActionCreate,
    CAPACreate,
    CAPASignRequest,
    CAPAUpdate,
    ChangeControlCreate,
    ChangeControlUpdate,
    DeviationCreate,
    DeviationUpdate,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _next_number(prefix: str, sequence: int) -> str:
    year = _utcnow().year
    return f"{prefix}-{year}-{sequence:04d}"


async def _require_permission(db: AsyncSession, user: User, permission_code: str) -> None:
    allowed = await AuthService.has_permission(db, str(user.id), permission_code)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Missing permission: {permission_code}",
        )


# State machine: maps action -> (required_from_state, next_state)
_DEVIATION_TRANSITIONS: dict[str, tuple[str, str]] = {
    "submit": ("draft", "under_review"),
    "approve": ("under_review", "approved"),
    "close":   ("approved", "closed"),
}

_CHANGE_CONTROL_TRANSITIONS: dict[str, tuple[str, str]] = {
    "submit":     ("draft", "under_review"),
    "approve":    ("under_review", "approved"),
    "implement":  ("approved", "implementation"),
    "close":      ("implementation", "closed"),
}


def _apply_transition(
    current_status: str,
    action: str,
    transitions: dict[str, tuple[str, str]],
) -> str:
    """
    Validate and apply a state machine transition.
    Raises HTTP 400 if the action is unknown or the current state doesn't allow it.
    """
    if action not in transitions:
        raise HTTPException(status_code=400, detail=f"Unknown transition action: '{action}'.")
    from_state, next_state = transitions[action]
    if current_status != from_state:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Action '{action}' requires state '{from_state}', "
                f"but record is currently '{current_status}'."
            ),
        )
    return next_state


# ── CAPA ──────────────────────────────────────────────────────────────────────

async def create_capa(
    db: AsyncSession,
    data: CAPACreate,
    user: User,
    ip_address: Optional[str],
) -> CAPA:
    """
    Create a CAPA record with optional initial actions.
    Generates sequential CAPA number (CAPA-YYYY-NNNN).
    Writes one AuditEvent on CREATE.
    """
    count_result = await db.execute(select(func.count()).select_from(CAPA))
    count = (count_result.scalar() or 0) + 1

    capa = CAPA(
        capa_number=_next_number("CAPA", count),
        owner_id=str(user.id),
        site_id=str(user.site_id) if getattr(user, "site_id", None) else "default",
        **data.model_dump(exclude={"actions"}),
    )
    db.add(capa)
    await db.flush([capa])

    for i, action_data in enumerate(data.actions, start=1):
        db.add(CAPAAction(
            capa_id=capa.id,
            sequence_number=i,
            **action_data.model_dump(),
        ))

    await AuditService.log(
        db,
        action="CREATE",
        record_type="capa",
        record_id=capa.id,
        module="qms",
        human_description=f"CAPA {capa.capa_number} created: {capa.title}",
        user_id=str(user.id),
        username=user.username,
        full_name=user.full_name,
        ip_address=ip_address,
        record_snapshot_after={
            "capa_number": capa.capa_number,
            "title": capa.title,
            "risk_level": capa.risk_level,
            "capa_type": capa.capa_type,
        },
    )

    await db.commit()
    await db.refresh(capa)
    return capa


async def list_capas(
    db: AsyncSession,
    *,
    status_filter: Optional[str] = None,
    risk_level: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
) -> list[CAPA]:
    """Return CAPAs filtered by status and/or risk level, ordered newest first."""
    query = select(CAPA).options(selectinload(CAPA.actions))
    if status_filter:
        query = query.where(CAPA.current_status == status_filter)
    if risk_level:
        query = query.where(CAPA.risk_level == risk_level)
    query = query.order_by(CAPA.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_capa_or_404(db: AsyncSession, capa_id: str) -> CAPA:
    result = await db.execute(
        select(CAPA)
        .where(CAPA.id == capa_id)
        .options(selectinload(CAPA.actions))
    )
    capa = result.scalar_one_or_none()
    if not capa:
        raise HTTPException(status_code=404, detail="CAPA not found.")
    return capa


async def update_capa(
    db: AsyncSession,
    capa_id: str,
    data: CAPAUpdate,
    user: User,
    ip_address: Optional[str],
) -> CAPA:
    """
    Partial update — only non-None fields are changed.
    Produces one AuditEvent per changed field (ALCOA+ field-level traceability).
    """
    capa = await get_capa_or_404(db, capa_id)
    changes = data.model_dump(exclude_none=True)

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
            user_id=str(user.id),
            username=user.username,
            full_name=user.full_name,
            ip_address=ip_address,
        )

    await db.commit()
    await db.refresh(capa)
    return capa


async def add_capa_action(
    db: AsyncSession,
    capa_id: str,
    data: CAPAActionCreate,
    user: User,
    ip_address: Optional[str],
) -> CAPAAction:
    """Add a new action to an existing CAPA, auto-assigning the next sequence number."""
    capa = await get_capa_or_404(db, capa_id)

    count_result = await db.execute(
        select(func.count()).select_from(CAPAAction).where(CAPAAction.capa_id == capa_id)
    )
    next_seq = (count_result.scalar() or 0) + 1

    action = CAPAAction(
        capa_id=capa_id,
        sequence_number=next_seq,
        **data.model_dump(),
    )
    db.add(action)

    await AuditService.log(
        db,
        action="CREATE",
        record_type="capa_action",
        record_id=capa_id,
        module="qms",
        human_description=f"Action #{next_seq} added to {capa.capa_number}: {data.description}",
        user_id=str(user.id),
        username=user.username,
        full_name=user.full_name,
        ip_address=ip_address,
    )

    await db.commit()
    await db.refresh(action)
    return action


async def sign_capa(
    db: AsyncSession,
    capa_id: str,
    data: CAPASignRequest,
    user: User,
    ip_address: str,
) -> dict:
    """
    Apply an electronic signature to a CAPA (21 CFR Part 11 §11.50).

    Password re-authentication is mandatory — ESignatureService enforces this.
    Meaning drives the status transition:
      reviewed  -> under_review
      approved  -> approved
      closed    -> closed (sets actual_completion_date)
    """
    capa = await get_capa_or_404(db, capa_id)

    sig = await ESignatureService.sign(
        db,
        user_id=str(user.id),
        password=data.password,
        record_type="capa",
        record_id=capa_id,
        record_version="1.0",
        record_data={
            "id": str(capa.id),
            "capa_number": capa.capa_number,
            "status": capa.current_status,
        },
        meaning=data.meaning,
        meaning_display=data.meaning.replace("_", " ").title(),
        ip_address=ip_address,
        comments=data.comments,
    )

    _meaning_to_status = {
        "reviewed": "under_review",
        "approved": "approved",
        "closed":   "closed",
    }
    if data.meaning in _meaning_to_status:
        capa.current_status = _meaning_to_status[data.meaning]

    # 21 CFR Part 11: capture actual completion timestamp at close — immutable thereafter
    if data.meaning == "closed" and capa.actual_completion_date is None:
        capa.actual_completion_date = _utcnow()

    await db.commit()
    return {
        "signature_id": str(sig.id),
        "signed_at": sig.signed_at,
        "meaning": sig.meaning,
    }


# ── DEVIATION ─────────────────────────────────────────────────────────────────

async def create_deviation(
    db: AsyncSession,
    data: DeviationCreate,
    user: User,
    ip_address: Optional[str],
) -> Deviation:
    """
    Create a Deviation record. Generates sequential DEV-YYYY-NNNN number.

    Can also be called by LIMS OOS auto-trigger (information-purity-spec.md §OOS lifecycle).
    In that case pass a system user and set ip_address=None.
    """
    count_result = await db.execute(select(func.count()).select_from(Deviation))
    count = (count_result.scalar() or 0) + 1

    deviation = Deviation(
        deviation_number=_next_number("DEV", count),
        detected_by_id=str(user.id),
        owner_id=str(user.id),
        site_id=str(user.site_id) if getattr(user, "site_id", None) else "default",
        **data.model_dump(),
    )
    db.add(deviation)
    await db.flush([deviation])

    await AuditService.log(
        db,
        action="CREATE",
        record_type="deviation",
        record_id=deviation.id,
        module="qms",
        human_description=(
            f"Deviation {deviation.deviation_number} created: {deviation.title} "
            f"(type={deviation.deviation_type}, risk={deviation.risk_level})"
        ),
        user_id=str(user.id),
        username=user.username,
        full_name=user.full_name,
        ip_address=ip_address,
        record_snapshot_after={
            "deviation_number": deviation.deviation_number,
            "deviation_type": deviation.deviation_type,
            "risk_level": deviation.risk_level,
            "category": deviation.category,
        },
    )

    await db.commit()
    await db.refresh(deviation)
    return deviation


async def list_deviations(
    db: AsyncSession,
    *,
    status_filter: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
) -> list[Deviation]:
    query = select(Deviation)
    if status_filter:
        query = query.where(Deviation.current_status == status_filter)
    query = query.order_by(Deviation.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_deviation_or_404(db: AsyncSession, deviation_id: str) -> Deviation:
    result = await db.execute(select(Deviation).where(Deviation.id == deviation_id))
    dev = result.scalar_one_or_none()
    if not dev:
        raise HTTPException(status_code=404, detail="Deviation not found.")
    return dev


async def update_deviation(
    db: AsyncSession,
    deviation_id: str,
    data: DeviationUpdate,
    user: User,
    ip_address: Optional[str],
) -> Deviation:
    """Partial update with field-level audit trail per changed field."""
    deviation = await get_deviation_or_404(db, deviation_id)

    for field, new_val in data.model_dump(exclude_none=True).items():
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
            user_id=str(user.id),
            username=user.username,
            full_name=user.full_name,
            ip_address=ip_address,
        )

    await db.commit()
    await db.refresh(deviation)
    return deviation


async def sign_deviation(
    db: AsyncSession,
    deviation_id: str,
    data: CAPASignRequest,
    user: User,
    ip_address: str,
) -> dict:
    """Apply e-signature to a Deviation. Requires qms.deviations.sign permission."""
    await _require_permission(db, user, "qms.deviations.sign")
    deviation = await get_deviation_or_404(db, deviation_id)

    sig = await ESignatureService.sign(
        db,
        user_id=str(user.id),
        password=data.password,
        record_type="deviation",
        record_id=deviation_id,
        record_version="1.0",
        record_data={
            "id": str(deviation.id),
            "deviation_number": deviation.deviation_number,
            "status": deviation.current_status,
        },
        meaning=data.meaning,
        meaning_display=data.meaning.replace("_", " ").title(),
        ip_address=ip_address,
        comments=data.comments,
    )

    await db.commit()
    return {
        "signature_id": str(sig.id),
        "signed_at": sig.signed_at,
        "meaning": sig.meaning,
    }


async def transition_deviation(
    db: AsyncSession,
    deviation_id: str,
    action: str,
    user: User,
    ip_address: Optional[str],
) -> Deviation:
    """
    Drive the Deviation state machine:
      draft -> under_review -> approved -> closed

    Each transition requires the matching permission (qms.deviations.<action>).
    Every transition is written to the audit trail.
    """
    if action not in _DEVIATION_TRANSITIONS:
        raise HTTPException(status_code=404, detail=f"Unknown transition action: '{action}'.")

    permission_code = f"qms.deviations.{action}"
    await _require_permission(db, user, permission_code)

    deviation = await get_deviation_or_404(db, deviation_id)
    old_state = deviation.current_status
    deviation.current_status = _apply_transition(old_state, action, _DEVIATION_TRANSITIONS)

    _, next_state = _DEVIATION_TRANSITIONS[action]
    await AuditService.log(
        db,
        action="TRANSITION",
        record_type="deviation",
        record_id=deviation_id,
        module="qms",
        human_description=(
            f"Deviation {deviation.deviation_number} transitioned "
            f"{old_state} -> {next_state} via '{action}'"
        ),
        user_id=str(user.id),
        username=user.username,
        full_name=user.full_name,
        ip_address=ip_address,
        reason=f"action={action}",
    )

    await db.commit()
    await db.refresh(deviation)
    return deviation


# ── CHANGE CONTROL ────────────────────────────────────────────────────────────

async def create_change_control(
    db: AsyncSession,
    data: ChangeControlCreate,
    user: User,
    ip_address: Optional[str],
) -> ChangeControl:
    """Create a Change Control record. Generates sequential CC-YYYY-NNNN number."""
    count_result = await db.execute(select(func.count()).select_from(ChangeControl))
    count = (count_result.scalar() or 0) + 1

    cc = ChangeControl(
        change_number=_next_number("CC", count),
        owner_id=str(user.id),
        site_id=str(user.site_id) if getattr(user, "site_id", None) else "default",
        **data.model_dump(),
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
        user_id=str(user.id),
        username=user.username,
        full_name=user.full_name,
        ip_address=ip_address,
        record_snapshot_after={
            "change_number": cc.change_number,
            "change_type": cc.change_type,
            "change_category": cc.change_category,
            "regulatory_impact": cc.regulatory_impact,
            "validation_required": cc.validation_required,
        },
    )

    await db.commit()
    await db.refresh(cc)
    return cc


async def list_change_controls(
    db: AsyncSession,
    *,
    status_filter: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
) -> list[ChangeControl]:
    query = select(ChangeControl)
    if status_filter:
        query = query.where(ChangeControl.current_status == status_filter)
    query = query.order_by(ChangeControl.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_change_control_or_404(db: AsyncSession, cc_id: str) -> ChangeControl:
    result = await db.execute(select(ChangeControl).where(ChangeControl.id == cc_id))
    cc = result.scalar_one_or_none()
    if not cc:
        raise HTTPException(status_code=404, detail="Change control not found.")
    return cc


async def update_change_control(
    db: AsyncSession,
    cc_id: str,
    data: ChangeControlUpdate,
    user: User,
    ip_address: Optional[str],
) -> ChangeControl:
    """Partial update with field-level audit trail per changed field."""
    cc = await get_change_control_or_404(db, cc_id)

    for field, new_val in data.model_dump(exclude_none=True).items():
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
            user_id=str(user.id),
            username=user.username,
            full_name=user.full_name,
            ip_address=ip_address,
        )

    await db.commit()
    await db.refresh(cc)
    return cc


async def sign_change_control(
    db: AsyncSession,
    cc_id: str,
    data: CAPASignRequest,
    user: User,
    ip_address: str,
) -> dict:
    """
    Apply e-signature to a Change Control. Requires qms.change_controls.sign permission.
    Meaning 'approved' -> status approved; 'closed' -> status closed + actual_implementation_date.
    """
    await _require_permission(db, user, "qms.change_controls.sign")
    cc = await get_change_control_or_404(db, cc_id)

    sig = await ESignatureService.sign(
        db,
        user_id=str(user.id),
        password=data.password,
        record_type="change_control",
        record_id=cc_id,
        record_version="1.0",
        record_data={
            "id": str(cc.id),
            "change_number": cc.change_number,
            "status": cc.current_status,
        },
        meaning=data.meaning,
        meaning_display=data.meaning.replace("_", " ").title(),
        ip_address=ip_address,
        comments=data.comments,
    )

    _meaning_to_status = {
        "approved": "approved",
        "closed":   "closed",
    }
    if data.meaning in _meaning_to_status:
        cc.current_status = _meaning_to_status[data.meaning]

    # Record actual implementation timestamp at close
    if data.meaning == "closed" and cc.actual_implementation_date is None:
        cc.actual_implementation_date = _utcnow()

    await db.commit()
    return {
        "signature_id": str(sig.id),
        "signed_at": sig.signed_at,
        "meaning": sig.meaning,
    }


async def transition_change_control(
    db: AsyncSession,
    cc_id: str,
    action: str,
    user: User,
    ip_address: Optional[str],
) -> ChangeControl:
    """
    Drive the Change Control state machine:
      draft -> under_review -> approved -> implementation -> closed

    Each transition requires qms.change_controls.<action> permission.
    'implement' action sets actual_implementation_date.
    """
    if action not in _CHANGE_CONTROL_TRANSITIONS:
        raise HTTPException(status_code=404, detail=f"Unknown transition action: '{action}'.")

    permission_code = f"qms.change_controls.{action}"
    await _require_permission(db, user, permission_code)

    cc = await get_change_control_or_404(db, cc_id)
    old_state = cc.current_status
    cc.current_status = _apply_transition(old_state, action, _CHANGE_CONTROL_TRANSITIONS)

    _, next_state = _CHANGE_CONTROL_TRANSITIONS[action]

    # Stamp actual_implementation_date when entering implementation state
    if action == "implement" and cc.actual_implementation_date is None:
        cc.actual_implementation_date = _utcnow()

    await AuditService.log(
        db,
        action="TRANSITION",
        record_type="change_control",
        record_id=cc_id,
        module="qms",
        human_description=(
            f"Change Control {cc.change_number} transitioned "
            f"{old_state} -> {next_state} via '{action}'"
        ),
        user_id=str(user.id),
        username=user.username,
        full_name=user.full_name,
        ip_address=ip_address,
        reason=f"action={action}",
    )

    await db.commit()
    await db.refresh(cc)
    return cc


# ── Cross-module hooks (called by other modules, never imported from them) ────

async def create_deviation_from_oos(
    db: AsyncSession,
    *,
    sample_id: str,
    result_id: str,
    test_name: str,
    observed_value: str,
    spec_limit: str,
    site_id: str,
    system_user: User,
) -> Deviation:
    """
    Called by lims.services.record_test_result() when an OOS condition is detected.

    This is an information-purity-spec.md §OOS lifecycle entry point:
      OOS detected -> Deviation auto-created -> OPEN investigation

    Uses a system_user (service account) so the audit trail shows system origin,
    not a random human user.
    """
    data = DeviationCreate(
        title=f"OOS Result: {test_name} (sample {sample_id})",
        deviation_type="unplanned",
        category="process",
        description=(
            f"Out-of-specification result detected automatically.\n"
            f"Test: {test_name}\n"
            f"Observed: {observed_value}\n"
            f"Specification limit: {spec_limit}\n"
            f"Sample ID: {sample_id}\n"
            f"Result ID: {result_id}"
        ),
        detected_during="laboratory_testing",
        detection_date=_utcnow(),
        risk_level="high",
        immediate_action="Sample quarantined pending investigation. Batch on hold.",
    )
    deviation = await create_deviation(db, data, system_user, ip_address=None)

    # Stamp the source reference so QMS records trace back to LIMS
    deviation.source_record_id = result_id if hasattr(deviation, "source_record_id") else None

    await db.commit()
    return deviation
