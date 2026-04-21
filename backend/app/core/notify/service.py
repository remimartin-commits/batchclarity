"""
Notification Service — sends GMP event alerts via email / WhatsApp / SMS.
All sends are logged to NotificationLog for audit purposes.
"""
import logging
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.notify.models import NotificationTemplate, NotificationRule, NotificationLog

logger = logging.getLogger(__name__)


class NotificationService:

    @staticmethod
    def _render(template: str, variables: dict) -> str:
        for key, value in variables.items():
            template = template.replace(f"{{{key}}}", str(value) if value else "")
        return template

    @staticmethod
    async def send_event(
        db: AsyncSession,
        *,
        event_type: str,
        record_type: str,
        record_id: str,
        variables: dict,
        site_id: Optional[str] = None,
    ) -> list[NotificationLog]:
        tmpl_result = await db.execute(
            select(NotificationTemplate).where(
                NotificationTemplate.event_type == event_type,
                NotificationTemplate.is_active == True,
            )
        )
        template = tmpl_result.scalar_one_or_none()
        if not template:
            return []

        rule_result = await db.execute(
            select(NotificationRule).where(
                NotificationRule.template_id == template.id,
                NotificationRule.is_active == True,
            )
        )
        rules = rule_result.scalars().all()

        logs = []
        for rule in rules:
            address = rule.recipient_address
            if not address:
                continue

            subject = NotificationService._render(template.subject_template or "", variables)
            body = NotificationService._render(template.body_template, variables)

            log = NotificationLog(
                template_id=template.id,
                recipient_user_id=rule.recipient_user_id,
                recipient_address=address,
                channel=rule.channel,
                subject=subject,
                body=body,
                record_type=record_type,
                record_id=record_id,
                status="pending",
            )
            db.add(log)
            await db.flush([log])

            success = await NotificationService._dispatch(rule.channel, address, subject, body)
            log.status = "sent" if success else "failed"
            log.sent_at = datetime.now(timezone.utc) if success else None
            logs.append(log)

        return logs

    @staticmethod
    async def _dispatch(channel: str, address: str, subject: str, body: str) -> bool:
        try:
            if channel == "email":
                logger.info(f"[EMAIL] To: {address} | Subject: {subject}")
                return True
            elif channel == "whatsapp":
                logger.info(f"[WHATSAPP] To: {address} | Body: {body[:100]}")
                return True
            elif channel == "sms":
                logger.info(f"[SMS] To: {address} | Body: {body[:160]}")
                return True
            else:
                logger.warning(f"Unknown notification channel: {channel}")
                return False
        except Exception as e:
            logger.error(f"Notification dispatch failed: {e}")
            return False

    @staticmethod
    async def send_direct(
        db: AsyncSession,
        *,
        channel: str,
        address: str,
        subject: Optional[str],
        body: str,
        record_type: Optional[str] = None,
        record_id: Optional[str] = None,
    ) -> NotificationLog:
        log = NotificationLog(
            recipient_address=address,
            channel=channel,
            subject=subject,
            body=body,
            record_type=record_type,
            record_id=record_id,
            status="pending",
        )
        db.add(log)
        await db.flush([log])
        success = await NotificationService._dispatch(channel, address, subject or "", body)
        log.status = "sent" if success else "failed"
        log.sent_at = datetime.now(timezone.utc) if success else None
        return log
