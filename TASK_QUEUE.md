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

## OPTION C GUARD RAILS — READ BEFORE STARTING ANY TASK
#
# Strategic decision (ADR-005, 2026-04-22): Option C — GMP Now, Truth Layer Later.
#
# PHASE 2 (truth layer SDK extraction) IS LOCKED until ALL FOUR conditions are met:
#   G1: At least 2 modules at FUNCTIONAL tier in registry.json
#   G2: At least 1 paying design partner live on the platform
#   G3: TASK-029 DONE (QMS FUNCTIONAL tier)
#   G4: TASK-031 DONE (Frontend QMS CAPA demo screen)
#
# Until all four are met: GMP features ONLY. No SDK extraction. No abstract truth layer work.
# If a guard condition is blocking, fix the condition — do not start Phase 2 early.
# See: decisions/ADR-005-option-c-hybrid-strategy.md

---

## ACTIVE SPRINT — 2026-04-22 (Updated)
#
# Sprint progress:
#   ✅ TASK-026 — git init + push to GitHub (remimartin-commits/batchclarity)
#   ✅ TASK-027 — Supabase PostgreSQL confirmed + Alembic migrated to head
#   ✅ TASK-020 — QMS services.py (CAPA + Deviation + ChangeControl)
#   ✅ TASK-021 — MES services.py + tasks.py (anti-backfill, e-sig release)
#   ✅ TASK-022 — Equipment services.py
#   ✅ TASK-023 — Training services.py
#   ✅ TASK-024 — LIMS services.py + tasks.py (OOS auto-trigger)
#   ✅ TASK-025 — ENV Monitoring services.py
#   ✅ TASK-028 — All 6 module routers wired to services (895 ins, 1413 del)
#   ✅ TASK-029 — QMS to FUNCTIONAL tier [DONE]
#   ✅ TASK-031 — Frontend QMS CAPA screen [DONE]
#   ✅ TASK-030 — Table partitioning runbook [DONE]
#   ✅ TASK-032 — Constitutional layer formalization [DONE]
#
# Matrix Agent completed this session (2026-04-22):
#   ✅ TASK-033 — ALCOA+ to EU AI Act article outline written
#   ✅ TASK-034 — Design partner research: 3 candidates identified (VIVEbiotech, Genezen, RoslinCT)
#   ✅ ADR-005 — Option C strategy formally committed
#   ✅ README.md — Strategic Path section added
#   ✅ CURSOR_HANDOVER.md — written (explains router change + Step 0 commit)

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
- **Status:** DONE — 2026-04-25
- **Summary:** Added `app/modules/env_monitoring/services.py`: `create_location` (site match), `record_result` (server timestamps, alert/action limits, `exceeds_alert_limit` + loose `linked_deviation_id` + `send_event` + `ALERT_LIMIT_EXCEEDED` audit when value > AL), `create_trend`, `review_trend` with `ESignatureService`, paginated `list_results`. Model+migration: `exceeds_alert_limit`, trend `status`; seed `env_monitoring_alert_exceeded` template+rule. Architecture + chaos pass.
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
- **Status:** DONE — 2026-04-22
- **Summary:** All six module routers (`qms`, `mes`, `equipment`, `training`, `lims`, `env_monitoring`) now delegate to their `services.py` layers. Extended `equipment` (status transitions, qualifications/maintenance listings, site-scoped calibration list), `lims` (specs, samples/reviews/OOS list helpers), and `env_monitoring` (location/alert-limit listings, global results filter, `record_result` uses client `sampled_at`). Training adds router-oriented assignment/completion helpers. Architecture boundary + router contract tests pass locally.
- **Depends on:** TASK-020 through TASK-025 (all services.py must exist first)
- **Task:** Go through router.py in each of the 6 modules. Replace any direct DB calls or
  placeholder returns with calls to the corresponding service function. Ensure every
  endpoint has: auth dependency, site_id enforcement, AuditEvent logging via service.
- **Tests:** run full pytest suite — all endpoints must return real data, not 200 + empty
- **Commit:** `feat(platform): wire all 6 module routers to services (TASK-028)`

---

