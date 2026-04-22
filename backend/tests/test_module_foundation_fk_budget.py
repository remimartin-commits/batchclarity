"""
TASK-016 — prevent unbounded foundation coupling: each business module `models.py`
should not declare an excessive number of ORM foreign keys (rough guardrail).
"""
from __future__ import annotations

from pathlib import Path

MODULES_ROOT = Path(__file__).resolve().parents[1] / "app" / "modules"
MAX_FK_PER_MODULE_MODELS = 40  # loose ceiling for current skeleton; tighten as modules grow


def test_each_module_models_fk_count_under_ceiling() -> None:
    for mod_dir in sorted(MODULES_ROOT.iterdir()):
        if not mod_dir.is_dir() or mod_dir.name.startswith("_"):
            continue
        p = mod_dir / "models.py"
        if not p.exists():
            continue
        n = p.read_text(encoding="utf-8").count("ForeignKey(")
        assert n <= MAX_FK_PER_MODULE_MODELS, (
            f"{mod_dir.name}/models.py declares {n} ForeignKey( occurrences (limit {MAX_FK_PER_MODULE_MODELS})"
        )
