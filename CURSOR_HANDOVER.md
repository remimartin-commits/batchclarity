# Cursor Handover — GMP Platform
# Written by: Matrix Agent — 2026-04-23
# READ THIS ENTIRE FILE BEFORE TOUCHING ANY CODE

---

## STEP 0 — FIRST ACTION (do this before anything else)

Three files were written last session but NOT yet committed to git.
Commit them now:

```powershell
cd "C:\Users\fella\OneDrive\Desktop\work\gmp-platform"
git add backend/app/modules/qms/services.py backend/app/modules/mes/services.py backend/app/modules/mes/tasks.py
git commit -m "feat(services): QMS + MES services.py and MES tasks.py — business logic layer"
git push origin main
```

Do NOT skip this. These files must be in version control before you write more.

---

## Current git state

- Last commit on main: `25ad331` — `fix(alembic): add missing importlib.metadata import; widen alembic_version.version_num to VARCHAR(64)`
- GitHub remote: `https://github.com/remimartin-commits/batchclarity`
- Untracked (commit above first):
  - `backend/app/modules/qms/services.py`  — TASK-020 complete
  - `backend/app/modules/mes/services.py`   — TASK-021 complete
  - `backend/app/modules/mes/tasks.py`      — TASK-021 complete

---

## Current module status

| Module         | models | schemas | router | services.py     | tasks.py        |
|----------------|--------|---------|--------|-----------------|-----------------|
| qms            | OK     | OK      | OK     | DONE (uncommit) | OK              |
| mes            | OK     | OK      | OK     | DONE (uncommit) | DONE (uncommit) |
| equipment      | OK     | OK      | OK     | MISSING         | OK              |
| training       | OK     | OK      | OK     | MISSING         | OK              |
| lims           | OK     | OK      | OK     | MISSING         | MISSING         |
| env_monitoring | OK     | OK      | OK     | MISSING         | OK              |

---

## Infrastructure (know before you touch anything)

- Database: Supabase PostgreSQL — NO Docker needed
  DATABASE_URL is in backend/.env — do not change it
  Alembic is fully migrated: head = 20260423_decouple_cross_module_fks
- Run alembic from backend dir: `.\.venv\Scripts\alembic.exe current`
  (do NOT use `python -m alembic` — will fail)
- Run tests: `cd backend && .\.venv\Scripts\pytest.exe tests/test_architecture_boundaries.py -v`
- Import test pattern (verify each services.py after writing):
  `cd backend && .\.venv\Scripts\python.exe -c "import app.modules.equipment.services; print('OK')"`

---

## Pattern reference — copy these, do not invent

### From qms/services.py (state machines + e-sig + cross-module hook)

```python
# State machine pattern:
_DEVIATION_TRANSITIONS: dict[str, tuple[str, str]] = {
    "submit": ("draft", "under_review"),
    "approve": ("under_review", "approved"),
    "close":   ("approved", "closed"),
}

async def _apply_transition(obj, action: str, transitions: dict, db) -> None:
    if action not in transitions:
        raise HTTPException(status_code=400, detail=f"Unknown action: {action}")
    required_from, next_state = transitions[action]
    if obj.status != required_from:
        raise HTTPException(
            status_code=409,
            detail=f"Cannot {action}: current status is '{obj.status}', expected '{required_from}'"
        )
    obj.status = next_state

# E-sig pattern:
from app.core.esig.service import ESignatureService
esig_svc = ESignatureService()
await esig_svc.sign(db=db, user=user, password=data.password,
                    action=data.meaning, record_type="CAPA", record_id=str(capa.id),
                    ip_address=ip_address)

# Audit log pattern (every write):
from app.core.audit.service import AuditService
audit_svc = AuditService()
await audit_svc.log(db=db, user_id=user.id, action="CREATE", resource_type="Deviation",
                    resource_id=str(obj.id), site_id=data.site_id, ip_address=ip_address,
                    details={"title": data.title})
```

### From mes/services.py (ANTI-BACKFILL pattern)

```python
# ANTI-BACKFILL — ALCOA Contemporaneous (BUILDING_RULES §5.3):
if step.performed_at is not None:
    raise HTTPException(
        status_code=400,
        detail=f"Step {step_id} has already been recorded. Backfill is not permitted."
    )
step.performed_at = _utcnow()   # server-set, never client

def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)  # stored as naive UTC
```

### APScheduler task pattern (from mes/tasks.py)

```python
from app.core.database import async_session_factory   # NOT get_db (not request-scoped)
from app.core.audit.service import AuditService

async def check_something() -> None:
    async with async_session_factory() as db:
        # do queries
        audit_svc = AuditService()
        await audit_svc.log(
            db=db, user_id=None, action="WARNING",
            resource_type="System", resource_id="scheduler",
            site_id=None, ip_address="127.0.0.1",
            details={"count": n, "is_system_action": True}
        )
        await db.commit()
```