### TASK-029 [P2] — Advance QMS to FUNCTIONAL tier in registry.json
- **Status:** DONE — 2026-04-22
- **Summary:** Verified QMS module file set (`models.py`, `router.py`, `services.py`, `tasks.py`, `schemas.py`), confirmed hook wiring in `app/main.py`, upgraded overdue CAPA hook to SQL `COUNT` + `NotificationService.send_rule_based("qms_capa_overdue")`, ran architecture boundary test and full pytest suite, then advanced `registry.json` `qms.tier` to `FUNCTIONAL`.
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
- **Status:** DONE — 2026-04-22
- **Summary:** Added `docs/architecture/partition-runbook.md` with table-by-table zero-downtime cutover plan for `audit_events`, `test_results`, `batch_record_steps`, Alembic migration template (documentation-only), rollback path, and dev clone validation plan. No partition migration executed.
- **Depends on:** TASK-027 (PostgreSQL running — DONE)
- **Task:** Write `docs/architecture/partition-runbook.md` with:
  1. Step-by-step cutover plan for audit_events, test_results, batch_record_steps
  2. Zero-downtime approach: create new partitioned table → copy data → rename → drop old
  3. Alembic migration template (do NOT run yet — document only)
  4. Test plan: run on dev DB clone, verify all existing queries still work
- **Do NOT execute the migration** — produce the runbook only. Matrix Agent approves before execution.

---

---

### TASK-033 [STRATEGIC] — Draft ALCOA+ to EU AI Act article outline
- **Status:** DONE — 2026-04-22 (Matrix Agent)
- **Owner:** Project founder (not Cursor — human writing task)
- **Summary:** Full article outline written to `docs/articles/alcoa-eu-ai-act-mapping-outline.md`.
  8 sections, ~3,000-word target, citation list, publication strategy. Maps each ALCOA+ principle
  to specific EU AI Act articles (9, 10, 12, 14, 17 + Annex IV). Working title recommended:
  "The Pharmaceutical Industry Already Solved AI Governance (And Nobody Noticed)".
- **Publish gate:** Do NOT publish before first design partner is live on the platform.
  Credibility requires "we built this" — not "we theorized this."
- **Draft target:** Phase 2, Month 7

---

### TASK-034 [STRATEGIC] — Design partner pipeline: identify and approach 3 CDMO targets
- **Status:** RESEARCH DONE — 2026-04-22 (Matrix Agent). Outreach = human task, not Cursor.
- **Owner:** Project founder
- **Summary:** 3 candidates researched and documented in `docs/strategy/design-partner-pipeline.md`:
  1. **VIVEbiotech** (Spain, EU) — hired first-ever CQO in Dec 2025; blank-slate QMS buildout.
     Contact: Tathiane Castro (CQO). ⭐ Highest priority.
  2. **Genezen** (Indiana + Massachusetts, USA) — two-site QMS integration + 6× headcount growth.
     Contact: Steve Favaloro (CEO).
  3. **RoslinCT** (Edinburgh UK + Massachusetts) — 22 GMP suites, multi-site, MHRA+FDA dual.
     Contact: Peter Coleman (CEO).
- **Outreach gate:** Do NOT start outreach before TASK-031 is DONE (no UI = no demo = no deal).
- **Cursor action:** None. This is a human outreach task.

---

### TASK-035 [LOCKED] — Truth layer SDK extraction (Phase 2)
- **Status:** LOCKED — do not start until ALL guard conditions are met
- **Guard conditions (all must be true before any work begins):**
  - [ ] G1: At least 2 modules at FUNCTIONAL tier in registry.json
  - [ ] G2: At least 1 paying design partner live on the platform
  - [ ] G3: TASK-029 DONE
  - [ ] G4: TASK-031 DONE
- **What this task will involve (when unlocked):**
  Extract audit trail engine, append-only record pattern, e-signature layer, and cross-module
  event propagation into a domain-agnostic internal SDK. Do NOT launch publicly — instrument
  and validate internally only. See ADR-005 Phase 2 for full scope.
- **Cursor action:** If you see this task and the guard conditions above are not all checked,
  ignore this task and work on GMP tasks instead.

---

## BACKLOG — not started (Phase 5+)

### TASK-016b — Build Serialization module
- **Status:** PENDING
- **Note:** New module with full GAMP lifecycle — deferred until Phase 5 planning.

