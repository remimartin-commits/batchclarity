# GMP Platform — Task Queue
# Cursor reads this file at the start of every session.
# Cursor updates this file after completing each task.
#
# HOW TO USE:
#   1. Find the highest-priority PENDING task
#   2. Set status → IN_PROGRESS + add your start timestamp
#   3. Work on it (follow BUILDING_RULES.md + .cursorrules)
#   4. Run quality gates when done
#   5. Set status → DONE + write a 3-line summary
#   6. Commit with: feat(module): description  or  fix(module): description
#   7. Pick the next PENDING task
#
# ESCALATION: If blocked, set status → BLOCKED + explain why. Stop. Do not guess.
#
# Priority: P0 (regulatory blocker) > P1 (correctness) > P2 (performance) > P3 (feature)

---

## ACTIVE SPRINT — 2026-04-23 Matrix Agent Review
#
# Sprint progress:
#   ✅ TASK-026 — git init + push to GitHub (remimartin-commits/batchclarity)
#   ✅ TASK-027 — Supabase PostgreSQL confirmed + Alembic migrated to head
#   ✅ TASK-020 — QMS services.py written (CAPA + Deviation + ChangeControl)
#   ✅ TASK-021 — MES services.py + tasks.py written (anti-backfill, e-sig release)
#   ✅ TASK-022 — Equipment services.py
#   ✅ TASK-023 — Training services.py
#   ✅ TASK-024 — LIMS services.py + tasks.py (OOS auto-trigger)
#   ⬜ TASK-025 — ENV Monitoring services.py
#
# IMPORTANT: qms/services.py, mes/services.py, mes/tasks.py are WRITTEN but
# not yet committed. Cursor's FIRST action must be to commit them.
# See CURSOR_HANDOVER.md Step 0.

---

### TASK-026 [P0] — Initialize git repository and push to GitHub
- **Status:** DONE — 2026-04-23
- **Summary:** git init + initial commit + pushed to GitHub remote (remimartin-commits/batchclarity).
  GitHub Actions workflows now trigger on push to main. Branch protection configured.
  Commit: `91b2be7 feat(platform): initial commit — foundation HARDENED, all 6 modules SKELETON`

---

### TASK-027 [P0] — Start PostgreSQL via Docker and verify Alembic migrations
- **Status:** DONE — 2026-04-23
- **Summary:** Docker not installed; Supabase PostgreSQL already configured in backend/.env —
  no Docker needed. Fixed 2 Alembic bugs: (1) missing `from importlib.metadata import version,
  PackageNotFoundError` in config.py; (2) revision ID 35 chars > VARCHAR(32) — widened to
  VARCHAR(64) via ALTER TABLE in upgrade(). `alembic current` → 20260423_decouple_cross_module_fks (head).
- **Commit:** `25ad331 fix(alembic): add missing importlib.metadata import; widen alembic_version.version_num to VARCHAR(64)`

---

### TASK-020 [P0] — QMS module: write services.py (CAPA + Deviation + ChangeControl)
- **Status:** DONE — 2026-04-23 (written but not yet committed — see CURSOR_HANDOVER.md Step 0)
- **Summary:** `backend/app/modules/qms/services.py` written (24,161 bytes). Full CAPA lifecycle
  (create, list, get, update, add_action, sign/close), Deviation state machine
  (draft→under_review→approved→closed), ChangeControl state machine (5-state), cross-module
  OOS hook `create_deviation_from_oos()` called by LIMS on OOS result. Import test passed.
- **Commit:** pending (include in first Cursor commit with TASK-021)

---

### TASK-021 [P0] — MES module: write services.py + tasks.py (BatchRecord workflow + batch release e-sig)
- **Status:** DONE — 2026-04-23 (written but not yet committed — see CURSOR_HANDOVER.md Step 0)
- **Summary:** `backend/app/modules/mes/services.py` (19,023 bytes) — ANTI-BACKFILL enforced
  in `execute_step` (HTTP 400 if performed_at already set, per ALCOA Contemporaneous).
  E-sig required for `release_batch` and `sign_mbr`. `backend/app/modules/mes/tasks.py`
  (8,762 bytes) — `check_stale_batches`, `flag_yield_outliers`, `daily_batch_summary`.
  Import test passed.
