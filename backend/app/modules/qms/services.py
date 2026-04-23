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
from app.core.audit.models import AuditEvent
from app.core.auth.models import User
from app.core.auth.models import Role, user_roles
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


CAPA_TRANSITIONS: dict[str, tuple[str, str]] = {
    "investigation": ("open", "investigation"),
    "action_plan_approved": ("investigation", "action_plan_approved"),
    "in_progress": ("action_plan_approved", "in_progress"),
    "effectiveness_check": ("in_progress", "effectiveness_check"),
    "closed": ("effectiveness_check", "closed"),
}


async def _role_at_time(db: AsyncSession, user_id: str) -> str:
    result = await db.execute(
        select(Role.name)
        .join(user_roles, Role.id == user_roles.c.role_id)
        .where(user_roles.c.user_id == user_id)
        .order_by(Role.name.asc())
    )
    names = [row[0] for row in result.all()]
    return ", ".join(names) if names else "Unassigned"


async def _require_permission(db: AsyncSession, user: User, permission_code: str) -> None:
    allowed = await AuthService.has_permission(db, str(user.id), permission_code)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Missing permission: {permission_code}",
        )


# State machine: maps action -> (required_from_state, next_state)
_DEVIATION_TRANSITIONS: dict[str, tuple[str, str]] = {
    "submit": ("open", "under_investigation"),
    "approve": ("under_investigation", "pending_approval"),
    "close": ("pending_approval", "closed"),
}

_CHANGE_CONTROL_TRANSITIONS: dict[str, tuple[str, str]] = {
    "submit":     ("draft", "under_review"),
    "approve":    ("under_review", "approved"),
    "implement":  ("approved", "in_implementation"),
    "review_effectiveness": ("in_implementation", "effectiveness_review"),
    "close":      ("effectiveness_review", "closed"),
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
    role_at_time = await _role_at_time(db, str(user.id))

    if data.regulatory_reportable and not (data.regulatory_reporting_justification or "").strip():
        raise HTTPException(
            status_code=400,
            detail="Regulatory reporting justification is required when regulatory reporting is required.",
        )

    capa = CAPA(
        capa_number=_next_number("CAPA", count),
        owner_id=str(user.id),
        site_id=str(user.site_id) if getattr(user, "site_id", None) else "default",
        current_status="open",
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
        role_at_time=role_at_time,
        ip_address=ip_address,
        record_snapshot_after={
            "capa_number": capa.capa_number,
            "title": capa.title,
            "risk_level": capa.risk_level,
            "capa_type": capa.capa_type,
        },
    )

    await db.commit()
    # Re-fetch with relationship loaded — db.refresh() does not load async relationships
    result = await db.execute(
        select(CAPA).where(CAPA.id == capa.id).options(selectinload(CAPA.actions))
    )
    return result.scalar_one()


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
    role_at_time = await _role_at_time(db, str(user.id))

    next_regulatory = changes.get("regulatory_reportable", capa.regulatory_reportable)
    next_justification = changes.get(
        "regulatory_reporting_justification", capa.regulatory_reporting_justification
    )
    if next_regulatory and not (next_justification or "").strip():
        raise HTTPException(
            status_code=400,
            detail="Regulatory reporting justification is required when regulatory reporting is required.",
        )

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
            role_at_time=role_at_time,
            ip_address=ip_address,
        )

    await db.commit()
    # Re-fetch with relationship loaded — db.refresh() does not load async relationships
    result = await db.execute(
        select(CAPA).where(CAPA.id == capa.id).options(selectinload(CAPA.actions))
    )
    return result.scalar_one()


async def add_capa_action(
    db: AsyncSession,
    capa_id: str,
    data: CAPAActionCreate,
    user: User,
    ip_address: Optional[str],
) -> CAPAAction:
    """Add a new action to an existing CAPA, auto-assigning the next sequence number."""
    capa = await get_capa_or_404(db, capa_id)
    role_at_time = await _role_at_time(db, str(user.id))
    if not data.username:
        raise HTTPException(status_code=400, detail="Username is required for CAPA transition signatures.")

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
        role_at_time=role_at_time,
        ip_address=ip_address,
    )

    await db.commit()
    await db.refresh(action)
    return action


