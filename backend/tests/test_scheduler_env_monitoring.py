from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.auth.models import Organisation, Site, User
from app.core.auth.service import AuthService
from app.core.database import Base
from app.modules.env_monitoring.models import MonitoringLocation, MonitoringTrend
from app.modules.env_monitoring.tasks import check_overdue_monitoring_reviews


@pytest_asyncio.fixture
async def env_scheduler_session(tmp_path: Path):
    db_path = tmp_path / "sched_env.db"
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_path.as_posix()}", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(
            lambda sc: Base.metadata.create_all(
                sc,
                tables=[
                    Organisation.__table__,
                    Site.__table__,
                    User.__table__,
                    MonitoringLocation.__table__,
                    MonitoringTrend.__table__,
                ],
            )
        )
    maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    try:
        yield maker
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_overdue_env_reviews_scheduler_notifies(env_scheduler_session, monkeypatch):
    notify_calls: list[tuple[str, dict]] = []

    async def _capture_send_rule_based(_session, rule_code: str, payload: dict) -> int:
        notify_calls.append((rule_code, payload))
        return 1

    monkeypatch.setattr(
        "app.modules.env_monitoring.tasks.async_session_factory",
        env_scheduler_session,
    )
    monkeypatch.setattr(
        "app.modules.env_monitoring.tasks.NotificationService.send_rule_based",
        _capture_send_rule_based,
    )

    now = datetime.now(timezone.utc)
    async with env_scheduler_session() as session:
        org = Organisation(name="O", code="O1", legal_name="O", is_active=True)
        site = Site(organisation=org, name="S", code="S1", country="CH", is_active=True)
        session.add_all([org, site])
        await session.flush()

        user = User(
            username="env",
            email="env@test.local",
            full_name="Env User",
            hashed_password=AuthService.hash_password("Env1234!"),
            site_id=site.id,
            is_active=True,
        )
        session.add(user)
        await session.flush()

        loc = MonitoringLocation(
            code="ENV-LOC-1",
            name="Grade C Corridor",
            room="C-12",
            gmp_grade="C",
            site_id=site.id,
            is_active=True,
        )
        session.add(loc)
        await session.flush()

        trend = MonitoringTrend(
            location_id=loc.id,
            parameter="particles_0_5um",
            period_start=now - timedelta(days=30),
            period_end=now - timedelta(days=1),
            status="pending",
            sample_count=10,
            alert_exceedances=1,
            action_exceedances=0,
            reviewed_at=None,
        )
        session.add(trend)
        await session.commit()

    result = await check_overdue_monitoring_reviews()
    assert result["overdue"] >= 1
    assert notify_calls
    assert notify_calls[0][0] == "env_monitoring_review_overdue"

