"""
DeltaV / historian read connector (TASK-015) — read-only; never write to the control system.
"""
from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.integration.models import IntegrationConnector, IntegrationEventLog

logger = logging.getLogger(__name__)


class DeltaVHistorianConnector:
    """Placeholder PI / DeltaV historian query; config in connection_config (tag server URL, creds)."""

    def __init__(self, connector: IntegrationConnector) -> None:
        self._connector = connector
        self._config: dict[str, Any] = connector.connection_config

    async def health_ping(self, session: AsyncSession) -> bool:
        try:
            return bool(self._config.get("historian_url", ""))
        except Exception as exc:  # pragma: no cover
            session.add(
                IntegrationEventLog(
                    connector_id=self._connector.id,
                    organisation_id=self._connector.organisation_id,
                    operation="deltav.historian.health",
                    direction="inbound",
                    status="failed",
                    error_message=str(exc)[:2000],
                )
            )
            await session.flush()
            return False