### TASK-031 [P3] — Frontend: QMS CAPA list + create + close flow (first demo screen)
- **Status:** DONE — 2026-04-22
- **Summary:** Added QMS CAPA dashboard UI with list + create modal (`frontend/src/pages/qms/CAPAList.tsx`), CAPA detail view with close/approve e-signature flow (`frontend/src/pages/qms/CAPADetail.tsx`), reusable shared e-sign wrapper (`frontend/src/components/shared/ESignatureModal.tsx`), and switched app routes/imports to the new CAPA pages. Legacy path compatibility shims were retained where needed. Frontend build and backend quality gates pass.
- **Depends on:** TASK-029 (QMS FUNCTIONAL)
- **Goal:** One working React screen — the CAPA management dashboard.
  List open CAPAs → click to view → close with e-signature modal.
  This is the demo screen for the first customer conversation.

### TASK-032 [P3] — Constitutional layer: formalize .cursorrules as enforced module
- **Status:** DONE — 2026-04-22
- **Summary:** Added `backend/app/core/constitutional/` with startup rule loading from `.cursorrules` and authenticated endpoint `GET /api/v1/constitutional/rules`. Wired router into `api/v1/router.py`, loaded rules during app lifespan in `main.py`, added API contract coverage, and added root `CODEOWNERS` requiring owner review for `.cursorrules` and `BUILDING_RULES.md` edits.
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
*Updated: 2026-04-23 15:00*
*Strategic path: Option C (ADR-005) — GMP Phase 1 now, truth layer Phase 2 after guard conditions met*

---

## ACTIVE SPRINT — 2026-04-23 (Kimi Parallelisation Strategy)
#
# SPEED-UP SYSTEM ACTIVATED (2026-04-23):
#   New reference files added to project root:
#   - ARCHITECTURE.md  ← frozen tech decisions, read at session start
#   - GMP_RULES.md     ← single source of truth for all GMP business rules
#   - frontend/src/lib/mock-api.ts ← fake backend for parallel frontend dev
#
# PARALLEL LANES (run simultaneously where possible):
#   Lane A — Data layer:    models, schemas, API contracts
#   Lane B — UI/Frontend:   forms, tables, views (use mock-api.ts)
#   Lane C — GMP Logic:     state machines, e-sig enforcement, validation
#
# MANDATORY CURSOR RULES (added to .cursorrules):
#   - shadcn/ui for ALL UI components (no custom CSS for existing patterns)
#   - TanStack Table (react-table v8) for ALL list/grid views
#   - React Hook Form + Zod for ALL forms
#
# SPEC-COMPLETE PROMPT FORMAT (required for every task):
#   Every task below follows the 5-section format:
#   ## CONTEXT | ## ACCEPTANCE CRITERIA | ## TECHNICAL NOTES | ## EXAMPLE | ## GMP RULE
#   If any section is missing: do not start the task, ask Matrix Agent to complete it.

---

### TASK-036 [P0] — CAPA: Full Functional Completion (TrackWise Parity)

## CONTEXT
QMS module, backend + frontend. CAPA list and detail screens exist but are missing critical
GMP-required fields and workflow enforcement. This makes the module non-functional for any
real GMP use.

## ACCEPTANCE CRITERIA
- [ ] CAPA form includes ALL fields: source_type, product_affected, batch_lot_number,
      gmp_classification, root_cause_category, root_cause_description,
      regulatory_reporting_required (+ justification text), effectiveness check sub-record
- [ ] Workflow states enforced strictly: OPEN → INVESTIGATION → ACTION_PLAN_APPROVED →
      IN_PROGRESS → EFFECTIVENESS_CHECK → CLOSED (no skipping)
- [ ] Every state transition requires electronic signature (username + password verified
      server-side — not just JWT). Uses shared ESignatureModal component.
- [ ] Effectiveness check records: check_date, method, result (PASS/FAIL), evidence note
- [ ] Action items sub-table (capa_actions): description, owner (user picker), due_date,
      status (PENDING/IN_PROGRESS/COMPLETE), completion_evidence
- [ ] ALL action items must be COMPLETE before CAPA can advance to EFFECTIVENESS_CHECK
- [ ] Audit trail view on CAPA detail shows: user_full_name, role, action, old_value,
      new_value, timestamp (UTC), ip_address — no missing fields
- [ ] TanStack Table used for CAPA list (sortable by status, classification, due date)
- [ ] All forms use React Hook Form + Zod validation
- [ ] All UI components use shadcn/ui
- [ ] pytest tests/ -x -q passes after changes

