# Audit — 2026-04-23 — Post-Fix Deliverable Review

## Scope
Full structured audit of Cursor's post-fix changes following the 2026-04-21 boundary
retrofit. Files read: core/tasks.py, qms/tasks.py, equipment/tasks.py, training/tasks.py,
core/documents/tasks.py, mes/models.py, lims/models.py, equipment/models.py,
training/models.py, main.py, test_architecture_boundaries.py,
alembic/versions/20260423_decouple_cross_module_fks.py

## Verdict: B+ — architecture clean, compliance loop hollow

---

## CRITICAL Findings (must fix before validation submission)

### 1. Overdue hooks count but never notify [ALL MODULES]
Every hook (qms/tasks.py, equipment/tasks.py, training/tasks.py, core/documents/tasks.py)
returns a count. None calls NotificationService. The scheduler logs a number. Nobody is
alerted. This is the single highest regulatory-risk gap.
FIX: Call NotificationService.send_rule_based() after counting overdue records.

### 2. Migration silently swallows exceptions [ALEMBIC]
_drop_fk_if_exists() catches all exceptions with `except Exception: pass`.
If a FK constraint name differs, migration exits 0 but FK is still in place.
FIX: Change to `except Exception as exc: logger.warning(...)` — never silent pass.

### 3. create_all runs unconditionally in production [MAIN.PY]
Base.metadata.create_all has no environment guard. In production, Alembic manages
schema. Running create_all bypasses migration tracking and causes Alembic state drift.
FIX: `if settings.ENVIRONMENT != "production":`

---

## HIGH Findings (fix before first user)

### 4. Calibration/training hooks load full tables into memory [PERFORMANCE]
equipment/tasks.py and training/tasks.py: SELECT * then filter in Python.
At 10k+ records this is a memory spike every 6 hours.
FIX: Use SQL COUNT with WHERE clause.

### 5. CalibrationRecord.is_overdue never written [DATA INTEGRITY]
Column exists, default=False, scheduler never updates it. Always reads False.
FIX: Scheduler must UPDATE is_overdue=True for overdue rows.

### 6. TrainingAssignment.status never set to "overdue" [DATA INTEGRITY]
Status enum includes "overdue". Scheduler never sets it.
FIX: Bulk UPDATE status="overdue" for past-due pending assignments.

### 7. CORS allow_origins=["*"] in production-bound code [SECURITY / PART 11]
Wildcard CORS breaks Part 11 access controls perimeter.
FIX: Lock to settings.FRONTEND_URL when ENVIRONMENT != "development".

---

## MEDIUM Findings

### 8. FK regex in architecture test has blind spots
Regex ForeignKey\("([^".]+)\.[^"]+"\) misses alternative FK styles.
FIX: Supplement with SQLAlchemy metadata inspection at test time.

### 9. New modules require manual main.py edits
No self-registration — adding a module means editing 2 lines in main.py.
RISK: Cursor will likely forget the hook registration when adding new modules.
FIX: Convention + CI test that checks module task files have registered hooks.

---

## PASS — Confirmed Clean

- core/tasks.py: zero module imports, clean registry ✅
- mes/models.py: linked_deviation_id is plain String(36), no FK ✅
- lims/models.py: all cross-module FKs removed ✅
- equipment/models.py: protocol_id, report_id are plain String(36) ✅
- training/models.py: document_id, triggered_by_document_version_id are plain String(36) ✅
- test_architecture_boundaries.py: real AST parsing, not decorative ✅
- Migration: correct upgrade/downgrade, covers all modules ✅
- main.py hook registration: clear_overdue_hooks() + 4 register_overdue_hook() calls ✅

---

## Top 3 fixes to send Cursor

1. Wire NotificationService into all 4 overdue hooks
2. Guard create_all + fix migration exception handler
3. Push DB filtering to SQL; flip is_overdue and status flags

## Audited by
Matrix Agent — 2026-04-23
