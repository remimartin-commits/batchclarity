# Information Purity — Operational Specification

**Module:** LIMS (Path A) / Information Purity Engine (Path B)
**Status:** SPECIFICATION — not yet implemented
**ADR:** ADR-004-module-as-capability.md
**Owner:** Matrix Agent
**Date:** 2026-04-22

---

## What This Document Is

This spec defines "information purity" operationally — moving it from a metaphor to a
set of verifiable conditions that can be implemented in code and tested.

It answers the question: **what does the LIMS module actually check?**

---

## The Six Purity Conditions

A data point (sample, test result, measurement, or any stored value) is considered **PURE**
if and only if all six conditions are satisfied. Failure of any single condition triggers
an OOS (Out-Of-Specification) investigation.

---

### Condition 1 — Provenance Verified

The source of the data is a known, trusted, and currently-qualified input.

**GMP implementation:**
- `Sample.sample_source` links to a qualified material or instrument
- The source instrument must have a current `CalibrationRecord` (not overdue)
- Samples from unqualified sources are rejected at ingestion

**AI governance implementation:**
- Every data input has a declared source (model, agent, API, human)
- The source must be in the approved source registry
- Data from unregistered or expired sources is quarantined

**Verification query:**
```sql
SELECT s.id, s.sample_source, cr.next_calibration_due
FROM samples s
LEFT JOIN calibration_records cr ON cr.equipment_id = s.source_instrument_id
WHERE cr.next_calibration_due < NOW() OR cr.id IS NULL
-- Any result = provenance failure
```

---

### Condition 2 — Chain of Custody Intact

Every transformation applied to the data is logged, attributed, and timestamped.
No gap in the lineage from raw input to final stored value.

**GMP implementation:**
- Every `TestResult` records: `tested_by_id`, `tested_at` (server UTC), `method_id`
- If a result is derived from another result, `derived_from_result_id` is populated
- The audit trail contains every state change: who, when, what changed

**AI governance implementation:**
- Every transformation step is an `AuditEvent` record
- No transformation occurs without a corresponding log entry
- The provenance graph is traversable from any output back to raw input

**Verification query:**
```sql
SELECT tr.id
FROM test_results tr
WHERE tr.derived_from_result_id IS NOT NULL
  AND NOT EXISTS (
    SELECT 1 FROM audit_events ae
    WHERE ae.entity_type = 'TestResult'
      AND ae.entity_id = tr.id
      AND ae.action LIKE '%.derived%'
  )
-- Any result = custody gap
```

---

### Condition 3 — Original Preserved

The raw input is never overwritten. Corrections create new records that reference the
original. The original remains immutable and queryable.

**GMP implementation:**
- `TestResult` rows are APPEND-ONLY (enforced in services.py)
- Corrections: new `TestResult` with `corrects_result_id = original.id` and `original.status = 'invalidated'`
- Original is never updated or deleted

**AI governance implementation:**
- Same append-only model for any stored inference, decision, or output
- "Editing" an AI output = creating a new record that references and supersedes the old one
- Old output remains in the provenance graph

**Code enforcement:**
```python
# In lims/services.py — correct_test_result()
if original.status == "invalidated":
    raise HTTPException(400, "Cannot correct an already-invalidated result.")
# Create new result
correction = TestResult(corrects_result_id=original.id, ...)
# Invalidate original — do NOT delete
original.status = "invalidated"
original.invalidated_by_id = corrected_by_id
original.invalidated_at = datetime.now(timezone.utc)
```

---

### Condition 4 — Anomaly Detection Passed

The value is within the accepted specification for this data type in this context.
Values outside specification are not rejected — they are flagged and investigated.

**GMP implementation:**
- `Specification` defines min/max/target for each test method
- `TestResult.is_oos` is set to True if the result falls outside spec
- `OOSInvestigation` is created automatically when `is_oos = True`

**AI governance implementation:**
- `Specification` = the definition of "what this data type should look like"
- Anomaly detection = comparing input against spec before trusting it
- OOS = anomaly detected → automatic investigation, not silent acceptance