- **Commit:** pending (include in first Cursor commit with TASK-020)

---

### TASK-022 [P1] — Equipment module: write services.py (Calibration + Qualification + Maintenance)
- **Status:** DONE — 2026-04-22
- **Summary:** Added `app/modules/equipment/services.py`: equipment CRUD helpers, `record_calibration` with server `performed_at`, `CALIBRATION_RECORDED` audit, `next_calibration_due` from interval, clearing stale `CalibrationRecord.is_overdue`, paginated `list_calibration_history`, and `record_qualification`. Set `pythonpath = ..` in `backend/pytest.ini` so `core.boundary_engine` loads for architecture tests. Chaos + boundary tests pass.
- **Depends on:** TASK-021 (done)
- **What to implement in app/modules/equipment/services.py:**
  - `create_equipment(db, data, user, ip_address) -> Equipment`
  - `list_equipment(db, site_id, page, page_size) -> list[Equipment]`
  - `get_equipment_or_404(db, equipment_id, site_id) -> Equipment`
  - `record_calibration(db, equipment_id, data, user, ip_address) -> CalibrationRecord`
    — set `next_calibration_due = utcnow + timedelta(days=equipment.calibration_interval_days)`
    — set `equipment.is_overdue = False` (reset on new calibration record)
  - `record_qualification(db, equipment_id, data, user, ip_address) -> QualificationRecord`
  - `list_calibration_history(db, equipment_id, site_id, page, page_size) -> list[CalibrationRecord]`
- **Every write must:** call `AuditService.log()` in the same transaction
- **Pattern reference:** copy structure from `app/modules/qms/services.py`
- **Commit:** `feat(equipment): equipment services.py — calibration lifecycle, overdue reset`

---

### TASK-023 [P1] — Training module: write services.py (Curriculum + Assignment + Completion)
- **Status:** DONE — 2026-04-22
- **Summary:** Added `app/modules/training/services.py` with `create_curriculum`, `assign_training` (one row per user × each curriculum item; duplicate user/item rejected), `complete_training` using `ESignatureService.sign` with meaning `read_and_understood` plus `TRAINING_COMPLETED` audit, and `list_assignments` / `get_overdue_count` scoped by curriculum `site_id`. Added `TrainingCompletionRequest` in `schemas.py` (password + completion fields). Boundary tests and chaos pass.
- **Depends on:** TASK-021 (done)
- **What to implement in app/modules/training/services.py:**
  - `create_curriculum(db, data, user, ip_address) -> TrainingCurriculum`
  - `assign_training(db, curriculum_id, user_ids: list[str], due_date, user, ip_address) -> list[TrainingAssignment]`
    — bulk insert one row per user_id
  - `complete_training(db, assignment_id, data, user, ip_address) -> TrainingCompletion`
    — MUST call ESignatureService.sign() (read-and-understood signature)
    — sets assignment.status = "completed"
  - `list_assignments(db, site_id, user_id, status_filter, page, page_size) -> list[TrainingAssignment]`
- **Commit:** `feat(training): training services.py — curriculum, assignment, e-sig completion`

---

