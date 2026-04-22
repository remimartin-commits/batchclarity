"""Smoke-import TASK-019 extracted packages (repo root `core/`)."""
from __future__ import annotations

from core import event_bus, task_orchestrator
from core.audit_reporter import Signal, classify_from_thresholds


def test_event_bus_register_clear() -> None:
    async def _a():
        return "x"

    event_bus.register("t1", _a)
    assert "t1" in event_bus.all_hooks()
    event_bus.clear()
    assert event_bus.all_hooks() == {}


def test_task_orchestrator_finds_task_queue() -> None:
    p = task_orchestrator.find_task_queue()
    assert p.name == "TASK_QUEUE.md"


def test_audit_reporter_signal() -> None:
    assert classify_from_thresholds(0.1, amber_above=0.2, red_above=0.5) is Signal.GREEN
    assert classify_from_thresholds(0.3, amber_above=0.2, red_above=0.5) is Signal.AMBER
    assert classify_from_thresholds(0.6, amber_above=0.2, red_above=0.5) is Signal.RED
