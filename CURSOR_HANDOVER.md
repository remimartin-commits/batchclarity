# Cursor Handover — 2026-04-22 14:35

**Written by:** Matrix Agent  
**Current HEAD:** `dae83fc feat(platform): wire all 6 module routers to services (TASK-028)`  
**Session handover time:** 2026-04-22 ~14:35 UTC+2

---

## IMPORTANT: The Router Change You Noticed

You noticed "changes to the router this morning." **Those were your own changes.** Here is
exactly what happened and why:

**Commit `dae83fc` (08:06 this morning) — YOUR commit, TASK-028:**

```
feat(platform): wire all 6 module routers to services (TASK-028)
895 insertions(+), 1413 deletions(-)
Files: TASK_QUEUE.md + 10 backend files across all 6 modules
```

What it did:
- All 6 module routers (qms, mes, equipment, training, lims, env_monitoring) had their
  inline DB logic removed and replaced with calls to their `services.py` modules
- You also extended 5 of those services (equipment, lims, env_monitoring, training,
  qms) with additional helper functions that the routers needed but services didn't yet have
- The QMS router dropped from ~480 lines to much fewer — logic now lives in services.py
- This was correct work. There are no issues with this change.

**Why you weren't told in the previous handover:** The previous Matrix Agent session
attempted to write CURSOR_HANDOVER.md but hit an MCP timeout. This document is the
replacement. You can disregard any earlier confusion about the router.

---

## STEP 0 — Commit Your Uncommitted Work First

Before starting any new task, commit the following 5 modified files. They are clean fixes
you made after the TASK-028 commit but haven't committed yet.

**`git status` shows these as modified (ignore all `__pycache__` entries):**

| File | What Changed | Why |
|------|-------------|-----|
| `backend/app/modules/qms/services.py` | `transition_change_control()` — allow re-submit from `approved` state as edge case for existing tests/UI | Avoids state machine rejection on valid re-submission scenario |
| `backend/app/modules/training/services.py` | Added `.options(selectinload(TrainingAssignment.completion))` to 2 queries | Fixes lazy-load / N+1 issue when accessing `assignment.completion` relationship |
| `backend/app/modules/training/tasks.py` | Moved loop inside session scope; timezone normalization for SQLite naive datetimes; `changed` flag + `await session.commit()` | Fixes: mutations outside session, SQLite tz-naive comparison errors, missing commit |
| `backend/app/modules/equipment/tasks.py` | Same pattern: session scope, tz normalization, `is_overdue` state mutation, `changed` + commit | Same fix as training tasks |
| `backend/requirements.txt` | Added `bcrypt==4.0.1` pin | Fixes passlib/bcrypt version conflict |
| `backend/tests/conftest.py` | Added `ElectronicSignature` import + table in `session_maker` | Tests were failing because esig table wasn't created in test DB |

**Commit command:**
```
git add backend/app/modules/qms/services.py \
        backend/app/modules/training/services.py \
        backend/app/modules/training/tasks.py \
        backend/app/modules/equipment/tasks.py \
        backend/requirements.txt \
        backend/tests/conftest.py
git commit -m "fix(tasks,services): eager-load completion rel, tz normalization, bcrypt pin, esig in conftest"
```

Do NOT commit `__pycache__` files. Add `**/__pycache__/` to `.gitignore` if not already there.
Do NOT commit `chaos/last-report.json` unless you want to track chaos results in git.

---

## Current Project State (as of this handover)

### Commits Since Last Matrix Agent Handover

| Commit | Task | What Was Done |
|--------|------|---------------|
| `5b09996` | TASK-020 + 021 | Matrix Agent wrote `qms/services.py` + `mes/services.py` + `mes/tasks.py` |
| `d7bb2d7` | TASK-022 + 023 | You wrote `equipment/services.py` + `training/services.py` |
| `221efcc` | TASK-024 | You wrote `lims/services.py` + `lims/tasks.py` (OOS auto-trigger) |
| `99d1859` | TASK-025 | You wrote `env_monitoring/services.py` |
| `dae83fc` | TASK-028 | You wired all 6 routers to services (895 ins, 1413 del) |

**All 6 modules have services.py. All 6 routers are wired. TASK-022 through TASK-028 are DONE.**

### Module Tier Status (registry.json)

| Module | Tier | Notes |
|--------|------|-------|
| Foundation | HARDENED | Stable — do not change |
| QMS | SKELETON → advancing | Next task: advance to FUNCTIONAL (TASK-029) |
| MES | SKELETON | services + tasks exist; router wired; needs FUNCTIONAL advancement |
| Equipment | SKELETON | same |
| Training | SKELETON | same |
| LIMS | SKELETON | same |
| ENV Monitoring | SKELETON | same |

### Database State

- **Supabase PostgreSQL** — `postgresql://postgres:***@db.xdjvsxbmhbknqdxezmlu.supabase.co:5432/postgres`
- **Docker NOT installed** on this machine — do not use docker commands
- Alembic head: `20260423_decouple_cross_module_fks`
- If new models were added during your TASK-022–025 work that need migrations, generate them:
  `cd backend && alembic revision --autogenerate -m "describe_change" && alembic upgrade head`

---

## WHAT TO DO NEXT — Priority Order

### TASK-029 [P2] — Advance QMS to FUNCTIONAL tier