### TASK-024 [P1] — LIMS module: write services.py + tasks.py (OOS auto-trigger on failed result)
- **Status:** DONE — 2026-04-24
- **Summary:** Added `app/modules/lims/services.py` (samples, server-time test results, `importlib` load of `qms.services` for OOS auto-deviation, append-only `correct_test_result` with `is_invalidated`/`corrects_result_id`, OOS investigation create/close with e-sig) and `lims/tasks.py` (`check_open_oos_investigations`). Migration `20260424_lims_test_result_correction_fields`, `NotificationService.send_rule_based` implementation, `main.py` hook `lims_oos_stale`, seed template `lims_oos_investigation_stale`. Architecture + chaos pass.
- **Depends on:** TASK-021 (done)
- **Why P1:** OOS auto-trigger is a GMP requirement. LIMS has NO tasks.py.
- **What to implement in app/modules/lims/services.py:**
  - `create_sample(db, data, user, ip_address) -> Sample`
  - `record_test_result(db, sample_id, data, user, ip_address) -> TestResult`
    — TestResult is APPEND-ONLY. Never update an existing result.
    — `performed_at = server UTC` — never trust client
    — if `data.is_oos is True`: LATE IMPORT qms.services → call `create_deviation_from_oos()`
      (late import inside function body — NOT at module level — to avoid circular dependency)
  - `correct_test_result(db, original_result_id, data, user, ip_address) -> TestResult`
    — creates new result with `corrects_result_id = original_result_id`
    — sets original `is_invalidated = True` — original row is NEVER deleted
  - `list_samples(db, site_id, page, page_size, status_filter) -> list[Sample]`
  - `create_oos_investigation(db, sample_id, triggered_by_result_id, site_id, user) -> OOSInvestigation`
  - `close_oos_investigation(db, oos_id, data, user, ip_address) -> OOSInvestigation`
    — MUST call ESignatureService.sign()
- **What to implement in app/modules/lims/tasks.py:**
  - `check_open_oos_investigations() -> None`
    — count OOSInvestigation where status != "closed" and age > 14 days
    — call NotificationService if count > 0
- **Information Purity 6 conditions** must all be satisfied (see docs/architecture/information-purity-spec.md)
- **Commit:** `feat(lims): LIMS services.py + tasks.py — OOS auto-trigger, append-only results`

---

### TASK-025 [P1] — ENV Monitoring module: write services.py (Location + Result + Alert enforcement)
- **Status:** PENDING
- **Depends on:** TASK-021 (done)
- **What to implement in app/modules/env_monitoring/services.py:**
  - `create_location(db, data, user, ip_address) -> MonitoringLocation`
  - `record_result(db, location_id, data, user, ip_address) -> MonitoringResult`
    — if `data.value > location.alert_limit`: set `result.exceeds_alert_limit = True`,
      store loose UUID deviation reference, call NotificationService
    — `recorded_at = server UTC`
  - `create_trend(db, location_id, data, user, ip_address) -> MonitoringTrend`
  - `review_trend(db, trend_id, data, user, ip_address) -> MonitoringTrend`
    — MUST call ESignatureService.sign()
  - `list_results(db, location_id, site_id, page, page_size) -> list[MonitoringResult]`
- **Commit:** `feat(env_monitoring): ENV monitoring services.py — alert detection, trend review e-sig`

---

### TASK-028 [P1] — Wire all 6 module routers to their new services.py
- **Status:** PENDING
- **Depends on:** TASK-020 through TASK-025 (all services.py must exist first)
- **Task:** Go through router.py in each of the 6 modules. Replace any direct DB calls or
  placeholder returns with calls to the corresponding service function. Ensure every
  endpoint has: auth dependency, site_id enforcement, AuditEvent logging via service.
- **Tests:** run full pytest suite — all endpoints must return real data, not 200 + empty
- **Commit:** `feat(platform): wire all 6 module routers to services (TASK-028)`

---

### TASK-029 [P2] — Advance QMS to FUNCTIONAL tier in registry.json
- **Status:** PENDING
- **Depends on:** TASK-020, TASK-028
- **Checklist** (from registry.json _advancement_requirements):
  - [ ] models.py, router.py, services.py, tasks.py, schemas.py all present
  - [ ] At least 3 API endpoints working end-to-end
  - [ ] Overdue hook wired and calling NotificationService
  - [ ] Architecture boundary tests still passing
  - [ ] Module added to MODULE_NAMES in test_architecture_boundaries.py (verify)
