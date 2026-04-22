"""
GMP Platform — Audit Report Generator
======================================
Generates a structured JSON report for Matrix Agent's 3-day review cycle.

Run locally:   python scripts/generate_audit_report.py
CI:            .github/workflows/audit-report.yml (every 3 days)
Output:        audit/reports/YYYY-MM-DD-audit.json
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
AUDIT_DIR = REPO_ROOT / "audit" / "reports"
CHAOS_REPORT = REPO_ROOT / "chaos" / "last-report.json"
TASK_QUEUE = REPO_ROOT / "TASK_QUEUE.md"
ALEMBIC_VERSIONS = REPO_ROOT / "backend" / "alembic" / "versions"


def _run(cmd: list[str]) -> tuple[int, str, str]:
    r = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True)
    return r.returncode, r.stdout.strip(), r.stderr.strip()


# ── Git activity ──────────────────────────────────────────────────────────────

def git_activity() -> dict:
    _, log, _ = _run(["git", "log", "--since=3 days ago", "--oneline", "--no-merges"])
    commits = [l for l in log.splitlines() if l.strip()]
    _, authors_raw, _ = _run(["git", "log", "--since=3 days ago", "--format=%ae", "--no-merges"])
    authors = list(set(a for a in authors_raw.splitlines() if a.strip()))
    _, files_raw, _ = _run(["git", "diff", f"HEAD~{max(len(commits),1)}", "--name-only"])
    files = [f for f in files_raw.splitlines() if f.strip()]
    return {
        "commits_last_3_days": len(commits),
        "commits": commits[:20],
        "authors": authors,
        "files_changed": len(files),
        "files": files[:50],
    }


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_results() -> dict:
    rc_arch, out_arch, err_arch = _run([
        sys.executable, "-m", "pytest",
        "backend/tests/test_architecture_boundaries.py",
        "-v", "--tb=short", "--no-header",
    ])
    rc_full, out_full, err_full = _run([
        sys.executable, "-m", "pytest", "backend/tests/",
        "--tb=line", "--no-header", "-q",
        "--ignore=backend/tests/test_architecture_boundaries.py",
    ])
    passed = failed = errors = 0
    for line in (out_full + err_full).splitlines():
        if m := re.search(r"(\d+) passed", line): passed = int(m.group(1))
        if m := re.search(r"(\d+) failed", line): failed = int(m.group(1))
        if m := re.search(r"(\d+) error", line): errors = int(m.group(1))
    return {
        "architecture_tests": {
            "passed": rc_arch == 0,
            "exit_code": rc_arch,
            "snippet": (out_arch + err_arch)[-1500:],
        },
        "full_suite": {
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "all_passing": rc_full == 0,
        },
    }


# ── Chaos ─────────────────────────────────────────────────────────────────────

def chaos_results() -> dict:
    if not CHAOS_REPORT.exists():
        _run([sys.executable, str(REPO_ROOT / "chaos.py")])
    if not CHAOS_REPORT.exists():
        return {"available": False}
    try:
        data = json.loads(CHAOS_REPORT.read_text())
        return {
            "available": True,
            "all_passed": data.get("all_passed", False),
            "timestamp": data.get("timestamp"),
            "scenarios": [
                {"name": s["name"], "passed": s["passed"],
                 "recovery_ms": s.get("time_to_recovery_ms"),
                 "integrity": s.get("data_integrity")}
                for s in data.get("scenarios", [])
            ],
        }
    except Exception as exc:
        return {"available": False, "error": str(exc)}


# ── Task queue ────────────────────────────────────────────────────────────────

def task_queue_status() -> dict:
    if not TASK_QUEUE.exists():
        return {"error": "TASK_QUEUE.md not found"}
    content = TASK_QUEUE.read_text(encoding="utf-8")
    tasks: list[dict] = []
    current: dict | None = None
    for line in content.splitlines():
        if m := re.match(r"^### (TASK-\d+) — (.+)$", line.strip()):
            if current:
                tasks.append(current)
            current = {"id": m.group(1), "title": m.group(2), "priority": "", "status": ""}
        if current:
            if m := re.match(r"^- \*\*Priority:\*\* (.+)$", line.strip()):
                current["priority"] = m.group(1)
            if m := re.match(r"^- \*\*Status:\*\* (.+)$", line.strip()):
                current["status"] = m.group(1)
    if current:
        tasks.append(current)
    counts: dict[str, int] = {"PENDING": 0, "IN_PROGRESS": 0, "DONE": 0, "BLOCKED": 0}
    for t in tasks:
        s = t["status"].upper()
        if s in counts:
            counts[s] += 1
    return {
        "counts": counts,
        "blocked": [t for t in tasks if "BLOCKED" in t["status"].upper()],
        "in_progress": [t for t in tasks if "IN_PROGRESS" in t["status"].upper()],
        "next_pending": [t for t in tasks if "PENDING" in t["status"].upper()][:3],
    }


# ── Migrations ────────────────────────────────────────────────────────────────

def migration_info() -> dict:
    if not ALEMBIC_VERSIONS.exists():
        return {"error": "alembic/versions not found"}
    all_m = sorted(ALEMBIC_VERSIONS.glob("*.py"), key=lambda p: p.name)
    _, recent_raw, _ = _run([
        "git", "log", "--since=3 days ago", "--name-only",
        "--format=", "--", "backend/alembic/versions/",
    ])
    new = [f for f in recent_raw.splitlines() if f.endswith(".py") and f.strip()]
    return {
        "total": len(all_m),
        "new_last_3_days": len(new),
        "new_files": new,
        "recent": [m.name for m in all_m[-5:]],
    }


# ── Module completeness ───────────────────────────────────────────────────────

def module_status() -> dict:
    modules_path = REPO_ROOT / "backend" / "app" / "modules"
    if not modules_path.exists():
        return {"error": "modules directory not found"}
    modules = []
    for d in sorted(modules_path.iterdir()):
        if not d.is_dir() or d.name.startswith("_"):
            continue
        files = {f.name for f in d.iterdir()}
        has = {
            "models": "models.py" in files,
            "router": "router.py" in files,
            "services": "services.py" in files,
            "tasks": "tasks.py" in files,
            "schemas": "schemas.py" in files,
        }
        score = sum(has.values())
        modules.append({"name": d.name, **has, "score": f"{score}/5"})
    return {
        "count": len(modules),
        "fully_complete": sum(1 for m in modules if m["score"] == "5/5"),
        "modules": modules,
    }


# ── Architecture violation scan ───────────────────────────────────────────────

def architecture_violations() -> dict:
    violations = []
    # Cross-module Python imports
    _, out, _ = _run([
        "grep", "-rn", "from app.modules.",
        "backend/app/modules/", "--include=*.py",
    ])
    for line in out.splitlines():
        if m := re.match(r"backend/app/modules/(\w+)/.+:.*from app\.modules\.(\w+)", line):
            if m.group(1) != m.group(2):
                violations.append({"type": "cross_module_import", "line": line.strip()})
    # Cross-module FKs (grep-based, supplements AST test)
    module_tables = {
        "qms": ["capas", "deviations", "change_controls", "capa_actions"],
        "mes": ["products", "master_batch_records", "batch_records", "batch_record_steps", "mbr_steps"],
        "equipment": ["equipment", "calibration_records", "qualification_records", "maintenance_records"],
        "training": ["training_curricula", "curriculum_items", "training_assignments", "training_completions"],
        "lims": ["test_methods", "specifications", "samples", "test_results", "oos_investigations"],
        "env_monitoring": ["monitoring_locations", "monitoring_results", "monitoring_trends"],
    }
    _, out2, _ = _run([
        "grep", "-rn", r'ForeignKey("',
        "backend/app/modules/", "--include=*.py",
    ])
    for line in out2.splitlines():
        src = re.match(r"backend/app/modules/(\w+)/", line)
        fk = re.search(r'ForeignKey\("(\w+)\.', line)
        if not src or not fk:
            continue
        for mod, tables in module_tables.items():
            if mod != src.group(1) and fk.group(1) in tables:
                violations.append({
                    "type": "cross_module_fk",
                    "from": src.group(1), "to": mod,
                    "table": fk.group(1), "line": line.strip(),
                })
    return {"count": len(violations), "clean": len(violations) == 0, "violations": violations}


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> int:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc)

    sections = {
        "git_activity": git_activity(),
        "tests": test_results(),
        "chaos": chaos_results(),
        "task_queue": task_queue_status(),
        "migrations": migration_info(),
        "modules": module_status(),
        "architecture_violations": architecture_violations(),
    }

    tests_ok = sections["tests"]["architecture_tests"]["passed"]
    chaos_ok = sections["chaos"].get("all_passed", False)
    violations_ok = sections["architecture_violations"]["clean"]
    blocked = sections["task_queue"]["counts"].get("BLOCKED", 0)

    health = (
        "GREEN" if (tests_ok and chaos_ok and violations_ok and blocked == 0)
        else "AMBER" if (tests_ok and violations_ok)
        else "RED"
    )

    report = {
        "generated_at": ts.isoformat(),
        "report_date": ts.strftime("%Y-%m-%d"),
        "health": {
            "overall": health,
            "architecture_tests_passing": tests_ok,
            "chaos_suite_passing": chaos_ok,
            "no_violations": violations_ok,
            "blocked_tasks": blocked,
        },
        "sections": sections,
    }

    out_path = AUDIT_DIR / f"{ts.strftime('%Y-%m-%d')}-audit.json"
    out_path.write_text(json.dumps(report, indent=2))

    print(f"\n{'═'*50}")
    print(f"  AUDIT — {report['report_date']}  [{health}]")
    print(f"{'═'*50}")
    print(f"  Arch tests:    {'PASS' if tests_ok else 'FAIL'}")
    print(f"  Chaos:         {'PASS' if chaos_ok else 'FAIL'}")
    print(f"  Violations:    {sections['architecture_violations']['count']}")
    print(f"  Tasks PENDING: {sections['task_queue']['counts'].get('PENDING',0)}")
    print(f"  Tasks BLOCKED: {blocked}")
    print(f"  Commits (3d):  {sections['git_activity']['commits_last_3_days']}")
    print(f"  Report:        {out_path}")
    print(f"{'═'*50}\n")
    return 0 if health != "RED" else 1


if __name__ == "__main__":
    sys.exit(main())