async def update_capa_action(
    db: AsyncSession,
    capa_id: str,
    action_id: str,
    payload: dict,
    user: User,
    ip_address: Optional[str],
) -> CAPAAction:
    capa = await get_capa_or_404(db, capa_id)
    role_at_time = await _role_at_time(db, str(user.id))
    result = await db.execute(
        select(CAPAAction).where(
            CAPAAction.id == action_id,
            CAPAAction.capa_id == capa_id,
        )
    )
    action = result.scalar_one_or_none()
    if not action:
        raise HTTPException(status_code=404, detail="CAPA action not found.")

    old_status = action.status
    new_status = payload.get("status")
    if new_status is not None and payload.get("password") is None:
        raise HTTPException(
            status_code=400,
            detail="Password is required when changing CAPA action status.",
        )

    allowed_fields = {"description", "assignee_id", "due_date", "status", "completion_evidence"}
    for field, value in payload.items():
        if field not in allowed_fields:
            continue
        old_val = getattr(action, field)
        setattr(action, field, value)
        await AuditService.log_field_change(
            db,
            record_type="capa_action",
            record_id=action_id,
            module="qms",
            field_name=field,
            old_value=old_val,
            new_value=value,
            user_id=str(user.id),
            username=user.username,
            full_name=user.full_name,
            role_at_time=role_at_time,
            ip_address=ip_address,
        )

    if new_status is not None and new_status != old_status:
        sig = await ESignatureService.sign(
            db,
            user_id=str(user.id),
            password=payload["password"],
            record_type="capa_action",
            record_id=action_id,
            record_version="1.0",
            record_data={
                "capa_id": capa_id,
                "description": action.description,
                "status_before": old_status,
            },
            meaning=f"status_{new_status}",
            meaning_display=f"CAPA action status -> {new_status}",
            ip_address=ip_address or "127.0.0.1",
            comments=payload.get("completion_evidence"),
        )
        await AuditService.log(
            db,
            action="TRANSITION",
            record_type="capa_action",
            record_id=action_id,
            module="qms",
            human_description=f"CAPA action status transitioned {old_status} -> {new_status}",
            user_id=str(user.id),
            username=user.username,
            full_name=user.full_name,
            role_at_time=role_at_time,
            ip_address=ip_address,
            old_value={"status": old_status},
            new_value={"status": new_status, "signature_id": str(sig.id)},
        )

    await AuditService.log(
        db,
        action="UPDATE",
        record_type="capa_action",
        record_id=action_id,
        module="qms",
        human_description=f"CAPA action updated for {capa.capa_number}",
        user_id=str(user.id),
        username=user.username,
        full_name=user.full_name,
        role_at_time=role_at_time,
        ip_address=ip_address,
    )
    await db.commit()
    await db.refresh(action)
    return action


async def list_capa_audit_events(db: AsyncSession, capa_id: str) -> list[dict]:
    await get_capa_or_404(db, capa_id)
    result = await db.execute(
        select(AuditEvent)
        .where(
            AuditEvent.record_id == capa_id,
            AuditEvent.record_type == "capa",
        )
        .order_by(AuditEvent.event_at.desc())
    )
    events = result.scalars().all()
    return [
        {
            "user_full_name": evt.full_name,
            "role_at_time": evt.role_at_time or "Unassigned",
            "action": evt.action,
            "old_value": evt.old_value,
            "new_value": evt.new_value,
            "timestamp_utc": evt.event_at,
            "ip_address": evt.ip_address,
        }
        for evt in events
    ]