**Trigger logic (in services.py):**
```python
async def record_test_result(session, sample_id, data, tested_by_id, site_id):
    result = TestResult(...)
    # Check against specification
    spec_test = await get_spec_test(session, data.method_id, site_id)
    if spec_test and not within_spec(data.value, spec_test):
        result.is_oos = True
        # Auto-create OOS investigation
        await create_oos_investigation(
            session,
            sample_id=sample_id,
            triggered_by_result_id=result.id,
            site_id=site_id,
        )
```

---

### Condition 5 — Timing is Contemporaneous

The record timestamp was set by the server at the moment of capture. No retrospective
backdating. No client-provided timestamps for audit-critical fields.

**GMP implementation:**
- `TestResult.tested_at = datetime.now(timezone.utc)` — set in service layer, never from request body
- `performed_at`, `completed_at`, `signed_at` — all server-set UTC
- BUILDING_RULES.md §5.3: back-fill prevention enforced in service layer

**AI governance implementation:**
- Every inference, decision, and output is timestamped at generation time by the system
- No post-hoc timestamp assignment
- The audit trail timestamp and the business record timestamp must match within tolerance

**Enforcement:**
```python
# In services.py — never accept performed_at from request body for audit fields
result = TestResult(
    tested_at=datetime.now(timezone.utc),  # server-set
    tested_by_id=tested_by_id,
    # NOT: tested_at=data.tested_at  — this would be a ALCOA violation
)
```

---

### Condition 6 — Correction is Transparent

If a data point was corrected, the correction is visible, attributed, and the reason is
documented. There is no "silent fix." The original and the correction coexist in the system.

**GMP implementation:**
- `TestResult.corrects_result_id` links correction to original
- `TestResult.correction_reason` is mandatory when `corrects_result_id` is set
- Audit trail shows both records and the correction event
- The correction itself requires a re-authentication (e-signature)

**AI governance implementation:**
- No "editing" of AI outputs — only transparent corrections with attribution
- Every correction is a new record that acknowledges the original
- Reason for correction is mandatory

---

## OOS Investigation — What It Is and What It Triggers

An OOS (Out-Of-Specification) investigation is created automatically when any purity
condition fails. It is NOT a manual step — it is triggered by the system.

**Trigger conditions:**
- Condition 4 failure: value outside specification
- Condition 1 failure: source not qualified (future implementation)
- Condition 2 failure: custody gap detected (future implementation)

**Investigation lifecycle:**
```
OPEN → UNDER_INVESTIGATION → CONCLUDED
         ↓                        ↓
    Root cause identified    Disposition: PASS / FAIL / VOID
```

**Disposition meanings:**
- `PASS` — investigation found the original result valid despite appearing OOS (e.g. instrument error, not product failure). Result reinstated.
- `FAIL` — investigation confirmed failure. Batch/record affected. Corrective action required.
- `VOID` — result was invalidated due to method error. Re-test required.

**All dispositions require e-signature** (21 CFR Part 11 + non-repudiation requirement).

---

## What Is NOT Checked (Known Limitations)

| Limitation | Why Not Solved | Future Path |
|---|---|---|
| Semantic distortion | "Pure" vs "framed to mislead" requires context. Statistical methods only partially detect this. | Adversarial red-team testing (TASK-017 extension). Watermarking research. |
| Cross-module data corruption | If MES feeds a corrupted batch number to LIMS, LIMS checks the number against its own spec but cannot verify MES internal integrity. | Cross-module provenance hash (future: each module signs its outputs). |
| Adversarial inputs designed to pass spec | A manipulated value that is within spec but factually wrong. | Requires reference datasets + statistical process control (SPC) — future module. |

---

## Implementation Priority

This spec is implemented as part of **TASK-024** (LIMS services.py).

The minimum viable implementation for LIMS FUNCTIONAL tier:
- [x] Append-only TestResult model (done)
- [ ] `record_test_result` sets `is_oos` and auto-creates OOSInvestigation
- [ ] `correct_test_result` enforces original preservation
- [ ] `tested_at` is server-set (never from request body)
- [ ] OOSInvestigation lifecycle (OPEN → CONCLUDED with e-sig)
- [ ] Condition 1 check: source instrument calibration status

Full information purity (all 6 conditions) requires LIMS HARDENED tier.

---

*Written by: Matrix Agent*
*Date: 2026-04-22*
*Implements: ADR-004, TASK-024*
*Next review: when LIMS reaches FUNCTIONAL tier*