- **When all checked:** update registry.json qms.tier → "FUNCTIONAL"
- **Commit:** `feat(governance): advance QMS module to FUNCTIONAL tier`

---

### TASK-030 [P2] — Table partitioning runbook (unblock TASK-010)
- **Status:** PENDING
- **Depends on:** TASK-027 (PostgreSQL running — DONE)
- **Task:** Write `docs/architecture/partition-runbook.md` with:
  1. Step-by-step cutover plan for audit_events, test_results, batch_record_steps
  2. Zero-downtime approach: create new partitioned table → copy data → rename → drop old
  3. Alembic migration template (do NOT run yet — document only)
  4. Test plan: run on dev DB clone, verify all existing queries still work
- **Do NOT execute the migration** — produce the runbook only. Matrix Agent approves before execution.

---

## BACKLOG — not started (Phase 5+)

### TASK-016b — Build Serialization module
- **Status:** PENDING
- **Note:** New module with full GAMP lifecycle — deferred until Phase 5 planning.

### TASK-031 [P3] — Frontend: QMS CAPA list + create + close flow (first demo screen)
- **Status:** PENDING
- **Depends on:** TASK-029 (QMS FUNCTIONAL)
- **Goal:** One working React screen — the CAPA management dashboard.
  List open CAPAs → click to view → close with e-signature modal.
  This is the demo screen for the first customer conversation.

### TASK-032 [P3] — Constitutional layer: formalize .cursorrules as enforced module
- **Status:** PENDING
- **Goal:** Create `core/constitutional/` module. Load .cursorrules at startup.
  Expose `GET /constitutional/rules` listing immutable constraints.
  Add GitHub branch protection: PRs that modify .cursorrules or BUILDING_RULES.md
  require human approval before merge (enforce via CODEOWNERS file).

---

## BLOCKED

### TASK-010 — Partition high-volume tables (audit_events, test_results, batch_record_steps)
- **Status:** BLOCKED → see TASK-030 (write runbook first, then unblock)
- **Reason:** Needs DBA runbook (TASK-030) before execution. PostgreSQL now confirmed (TASK-027 done).

---

## DONE

### TASK-026 [P0] — Initialize git repository and push to GitHub
- **Status:** DONE — 2026-04-23
- **Summary:** git init + initial commit + pushed to GitHub (remimartin-commits/batchclarity).
  GitHub Actions workflows now trigger on push. Branch protection configured.

### TASK-027 [P0] — Start PostgreSQL and verify Alembic migrations
- **Status:** DONE — 2026-04-23
- **Summary:** Supabase PostgreSQL already configured in backend/.env — no Docker needed.
  Fixed 2 Alembic bugs: missing importlib.metadata import + VARCHAR(32) revision ID overflow.
  `alembic current` → 20260423_decouple_cross_module_fks (head). ✅

### TASK-020 [P0] — QMS module: write services.py
- **Status:** DONE — 2026-04-23
- **Summary:** backend/app/modules/qms/services.py (24,161 bytes). Full CAPA + Deviation +
  ChangeControl business logic. State machines, e-sig hooks, cross-module OOS hook. Import test passed.
  Files written; pending commit (Cursor Step 0 in CURSOR_HANDOVER.md).

### TASK-021 [P0] — MES module: write services.py + tasks.py
- **Status:** DONE — 2026-04-23
- **Summary:** backend/app/modules/mes/services.py (19,023 bytes) — ANTI-BACKFILL enforced,
  e-sig batch release. backend/app/modules/mes/tasks.py (8,762 bytes) — 3 APScheduler jobs.
  Import test passed. Files written; pending commit (Cursor Step 0 in CURSOR_HANDOVER.md).

### TASK-002 — Overdue status flags (equipment, training)
- **Status:** DONE — 2026-04-21
- **Summary:** Bulk UPDATE for CalibrationRecord.is_overdue and TrainingAssignment.status=overdue;
  combined with SQL counts in tasks.py. Tests: tests/test_scheduler_equipment_training.py.

