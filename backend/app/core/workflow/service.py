"""
Workflow Engine Service — executes state machine transitions for all GMP records.

Usage from any module router:
    await WorkflowService.transition(db, instance_id, "submit_for_review", user, ip)
"""
from datetime import datetime, timezone, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from app.core.workflow.models import (
    WorkflowDefinition, WorkflowState, WorkflowTransition,
    WorkflowInstance, WorkflowHistoryEntry,
)
from app.core.esig.service import ESignatureService
from app.core.audit.service import AuditService
from app.core.auth.models import User


class WorkflowService:

    @staticmethod
    async def get_or_create_instance(
        db: AsyncSession,
        *,
        workflow_code: str,
        record_type: str,
        record_id: str,
        started_by: User,
        due_days: Optional[int] = None,
    ) -> WorkflowInstance:
        """Get existing or create new workflow instance for a record."""
        result = await db.execute(
            select(WorkflowInstance).where(
                WorkflowInstance.record_type == record_type,
                WorkflowInstance.record_id == record_id,
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            return existing

        defn_result = await db.execute(
            select(WorkflowDefinition).where(
                WorkflowDefinition.code == workflow_code,
                WorkflowDefinition.is_active == True,
            )
        )
        defn = defn_result.scalar_one_or_none()
        if not defn:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Workflow definition '{workflow_code}' not found.",
            )

        now = datetime.now(timezone.utc)
        instance = WorkflowInstance(
            definition_id=defn.id,
            record_type=record_type,
            record_id=record_id,
            current_state=defn.initial_state,
            started_at=now,
            started_by_id=started_by.id,
            due_date=now + timedelta(days=due_days) if due_days else None,
        )
        db.add(instance)
        await db.flush([instance])
        return instance

    @staticmethod
    async def get_available_transitions(
        db: AsyncSession,
        instance_id: str,
        user: User,
    ) -> list[WorkflowTransition]:
        """Returns transitions available from the current state for this user."""
        result = await db.execute(
            select(WorkflowInstance).where(WorkflowInstance.id == instance_id)
        )
        instance = result.scalar_one_or_none()
        if not instance:
            return []

        user_roles = {r.code for r in user.roles} if hasattr(user, "roles") and user.roles else set()

        trans_result = await db.execute(
            select(WorkflowTransition).where(
                WorkflowTransition.definition_id == instance.definition_id,
                WorkflowTransition.from_state == instance.current_state,
            )
        )
        all_transitions = trans_result.scalars().all()

        available = []
        for t in all_transitions:
            required = set(t.required_roles or [])
            if not required or required.intersection(user_roles):
                available.append(t)
        return available

    @staticmethod
    async def transition(
        db: AsyncSession,
        *,
        instance_id: str,
        transition_name: str,
        user: User,
        ip_address: str,
        reason: Optional[str] = None,
        password: Optional[str] = None,     # Required when transition needs e-sig
        record_data: Optional[dict] = None,  # For e-sig hash
    ) -> WorkflowInstance:
        """
        Execute a state transition. Validates roles, signatures, and records history.
        """
        result = await db.execute(
            select(WorkflowInstance).where(WorkflowInstance.id == instance_id)
        )
        instance = result.scalar_one_or_none()
        if not instance:
            raise HTTPException(status_code=404, detail="Workflow instance not found.")

        # Find the requested transition
        trans_result = await db.execute(
            select(WorkflowTransition).where(
                WorkflowTransition.definition_id == instance.definition_id,
                WorkflowTransition.from_state == instance.current_state,
                WorkflowTransition.action_label == transition_name,
            )
        )
        transition = trans_result.scalar_one_or_none()
        if not transition:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Transition '{transition_name}' not valid from state '{instance.current_state}'.",
            )

        # Validate role
        user_roles = {r.code for r in user.roles} if hasattr(user, "roles") and user.roles else set()
        required_roles = set(transition.required_roles or [])
        if required_roles and not required_roles.intersection(user_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Roles required: {', '.join(required_roles)}",
            )

        # Validate reason if required
        if transition.requires_reason and not reason:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A reason is required for this transition.",
            )

        # Electronic signature if required
        sig_id = None
        if transition.required_signature_meaning:
            if not password:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Electronic signature (password re-entry) required for this transition.",
                )
            sig = await ESignatureService.sign(
                db,
                user_id=user.id,
                password=password,
                record_type=instance.record_type,
                record_id=instance.record_id,
                record_version="1.0",
                record_data=record_data or {"instance_id": instance_id},
                meaning=transition.required_signature_meaning,
                meaning_display=transition.required_signature_meaning.replace("_", " ").title(),
                ip_address=ip_address,
            )
            sig_id = sig.id

        from_state = instance.current_state
        instance.current_state = transition.to_state

        # Check if terminal state
        state_result = await db.execute(
            select(WorkflowState).where(
                WorkflowState.definition_id == instance.definition_id,
                WorkflowState.code == transition.to_state,
            )
        )
        new_state = state_result.scalar_one_or_none()
        if new_state and new_state.is_terminal:
            instance.completed_at = datetime.now(timezone.utc)

        # Record history (immutable)
        history = WorkflowHistoryEntry(
            instance_id=instance.id,
            from_state=from_state,
            to_state=transition.to_state,
            transitioned_by_id=user.id,
            transitioned_by_name=user.full_name,
            transitioned_at=datetime.now(timezone.utc),
            reason=reason,
            signature_id=sig_id,
        )
        db.add(history)

        await AuditService.log(
            db,
            action="STATE_TRANSITION",
            record_type=instance.record_type,
            record_id=instance.record_id,
            module="workflow",
            human_description=(
                f"Record {instance.record_id} transitioned from '{from_state}' to "
                f"'{transition.to_state}' via '{transition_name}' by {user.full_name}"
            ),
            user_id=user.id,
            username=user.username,
            full_name=user.full_name,
            ip_address=ip_address,
            old_value=from_state,
            new_value=transition.to_state,
            reason=reason,
        )

        return instance

    @staticmethod
    async def get_history(db: AsyncSession, instance_id: str) -> list[WorkflowHistoryEntry]:
        result = await db.execute(
            select(WorkflowHistoryEntry)
            .where(WorkflowHistoryEntry.instance_id == instance_id)
            .order_by(WorkflowHistoryEntry.transitioned_at)
        )
        return result.scalars().all()
