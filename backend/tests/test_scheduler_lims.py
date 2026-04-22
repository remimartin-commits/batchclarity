from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.audit.models import AuditEvent
from app.core.auth.models import Organisation, Site, User
from app.core.auth.service import AuthService
from app.core.database import Base
from app.modules.lims.models import OOSInvestigation, Sample, TestResult as LimsTestResult
from app.modules.lims.tasks import check_open_oos_investigations


@pytest_asyncio.fixture
async def lims_scheduler_session(tmp_path: Path):
    db_path = tmp_path / "sched_lims.db"
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_path.as_posix()}", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(
            lambda sc: Base.metadata.create_all(
                sc,
                tables=[
                    Organisation.__table__,
                    Site.__table__,
                    User.__table__,
                    AuditEvent.__table__,
                    Sample.__table__,
                    LimsTestResult.__table__,
                    OOSInvestigation.__table__,
                ],
            )
        )
    maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    try:
        yield maker
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_open_oos_scheduler_sends_notification(lims_scheduler_session, monkeypatch):
    notify_calls: list[tuple[str, dict]] = []

    async def _capture_send_rule_based(_session, rule_code: str, payload: dict) -> int:
        notify_calls.append((rule_code, payload))
        return 1

    monkeypatch.setattr(
        "app.modules.lims.tasks.async_session_factory",
        lims_scheduler_session,
    )
    monkeypatch.setattr(
        "app.modules.lims.tasks.NotificationService.send_rule_based",
        _capture_send_rule_based,
    )

    now = datetime.now(timezone.utc)
    async with lims_scheduler_session() as session:
        org = Organisation(name="O", code="O1", legal_name="O", is_active=True)
        site = Site(organisation=org, name="S", code="S1", country="CH", is_active=True)
        session.add_all([org, site])
        await session.flush()

        user = User(
            username="lims",
            email="lims@test.local",
            full_name="LIMS User",
            hashed_password=AuthService.hash_password("Lims1234!"),
            site_id=site.id,
            is_active=True,
        )
        session.add(user)
        await session.flush()

        sample = Sample(
            sample_number="SCHED-SAMPLE-1",
            sample_type="finished_product",
            sampled_at=now - timedelta(days=20),
            sampled_by_id=user.id,
            received_at=now - timedelta(days=20),
            received_by_id=user.id,
            site_id=site.id,
            status="received",
        )
        session.add(sample)
        await session.flush()

        result = LimsTestResult(
            sample_id=sample.id,
            test_method_id="TM-1",
            result_value="120.0",
            result_numeric=120.0,
            unit="%",
            analyst_id=user.id,
            tested_at=now - timedelta(days=20),
            entered_at=now - timedelta(days=20),
            status="oos",
            is_oos=True,
        )
        session.add(result)
        await session.flush()

        investigation = OOSInvestigation(
            investigation_number="OOS-2026-0001",
            sample_id=sample.id,
            initial_result_id=result.id,
            assigned_to_id=user.id,
            status="open",
            created_at=now - timedelta(days=20),
        )
        session.add(investigation)
        await session.commit()

    await check_open_oos_investigations()

    assert notify_calls
    assert notify_calls[0][0] == "lims_oos_investigation_stale"
    assert notify_calls[0][1]["count"] >= 1