### TASK-003 — SQL COUNT in calibration/training hooks
- **Status:** DONE — 2026-04-21 (same commit as 002)
- **Summary:** func.count queries; no full-table select *.

### TASK-004 — Guard create_all
- **Status:** DONE — 2026-04-21
- **Summary:** main.py runs Base.metadata.create_all only if settings.ENVIRONMENT != "production".

### TASK-005 — Migration logging
- **Status:** DONE — 2026-04-21
- **Summary:** 20260423_decouple_cross_module_fks.py — _drop_fk_if_exists logs logger.warning.

### TASK-006 — CORS + FRONTEND_URL
- **Status:** DONE — 2026-04-21
- **Summary:** config.FRONTEND_URL; main.py CORS uses dev localhost list or [FRONTEND_URL] — no * in non-development.

### TASK-007 — DB pool + statement_timeout
- **Status:** DONE — 2026-04-21
- **Summary:** database.py pool 20/40/30s/3600 + connect event sets statement_timeout 30s on PostgreSQL.

### TASK-008 — Advisory lock for scheduler
- **Status:** DONE — 2026-04-21
- **Summary:** pg_try_advisory_lock(738194501) before APScheduler; unlock on shutdown; skipped on SQLite.

### TASK-009 — /health/db, /health/integrations
- **Status:** DONE — 2026-04-21
- **Summary:** main.py — SELECT 1 + latency; list IntegrationConnector fields.

### TASK-011 — ENV monitoring hook
- **Status:** DONE — 2026-04-21
- **Summary:** env_monitoring/tasks.py check_overdue_monitoring_reviews; template seeded; registered in main.py.

### TASK-012 / TASK-013 — URS + IQ/OQ templates
- **Status:** DONE — 2026-04-21
- **Summary:** docs/urs/*.md (6 modules), validation/iq|oq/*-protocol-template.md.

### TASK-014 / TASK-015 — SAP + DeltaV connector stubs
- **Status:** DONE — 2026-04-21
- **Summary:** app/core/integration/connectors/sap.py, deltav.py with health_ping placeholders.

### TASK-016 — Foundation FK budget
- **Status:** DONE — 2026-04-21
- **Summary:** test_module_foundation_fk_budget.py + quality-gates workflow step.

### TASK-017 — Real-app chaos
- **Status:** DEFERRED — 2026-04-21
- **Summary:** tests/test_chaos_real_app_deferred.py marked skip until CI postgres + harness exist.

### TASK-019 — Repo core/ extraction
- **Status:** DONE — 2026-04-21
- **Summary:** core/boundary_engine, core/event_bus, core/task_orchestrator, core/audit_reporter extracted.

### TASK-001 — Wire NotificationService into all 4 overdue hooks
- **Status:** DONE — 2026-04-21
- **Summary:** send_rule_based when count > 0 for qms_capa_overdue, equipment_calibration_overdue,
  training_assignment_overdue, document_review_due.

### TASK-018 — NotificationService.send_rule_based FUNCTIONAL
- **Status:** DONE — 2026-04-21
- **Summary:** send_rule_based() in app/core/notify/service.py; four scheduler templates +
  NotificationRule rows seeded; tests passing.

### TASK-000 — Foundation layer + all 6 business modules skeleton
- **Status:** DONE — 2026-04-21
- **Summary:** Built complete foundation (auth, audit, esig, workflow, documents, notify, integration)
  and all 6 business module skeletons (qms, mes, equipment, training, lims, env_monitoring).
  Architecture boundary tests added. Chaos suite added.

---

*Queue maintained by: Matrix Agent*
*Updated: 2026-04-23*
*Next Matrix Agent review: 2026-04-26 (3-day cycle)*
*Dual-path strategy: README-GMP.md (regulatory) + README-AI.md (AI governance) — both paths warm*
*Sprint focus: equipment/training/lims/env_monitoring services.py → wire routers → QMS FUNCTIONAL*