## TECHNICAL NOTES
- Backend: backend/app/modules/qms/ (models.py, schemas.py, services.py, router.py)
- Frontend: frontend/src/pages/qms/CAPAList.tsx + CAPADetail.tsx
- E-sig: use ESignatureService.sign() in services.py, ESignatureModal in frontend
- Audit: use AuditService.log() in every service function
- GMP Rules: see GMP_RULES.md section 1 (CAPA)
- Mock data: frontend/src/lib/mock-api.ts (mockCAPAs — already seeded with realistic data)

## EXAMPLE
Request: POST /api/v1/qms/capas/{id}/close
Body: {"username": "admin", "password": "Admin@GMP2024!", "reason": "All actions verified"}
Expected: 200 + updated CAPA with status=CLOSED, close_date set, e-sig record created
Error if password wrong: 401 {"detail": "Invalid credentials", "code": "AUTH_FAILED"}
Error if actions not complete: 422 {"detail": "All action items must be COMPLETE before closing", "code": "ACTIONS_INCOMPLETE"}

## GMP RULE (from GMP_RULES.md §1)
CAPA cannot be CLOSED without: root_cause_description, effectiveness check record,
and all action items at status=COMPLETE. E-signature mandatory on every state transition.

- **Status:** DONE — 2026-04-23
- **Summary:** CAPA workflow enforcement hardened to GMP rule set (mandatory root-cause/effectiveness/action-complete gates before close),
  CAPA source enums expanded (OOS/OOT/supplier issue coverage), and E2E tests updated for new close criteria.
  Frontend CAPA list/detail now use TanStack Table + RHF/Zod + shadcn/ui patterns with mock-api compatibility and toast hook.
- **Priority:** P0 (regulatory — nothing is GMP-functional without this)
- **Lane:** A + B + C (full stack)
- **Commit:** feat(qms): CAPA functional completion - TrackWise parity

---

### TASK-037 [P0] — Deviation: Full Functional Completion

## CONTEXT
QMS module, backend + frontend. Deviation screens exist but missing mandatory GMP fields,
workflow enforcement, and CAPA auto-linkage rules.

## ACCEPTANCE CRITERIA
- [ ] All mandatory fields present: deviation_type, gmp_impact_classification,
      product_affected, batches_affected (multi-entry), immediate_containment (required on
      creation), root_cause, potential_patient_impact (boolean + justification),
      regulatory_notification_required (boolean + authority + deadline)
- [ ] Workflow: OPEN → UNDER_INVESTIGATION → PENDING_APPROVAL → CLOSED
- [ ] Every state transition requires e-signature (server-side password verification)
- [ ] If gmp_impact_classification = Critical or Major: system prompts QA to create/link a CAPA
      before allowing CLOSED. If QA confirms no CAPA needed: mandatory written justification field.
- [ ] Linked batches shown in MES with "has open deviation" badge — cannot be released
- [ ] If potential_patient_impact=True: QA Director approval required (not just QA Manager)
- [ ] Audit trail complete (same standard as TASK-036)
- [ ] TanStack Table for deviation list, shadcn/ui for all UI
- [ ] pytest tests/ -x -q passes

## TECHNICAL NOTES
- Backend: backend/app/modules/qms/ (same pattern as CAPA)
- Cross-module batch flag: store loose UUID string in batch record (no FK constraint)
- GMP Rules: see GMP_RULES.md section 2 (Deviation)
- Mock data: use mockDeviations from mock-api.ts

## EXAMPLE
POST /api/v1/qms/deviations/{id}/close
Body: {"username": "...", "password": "...", "reason": "...", "capa_not_required_justification": "..."}
Error if Major/Critical with no CAPA and no justification: 422 {"code": "CAPA_REQUIRED"}

## GMP RULE (from GMP_RULES.md §2)
Major/Critical deviations require CAPA or explicit written justification for no CAPA.
Batches affected by open deviation cannot be released.

- **Status:** PENDING
- **Priority:** P0
- **Lane:** A + B + C
- **Depends on:** TASK-036 pattern established
- **Commit:** feat(qms): deviation management functional completion

---

### TASK-038 [P0] — Change Control: Full Functional Completion

## CONTEXT
QMS module, backend + frontend. Change control screens exist but missing mandatory fields,
multi-signature enforcement, and regulatory filing tracking.

## ACCEPTANCE CRITERIA
- [ ] All fields: change_type, change_classification, reason_for_change, regulatory_filing_required
      (+ filing_type + deadline), validation_required (+ scope), affected_documents (multi-select),
      affected_equipment (multi-select), implementation_plan (text + target_date),
      post_change_effectiveness_review (date + outcome + approver)
