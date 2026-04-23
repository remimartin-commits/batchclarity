"""
Audit Trail Service — called by every module on every data change.
This is never called directly from API handlers; it's called automatically
by the base CRUD service so no module can forget to audit.
"""
from datetime import datetime, timezone
from typing import Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.audit.models import AuditEvent
from app.core.config import settings


class AuditService:

    @staticmethod
    async def log(
        db: AsyncSession,
        *,
        action: str,
        record_type: str,
        record_id: str,
        module: str,
        human_description: str,
        user_id: Optional[str] = None,
        username: str = "system",
        full_name: str = "System",
        role_at_time: Optional[str] = None,
        ip_address: Optional[str] = None,
        session_id: Optional[str] = None,
        site_id: Optional[str] = None,
        field_name: Optional[str] = None,
        old_value: Optional[Any] = None,
        new_value: Optional[Any] = None,
        record_snapshot_before: Optional[dict] = None,
        record_snapshot_after: Optional[dict] = None,
        record_display: Optional[str] = None,
        reason: Optional[str] = None,
        is_system_action: bool = False,
    ) -> AuditEvent:
        """
        Write one immutable audit event. Called for every state-changing operation.
        The event_at is set SERVER-SIDE in UTC — never trust client-provided timestamps.
        """
        event = AuditEvent(
            user_id=user_id,
            username=username,
            full_name=full_name,
            role_at_time=role_at_time,
            ip_address=ip_address,
            session_id=session_id,
            action=action,
            record_type=record_type,
            record_id=record_id,
            record_display=record_display,
            field_name=field_name,
            old_value=old_value,
            new_value=new_value,
            record_snapshot_before=record_snapshot_before,
            record_snapshot_after=record_snapshot_after,
            human_description=human_description,
            event_at=datetime.now(timezone.utc),  # Server UTC — immutable
            module=module,
            site_id=site_id,
            reason=reason,
            system_version=settings.APP_VERSION,
            is_system_action=is_system_action,
        )
        db.add(event)
        # We flush but don't commit — the calling transaction commits everything atomically.
        # This means if the main operation fails, the audit event also rolls back (no phantom audit entries).
        await db.flush([event])
        return event

    @staticmethod
    async def log_login(
        db: AsyncSession,
        *,
        user_id: Optional[str],
        username: str,
        full_name: str,
        ip_address: str,
        success: bool,
        failure_reason: Optional[str] = None,
    ) -> AuditEvent:
        action = "LOGIN_SUCCESS" if success else "LOGIN_FAILURE"
        description = (
            f"User '{username}' logged in successfully from {ip_address}"
            if success
            else f"Failed login attempt for '{username}' from {ip_address}: {failure_reason}"
        )
        rid = user_id if user_id else "00000000-0000-4000-8000-000000000001"
        return await AuditService.log(
            db,
            action=action,
            record_type="user_session",
            record_id=rid,
            module="auth",
            human_description=description,
            user_id=user_id,
            username=username,
            full_name=full_name,
            ip_address=ip_address,
        )

    @staticmethod
    async def log_field_change(
        db: AsyncSession, *, record_type: str, record_id: str, module: str,
        field_name: str, old_value: Any, new_value: Any,
        user_id: str, username: str, full_name: str,
        role_at_time: Optional[str] = None,
        ip_address: Optional[str] = None, reason: Optional[str] = None,
    ) -> AuditEvent:
        """Log a single field value change with before/after."""
        description = (
            f"Field '{field_name}' on {record_type} {record_id} changed "
            f"from '{old_value}' to '{new_value}' by {full_name}"
        )
        return await AuditService.log(
            db, action="UPDATE", record_type=record_type, record_id=record_id,
            module=module, human_description=description,
            user_id=user_id, username=username, full_name=full_name,
            role_at_time=role_at_time,
            ip_address=ip_address, field_name=field_name,
            old_value=old_value, new_value=new_value, reason=reason,
        )

    @staticmethod
    async def log_signature(
        db: AsyncSession, *, record_type: str, record_id: str, module: str,
        meaning: str, user_id: str, username: str, full_name: str,
        role_at_time: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> AuditEvent:
        description = f"Electronic signature '{meaning}' applied to {record_type} {record_id} by {full_name}"
        return await AuditService.log(
            db, action="SIGN", record_type=record_type, record_id=record_id,
            module=module, human_description=description,
            user_id=user_id, username=username, full_name=full_name,
            role_at_time=role_at_time,
            ip_address=ip_address,
        )
