"""Alembic migration environment — GMP Platform.

Supports async SQLAlchemy (asyncpg driver).
Database URL: DATABASE_URL env, or backend/.env (same keys as the app), then alembic.ini.
All postgres:// / postgresql:// URLs are normalized to postgresql+asyncpg:// for async.
"""
import asyncio
import os
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context


def _load_backend_dotenv() -> None:
    """Populate os.environ from backend/.env when vars are not already set (CLI has no pydantic)."""
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if not env_path.is_file():
        return
    try:
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = val
    except OSError:
        pass


# ── Import ALL models so Alembic detects every table ─────────────────────────
_load_backend_dotenv()

from app.core.database import Base, _async_postgres_url  # noqa: F401

# Core models
import app.core.auth.models  # noqa: F401
import app.core.audit.models  # noqa: F401
import app.core.esig.models  # noqa: F401
import app.core.workflow.models  # noqa: F401
import app.core.notify.models  # noqa: F401
import app.core.documents.models  # noqa: F401
import app.core.integration.models  # noqa: F401

# Module models
import app.modules.qms.models  # noqa: F401
import app.modules.mes.models  # noqa: F401
import app.modules.equipment.models  # noqa: F401
import app.modules.training.models  # noqa: F401
import app.modules.env_monitoring.models  # noqa: F401
import app.modules.lims.models  # noqa: F401

# ── Alembic config ────────────────────────────────────────────────────────────
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# ── Resolve async database URL (sync psycopg2 URLs break async_engine_from_config) ─
_env_url = os.getenv("DATABASE_URL", "").strip()
_ini_url = (config.get_main_option("sqlalchemy.url") or "").strip()
if _env_url:
    _resolved = _async_postgres_url(_env_url)
elif _ini_url:
    _resolved = _async_postgres_url(_ini_url)
else:
    _resolved = ""
if _resolved:
    config.set_main_option("sqlalchemy.url", _resolved)


# ── Offline mode (generate SQL without connecting) ────────────────────────────
def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    In this mode, the context is configured with just a URL and not an Engine.
    Useful for generating migration SQL scripts without a live database.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


# ── Online (async) mode ────────────────────────────────────────────────────────
def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    configuration = config.get_section(config.config_ini_section, {})
    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
