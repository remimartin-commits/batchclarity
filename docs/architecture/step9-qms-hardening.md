# Step 9 QMS Hardening (Current Slice)

This slice hardens QMS behavior so CAPA/Deviation/Change Control API logic is consistent and testable for team-scale use.

## What was fixed

- Corrected Deviation status filtering to use `current_status` (model field), not `status`.
- Corrected Change Control status filtering to use `current_status`.
- Replaced permissive dict-based patch handlers with typed update schemas:
  - `DeviationUpdate`
  - `ChangeControlUpdate`
- Update schemas now reject unknown fields (`extra="forbid"`), reducing silent bad writes.
- Added Deviation transition endpoints with permission checks and audit:
  - `POST /api/v1/qms/deviations/{id}/submit`
  - `POST /api/v1/qms/deviations/{id}/approve`
  - `POST /api/v1/qms/deviations/{id}/close`
- Added Change Control transition endpoints with permission checks and audit:
  - `POST /api/v1/qms/change-controls/{id}/submit`
  - `POST /api/v1/qms/change-controls/{id}/approve`
  - `POST /api/v1/qms/change-controls/{id}/implement`
  - `POST /api/v1/qms/change-controls/{id}/close`
- Added Deviation and Change Control signing endpoints:
  - `POST /api/v1/qms/deviations/{id}/sign`
  - `POST /api/v1/qms/change-controls/{id}/sign`
- Frontend detail pages were rewritten to use live backend schema and supported actions:
  - `frontend/src/pages/qms/DeviationDetail.tsx`
  - `frontend/src/pages/qms/ChangeControlDetail.tsx`
- Frontend routes now include:
  - `/qms/deviations/:id`
  - `/qms/change-controls/:id`

## Automated coverage added

- New API behavior test: `backend/tests/test_api_behavior_qms.py`
  - Deviation: create -> update -> list/filter -> transition -> sign -> invalid update payload
  - Change Control: create -> update -> list/filter -> transition chain -> sign
  - Permission guardrail: operator denied transition action
- Router contract test extended: `backend/tests/test_api_router_contract.py`
  - Verifies key QMS CRUD, sign, and transition routes are registered under API router.
- Test harness updated in `backend/tests/conftest.py` to include QMS router and required tables.
- QMS permissions seeded in test role setup so transition/sign checks are exercised.
- Smoke script expanded: `backend/scripts/smoke_auth_admin.py`
  - Flow: `login -> me -> users -> qms/deviations list -> deviation detail -> deviation update`
- Added one-command quality gate script:
  - `backend/scripts/run-autonomous-gate.ps1`
  - Runs backend checks then frontend production build; fails fast on first error.

## Validation commands

```powershell
cd "C:\Users\fella\OneDrive\Desktop\work\gmp-platform\backend"
.\scripts\run-checks.ps1
```

```powershell
cd "C:\Users\fella\OneDrive\Desktop\work\gmp-platform\backend"
.\.venv\Scripts\python.exe -m pytest tests\test_api_behavior_qms.py -q
```

```powershell
cd "C:\Users\fella\OneDrive\Desktop\work\gmp-platform\backend"
.\scripts\run-autonomous-gate.ps1
```
