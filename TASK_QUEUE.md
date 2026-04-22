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

## 🔴 ACTIVE SPRINT — 2026-04-23 Matrix Agent Review
#
# Findings from full audit:
#   1. services.py MISSING from ALL 6 modules — this is the hollow core. Fix first.
#   2. LIMS and MES missing tasks.py — not wired into scheduler at all.
#   3. No git repository → GitHub Actions NEVER trigger → audit loop is local only.
#   4. PostgreSQL not running → all testing against SQLite → untested on real DB.
#   5. E-sig on MES batch release not connected.
#   6. OOS auto-trigger on failed LIMS result not implemented.
#
# Sprint order: TASK-026 → TASK-027 → TASK-020 → TASK-021 → TASK-022 → TASK-023 → TASK-024 → TASK-025

---

### TASK-026 [P0] — Initialize git repository and push to GitHub
- **Status:** PENDING
- **Why P0:** GitHub Actions workflows exist but NEVER trigger without a git repo + remote.
  The entire audit loop, chaos-weekly, quality-gates CI — all theoretical until this is done.
- **Steps:**
  1. `git init` in project root
  2. `git add .`
  3. `git commit -m "feat(platform): initial commit — foundation HARDENED, all 6 modules SKELETON"`
  4. Create GitHub repo (private) — do NOT create with README (will conflict)
  5. `git remote add origin https://github.com/<username>/gmp-platform.git`
  6. `git push -u origin main`
  7. In GitHub Settings → Branches: protect `main`, require PR for changes to `.cursorrules` and `BUILDING_RULES.md`
  8. Verify: push a small change and confirm quality-gates.yml triggers