---

## Task queue — do in this order

### TASK-022 [P1] — Equipment services.py

**File:** `backend/app/modules/equipment/services.py`

Key functions to implement:
- `create_equipment(db, data, user, ip_address) -> Equipment`
- `list_equipment(db, site_id, page, page_size) -> list[Equipment]`
- `get_equipment_or_404(db, equipment_id, site_id) -> Equipment`
- `record_calibration(db, equipment_id, data, user, ip_address) -> CalibrationRecord`
  - set `next_calibration_due = now + timedelta(days=equipment.calibration_interval_days)`
  - set `equipment.is_overdue = False` (reset on new calibration)
  - AuditEvent: action="CALIBRATION_RECORDED"
- `record_qualification(db, equipment_id, data, user, ip_address) -> QualificationRecord`
- `list_calibration_history(db, equipment_id, site_id, page, page_size) -> list[CalibrationRecord]`

Boundary rules:
- No cross-module imports
- All writes: AuditService.log() in same transaction
- All lists: filter by site_id, paginate (max 100)

Commit: `feat(equipment): equipment services.py — calibration lifecycle, overdue reset`

---

### TASK-023 [P1] — Training services.py

**File:** `backend/app/modules/training/services.py`

Key functions:
- `create_curriculum(db, data, user, ip_address) -> TrainingCurriculum`
- `assign_training(db, curriculum_id, user_ids: list[str], due_date, user, ip_address) -> list[TrainingAssignment]`
  - One TrainingAssignment row per user_id; bulk insert
- `complete_training(db, assignment_id, data: TrainingCompletionRequest, user, ip_address) -> TrainingCompletion`
  - MUST call ESignatureService.sign() — read-and-understood signature
  - Sets assignment.status = "completed"
  - AuditEvent: action="TRAINING_COMPLETED", meaning="read_and_understood"
- `list_assignments(db, site_id, user_id, status_filter, page, page_size) -> list[TrainingAssignment]`
- `get_overdue_count(db, site_id) -> int`
  - Used by tasks.py; count where status="pending" and due_date < utcnow

Commit: `feat(training): training services.py — curriculum, assignment, e-sig completion`

---

### TASK-024 [P1] — LIMS services.py + tasks.py

**Files:**
- `backend/app/modules/lims/services.py`
- `backend/app/modules/lims/tasks.py`

#### lims/services.py key functions:

- `create_sample(db, data, user, ip_address) -> Sample`
- `record_test_result(db, sample_id, data, user, ip_address) -> TestResult`
  - TestResult is APPEND-ONLY. Never update an existing result.
  - `performed_at = _utcnow()` — server-set (ALCOA Contemporaneous)
  - If `data.is_oos is True`:
    ```python
    # LATE IMPORT — avoids circular dependency (lims cannot import qms at module level)
    from app.modules.qms import services as qms_services
    await qms_services.create_deviation_from_oos(
        db=db,
        sample_id=str(sample.id),
        result_id=str(result.id),
        test_name=data.test_name,
        observed_value=str(data.value),
        spec_limit=str(data.spec_limit),
        site_id=data.site_id,
        system_user=user,
    )
    ```
  - AuditEvent: action="OOS_AUTO_DEVIATION_CREATED" in details if triggered
- `correct_test_result(db, original_result_id, data, user, ip_address) -> TestResult`
  - Creates new TestResult with `corrects_result_id = original_result_id`
  - Sets original result `is_invalidated = True`
  - AuditEvent: action="RESULT_CORRECTED", details include original_id and reason
  - Original result row is NEVER deleted or overwritten (append-only, ALCOA Original)
- `list_samples(db, site_id, page, page_size, status_filter) -> list[Sample]`
- `create_oos_investigation(db, sample_id, triggered_by_result_id, site_id, user) -> OOSInvestigation`
- `close_oos_investigation(db, oos_id, data, user, ip_address) -> OOSInvestigation`
  - MUST call ESignatureService.sign()

**INFORMATION PURITY — 6 conditions for lims/services.py:**
1. Provenance Verified — log who performed_by_id on every result
2. Chain of Custody Intact — sample linked to all results
3. Original Preserved — append-only, set is_invalidated on old result (never delete)
4. Anomaly Detection — OOS auto-triggers deviation
5. Contemporaneous — performed_at = server UTC, never client
6. Correction Transparent — corrects_result_id chain + AuditEvent

#### lims/tasks.py key functions:

```python
async def check_open_oos_investigations() -> None:
    # Count OOSInvestigation where status != "closed" and created_at < utcnow - 14 days
    # Notify via NotificationService if count > 0
    # AuditEvent with is_system_action=True
```

Commit: `feat(lims): LIMS services.py + tasks.py — OOS auto-trigger, append-only results`

---

### TASK-025 [P1] — ENV Monitoring services.py

