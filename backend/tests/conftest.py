from __future__ import annotations

from pathlib import Path

import pytest
import pytest_asyncio
from fastapi import APIRouter, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api.v1.users import router as users_router
from app.core.audit.models import AuditEvent
from app.core.auth.models import (
    Organisation,
    PasswordHistory,
    Permission,
    Role,
    Site,
    User,
    UserSession,
    role_permissions,
    user_roles,
)
from app.core.auth.router import router as auth_router
from app.core.auth.service import AuthService
from app.core.database import Base, get_db
from app.core.documents.models import Document, DocumentType, DocumentVersion
from app.core.documents.router import router as documents_router
from app.core.esig.models import ElectronicSignature
from app.core.workflow.models import WorkflowDefinition, WorkflowInstance
from app.modules.equipment.models import CalibrationRecord, Equipment, MaintenanceRecord, QualificationRecord
from app.modules.equipment.router import router as equipment_router
from app.modules.qms.models import CAPA, CAPAAction, ChangeControl, Deviation
from app.modules.qms.router import router as qms_router
from app.modules.mes.models import Product, MasterBatchRecord, MBRStep, BatchRecord, BatchRecordStep
from app.modules.mes.router import router as mes_router
from app.modules.lims.models import TestMethod, Specification, SpecificationTest, Sample, TestResult, OOSInvestigation
from app.modules.lims.router import router as lims_router
from app.modules.training.models import CurriculumItem, TrainingAssignment, TrainingCompletion, TrainingCurriculum
from app.modules.training.router import router as training_router


@pytest_asyncio.fixture
async def session_maker(tmp_path: Path):
    db_path = tmp_path / "api_behavior.db"
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_path.as_posix()}", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(
            lambda sync_conn: Base.metadata.create_all(
                sync_conn,
                tables=[
                    Organisation.__table__,
                    Site.__table__,
                    User.__table__,
                    Role.__table__,
                    Permission.__table__,
                    user_roles,
                    role_permissions,
                    UserSession.__table__,
                    PasswordHistory.__table__,
                    AuditEvent.__table__,
                    WorkflowDefinition.__table__,
                    WorkflowInstance.__table__,
                    CAPA.__table__,
                    CAPAAction.__table__,
                    Deviation.__table__,
                    ChangeControl.__table__,
                    DocumentType.__table__,
                    Document.__table__,
                    DocumentVersion.__table__,
                    ElectronicSignature.__table__,
                    TrainingCurriculum.__table__,
                    CurriculumItem.__table__,
                    TrainingAssignment.__table__,
                    TrainingCompletion.__table__,
                    Product.__table__,
                    MasterBatchRecord.__table__,
                    MBRStep.__table__,
                    BatchRecord.__table__,
                    BatchRecordStep.__table__,
                    TestMethod.__table__,
                    Specification.__table__,
                    SpecificationTest.__table__,
                    Sample.__table__,
                    TestResult.__table__,
                    OOSInvestigation.__table__,
                    Equipment.__table__,
                    CalibrationRecord.__table__,
                    QualificationRecord.__table__,
                    MaintenanceRecord.__table__,
                ],
            )
        )

    maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    try:
        yield maker
    finally:
        await engine.dispose()


