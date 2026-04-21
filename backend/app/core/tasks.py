"""Background task registry used by scheduler.

This module intentionally has no imports from business modules.
Business modules register their own hooks at startup.
"""
from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable

logger = logging.getLogger(__name__)

OverdueHook = Callable[[], Awaitable[object]]
_overdue_hooks: dict[str, OverdueHook] = {}


def register_overdue_hook(name: str, hook: OverdueHook) -> None:
    _overdue_hooks[name] = hook


def clear_overdue_hooks() -> None:
    _overdue_hooks.clear()


async def run_overdue_checks() -> dict[str, object]:
    """Run registered overdue hooks sequentially."""
    results: dict[str, object] = {}
    logger.info("=== Background task: run_overdue_checks START ===")
    for name, hook in _overdue_hooks.items():
        try:
            results[name] = await hook()
        except Exception as exc:  # pragma: no cover - scheduler safety net
            logger.error("Overdue hook '%s' failed: %s", name, exc)
            results[name] = "error"
    logger.info("=== Background task: run_overdue_checks COMPLETE: %s ===", results)
    return results
