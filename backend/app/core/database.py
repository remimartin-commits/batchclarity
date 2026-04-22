import logging

from sqlalchemy import DateTime, String, event
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from datetime import datetime, timezone
import uuid
from app.core.config import settings


def _async_postgres_url(url: str) -> str:
    """Supabase and many dashboards give postgresql://… which defaults to sync psycopg2.
    create_async_engine needs an async driver (we use asyncpg).
    """
    if url.startswith("sqlite"):
        return url
    if url.startswith("postgres://"):
        return "postgresql+asyncpg://" + url[len("postgres://") :]
    if url.startswith("postgresql+psycopg2://"):
        return "postgresql+asyncpg://" + url[len("postgresql+psycopg2://") :]
    if url.startswith("postgresql://"):
        return "postgresql+asyncpg://" + url[len("postgresql://") :]
    return url


_database_url = _async_postgres_url(settings.DATABASE_URL)

_is_sqlite = _database_url.startswith("sqlite")
_logger = logging.getLogger(__name__)

_engine_kwargs: dict = {"echo": settings.DEBUG}
if _is_sqlite:
    # SQLite: single-file, no pool config needed, check_same_thread=False for async
    from sqlalchemy.pool import StaticPool
    _engine_kwargs["connect_args"] = {"check_same_thread": False}
    _engine_kwargs["poolclass"] = StaticPool
else:
    _engine_kwargs["pool_pre_ping"] = True
    _engine_kwargs["pool_size"] = 20
    _engine_kwargs["max_overflow"] = 40
    _engine_kwargs["pool_timeout"] = 30
    _engine_kwargs["pool_recycle"] = 3600

engine = create_async_engine(_database_url, **_engine_kwargs)

if not _is_sqlite:
    @event.listens_for(engine.sync_engine, "connect")
    def _set_postgres_statement_timeout(dbapi_connection, _connection_record) -> None:
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("SET statement_timeout = '30s'")
        except Exception as exc:  # pragma: no cover
            _logger.warning("Could not set statement_timeout: %s", exc)
        finally:
            cursor.close()

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """
    All GMP platform models inherit from this base.
    Every table automatically gets:
      - id (UUID primary key)
      - created_at (immutable, set on insert)
      - updated_at (auto-updated on every write)
    These fields are part of the ALCOA+ data integrity guarantee.
    """
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Standalone session factory for background tasks (not request-scoped).
# Background tasks (APScheduler jobs, Celery workers) must use this instead
# of get_db() because they operate outside the FastAPI request/response cycle.
async_session_factory = AsyncSessionLocal
