from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import TypedDict


class ConstitutionalRule(TypedDict):
    line_number: int
    text: str


class ConstitutionalSnapshot(TypedDict):
    source_path: str
    loaded_at: str
    rule_count: int
    rules: list[ConstitutionalRule]


_snapshot: ConstitutionalSnapshot = {
    "source_path": "",
    "loaded_at": "",
    "rule_count": 0,
    "rules": [],
}


def _rules_path() -> Path:
    # backend/app/core/constitutional/service.py -> repo root/.cursorrules
    return Path(__file__).resolve().parents[4] / ".cursorrules"


def load_constitutional_rules() -> ConstitutionalSnapshot:
    path = _rules_path()
    if not path.exists():
        snapshot: ConstitutionalSnapshot = {
            "source_path": str(path),
            "loaded_at": datetime.now(timezone.utc).isoformat(),
            "rule_count": 0,
            "rules": [],
        }
        global _snapshot
        _snapshot = snapshot
        return snapshot

    lines = path.read_text(encoding="utf-8").splitlines()
    rules: list[ConstitutionalRule] = []
    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        rules.append({"line_number": idx, "text": stripped})

    snapshot = {
        "source_path": str(path),
        "loaded_at": datetime.now(timezone.utc).isoformat(),
        "rule_count": len(rules),
        "rules": rules,
    }
    _snapshot = snapshot
    return snapshot


def get_constitutional_rules() -> ConstitutionalSnapshot:
    if not _snapshot["loaded_at"]:
        return load_constitutional_rules()
    return _snapshot

