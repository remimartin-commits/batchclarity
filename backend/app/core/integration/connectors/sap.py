"""
SAP integration (TASK-014) — read-only ERP sync; use IntegrationConnector rows + IntegrationEventLog.
"""
from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.integration.models import IntegrationConnector, IntegrationEventLog

logger = logging.getLogger(__name__)


class SAPRestConnector:
    """Minimal SAP OData / REST shape; wire credentials from connector.connection_config."""

    def __init__(self, connector: IntegrationConnector) -> None:
        self._connector = connector
        self._config: dict[str, Any] = connector.connection_config

    async def health_ping(self, session: AsyncSession) -> bool:
        """Return True if endpoint is configured; real call would use httpx + OAuth."""
        try:
            _ = self._config.get("base_url", "")
            return bool(_)
        except Exception as exc:  # pragma: no cover
            session.add(
                IntegrationEventLog(
                    connector_id=self._connector.id,
                    organisation_id=self._connector.organisation_id,
                    operation="sap.health",
                    direction="outbound",
                    status="failed",
                    error_message=str(exc)[:2000],
                )
            )
            await session.flush()
            return False