- [ ] Workflow: DRAFT → UNDER_REVIEW → APPROVED → IN_IMPLEMENTATION → EFFECTIVENESS_REVIEW → CLOSED
- [ ] APPROVED state requires MINIMUM 2 signatures (Initiator + QA)
- [ ] Emergency classification: can go DRAFT → APPROVED (skip UNDER_REVIEW) with QA Director
      e-sig + retrospective review task created automatically (due 30 days)
- [ ] If validation_required=True: cannot CLOSE without linked approved qualification record
- [ ] Regulatory filing reminder notifications created at 90 days and 30 days before deadline
- [ ] Audit trail complete
- [ ] pytest tests/ -x -q passes

## TECHNICAL NOTES
- Backend: backend/app/modules/qms/
- Multi-sig: store array of signatures on APPROVED transition, verify count >= 2 before advancing
- GMP Rules: see GMP_RULES.md section 3 (Change Control)

## EXAMPLE
POST /api/v1/qms/change-controls/{id}/approve (first signature)
POST /api/v1/qms/change-controls/{id}/approve (second signature — now status = APPROVED)
Second call: if already 2+ sigs, advance to APPROVED

## GMP RULE (from GMP_RULES.md §3)
APPROVED state requires minimum 2 e-signatures. Emergency changes bypass review but
require QA Director sign-off and a 30-day retrospective review.

- **Status:** PENDING
- **Priority:** P0
- **Lane:** A + B + C
- **Depends on:** TASK-036 pattern established
- **Commit:** feat(qms): change control functional completion

---

### TASK-039 [P0] — E-Signature Audit: Enforce Across ALL Modules

## CONTEXT
Foundation layer — compliance. Every module's state-changing endpoints must be verified
for Part 11 / Annex 11 e-sig compliance. This is a hard regulatory requirement, not optional.

## ACCEPTANCE CRITERIA
- [ ] Audit every endpoint in all 6 modules that changes a record's status/state field
- [ ] Each endpoint must: (1) be JWT-protected, (2) re-verify password server-side,
      (3) write to electronic_signatures table, (4) write old_state + new_state to audit_events
- [ ] Fix any endpoint that fails any of the 4 checks
- [ ] Create docs/part11_esig_audit.md: table of every endpoint, state transitions,
      compliance status (PASS / FAIL / FIXED), fix description
- [ ] pytest tests/ -x -q passes after all fixes

## TECHNICAL NOTES
- Modules to audit: qms (CAPA, Deviation, Change Control, Risk), mes (batch release, EBR sign-off),
  equipment (calibration record approval, qualification sign-off),
  lims (OOS disposition, CoA approval), training (completion sign-off),
  documents (approval, effective, obsolete)
- Pattern: ESignatureService.sign() in services.py, verify password before calling sign()
- GMP Rules: see GMP_RULES.md §0 (Electronic Signatures)

## EXAMPLE
Any endpoint that changes status without calling ESignatureService.sign() = FAIL.
Any endpoint that does not verify password server-side = FAIL.
Output: docs/part11_esig_audit.md with PASS/FAIL/FIXED column per endpoint.

## GMP RULE (from GMP_RULES.md §0)
E-sig requires username + password verified at time of signing. JWT alone is insufficient.
Every approval/closure/rejection is an e-sig event.

- **Status:** PENDING
- **Priority:** P0 (regulatory blocker — cannot demo without this)
- **Lane:** C (GMP logic)
- **Depends on:** TASK-036, TASK-037, TASK-038
- **Commit:** feat(compliance): e-signature audit - Part 11 / Annex 11 enforcement

---

### TASK-040 [P1] — Dashboard: Live KPI Data (All Modules)

## CONTEXT
Frontend + backend. Dashboard exists but may show placeholder data. Need live DB queries
for all KPI cards. This is required for the demo.

## ACCEPTANCE CRITERIA
- [ ] All KPI cards pull from live DB (not hardcoded / mock data in production build):
      open CAPAs, overdue CAPAs, open deviations, overdue deviations, pending change controls,
      calibrations due in 30 days, calibrations overdue, open OOS investigations,
      documents expiring in 60 days, training overdue, pending my signatures