**File:** `backend/app/modules/env_monitoring/services.py`

Key functions:
- `create_location(db, data, user, ip_address) -> MonitoringLocation`
- `record_result(db, location_id, data, user, ip_address) -> MonitoringResult`
  - If `data.value > location.alert_limit`:
    - Set `result.exceeds_alert_limit = True`
    - Create loose deviation reference: `result.linked_deviation_id = str(uuid4())` (no FK)
    - Call NotificationService to alert
    - AuditEvent: action="ALERT_LIMIT_EXCEEDED"
  - `recorded_at = _utcnow()` — server-set
- `create_trend(db, location_id, data, user, ip_address) -> MonitoringTrend`
- `review_trend(db, trend_id, data, user, ip_address) -> MonitoringTrend`
  - MUST call ESignatureService.sign()
  - Sets trend.reviewed_by_id, trend.reviewed_at, trend.status = "reviewed"
- `list_results(db, location_id, site_id, page, page_size) -> list[MonitoringResult]`

Commit: `feat(env_monitoring): ENV monitoring services.py — alert detection, trend review e-sig`

---

### TASK-028 [P1] — Wire all 6 routers to their services

After TASK-022 through TASK-025 are done:
- Open each `router.py` in all 6 modules
- Replace any direct `db.execute(...)` or stub returns with calls to the corresponding service
- Every endpoint must: authenticate (Depends(get_current_user)), enforce site_id, call service
- Run full test suite: `.\.venv\Scripts\pytest.exe backend/tests/ -v`

Commit: `feat(platform): wire all 6 module routers to services (TASK-028)`

---

### TASK-029 [P2] — Advance QMS to FUNCTIONAL in registry.json

- Open `registry.json`
- Set `modules.qms.tier` → `"FUNCTIONAL"`
- Verify checklist: models + router + services + tasks + schemas all present ✅
- At least 3 API endpoints working end-to-end ✅ (after TASK-028)

Commit: `feat(governance): advance QMS module to FUNCTIONAL tier`

---

## Boundary rules (violations will break architecture tests)

1. `app.modules.X` CANNOT import from `app.modules.Y` at module level
   - Exception: LIMS → QMS OOS hook uses LATE IMPORT inside the function body
2. No `ForeignKey()` across module boundaries — use `Column(String(36))` loose references
3. `app.core.*` is importable from any module
4. Every module's `tasks.py` uses `async_session_factory` (NOT `get_db`)
5. Timestamps (performed_at, recorded_at, actual_start) are ALWAYS server-set UTC
6. Backfill prevention: if a timestamp field is already set → HTTP 400

---

## Quality gates (run after EACH task before marking DONE)

```powershell
cd "C:\Users\fella\OneDrive\Desktop\work\gmp-platform\backend"
.\.venv\Scripts\pytest.exe tests/test_architecture_boundaries.py -v
.\.venv\Scripts\python.exe ..\chaos.py
```

Both must pass. If failing, fix before committing.

---

## Commit message convention

```
feat(equipment): equipment services.py — calibration lifecycle, overdue reset
feat(training): training services.py — curriculum, assignment, e-sig completion
feat(lims): LIMS services.py + tasks.py — OOS auto-trigger, append-only results
feat(env_monitoring): ENV monitoring services.py — alert detection, trend review e-sig
feat(platform): wire all 6 module routers to services (TASK-028)
feat(governance): advance QMS module to FUNCTIONAL tier (TASK-029)
```

---

## Hard stops — do NOT do these

- Do NOT modify `.cursorrules` or `BUILDING_RULES.md`
- Do NOT add ForeignKey constraints that cross module boundaries
- Do NOT use `python -m alembic` — use `.\.venv\Scripts\alembic.exe`
- Do NOT trust client-provided timestamps for performed_at / recorded_at fields
- Do NOT mark a task DONE before running quality gates
- Do NOT allow lims/services.py to import qms at module level (use late import inside function)
- Do NOT delete or overwrite TestResult rows — append only, set is_invalidated on old row

---

## Files to read before writing each service

Before writing each services.py, read these files in that module:
- `backend/app/modules/<module>/models.py`
- `backend/app/modules/<module>/schemas.py`
- `backend/app/modules/<module>/router.py`

Reference implementations:
- `backend/app/modules/qms/services.py` (state machines, e-sig, audit, cross-module hook)
- `backend/app/modules/mes/services.py` (anti-backfill, batch lifecycle, e-sig release)
- `backend/app/core/esig/service.py` (ESignatureService.sign() signature)
- `backend/app/core/audit/service.py` (AuditService.log() signature)
- `backend/app/core/notify/service.py` (NotificationService.send_rule_based())

---

*Handover written by: Matrix Agent*
*Session ended: 2026-04-23*
*Resume from: STEP 0 — commit the 3 untracked files, then TASK-022*
