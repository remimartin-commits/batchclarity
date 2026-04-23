# Part 11 / Annex 11 E-Signature Audit

Date: 2026-04-23
Scope: state/status transition endpoints across QMS, MES, Equipment, LIMS, Training, and Documents.

## Audit Criteria

For each endpoint that changes a `status`/`state` field:

1. JWT protection present (`Depends(get_current_user)`).
2. Electronic signature record written (`electronic_signatures` via `ESignatureService.sign`).
3. Audit log includes old/new state values.
4. Password is re-verified at sign time.

Status legend:
- `PASS` = already compliant before this task.
- `FIXED` = gap found and remediated in this task.
- `N/A` = no qualifying endpoint exists in this codebase area.

## QMS

- `POST /api/v1/qms/capas/{capa_id}/sign` (`open|investigation|action_plan_approved|in_progress|effectiveness_check|closed`): `PASS`
- `POST /api/v1/qms/deviations/{deviation_id}/sign` (`open|under_investigation|pending_approval|closed`): `PASS`
- `POST /api/v1/qms/change-controls/{cc_id}/sign` (`draft|under_review|approved|in_implementation|effectiveness_review|closed`): `PASS`
- `PATCH /api/v1/qms/capas/{capa_id}/actions/{action_id}` (`capa_action.status` transition): `FIXED` (added password-gated e-signature + transition audit with old/new status)
- Risk/Supplier/Complaint/Audit submodules: `N/A` (no status-transition API endpoints currently implemented)

## MES

- `POST /api/v1/mes/mbrs/{mbr_id}/sign` (`mbr.status`): `FIXED` (added explicit transition audit old/new status)
- `PATCH /api/v1/mes/batch-records/{br_id}/steps/{step_id}` (`batch_record_step.status` sign-off): `FIXED` (added password-gated e-signature + transition audit old/new status)
- `POST /api/v1/mes/batch-records/{br_id}/release` (`batch_record.status` to `released|rejected`): `FIXED` (added explicit transition audit old/new status)

## Equipment

- `PATCH /api/v1/equipment/{eq_id}/status` (`equipment.status`): `FIXED` (added password-gated e-signature; old/new audit already present and retained)
- Calibration and qualification creation endpoints: `N/A` for status transitions (record creation, not transition endpoints)

## LIMS

- `POST /api/v1/lims/results/{result_id}/review` (`test_result.status`): `FIXED` (added transition audit old/new status)
- OOS disposition endpoint: `N/A` (close/disposition API route not currently exposed in `lims/router.py`)
- CoA approval endpoint: `N/A` (not present in current API surface)

## Training

- `POST /api/v1/training/assignments/{assignment_id}/complete` (`training_assignment.status`): `FIXED` (added password-gated e-signature + transition audit old/new status)
- `POST /api/v1/training/assignments/{assignment_id}/read-and-understood` (`training_assignment.status`): `FIXED` (added transition audit old/new status; e-signature already present)

## Documents

- `POST /api/v1/documents/{doc_id}/versions/{version_id}/sign` (`document_version.status` to `under_review|approved|effective|obsolete`): `FIXED` (added transition audit old/new status)

## Notes

- All audited transition endpoints are JWT-protected at the router layer.
- Password verification at signing time is enforced through `ESignatureService.sign`.
- Transition audits now consistently capture `old_value.status` and `new_value.status`.