async def sign_capa(
    db: AsyncSession,
    capa_id: str,
    data: CAPASignRequest,
    user: User,
    ip_address: str,
) -> dict:
    """
    Apply an electronic signature to a CAPA (21 CFR Part 11 §11.50).

    Password re-authentication is mandatory and includes explicit username entry.
    Meaning drives strict TrackWise transitions:
      open -> investigation -> action_plan_approved -> in_progress -> effectiveness_check -> closed
    """
    capa = await get_capa_or_404(db, capa_id)
    role_at_time = await _role_at_time(db, str(user.id))

    if data.meaning not in CAPA_TRANSITIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported CAPA transition meaning '{data.meaning}'.",
        )

    required_from, next_status = CAPA_TRANSITIONS[data.meaning]
    if capa.current_status != required_from:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Transition '{data.meaning}' requires CAPA in '{required_from}', "
                f"but CAPA is in '{capa.current_status}'."
            ),
        )

    if data.meaning == "in_progress" and not (capa.root_cause or "").strip():
        raise HTTPException(
            status_code=400,
            detail="Root cause description is mandatory before moving CAPA to IN_PROGRESS.",
        )

    if data.meaning == "effectiveness_check":
        result = await db.execute(
            select(func.count())
            .select_from(CAPAAction)
            .where(
                CAPAAction.capa_id == capa_id,
                CAPAAction.status != "complete",
            )
        )
        incomplete_count = int(result.scalar() or 0)
        if incomplete_count > 0:
            raise HTTPException(
                status_code=400,
                detail="All CAPA actions must be COMPLETE before moving to EFFECTIVENESS_CHECK.",
            )

    sig = await ESignatureService.sign(
        db,
        user_id=str(user.id),
        username=data.username,
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
    old_status = capa.current_status
    capa.current_status = next_status

    # 21 CFR Part 11: capture actual completion timestamp at close — immutable thereafter
    if data.meaning == "closed" and capa.actual_completion_date is None:
        capa.actual_completion_date = _utcnow()

    await AuditService.log(
        db,
        action="TRANSITION",
        record_type="capa",
        record_id=capa_id,
        module="qms",
        human_description=(
            f"CAPA {capa.capa_number} transitioned {old_status} -> {next_status} "
            f"via e-signature meaning '{data.meaning}'"
        ),
        user_id=str(user.id),
        username=user.username,
        full_name=user.full_name,
        role_at_time=role_at_time,
        ip_address=ip_address,
        old_value={"current_status": old_status},
        new_value={"current_status": next_status},
        reason=data.comments,
    )

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
    role_at_time = await _role_at_time(db, str(user.id))

    if data.potential_patient_impact and not (data.potential_patient_impact_justification or "").strip():
        raise HTTPException(
            status_code=400,
            detail="Patient impact justification is required when potential patient impact is Yes.",
        )
    if data.regulatory_notification_required:
        if not (data.regulatory_authority_name or "").strip():
            raise HTTPException(status_code=400, detail="Regulatory authority name is required.")
        if data.regulatory_notification_deadline is None:
            raise HTTPException(status_code=400, detail="Regulatory notification deadline is required.")

    deviation = Deviation(
        deviation_number=_next_number("DEV", count),
        detected_by_id=str(user.id),
        owner_id=str(user.id),
        site_id=str(user.site_id) if getattr(user, "site_id", None) else "default",
        current_status="open",
        immediate_containment_actions_at=_utcnow(),
        batches_affected=data.batches_affected or ([data.batch_number] if data.batch_number else []),
        immediate_action=data.immediate_action or data.immediate_containment_actions,
        **data.model_dump(exclude={"batches_affected", "immediate_action"}),
    )
    if not deviation.immediate_containment_actions:
        raise HTTPException(status_code=400, detail="Immediate containment actions are required.")

    if deviation.requires_capa and not deviation.linked_capa_id:
        capa_count_result = await db.execute(select(func.count()).select_from(CAPA))
        capa_count = (capa_count_result.scalar() or 0) + 1
        auto_capa = CAPA(
            capa_number=_next_number("CAPA", capa_count),
            title=f"Auto CAPA for deviation {deviation.deviation_number}",
            capa_type="corrective",
            source="deviation",
            source_record_id=deviation.id,
            risk_level=deviation.risk_level,
            product_impact=False,
            patient_safety_impact=deviation.potential_patient_impact,
            regulatory_reportable=deviation.regulatory_notification_required,
            problem_description=(
                f"Auto-created from deviation {deviation.deviation_number}. "
                f"{deviation.description[:400]}"
            ),
            immediate_actions=deviation.immediate_containment_actions,
            root_cause=deviation.root_cause,
            root_cause_category=deviation.root_cause_category,
            department=user.department or "Quality",
            identified_date=_utcnow(),
            owner_id=str(user.id),
            site_id=str(user.site_id) if getattr(user, "site_id", None) else "default",
            current_status="open",
        )
        db.add(auto_capa)
        await db.flush([auto_capa])
        deviation.linked_capa_id = auto_capa.id

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
        role_at_time=role_at_time,
        ip_address=ip_address,
        record_snapshot_after={
            "deviation_number": deviation.deviation_number,
            "deviation_type": deviation.deviation_type,
            "risk_level": deviation.risk_level,
            "gmp_impact_classification": deviation.gmp_impact_classification,
            "linked_capa_id": deviation.linked_capa_id,
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
    role_at_time = await _role_at_time(db, str(user.id))
    changes = data.model_dump(exclude_none=True)

    if changes.get("potential_patient_impact", deviation.potential_patient_impact):
        new_justification = changes.get(
            "potential_patient_impact_justification",
            deviation.potential_patient_impact_justification,
        )
        if not (new_justification or "").strip():
            raise HTTPException(
                status_code=400,
                detail="Patient impact justification is required when potential patient impact is Yes.",
            )

    if changes.get("regulatory_notification_required", deviation.regulatory_notification_required):
        auth_name = changes.get("regulatory_authority_name", deviation.regulatory_authority_name)
        deadline = changes.get(
            "regulatory_notification_deadline", deviation.regulatory_notification_deadline
        )
        if not (auth_name or "").strip():
            raise HTTPException(status_code=400, detail="Regulatory authority name is required.")
        if deadline is None:
            raise HTTPException(status_code=400, detail="Regulatory notification deadline is required.")

    for field, new_val in changes.items():
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
            role_at_time=role_at_time,
            ip_address=ip_address,
        )

    if (
        changes.get("requires_capa", deviation.requires_capa)
        and not changes.get("linked_capa_id", deviation.linked_capa_id)
    ):
        capa_count_result = await db.execute(select(func.count()).select_from(CAPA))
        capa_count = (capa_count_result.scalar() or 0) + 1
        auto_capa = CAPA(
            capa_number=_next_number("CAPA", capa_count),
            title=f"Auto CAPA for deviation {deviation.deviation_number}",
            capa_type="corrective",
            source="deviation",
            source_record_id=deviation.id,
            risk_level=deviation.risk_level,
            product_impact=False,
            patient_safety_impact=deviation.potential_patient_impact,
            regulatory_reportable=deviation.regulatory_notification_required,
            problem_description=(
                f"Auto-created from deviation {deviation.deviation_number}. "
                f"{deviation.description[:400]}"
            ),
            immediate_actions=deviation.immediate_containment_actions,
            root_cause=deviation.root_cause,
            root_cause_category=deviation.root_cause_category,
            department=user.department or "Quality",
            identified_date=_utcnow(),
            owner_id=str(user.id),
            site_id=deviation.site_id,
            current_status="open",
        )
        db.add(auto_capa)
        await db.flush([auto_capa])
        deviation.linked_capa_id = auto_capa.id

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
    """Apply e-signature to a Deviation transition with strict state machine."""
    await _require_permission(db, user, "qms.deviations.sign")
    deviation = await get_deviation_or_404(db, deviation_id)
    role_at_time = await _role_at_time(db, str(user.id))

    meaning_to_transition = {
        "under_investigation": ("open", "under_investigation"),
        "pending_approval": ("under_investigation", "pending_approval"),
        "closed": ("pending_approval", "closed"),
    }
    if data.meaning not in meaning_to_transition:
        raise HTTPException(status_code=400, detail=f"Unsupported transition meaning '{data.meaning}'.")
    required_from, next_state = meaning_to_transition[data.meaning]
    if deviation.current_status != required_from:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Transition '{data.meaning}' requires state '{required_from}', "
                f"but deviation is '{deviation.current_status}'."
            ),
        )
    if data.username is None:
        raise HTTPException(status_code=400, detail="Username is required for deviation signatures.")
    if next_state == "closed" and not deviation.linked_capa_id:
        if data.no_capa_needed_confirmed is not True:
            raise HTTPException(
                status_code=400,
                detail="Closing without linked CAPA requires explicit no-CAPA confirmation.",
            )
        if not (data.no_capa_needed_justification or "").strip():
            raise HTTPException(
                status_code=400,
                detail="Closing without linked CAPA requires justification.",
            )
        deviation.no_capa_needed_confirmed = True
        deviation.no_capa_needed_justification = data.no_capa_needed_justification

    sig = await ESignatureService.sign(
        db,
        user_id=str(user.id),
        username=data.username,
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
    old_state = deviation.current_status
    deviation.current_status = next_state

    await AuditService.log(
        db,
        action="TRANSITION",
        record_type="deviation",
        record_id=deviation_id,
        module="qms",
        human_description=(
            f"Deviation {deviation.deviation_number} transitioned "
            f"{old_state} -> {next_state} via e-signature '{data.meaning}'"
        ),
        user_id=str(user.id),
        username=user.username,
        full_name=user.full_name,
        role_at_time=role_at_time,
        ip_address=ip_address,
        old_value={"current_status": old_state},
        new_value={"current_status": next_state},
        reason=data.comments,
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
    raise HTTPException(
        status_code=400,
        detail="Deprecated endpoint. Use /deviations/{id}/sign with username+password for transitions.",
    )


async def list_deviation_audit_events(db: AsyncSession, deviation_id: str) -> list[dict]:
    await get_deviation_or_404(db, deviation_id)
    result = await db.execute(
        select(AuditEvent)
        .where(
            AuditEvent.record_id == deviation_id,
            AuditEvent.record_type == "deviation",
        )
        .order_by(AuditEvent.event_at.desc())
    )
    events = result.scalars().all()
    return [
        {
            "user_full_name": evt.full_name,
            "role_at_time": evt.role_at_time or "Unassigned",
            "action": evt.action,
            "old_value": evt.old_value,
            "new_value": evt.new_value,
            "timestamp_utc": evt.event_at,
            "ip_address": evt.ip_address,
        }
        for evt in events
    ]


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
    role_at_time = await _role_at_time(db, str(user.id))

    if data.regulatory_filing_required and data.regulatory_filing_type is None:
        raise HTTPException(status_code=400, detail="Regulatory filing type is required when filing is required.")
    if data.validation_qualification_required and not (data.validation_scope_description or "").strip():
        raise HTTPException(status_code=400, detail="Validation scope description is required when validation/qualification is required.")

    cc = ChangeControl(
        change_number=_next_number("CC", count),
        owner_id=str(user.id),
        site_id=str(user.site_id) if getattr(user, "site_id", None) else "default",
        approval_signature_roles=[],
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
        role_at_time=role_at_time,
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
    role_at_time = await _role_at_time(db, str(user.id))
    changes = data.model_dump(exclude_none=True)

    if changes.get("regulatory_filing_required", cc.regulatory_filing_required) and not (
        changes.get("regulatory_filing_type", cc.regulatory_filing_type)
    ):
        raise HTTPException(status_code=400, detail="Regulatory filing type is required when filing is required.")

    if changes.get(
        "validation_qualification_required", cc.validation_qualification_required
    ) and not (changes.get("validation_scope_description", cc.validation_scope_description) or "").strip():
        raise HTTPException(
            status_code=400,
            detail="Validation scope description is required when validation/qualification is required.",
        )

    for field, new_val in changes.items():
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
            role_at_time=role_at_time,
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
    role_at_time = await _role_at_time(db, str(user.id))
    if data.username is None:
        raise HTTPException(status_code=400, detail="Username is required for change control signatures.")

    sig = await ESignatureService.sign(
        db,
        user_id=str(user.id),
        username=data.username,
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

    old_status = cc.current_status
    meaning_to_transition = {
        "under_review": ("draft", "under_review"),
        "initiator_approved": ("under_review", "approved_pending"),
        "qa_approved": ("under_review", "approved_pending"),
        "in_implementation": ("approved", "in_implementation"),
        "effectiveness_review": ("in_implementation", "effectiveness_review"),
        "closed": ("effectiveness_review", "closed"),
    }
    if data.meaning not in meaning_to_transition:
        raise HTTPException(status_code=400, detail=f"Unsupported meaning '{data.meaning}' for change control.")

    required_from, target = meaning_to_transition[data.meaning]
    if cc.current_status != required_from and not (
        data.meaning in {"initiator_approved", "qa_approved"} and cc.current_status == "under_review"
    ):
        raise HTTPException(
            status_code=400,
            detail=f"Meaning '{data.meaning}' requires status '{required_from}', but current is '{cc.current_status}'.",
        )

    if data.meaning in {"initiator_approved", "qa_approved"}:
        roles = set((cc.approval_signature_roles or []))
        roles.add("initiator" if data.meaning == "initiator_approved" else "qa")
        cc.approval_signature_roles = sorted(list(roles))
        if {"initiator", "qa"}.issubset(roles):
            cc.current_status = "approved"
        else:
            cc.current_status = "under_review"
    else:
        cc.current_status = target

    if cc.current_status == "in_implementation" and cc.actual_implementation_date is None:
        cc.actual_implementation_date = _utcnow()

    if data.meaning == "closed":
        if not cc.post_change_effectiveness_date or not (cc.post_change_effectiveness_outcome or "").strip():
            raise HTTPException(
                status_code=400,
                detail="Post-change effectiveness review date and outcome are required before close.",
            )

    await AuditService.log(
        db,
        action="TRANSITION",
        record_type="change_control",
        record_id=cc_id,
        module="qms",
        human_description=(
            f"Change Control {cc.change_number} transitioned {old_status} -> {cc.current_status} "
            f"via signature meaning '{data.meaning}'"
        ),
        user_id=str(user.id),
        username=user.username,
        full_name=user.full_name,
        role_at_time=role_at_time,
        ip_address=ip_address,
        old_value={"current_status": old_status},
        new_value={"current_status": cc.current_status, "approval_signature_roles": cc.approval_signature_roles},
        reason=data.comments,
    )

    await db.commit()
    return {
        "signature_id": str(sig.id),
        "signed_at": sig.signed_at,
        "meaning": sig.meaning,
        "status": cc.current_status,
        "approval_signature_roles": cc.approval_signature_roles or [],
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
    raise HTTPException(
        status_code=400,
        detail="Deprecated endpoint. Use /change-controls/{id}/sign with username+password for transitions.",
    )


async def list_change_control_audit_events(db: AsyncSession, cc_id: str) -> list[dict]:
    await get_change_control_or_404(db, cc_id)
    result = await db.execute(
        select(AuditEvent)
        .where(
            AuditEvent.record_id == cc_id,
            AuditEvent.record_type == "change_control",
        )
        .order_by(AuditEvent.event_at.desc())
    )
    events = result.scalars().all()
    return [
        {
            "user_full_name": evt.full_name,
            "role_at_time": evt.role_at_time or "Unassigned",
            "action": evt.action,
            "old_value": evt.old_value,
            "new_value": evt.new_value,
            "timestamp_utc": evt.event_at,
            "ip_address": evt.ip_address,
        }
        for evt in events
    ]


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
        deviation_type="laboratory",
        gmp_impact_classification="major",
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
        immediate_containment_actions="Sample quarantined pending investigation. Batch on hold.",
    )
    deviation = await create_deviation(db, data, system_user, ip_address=None)

    # Stamp the source reference so QMS records trace back to LIMS
    deviation.source_record_id = result_id if hasattr(deviation, "source_record_id") else None

    await db.commit()
    return deviation
