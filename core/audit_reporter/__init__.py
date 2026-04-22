"""Audit report helpers (TASK-019 shell) — JSON status triage for Matrix Agent reviews."""

from __future__ import annotations

from enum import StrEnum


class Signal(StrEnum):
    GREEN = "GREEN"
    AMBER = "AMBER"
    RED = "RED"


def classify_from_thresholds(
    value: float,
    *,
    amber_above: float | None = None,
    red_above: float | None = None,
) -> Signal:
    if red_above is not None and value >= red_above:
        return Signal.RED
    if amber_above is not None and value >= amber_above:
        return Signal.AMBER
    return Signal.GREEN