- [ ] Each KPI card is clickable → navigates to filtered list view
- [ ] "My Actions" panel shows all items requiring logged-in user's signature or action today
- [ ] GET /api/v1/dashboard/summary endpoint returns all above, scoped to authenticated user's site
- [ ] Uses shadcn/ui Card + Badge components for KPI display
- [ ] Uses mock-api.ts mockDashboardSummary during dev (swap to real API for build)
- [ ] pytest tests/ -x -q passes

## TECHNICAL NOTES
- Backend: add backend/app/api/v1/dashboard.py
- Query pattern: COUNT(*) + WHERE site_id=X + WHERE overdue = (target_date < NOW())
- Frontend: frontend/src/pages/Dashboard.tsx
- Mock: mockGetDashboardSummary() already in mock-api.ts

## EXAMPLE
GET /api/v1/dashboard/summary
Response: {"open_capas": 3, "overdue_capas": 1, "calibrations_overdue": 2, ...}

## GMP RULE
Dashboard does not have direct GMP rules, but must accurately reflect the GMP state of the
facility at the time of access. No caching of KPI values > 5 minutes.

- **Status:** PENDING
- **Priority:** P1
- **Lane:** A + B
- **Commit:** feat(dashboard): live KPI data - all modules

---

### TASK-041 [P1] — MES: Electronic Batch Record Execution (Step Sign-Off)

## CONTEXT
MES module. Batch record model and service exist but EBR step-by-step execution UI and
operator sign-off flow is not built. This is the core of MES functionality.

## ACCEPTANCE CRITERIA
- [ ] Start Batch creates EBR from approved MBR version, locks MBR version during active batch
- [ ] Each EBR step shows: instruction (read-only from MBR), expected parameters, actual value
      entry field, pass/fail (auto-flagged if outside [spec_min, spec_max]), operator e-sig slot,
      timestamp (auto server-set)
- [ ] Reviewer e-sig slot for QA (different person from operator)
- [ ] If actual value outside range → step flagged red + deviation auto-created (type=Process)
- [ ] Anti-backfill enforced: cannot sign a step if performed_at already set
      (HTTP 400 "Step already recorded. ALCOA violation prevented.")
- [ ] Material reconciliation: dispensed_qty - used_qty - waste_qty = 0 (within tolerance)
- [ ] Batch completion: all steps signed + reconciliation balanced → PENDING_QA_REVIEW
- [ ] QA release requires e-sig: batch → RELEASED
- [ ] Progress bar showing steps_completed / steps_total
- [ ] shadcn/ui for UI, mock-api.ts mockBatchRecords for dev

## TECHNICAL NOTES
- Backend: backend/app/modules/mes/ (services.py already has anti-backfill)
- Frontend: frontend/src/pages/mes/BatchRecordDetail.tsx (extend existing)
- GMP Rules: see GMP_RULES.md section 4 (MES — Batch Records)

## EXAMPLE
POST /api/v1/mes/batch-records/{batch_id}/steps/{step_id}/sign
Body: {"username": "...", "password": "...", "actual_value": "7.2", "unit": "pH"}
Error if step already signed: 400 {"detail": "Step already recorded. ALCOA violation prevented."}
If value outside range: step flagged + deviation created automatically

## GMP RULE (from GMP_RULES.md §4)
Anti-backfill is an ALCOA hard stop. Operator must sign each step at time of execution.
QA reviewer e-sig required before batch can be RELEASED.

- **Status:** PENDING
- **Priority:** P1
- **Lane:** A + B + C
- **Commit:** feat(mes): EBR step sign-off + anti-backfill + batch release

---

### TASK-042 [P1] — Equipment: Calibration Workflow Completion

## CONTEXT
Equipment module. Calibration model exists but full workflow (measurement points, auto-flag
on failure, status badges, schedule view) is not complete.

## ACCEPTANCE CRITERIA
- [ ] Equipment list shows status badge: CALIBRATED (green) / DUE SOON (amber, ≤30 days) /
      OVERDUE (red) / OUT_OF_CALIBRATION (red + "DO NOT USE" warning)
- [ ] Calibration record: certificate_number (mandatory), performed_by, external_company (optional),
      measurement_points sub-table (point_name, nominal, tolerance, actual, pass/fail),
      as_found_condition, as_left_condition
