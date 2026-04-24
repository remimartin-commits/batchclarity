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
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.core.config import settings
from app.core.attachment_config import validate_supabase_for_startup
from app.core.database import engine, Base
from app.core.tasks import run_overdue_checks, clear_overdue_hooks, register_overdue_hook
from app.core.constitutional.service import load_constitutional_rules
from app.api.v1.router import api_router
from app.modules.qms.tasks import check_overdue_capas
from app.modules.equipment.tasks import check_calibration_due
from app.modules.training.tasks import check_overdue_training
from app.core.documents.tasks import check_document_reviews
from app.modules.lims.tasks import check_open_oos_investigations
from app.modules.mes.tasks import check_stale_batches

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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.

    Startup:
      1. Create all database tables (dev/test convenience — production uses Alembic).
      2. Start APScheduler with GMP compliance background jobs.

    Shutdown:
      3. Gracefully shut down the scheduler (allow in-flight jobs to finish).
      4. Dispose the SQLAlchemy engine connection pool.
    """
    validate_supabase_for_startup()
    # 1. Database table creation (idempotent; Alembic handles migrations in production)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables verified/created.")
    constitutional_snapshot = load_constitutional_rules()
    logger.info(
        "Constitutional rules loaded: %s rule(s) from %s",
        constitutional_snapshot["rule_count"],
        constitutional_snapshot["source_path"],
    )

    # 2. Register and start background jobs
    clear_overdue_hooks()
    register_overdue_hook("qms_overdue_capas", check_overdue_capas)
    register_overdue_hook("equipment_calibration", check_calibration_due)
    register_overdue_hook("training_overdue", check_overdue_training)
    register_overdue_hook("document_reviews", check_document_reviews)
    register_overdue_hook("mes_stale_batches", check_stale_batches)
    register_overdue_hook("lims_oos_stale", check_open_oos_investigations)
    #    run_overdue_checks() fires every 6 hours and handles:
    #      - Overdue CAPA notifications
    #      - Equipment calibration due / overdue alerts
    #      - Overdue training assignment reminders
    #      - Document periodic review reminders (60-day look-ahead)
    scheduler.add_job(
        run_overdue_checks,
        trigger=IntervalTrigger(hours=6),
        id="overdue_checks",
        name="GMP Overdue Checks (CAPA / Calibration / Training / Documents)",
        replace_existing=True,
        misfire_grace_time=300,   # 5-minute grace period if a fire is missed
        coalesce=True,            # Collapse multiple missed fires into one
    )
    scheduler.start()
    logger.info("APScheduler started — overdue checks every 6 hours.")

    yield

    # 3. Graceful scheduler shutdown
    scheduler.shutdown(wait=True)
    logger.info("APScheduler shut down.")

    # 4. Release DB connection pool
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

# Production: lock to known origins. Development: allow all for convenience.
_PRODUCTION_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "https://t160mfctr8bq.space.minimax.io",
    "https://nqedqxebbh8j.space.minimax.io",
    "https://gmp-platform-backend-production.up.railway.app",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_PRODUCTION_ORIGINS if settings.ENVIRONMENT == "production" else ["*"],
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
