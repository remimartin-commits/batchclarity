"""Task-queue helpers (TASK-019 shell) — parse TASK_QUEUE.md for tooling / audit scripts."""

from __future__ import annotations

from pathlib import Path


def find_task_queue(start: Path | None = None) -> Path:
    root = start or Path(__file__).resolve().parents[2]
    return root / "TASK_QUEUE.md"