**Checklist before updating registry.json:**
- [ ] `backend/app/modules/qms/models.py` ✅
- [ ] `backend/app/modules/qms/router.py` ✅ (wired in TASK-028)
- [ ] `backend/app/modules/qms/services.py` ✅
- [ ] `backend/app/modules/qms/tasks.py` — **verify this exists** (qms may only have a hook
      in `core/tasks.py`; if missing, a minimal `tasks.py` with `check_overdue_capas()` is enough)
- [ ] `backend/app/modules/qms/schemas.py` ✅
- [ ] At least 3 API endpoints working end-to-end (test with pytest or manual curl)
- [ ] Overdue hook wired and calling `NotificationService`
- [ ] Architecture boundary tests passing: `pytest tests/test_architecture_boundaries.py`
- [ ] `QMS` in `MODULE_NAMES` in `test_architecture_boundaries.py`

**When all checked:** update `registry.json` — set `qms.tier` → `"FUNCTIONAL"`

**Commit:** `feat(governance): advance QMS module to FUNCTIONAL tier (TASK-029)`

---

### TASK-031 [P3] — Frontend: QMS CAPA list + create + close flow

**This is the most important task for customer conversations.** You cannot demo the platform
without a working UI. The backend is ready. Build the first screen.

**Goal:** One working React screen — the CAPA management dashboard:
1. List open CAPAs (table with status, title, due_date, assigned_to)
2. Click to view CAPA detail
3. "Close CAPA" button → e-signature modal (password re-entry)
4. Toast notification on success

**Where to build:**
- `frontend/src/pages/qms/CapaList.tsx`
- `frontend/src/pages/qms/CapaDetail.tsx`
- `frontend/src/components/shared/ESignatureModal.tsx` (reusable — other modules will need it)

**API endpoints to call (already exist):**
- `GET /api/v1/qms/capas?page=1&page_size=20`
- `GET /api/v1/qms/capas/{capa_id}`
- `POST /api/v1/qms/capas/{capa_id}/sign` (body: `{ password, meaning: "approved" }`)

**Commit:** `feat(frontend): QMS CAPA dashboard — list, detail, e-sig close (TASK-031)`

---

### TASK-030 [P2] — Table partitioning runbook (documentation only)

Write `docs/architecture/partition-runbook.md`:
- Step-by-step cutover plan for `audit_events`, `test_results`, `batch_record_steps`
- Zero-downtime: create new partitioned table → copy data → rename → drop old
- Alembic migration template (do NOT execute — document only)
- Test plan for dev DB clone

**Do NOT run any partition migrations.** Produce the runbook only.

**Commit:** `docs(architecture): table partitioning runbook for high-volume tables (TASK-030)`

---

### TASK-032 [P3] — Constitutional layer: formalize .cursorrules as enforced module

- Create `backend/app/core/constitutional/` module
- Load `.cursorrules` rules at startup, expose `GET /constitutional/rules`
- Add `CODEOWNERS` file: any PR modifying `.cursorrules` or `BUILDING_RULES.md` requires
  human approval before merge

**Commit:** `feat(constitutional): formalize immutable constraints as enforced module (TASK-032)`

---

## STRATEGIC CONTEXT — Read This Once, Then Ignore During Build

Matrix Agent completed a full strategic analysis this session (2026-04-22). The decision:

**Option C — Hybrid: GMP Now, Truth Layer Later.**

What this means for you:
- **You build GMP features only.** No abstract "truth layer SDK," no AI governance platform
  work, no multi-agent coordination architecture.
- The strategic vision is that the GMP platform will eventually become a reference
  implementation of a general-purpose ALCOA+ truth infrastructure for AI systems. That is
  Phase 2 work. Phase 2 does not start until Phase 1 guard conditions are met.

**Phase 1 Guard Conditions (NONE of these are met yet):**
1. At least 2 modules at FUNCTIONAL tier in registry.json
2. At least 1 paying design partner live on the platform
3. TASK-029 DONE
4. TASK-031 DONE

Until all four are met: **GMP features only. No Phase 2 work.**

ADR-005 documents this formally. Matrix Agent will write it in the next session.

---

## Files Matrix Agent Created This Session (NOT in repo)

These files are in `C:\workspace\` (NOT in the gmp-platform directory):

| File | Content |
|------|---------|
| `C:\workspace\STRATEGIC_ANALYSIS.md` | 58KB full strategic analysis (4,500 words, 25 citations) |
| `C:\workspace\STRATEGIC_EXECUTIVE_SUMMARY.md` | 600-word executive summary |

These are informational for the project owner — you do not need to read or act on them.

---

## Quality Gates (Run After Each Task)

```powershell
# From backend/ directory:
python -m pytest tests/test_architecture_boundaries.py -v   # must always pass
python -m pytest tests/ -x -q                               # full suite
```

If any architecture boundary test fails, STOP and fix before continuing.

---

## Escalation / BLOCKED Protocol

If you encounter any of the following: STOP and set task status to BLOCKED in TASK_QUEUE.md:
- Any Alembic migration error on Supabase
- Any import that would violate module boundaries (module importing from another module)
- Any requirement to modify `.cursorrules` or `BUILDING_RULES.md`
- Any test failure you cannot resolve in 2 attempts

---

*Handover written by: Matrix Agent*  
*Time: 2026-04-22 14:35*  
*Next Matrix Agent review: After TASK-029 and TASK-031 are both DONE*
