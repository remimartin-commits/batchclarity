from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.core.database import async_session_factory
from app.core.documents.models import DocumentVersion
from app.core.notify.service import NotificationService

_RULE_DOC_REVIEW = "document_review_due"


async def check_document_reviews() -> dict[str, int]:
    """Count approved/effective document versions due for review; notify when count > 0."""
    now = datetime.now(timezone.utc)
    threshold = now + timedelta(days=60)
    async with async_session_factory() as session:
        result = await session.execute(
            select(DocumentVersion).where(
                DocumentVersion.status.in_(["approved", "effective"]),
                DocumentVersion.next_review_date.is_not(None),
                DocumentVersion.next_review_date <= threshold,
            )
        )
        rows = result.scalars().all()
        overdue = len(rows)

        notified = 0
        if overdue > 0:
            notified = await NotificationService.send_rule_based(
                session,
                _RULE_DOC_REVIEW,
                {
                    "count": overdue,
                    "site_id": "aggregated (all sites)",
                },
            )
        await session.commit()
    return {"overdue": overdue, "notified": notified}
