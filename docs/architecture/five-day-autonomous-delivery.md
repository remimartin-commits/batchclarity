# Five-Day Autonomous Delivery (Completed)

This document records the autonomous hardening pass across QMS, Document Control, Training, and Equipment modules.

## Day 1 — QMS

- Hardened status-field consistency (`current_status`) across Deviation and Change Control.
- Added typed update schemas and forbidden unknown-field payloads.
- Added transition endpoints with guardrails and audit logs.
- Added sign endpoints for Deviation and Change Control.
- Rebuilt QMS detail pages and wired list-to-detail routes.
- Expanded QMS behavior and route contract tests.

## Day 2 — Document Control

- Added document list filtering (`type_id`, `search`, `include_obsolete`) and pagination.
- Added duplicate version checks.
- Enforced change reason on revisions after initial version.
- Hardened signing flow with supported meanings:
  - `reviewed`, `approved`, `effective`, `obsolete`
- Added one-effective-version behavior:
  - previous effective becomes `superseded` on new `effective`.

## Day 3 — Training

- Added strict payload validation on completion and read-and-understood requests.
- Added assignment detail endpoint (`GET /training/assignments/{assignment_id}`).
- Added curriculum detail endpoint including items (`GET /training/curricula/{id}`).
- Enforced ownership:
  - users can only complete/acknowledge their own assignments.
- Rebuilt training list/detail pages to match backend schema and available actions.

## Day 4 — Equipment

- Added equipment status-transition guardrails with explicit allowed transitions.
- Added strict payload validation for status updates.
- Rebuilt equipment list/detail pages to match backend schema and available actions.
- Wired list-to-detail routes and retained calibration/qualification/maintenance visibility.

## Day 5 — Integration and Quality Gate

- Extended smoke script to cover:
  - auth/me/users
  - qms deviations
  - documents
  - training
  - equipment
- Added combined gate script (`run-autonomous-gate.ps1`) to run backend checks and frontend build.
- Expanded behavior test suite for documents/training/equipment.
- Expanded route-contract assertions for documents/training/equipment endpoints.

## Validation Commands

```powershell
cd "C:\Users\fella\OneDrive\Desktop\work\gmp-platform\backend"
.\.venv\Scripts\python.exe -m pytest tests\test_api_behavior_qms.py tests\test_api_behavior_docs_training_equipment.py tests\test_api_router_contract.py -q
```

```powershell
cd "C:\Users\fella\OneDrive\Desktop\work\gmp-platform\backend"
.\scripts\run-checks.ps1
```

```powershell
cd "C:\Users\fella\OneDrive\Desktop\work\gmp-platform\frontend"
npm run build
```

```powershell
cd "C:\Users\fella\OneDrive\Desktop\work\gmp-platform\backend"
.\scripts\run-autonomous-gate.ps1
```