@pytest_asyncio.fixture
async def seeded_db(session_maker):
    async with session_maker() as session:
        org = Organisation(name="Test Org", code="TST", legal_name="Test Org Ltd", is_active=True)
        site = Site(organisation=org, name="Main", code="MAIN", country="CH", is_active=True)
        session.add_all([org, site])
        await session.flush([org, site])

        p_users = Permission(
            code="admin.users.manage",
            module="admin",
            resource="users",
            action="manage",
            description="Manage users",
        )
        p_roles = Permission(
            code="admin.roles.manage",
            module="admin",
            resource="roles",
            action="manage",
            description="Manage roles",
        )
        p_dev_submit = Permission(code="qms.deviations.submit", module="qms", resource="deviations", action="submit", description="Submit deviations")
        p_dev_approve = Permission(code="qms.deviations.approve", module="qms", resource="deviations", action="approve", description="Approve deviations")
        p_dev_close = Permission(code="qms.deviations.close", module="qms", resource="deviations", action="close", description="Close deviations")
        p_dev_sign = Permission(code="qms.deviations.sign", module="qms", resource="deviations", action="sign", description="Sign deviations")
        p_cc_submit = Permission(code="qms.change_controls.submit", module="qms", resource="change_controls", action="submit", description="Submit change controls")
        p_cc_approve = Permission(code="qms.change_controls.approve", module="qms", resource="change_controls", action="approve", description="Approve change controls")
        p_cc_implement = Permission(code="qms.change_controls.implement", module="qms", resource="change_controls", action="implement", description="Implement change controls")
        p_cc_close = Permission(code="qms.change_controls.close", module="qms", resource="change_controls", action="close", description="Close change controls")
        p_cc_sign = Permission(code="qms.change_controls.sign", module="qms", resource="change_controls", action="sign", description="Sign change controls")

        role_admin = Role(name="Administrator", description="System admin", is_system_role=True)
        role_admin.permissions.extend([
            p_users, p_roles,
            p_dev_submit, p_dev_approve, p_dev_close, p_dev_sign,
            p_cc_submit, p_cc_approve, p_cc_implement, p_cc_close, p_cc_sign,
        ])
        role_view = Role(name="Viewer", description="Read only", is_system_role=False)

        admin_user = User(
            username="admin",
            email="admin@test.local",
            full_name="Admin User",
            hashed_password=AuthService.hash_password("Admin1234!"),
            site_id=site.id,
            is_active=True,
            must_change_password=False,
        )
        basic_user = User(
            username="operator",
            email="operator@test.local",
            full_name="Operator User",
            hashed_password=AuthService.hash_password("Operator1234!"),
            site_id=site.id,
            is_active=True,
            must_change_password=False,
        )
        admin_user.roles.append(role_admin)
        basic_user.roles.append(role_view)

        doc_type = DocumentType(
            code="SOP",
            name="Standard Operating Procedure",
            prefix="SOP",
            requires_periodic_review=True,
            review_period_months=24,
            requires_training=True,
        )

        curriculum = TrainingCurriculum(
            name="Core GMP",
            code="GMP-CORE",
            description="Baseline GMP curriculum",
            target_roles=["operator"],
            target_departments=["manufacturing"],
            is_gmp_mandatory=True,
            site_id=site.id,
            is_active=True,
        )
        session.add_all([doc_type, curriculum])
        await session.flush([doc_type, curriculum])
        curriculum_item = CurriculumItem(
            curriculum_id=curriculum.id,
            sequence=1,
            item_type="document",
            title="Read core SOP",
            is_mandatory=True,
            requires_assessment=False,
        )
        session.add(curriculum_item)

        session.add_all([
            p_users, p_roles,
            p_dev_submit, p_dev_approve, p_dev_close, p_dev_sign,
            p_cc_submit, p_cc_approve, p_cc_implement, p_cc_close, p_cc_sign,
            role_admin, role_view, admin_user, basic_user,
        ])
        await session.commit()
    return {
        "admin_username": "admin",
        "admin_password": "Admin1234!",
        "operator_username": "operator",
        "operator_password": "Operator1234!",
    }


@pytest.fixture
def client(session_maker, seeded_db):
    app = FastAPI()
    api = APIRouter(prefix="/api/v1")
    api.include_router(auth_router)
    api.include_router(users_router)
    api.include_router(qms_router)
    api.include_router(mes_router)
    api.include_router(lims_router)
    api.include_router(documents_router)
    api.include_router(training_router)
    api.include_router(equipment_router)
    app.include_router(api)

    async def override_get_db():
        async with session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c