- [ ] If any measurement point FAILS: equipment.status = OUT_OF_CALIBRATION + deviation auto-created
- [ ] QA approval e-sig required before calibration record is APPROVED
- [ ] Calibration schedule view: all equipment ordered by next_calibration_due (soonest first)
- [ ] APScheduler job: daily at 06:00 UTC — notify equipment owner + QA for ≤30 days due or overdue
- [ ] shadcn/ui + TanStack Table for equipment list and calibration history
- [ ] pytest tests/ -x -q passes

## TECHNICAL NOTES
- Backend: backend/app/modules/equipment/ (extend services.py + models.py)
- Frontend: frontend/src/pages/equipment/ (extend existing)
- GMP Rules: see GMP_RULES.md section 5 (Equipment — Calibration)
- Mock: mockEquipment from mock-api.ts (HVAC-B-02 already overdue — good test case)

## EXAMPLE
POST /api/v1/equipment/{id}/calibrations
Body: {"certificate_number": "CAL-2026-442", "measurement_points": [{"name": "temp_sensor_1", "nominal": 20.0, "tolerance": 0.5, "actual": 20.3}]}
If actual outside tolerance: point.pass = false + equipment flagged

## GMP RULE (from GMP_RULES.md §5)
Equipment with status=OUT_OF_CALIBRATION must not be used in GMP production.
System must enforce this by blocking batch step sign-off on that equipment.

- **Status:** PENDING
- **Priority:** P1
- **Lane:** A + B + C
- **Commit:** feat(equipment): calibration workflow + OOC auto-flag

---

### TASK-043 [P1] — LIMS: OOS Investigation Workflow (Phase 1 + Phase 2)

## CONTEXT
LIMS module. OOS auto-trigger exists in services.py but the full Phase 1 / Phase 2
investigation workflow and CoA generation are not built.

## ACCEPTANCE CRITERIA
- [ ] Phase 1 investigation: analyst_error_check (text), retest_authorised (boolean, requires QA e-sig),
      retest_result (if applicable), phase1_conclusion (Assignable Cause Found / No Assignable Cause)
- [ ] If Assignable Cause: original result invalidated (is_invalidated=True, preserved), retest official
- [ ] If No Assignable Cause: automatically opens Phase 2
- [ ] Phase 2: manufacturing_investigation_notes, additional_testing_authorised, statistical_evaluation,
      root_cause, disposition (PASS / FAIL / REJECT), QA Director e-sig on Final Disposition
- [ ] OOT workflow: DETECTED → UNDER_REVIEW → CLOSED (lighter, QA review + e-sig)
- [ ] CoA generation: auto-built from PASSED test results for a batch
      Contents: product, batch, all tests (name, spec, result, pass/fail), analyst, QA approver, date
      Available as PDF (use html2canvas + jsPDF or backend PDF)
      CoA LOCKED after QA e-sig (no further edits)
- [ ] shadcn/ui + TanStack Table throughout
- [ ] pytest tests/ -x -q passes

## TECHNICAL NOTES
- Backend: backend/app/modules/lims/ (extend OOS investigation model + services)
- Frontend: frontend/src/pages/lims/ (extend SampleDetail.tsx)
- GMP Rules: see GMP_RULES.md section 6 (LIMS — OOS)
- Mock: mockSamples from mock-api.ts (smp-002 is OOS — good test case)

## EXAMPLE
POST /api/v1/lims/oos-investigations/{id}/close-phase1
Body: {"conclusion": "No Assignable Cause", "username": "...", "password": "..."}
→ Phase 2 opens automatically

POST /api/v1/lims/oos-investigations/{id}/dispose
Body: {"disposition": "FAIL", "username": "...", "password": "...", "reason": "..."}
→ Requires QA Director role (403 if not QA Director)

## GMP RULE (from GMP_RULES.md §6)
OOS investigation follows USP <1010> Phase 1 → Phase 2 structure.
QA Director e-sig required on Final Disposition. CoA locked after QA approval.

- **Status:** PENDING
- **Priority:** P1
- **Lane:** A + B + C
- **Commit:** feat(lims): OOS Phase 1+2 investigation + CoA generation

---

### TASK-044 [P1] — Backend: Public Deployment (Railway + Live API)

## CONTEXT
Infrastructure. Frontend is deployed at https://t160mfctr8bq.space.minimax.io but backend
is localhost-only. The deployed frontend cannot reach the API. Must fix before any external demo.

