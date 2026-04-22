"""
Lightweight async hook registry (TASK-019 extraction shell).
Production scheduling still uses app.core.tasks for GMP hooks.
"""
from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable

logger = logging.getLogger(__name__)

AsyncHook = Callable[[], Awaitable[object]]
_registry: dict[str, AsyncHook] = {}


def register(name: str, hook: AsyncHook) -> None:
    _registry[name] = hook


def clear() -> None:
    _registry.clear()


def all_hooks() -> dict[str, AsyncHook]:
    return dict(_registry)
