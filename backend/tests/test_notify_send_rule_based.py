"""Tests for NotificationService.send_rule_based (TASK-018)."""
from __future__ import annotations

from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.auth.models import Organisation, Site, User
from app.core.auth.service import AuthService
from app.core.database import Base
from app.core.notify.models import NotificationLog, NotificationRule, NotificationTemplate
from app.core.notify.service import NotificationService


@pytest_asyncio.fixture
async def notify_session(tmp_path: Path):
    db_path = tmp_path / "notify_rule_test.db"
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_path.as_posix()}", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(
            lambda sc: Base.metadata.create_all(
                sc,
                tables=[
                    Organisation.__table__,
                    Site.__table__,
                    User.__table__,
                    NotificationTemplate.__table__,
                    NotificationRule.__table__,
                    NotificationLog.__table__,
                ],
            )
        )
    maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    try:
        yield maker
    finally:
        await engine.dispose()


async def _seed_minimal(maker: async_sessionmaker) -> dict:
    async with maker() as session:
        org = Organisation(name="O", code="O1", legal_name=None, is_active=True)
        site = Site(organisation=org, name="Main", code="M1", country="CH", is_active=True)
        session.add_all([org, site])
        await session.flush([org, site])
        user = User(
            username="u1",
            email="qa@gmp.test",
            full_name="QA",
            hashed_password=AuthService.hash_password("x" * 12 + "1Aa!"),
            site_id=site.id,
            is_active=True,
        )
        session.add(user)
        await session.flush([user])

        tmpl = NotificationTemplate(
            code="qms_capa_overdue",
            name="Test CAPA overdue",
            event_type="test.capa",
            subject_template="Subject: count={{count}}",
            body_template="Body site={{site_id}} count={{count}}",
            channels=["email"],
            is_active=True,
        )
        session.add(tmpl)
        await session.flush([tmpl])
        session.add(
            NotificationRule(
                template_id=tmpl.id,
                site_id=None,
                recipient_type="fixed_address",
                recipient_address="ops@gmp.test",
                channel="email",
                is_active=True,
            )
        )
        await session.commit()
        return {"site_id": site.id}


@pytest.mark.asyncio
async def test_send_rule_based_writes_log_and_returns_sent_count(notify_session):
    data = await _seed_minimal(notify_session)
    async with notify_session() as session:
        sent = await NotificationService.send_rule_based(
            session,
            "qms_capa_overdue",
            {"count": 3, "site_id": data["site_id"]},
        )
        assert sent == 1
        n = await session.scalar(
            select(func.count()).select_from(NotificationLog).where(
                NotificationLog.recipient_address == "ops@gmp.test"
            )
        )
        assert n == 1
        row = (
            await session.execute(select(NotificationLog).where(NotificationLog.body.contains("3")))
        ).scalar_one()
        assert "count=3" in row.body or "3" in row.body
        assert row.status == "sent"
        assert row.template_id is not None
        await session.commit()


@pytest.mark.asyncio
async def test_send_rule_based_unknown_rule_returns_zero(notify_session):
    await _seed_minimal(notify_session)
    async with notify_session() as session:
        n = await NotificationService.send_rule_based(
            session,
            "nonexistent_rule",
            {"count": 0},
        )
        assert n == 0
        count_logs = await session.scalar(select(func.count()).select_from(NotificationLog))
        assert count_logs == 0
