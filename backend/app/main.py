import os
import sys
import importlib.metadata

# Before FastAPI/Pydantic: plugin discovery scans importlib.metadata over site-packages.
# On Windows, a OneDrive-synced .venv can trigger OSError [Errno 22] during that scan.
if os.name == "nt" and "PYDANTIC_DISABLE_PLUGINS" not in os.environ:
    os.environ["PYDANTIC_DISABLE_PLUGINS"] = "1"

# APScheduler (and others) call importlib.metadata.entry_points() at import time; same OneDrive bug.
if sys.platform == "win32":
    _gmp_entry_points = importlib.metadata.entry_points

    def _gmp_safe_entry_points(*args, **kwargs):
        try:
            return _gmp_entry_points(*args, **kwargs)
        except OSError as exc:
            if exc.errno == 22:
                return importlib.metadata.EntryPoints()
            raise

    importlib.metadata.entry_points = _gmp_safe_entry_points  # type: ignore[assignment]

import logging
from time import perf_counter
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import select, text

from app.core.config import settings
from app.core.database import engine, Base, AsyncSessionLocal
from app.core.tasks import run_overdue_checks, clear_overdue_hooks, register_overdue_hook
from app.api.v1.router import api_router
from app.modules.qms.tasks import check_overdue_capas
from app.modules.equipment.tasks import check_calibration_due
from app.modules.training.tasks import check_overdue_training
from app.core.documents.tasks import check_document_reviews
from app.modules.env_monitoring.tasks import check_overdue_monitoring_reviews
from app.core.integration.models import IntegrationConnector

# ── Import all models so SQLAlchemy/Alembic can discover every table ──────────
# Foundation
from app.core.auth.models import User, Role, Permission, UserSession, PasswordHistory, Site  # noqa
from app.core.audit.models import AuditEvent  # noqa
from app.core.esig.models import ElectronicSignature, SignatureRequirement  # noqa
from app.core.workflow.models import (  # noqa
    WorkflowDefinition, WorkflowState, WorkflowTransition,
    WorkflowInstance, WorkflowHistoryEntry,
)
from app.core.documents.models import DocumentType, Document, DocumentVersion  # noqa
from app.core.notify.models import NotificationTemplate, NotificationRule, NotificationLog  # noqa
from app.core.integration.models import (  # noqa
    IntegrationConnector,
    IntegrationDataFeed,
    IntegrationEventLog,
)

# QMS
from app.modules.qms.models import CAPA, CAPAAction, CAPAAttachment, Deviation, ChangeControl  # noqa

# MES
from app.modules.mes.models import (  # noqa
    Product, MasterBatchRecord, MBRStep, BatchRecord, BatchRecordStep,
)

# Equipment
from app.modules.equipment.models import (  # noqa
    Equipment, CalibrationRecord, QualificationRecord, MaintenanceRecord,
)

# Training
from app.modules.training.models import (  # noqa
    TrainingCurriculum, CurriculumItem, TrainingAssignment, TrainingCompletion,
)

# Environmental Monitoring
from app.modules.env_monitoring.models import (  # noqa
    MonitoringLocation, AlertLimit, MonitoringResult, SamplingPlan, MonitoringTrend,
)

# LIMS
from app.modules.lims.models import (  # noqa
    TestMethod, Specification, SpecificationTest, Sample, TestResult, OOSInvestigation,
)

logger = logging.getLogger(__name__)

# ── APScheduler instance (module-level so lifespan can manage it) ─────────────
scheduler = AsyncIOScheduler(timezone="UTC")

_use_pg_scheduler_lock: bool = not settings.DATABASE_URL.lower().startswith("sqlite")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.

    Startup:
      1. Create all database tables in non-production (dev/test — production uses Alembic).
      2. Optionally acquire PostgreSQL advisory lock; start APScheduler on one worker only.

    Shutdown:
      3. Gracefully shut down the scheduler, release advisory lock, dispose engine.
    """
    if settings.ENVIRONMENT != "production":
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables verified/created (non-production).")
    else:
        logger.info("Skipping create_all in production; use Alembic migrations.")

    run_scheduler = True
    if _use_pg_scheduler_lock:
        async with AsyncSessionLocal() as session:
            r = await session.execute(text("SELECT pg_try_advisory_lock(738194501)"))
            run_scheduler = bool(r.scalar())
            await session.commit()

    if not run_scheduler:
        logger.warning(
            "Scheduler advisory lock not acquired; skipping APScheduler in this worker."
        )
    else:
        clear_overdue_hooks()
        register_overdue_hook("qms_overdue_capas", check_overdue_capas)
        register_overdue_hook("equipment_calibration", check_calibration_due)
        register_overdue_hook("training_overdue", check_overdue_training)
        register_overdue_hook("document_reviews", check_document_reviews)
        register_overdue_hook("env_monitoring_reviews", check_overdue_monitoring_reviews)
        scheduler.add_job(
            run_overdue_checks,
            trigger=IntervalTrigger(hours=6),
            id="overdue_checks",
            name="GMP Overdue Checks (all modules)",
            replace_existing=True,
            misfire_grace_time=300,
            coalesce=True,
        )
        scheduler.start()
        logger.info("APScheduler started — overdue checks every 6 hours.")

    yield

    if run_scheduler:
        scheduler.shutdown(wait=True)
        logger.info("APScheduler shut down.")

    if _use_pg_scheduler_lock and run_scheduler:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT pg_advisory_unlock(738194501)"))
            await session.commit()
        logger.info("Released scheduler PostgreSQL advisory lock.")

    await engine.dispose()
    logger.info("Database engine disposed.")


# ── FastAPI application ───────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Unified GMP Facility Management Platform — "
        "21 CFR Part 11 / EU Annex 11 / ISO 13485 compliant. "
        "Modules: QMS · MES · Equipment · Training · Env Monitoring · LIMS"
    ),
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

if settings.ENVIRONMENT == "development":
    _cors_origins = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]
else:
    _cors_origins = [settings.FRONTEND_URL]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


# ── Health & Scheduler Status Endpoints ──────────────────────────────────────
@app.get("/health", tags=["ops"])
async def health():
    """Docker / load-balancer health probe."""
    return {
        "status": "ok",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "modules": [
            "auth", "documents", "qms", "mes",
            "equipment", "training", "env_monitoring", "lims",
        ],
    }


@app.get("/health/scheduler", tags=["ops"])
async def scheduler_status():
    """Returns APScheduler job state for ops visibility."""
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
            "trigger": str(job.trigger),
        })
    return {
        "scheduler_running": scheduler.running,
        "jobs": jobs,
    }


@app.get("/health/db", tags=["ops"])
async def health_db():
    t0 = perf_counter()
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        ms = (perf_counter() - t0) * 1000.0
        return {"status": "ok", "latency_ms": round(ms, 2)}
    except Exception as exc:
        return {"status": "error", "detail": str(exc), "latency_ms": None}


@app.get("/health/integrations", tags=["ops"])
async def health_integrations():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(IntegrationConnector))
        rows = result.scalars().all()
    return {
        "connectors": [
            {
                "id": c.id,
                "name": c.name,
                "system_type": c.system_type,
                "is_active": c.is_active,
                "last_ping_status": c.last_ping_status,
                "last_ping_at": c.last_ping_at.isoformat() if c.last_ping_at else None,
            }
            for c in rows
        ]
    }