- **BLOCKED condition:** If GitHub auth fails in terminal, stop and report.
- **Do NOT:** commit `backend/.env` (it's in .gitignore already — verify before pushing)

---

### TASK-027 [P0] — Start PostgreSQL via Docker and verify Alembic migrations
- **Status:** PENDING
- **Depends on:** TASK-026 (git must exist so migration failures can be committed as fixes)
- **Why P0:** Every test has run on SQLite. PostgreSQL handles UUID, timezone-aware DateTime,
  RETURNING, advisory locks, and index concurrency differently. We need to find breakage now,
  not at customer demo.
- **Steps:**
  1. `docker-compose up -d` — start PostgreSQL (check docker-compose.yml for service name)
  2. Update `backend/.env` → set `DATABASE_URL` to postgres connection string
  3. Run `alembic upgrade head` — fix any errors that surface
  4. Run the full test suite: `pytest backend/tests/ -v`
  5. Run chaos.py
  6. Fix any SQLite→PostgreSQL compatibility issues found
  7. Re-enable TASK-010 planning: now that PostgreSQL is running, write the
     partitioning runbook to `docs/architecture/partition-runbook.md`
- **BLOCKED condition:** If docker-compose.yml doesn't define a postgres service, add one
  using the standard `postgres:16` image with `POSTGRES_DB=gmp_platform`.

---

### TASK-020 [P0] — QMS module: write services.py (CAPA + Deviation + ChangeControl)
- **Status:** PENDING
- **Depends on:** TASK-027 (need PostgreSQL running to test service queries properly)
- **Why P0:** services.py is missing from ALL 6 modules. QMS goes first — it's the highest
  regulatory risk module and will form the first customer demo.
- **Mandatory for FUNCTIONAL tier advancement.**
- **What to implement in app/modules/qms/services.py:**
  - `create_capa(session, data, created_by_id, site_id) → CAPA`
  - `get_capa(session, capa_id, site_id) → CAPA`
  - `list_capas(session, site_id, page, page_size, status_filter) → Page[CAPA]`
  - `assign_capa_action(session, capa_id, data, assigned_by_id, site_id) → CAPAAction`
  - `close_capa(session, capa_id, esig_data, closed_by_id, site_id) → CAPA`
    — MUST call ESignatureService.sign() before closing
  - `create_deviation(session, data, created_by_id, site_id) → Deviation`
  - `list_deviations(session, site_id, page, page_size) → Page[Deviation]`
  - `create_change_control(session, data, created_by_id, site_id) → ChangeControl`
- **Every write must:** call `AuditService.log()` in the same transaction
- **Every list must:** filter by `site_id`, paginate (max 100)
- **Wire router.py** to call services (not the DB directly)
- **Add tests:** `tests/test_qms_services.py` — at minimum: create, list (site isolation), close with esig
- **Run quality gates before marking DONE**

---

### TASK-021 [P0] — MES module: write services.py + tasks.py (BatchRecord workflow + batch release e-sig)
- **Status:** PENDING
- **Depends on:** TASK-020
- **Why P0:** MES has NO tasks.py — it is completely unwired from the scheduler. Batch releases
  have no e-signature enforcement. This is a 21 CFR Part 11 regulatory blocker.
- **What to implement in app/modules/mes/services.py:**
  - `create_master_batch_record(session, data, created_by_id, site_id) → MasterBatchRecord`
  - `approve_mbr(session, mbr_id, esig_data, approved_by_id, site_id) → MasterBatchRecord`
    — MUST call ESignatureService.sign()
  - `create_batch_record(session, mbr_id, data, created_by_id, site_id) → BatchRecord`
  - `record_batch_step(session, batch_id, step_id, data, performed_by_id, site_id) → BatchRecordStep`
    — MUST enforce back-fill prevention (BUILDING_RULES §5.3)
  - `release_batch_record(session, batch_id, esig_data, released_by_id, site_id) → BatchRecord`
    — MUST call ESignatureService.sign()
  - `list_batch_records(session, site_id, page, page_size, status) → Page[BatchRecord]`
- **What to implement in app/modules/mes/tasks.py:**
  - `check_overdue_batch_records() → dict` — counts batch records open >30 days, notifies
  - Register in main.py lifespan (add line: `register_overdue_hook("mes_overdue_batches", check_overdue_batch_records)`)
- **Tests:** back-fill prevention test is mandatory (attempt to record a step twice → 400)

---

### TASK-022 [P1] — Equipment module: write services.py (Calibration + Qualification + Maintenance)
- **Status:** PENDING
- **Depends on:** TASK-021
- **What to implement in app/modules/equipment/services.py:**
  - `create_equipment(session, data, created_by_id, site_id) → Equipment`
  - `list_equipment(session, site_id, page, page_size) → Page[Equipment]`
  - `record_calibration(session, equipment_id, data, performed_by_id, site_id) → CalibrationRecord`
    — must set `next_calibration_due` based on `calibration_interval_days`
    — must set `is_overdue=False` on the new record (resets overdue state)
  - `record_qualification(session, equipment_id, data, performed_by_id, site_id) → QualificationRecord`
  - `list_calibration_history(session, equipment_id, site_id, page, page_size) → Page[CalibrationRecord]`
- **Wire router.py** to call services
- **Tests:** recording calibration resets is_overdue; listing is site-isolated

---

### TASK-023 [P1] — Training module: write services.py (Curriculum + Assignment + Completion)
- **Status:** PENDING
- **Depends on:** TASK-021
- **What to implement in app/modules/training/services.py:**
  - `create_curriculum(session, data, created_by_id, site_id) → TrainingCurriculum`
  - `assign_training(session, curriculum_id, user_ids, due_date, assigned_by_id, site_id) → list[TrainingAssignment]`
  - `complete_training(session, assignment_id, esig_data, completed_by_id, site_id) → TrainingCompletion`
    — MUST call ESignatureService.sign() (read-and-understood signature)
  - `list_assignments(session, site_id, user_id, status, page, page_size) → Page[TrainingAssignment]`
- **Tests:** complete_training without e-sig → 403; completed assignment doesn't appear as overdue

---

### TASK-024 [P1] — LIMS module: write services.py + tasks.py (OOS auto-trigger on failed result)
- **Status:** PENDING
- **Depends on:** TASK-021
- **Why P1:** OOS auto-trigger is a GMP requirement. LIMS also has no tasks.py.
- **What to implement in app/modules/lims/services.py:**
  - `create_sample(session, data, created_by_id, site_id) → Sample`
  - `record_test_result(session, sample_id, data, tested_by_id, site_id) → TestResult`
    — if result status == "failed": automatically create OOSInvestigation
    — TestResult is APPEND-ONLY. Corrections = new result with `corrects_result_id` set.
  - `correct_test_result(session, original_id, data, corrected_by_id, site_id) → TestResult`
    — invalidates original, creates new result referencing it
  - `list_samples(session, site_id, page, page_size, status) → Page[Sample]`
  - `create_oos_investigation(session, sample_id, triggered_by_result_id, site_id) → OOSInvestigation`
  - `close_oos_investigation(session, oos_id, esig_data, closed_by_id, site_id) → OOSInvestigation`
- **What to implement in app/modules/lims/tasks.py:**
  - `check_open_oos_investigations() → dict` — counts OOS open >14 days, notifies
  - Register in main.py lifespan
- **Tests:** record failed result → OOS created automatically; correct result → original invalidated

---

### TASK-025 [P1] — ENV Monitoring module: write services.py (Location + Result + Alert enforcement)
- **Status:** PENDING
- **Depends on:** TASK-021
- **What to implement in app/modules/env_monitoring/services.py:**
  - `create_location(session, data, created_by_id, site_id) → MonitoringLocation`
  - `record_result(session, location_id, data, recorded_by_id, site_id) → MonitoringResult`
    — if reading exceeds AlertLimit: automatically create a deviation record reference (loose UUID)
    — and notify via NotificationService
  - `create_trend(session, location_id, data, created_by_id, site_id) → MonitoringTrend`
  - `review_trend(session, trend_id, esig_data, reviewed_by_id, site_id) → MonitoringTrend`
  - `list_results(session, location_id, site_id, page, page_size) → Page[MonitoringResult]`
- **Tests:** reading above alert limit → notification triggered

---

### TASK-028 [P1] — Wire all 6 module routers to their new services.py (replace any stub responses)
- **Status:** PENDING
- **Depends on:** TASK-020 through TASK-025 (all services.py must exist first)
- **Task:** Go through router.py in each of the 6 modules. Replace any direct DB calls or
  placeholder returns with calls to the corresponding services function. Ensure every
  endpoint has: auth dependency, site_id enforcement, AuditEvent logging via service.
- **Tests:** run full pytest suite — all endpoints must return real data, not 200 + empty

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

---

### TASK-030 [P2] — Table partitioning runbook (unblock TASK-010)
- **Status:** PENDING
- **Depends on:** TASK-027 (PostgreSQL must be running)
- **Task:** Write `docs/architecture/partition-runbook.md` with:
  1. Step-by-step cutover plan for audit_events, test_results, batch_record_steps
  2. Zero-downtime approach: create new partitioned table → copy data → rename → drop old
  3. Alembic migration template (do NOT run yet — document only)
  4. Test plan: run on dev DB clone, verify all existing queries still work
- **Do NOT execute the migration** — produce the runbook only. Matrix Agent approves before execution.

---

## 🟡 BACKLOG — not started (Phase 5+)

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

## 📋 BLOCKED

### TASK-010 — Partition high-volume tables (audit_events, test_results, batch_record_steps)
- **Status:** BLOCKED → see TASK-030 (write runbook first, then unblock)
- **Reason:** Needs PostgreSQL running (TASK-027) + DBA runbook (TASK-030) before execution.

---

## ✅ DONE

### TASK-002 — Overdue status flags (equipment, training)
- **Status:** DONE — 2026-04-21
- **Summary:** Bulk `UPDATE` for `CalibrationRecord.is_overdue` and `TrainingAssignment.status=overdue`; combined with SQL counts in `tasks.py`. Tests: `tests/test_scheduler_equipment_training.py`.

### TASK-003 — SQL COUNT in calibration/training hooks
- **Status:** DONE — 2026-04-21 (same commit as 002)
- **Summary:** `func.count` queries; no full-table `select *`.

### TASK-004 — Guard `create_all`
- **Status:** DONE — 2026-04-21
- **Summary:** `main.py` runs `Base.metadata.create_all` only if `settings.ENVIRONMENT != "production"`.

### TASK-005 — Migration logging
- **Status:** DONE — 2026-04-21
- **Summary:** `20260423_decouple_cross_module_fks.py` — `_drop_fk_if_exists` logs `logger.warning` instead of silent `pass`.

### TASK-006 — CORS + FRONTEND_URL
- **Status:** DONE — 2026-04-21
- **Summary:** `config.FRONTEND_URL`; `main.py` CORS uses dev localhost list or `[FRONTEND_URL]` — no `*` in non-development.

### TASK-007 — DB pool + statement_timeout
- **Status:** DONE — 2026-04-21
- **Summary:** `database.py` pool 20/40/30s/3600 + `connect` event sets `statement_timeout` 30s on PostgreSQL; SQLite unchanged.

### TASK-008 — Advisory lock for scheduler
- **Status:** DONE — 2026-04-21
- **Summary:** `pg_try_advisory_lock(738194501)` before APScheduler; unlock on shutdown; skipped on SQLite.

### TASK-009 — /health/db, /health/integrations
- **Status:** DONE — 2026-04-21
- **Summary:** `main.py` — `SELECT 1` + latency; list `IntegrationConnector` fields.

### TASK-011 — ENV monitoring hook
- **Status:** DONE — 2026-04-21
- **Summary:** `env_monitoring/tasks.py` `check_overdue_monitoring_reviews`; template seeded; registered in `main.py`.

### TASK-012 / TASK-013 — URS + IQ/OQ templates
- **Status:** DONE — 2026-04-21
- **Summary:** `docs/urs/*.md` (6 modules), `validation/iq|oq/*-protocol-template.md`.

### TASK-014 / TASK-015 — SAP + DeltaV connector stubs
- **Status:** DONE — 2026-04-21
- **Summary:** `app/core/integration/connectors/sap.py`, `deltav.py` with `health_ping` placeholders.

### TASK-016 — Foundation FK budget
- **Status:** DONE — 2026-04-21
- **Summary:** `test_module_foundation_fk_budget.py` + quality-gates workflow step.

### TASK-017 — Real-app chaos
- **Status:** DEFERRED — 2026-04-21
- **Summary:** `tests/test_chaos_real_app_deferred.py` marked `skip` until CI postgres + harness exist.

### TASK-019 — Repo `core/` extraction
- **Status:** DONE — 2026-04-21
- **Summary:** `core/boundary_engine`, `core/event_bus`, `core/task_orchestrator`, `core/audit_reporter` extracted.

### TASK-001 — Wire NotificationService into all 4 overdue hooks
- **Status:** DONE — 2026-04-21
- **Summary:** `send_rule_based` when count `> 0` for qms_capa_overdue, equipment_calibration_overdue, training_assignment_overdue, document_review_due.

### TASK-018 — NotificationService.send_rule_based FUNCTIONAL
- **Status:** DONE — 2026-04-21
- **Summary:** `send_rule_based()` in `app/core/notify/service.py`; four scheduler templates + NotificationRule rows seeded; tests passing.

### TASK-000 — Foundation layer + all 6 business modules skeleton
- **Status:** DONE — 2026-04-21
- **Summary:** Built complete foundation (auth, audit, esig, workflow, documents, notify, integration) and all 6 business module skeletons (qms, mes, equipment, training, lims, env_monitoring). Architecture boundary tests added. Chaos suite added.

---

*Queue maintained by: Matrix Agent*
*Updated: 2026-04-23*
*Next Matrix Agent review: 2026-04-26 (3-day cycle)*
*Dual-path strategy: README-GMP.md (regulatory) + README-AI.md (AI governance) — both paths warm*
*Sprint focus: git init → PostgreSQL → services.py for all 6 modules → QMS FUNCTIONAL*
