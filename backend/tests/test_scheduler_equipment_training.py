"""TASK-002: overdue flags on calibration & training after hooks run (SQLite)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.auth.models import Organisation, Site, User
from app.core.auth.service import AuthService
from app.core.database import Base
from app.modules.equipment.models import CalibrationRecord, Equipment
from app.core.notify.service import NotificationService
from app.modules.equipment.tasks import check_calibration_due
from app.modules.training.models import CurriculumItem, TrainingAssignment, TrainingCurriculum
from app.modules.training.tasks import check_overdue_training


async def _noop_send_rule_based(*args, **kwargs) -> int:
    return 0


@pytest_asyncio.fixture
async def eq_tr_session(tmp_path: Path):
    db_path = tmp_path / "sched_eq_tr.db"
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_path.as_posix()}", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(
            lambda sc: Base.metadata.create_all(
                sc,
                tables=[
                    Organisation.__table__,
                    Site.__table__,
                    User.__table__,
                    Equipment.__table__,
                    CalibrationRecord.__table__,
                    TrainingCurriculum.__table__,
                    CurriculumItem.__table__,
                    TrainingAssignment.__table__,
                ],
            )
        )
    maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    try:
        yield maker
    finally:
        await engine.dispose()


async def _seed_user_site(session) -> User:
    org = Organisation(name="O", code="O1", legal_name="O", is_active=True)
    site = Site(organisation=org, name="S", code="S1", country="CH", is_active=True)
    session.add_all([org, site])
    await session.flush()
    u = User(
        username="cal",
        email="cal@t.local",
        full_name="Cal",
        hashed_password=AuthService.hash_password("x" * 12 + "1Aa!"),
        site_id=site.id,
        is_active=True,
    )
    session.add(u)
    await session.flush()
    return u


@pytest.mark.asyncio
async def test_calibration_is_overdue_flag_after_hook(eq_tr_session, monkeypatch):
    notify_calls: list[tuple[str, dict]] = []

    async def _capture_send_rule_based(_session, rule_code: str, payload: dict) -> int:
        notify_calls.append((rule_code, payload))
        return 1

    monkeypatch.setattr(
        "app.modules.equipment.tasks.async_session_factory",
        eq_tr_session,
    )
    monkeypatch.setattr(
        NotificationService,
        "send_rule_based",
        _capture_send_rule_based,
    )
    now = datetime.now(timezone.utc)
    rid: str
    async with eq_tr_session() as session:
        u = await _seed_user_site(session)
        eq = Equipment(
            equipment_id="EQ1",
            name="X",
            equipment_type="a",
            site_id=(await session.execute(select(Site).limit(1))).scalar_one().id,
            owner_id=u.id,
        )
        session.add(eq)
        await session.flush()
        rec = CalibrationRecord(
            equipment_id=eq.id,
            calibration_number="C1",
            calibration_type="scheduled",
            performed_by_id=u.id,
            performed_at=now - timedelta(days=60),
            next_calibration_due=now - timedelta(days=1),
            result="pass",
            is_overdue=False,
        )
        session.add(rec)
        await session.flush()
        rid = rec.id
        await session.commit()

    await check_calibration_due()

    async with eq_tr_session() as session:
        r = (await session.execute(select(CalibrationRecord).where(CalibrationRecord.id == rid))).scalar_one()
        assert r.is_overdue is True
    assert notify_calls
    assert notify_calls[0][0] == "equipment_calibration_due"


@pytest.mark.asyncio
async def test_training_status_overdue_after_hook(eq_tr_session, monkeypatch):
    monkeypatch.setattr(
        "app.modules.training.tasks.async_session_factory",
        eq_tr_session,
    )
    monkeypatch.setattr(
        NotificationService,
        "send_rule_based",
        _noop_send_rule_based,
    )
    now = datetime.now(timezone.utc)
    async with eq_tr_session() as session:
        u = await _seed_user_site(session)
        site = (await session.execute(select(Site).limit(1))).scalar_one()
        cur = TrainingCurriculum(
            name="C",
            code="C1",
            site_id=site.id,
        )
        session.add(cur)
        await session.flush()
        item = CurriculumItem(
            curriculum_id=cur.id,
            sequence=1,
            item_type="document",
            title="T",
        )
        session.add(item)
        await session.flush()
        ass = TrainingAssignment(
            user_id=u.id,
            curriculum_item_id=item.id,
            assigned_by_id=u.id,
            assigned_at=now - timedelta(days=10),
            due_date=now - timedelta(days=1),
            status="pending",
        )
        session.add(ass)
        await session.commit()
        aid = ass.id

    await check_overdue_training()

    async with eq_tr_session() as session:
        row = (await session.execute(select(TrainingAssignment).where(TrainingAssignment.id == aid))).scalar_one()
        assert row.status == "overdue"