## ACCEPTANCE CRITERIA
- [ ] Backend deployed on Railway (or equivalent) with public URL
- [ ] Railway PostgreSQL provisioned OR Supabase URL used (already configured in .env)
- [ ] Alembic migrations run against deployed DB (alembic upgrade head)
- [ ] Seed data applied (admin user + base org + site)
- [ ] frontend/.env.production updated: VITE_API_BASE_URL=https://<deployed-url>/api/v1
- [ ] Frontend rebuilt + redeployed pointing to live API
- [ ] Smoke test: login at Minimax URL → create CAPA → see in DB → close with e-sig
- [ ] docs/deployment.md documents: railway URL, env vars, redeploy steps

## TECHNICAL NOTES
- Railway CLI: npm install -g @railway/cli; railway login; railway init; railway up
- Alternative: Render.com, Fly.io (same pattern)
- Env vars to set on Railway: DATABASE_URL, SECRET_KEY, ALGORITHM, FRONTEND_URL, ENVIRONMENT=production
- Do NOT set ENVIRONMENT=production locally — only on Railway
- Supabase already has migrations run (TASK-027 done) — Railway needs fresh DB or use Supabase directly

## EXAMPLE
Local test: curl https://<railway-url>/health → {"status": "ok"}
Frontend test: login at https://t160mfctr8bq.space.minimax.io → enter admin/Admin@GMP2024!
→ Dashboard loads with real data

## GMP RULE
No GMP-specific rule. However: production environment must have ENVIRONMENT=production set
to prevent Base.metadata.create_all from running (TASK-004 guard).

- **Status:** PENDING
- **Priority:** P1 (blocks external demo)
- **Lane:** A (infrastructure)
- **Commit:** feat(deploy): backend on Railway + frontend pointed to live API

---

### TASK-045 [P2] — SAP Integration: Connector Skeleton + Mock Mode

## CONTEXT
Integration layer. SAP connector stubs exist (TASK-014 done) but no realistic API,
mock mode, or UI. This is a commercial differentiator — start early.

## ACCEPTANCE CRITERIA
- [ ] SAP config schema validated (host, system_number, client, username, password_env_var, protocol)
- [ ] SAP connector service (core/integration/connectors/sap.py):
      ping(), get_material(material_number), get_batch(material, batch),
      post_quality_notification(data), sync_material_master(site_id)
- [ ] Mock mode: if SAP_MOCK=true in .env → all methods return realistic mock data
      Mock material includes: material_number, description, base_unit, material_type,
      batch_managed, shelf_life_days, storage_conditions
- [ ] API endpoints: POST /api/v1/integrations/sap/ping, GET /api/v1/integrations/sap/material/{id},
      POST /api/v1/integrations/sap/sync/materials, GET /api/v1/integrations/sap/sync/status
- [ ] Every SAP call logged to integration_event_logs (operation, status, duration_ms, records)
- [ ] Frontend Integrations settings page: connector list with status badge + ping button + last sync
- [ ] Uses shadcn/ui for settings UI
- [ ] pytest tests/ -x -q passes (mock mode only — no real SAP needed)

## TECHNICAL NOTES
- Backend: backend/app/core/integration/connectors/sap.py (extend existing stub)
- Frontend: new page frontend/src/pages/settings/Integrations.tsx
- Table: integration_event_logs already in schema
- GMP Rules: see ARCHITECTURE.md §8 (Integration Architecture) — SAP = INTEGRATE, not REPLACE

## EXAMPLE
POST /api/v1/integrations/sap/ping (with SAP_MOCK=true)
→ {"status": "ok", "latency_ms": 42, "system": "SAP S/4HANA 2023", "mock": true}

GET /api/v1/integrations/sap/material/MRNA-DS-001
→ {"material_number": "MRNA-DS-001", "description": "mRNA Vaccine DS", "batch_managed": true, ...}

## GMP RULE
SAP integration must log every call (success, failure, duration) to integration_event_logs.
Passwords/credentials must never be stored in DB — use environment variable references only.

- **Status:** PENDING
- **Priority:** P2
- **Lane:** A + C
- **Commit:** feat(integration): SAP connector skeleton with mock mode

---

*Queue maintained by: Matrix Agent*
*Updated: 2026-04-23 15:00*
*Strategic path: Option C (ADR-005) — GMP Phase 1 now, truth layer Phase 2 after guard conditions met*
*Sprint focus: TASK-036 → TASK-037 → TASK-038 → TASK-039 (QMS complete + e-sig audit) then parallel: TASK-040/041/042/043*
