from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.core.database import async_session_factory
from app.core.documents.models import DocumentVersion


async def check_document_reviews() -> int:
    """Count approved/effective document versions due for review in 60 days."""
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
    return len(rows)
