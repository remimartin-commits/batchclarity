"""
TASK-017 — real FastAPI + Postgres chaos: deferred until CI has a postgres service
and a stable test harness (see .github/workflows/chaos-weekly.yml for roadmap).
"""
import pytest


@pytest.mark.skip(reason="Phase-2 chaos against live app: requires postgres service + DSN (TASK-017)")
def test_deferred_chaos_harness_placeholder() -> None:
    assert False
