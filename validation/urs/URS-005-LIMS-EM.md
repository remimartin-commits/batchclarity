# URS-005 — User Requirements Specification: LIMS and Environmental Monitoring

| Field | Value |
|---|---|
| Document Number | URS-005 |
| Title | User Requirements Specification — LIMS and Environmental Monitoring |
| Version | 1.0 |
| Status | Draft |
| Author | GMP Platform Project Team |
| Review Date | 2027-04-01 |
| Classification | GAMP 5 Category 5 — Custom Software |
| Regulatory Basis | EU GMP Annex 11, EU GMP Chapter 6 (QC), EU GMP Annex 1 (Sterile Manufacturing), 21 CFR Part 211 §211.194, ICH Q2(R1), USP <1058> |

---

## 1. Introduction

### 1.1 Purpose

This document specifies user requirements for two GMP Platform modules:

1. **Laboratory Information Management System (LIMS)** — sample management, test result entry, OOS/OOT handling, and laboratory data integrity
2. **Environmental Monitoring (EM)** — cleanroom and controlled-area monitoring data capture, alert/action limit management, and trend analysis

Both modules generate primary analytical GMP records and must comply with EU GMP Annex 11, 21 CFR Part 11, and laboratory data integrity guidance (MHRA, FDA, PIC/S).

### 1.2 Critical Data Integrity Note

Laboratory data is subject to **specific data integrity vulnerabilities** including manipulation, selective reporting, and result invalidation. The system shall implement controls to prevent all forms of data manipulation:

- Test results shall be **append-only**; corrections require a new result entry with reason
- OOS results shall **never be invalidated without a documented Phase 1 laboratory investigation**
- Analysts shall not be permitted to delete or overwrite their own results
- All result entries shall be timestamped server-side at submission time

---

## 2. Regulatory and Compliance Requirements

| Regulation / Guidance | Section | Requirement |
|---|---|---|
| EU GMP Chapter 6 | 6.17–6.22 | Laboratory documentation and result recording |
| EU GMP Annex 11 | Clause 7 | Data entry and data capture requirements |
| EU GMP Annex 1 | 9.28–9.32 | Environmental monitoring in sterile manufacturing |
| 21 CFR Part 211 | §211.192 | Investigation of unexplained discrepancy or OOS result |
| 21 CFR Part 211 | §211.194 | Laboratory records |
| FDA OOS Guidance | 2006 | Two-phase OOS investigation requirement |
| MHRA Data Integrity Guide | 2018 | Data integrity expectations for computerised systems |
| PIC/S PI 041 | 2021 | Data integrity in pharmaceutical manufacturing |
| ICH Q2(R1) | — | Analytical method validation |

---

## 3. LIMS Requirements

### 3.1 Test Methods and Specifications

| ID | Requirement | Priority |
|---|---|---|
| LIMS-SPEC-001 | The system shall maintain a library of test methods with: code, name, description, type (physical/chemical/microbiological), compendial flag | Must |
| LIMS-SPEC-002 | The system shall maintain product specifications linked to products and test methods | Must |
| LIMS-SPEC-003 | Each specification test shall define: test name, lower limit, upper limit, acceptance criteria text, unit, mandatory flag | Must |
| LIMS-SPEC-004 | Specification versions shall be controlled; a new version required for any acceptance criteria change | Must |
| LIMS-SPEC-005 | Approved specifications shall be read-only; changes require a new version with change control | Must |

### 3.2 Sample Registration

| ID | Requirement | Priority |
|---|---|---|
| LIMS-SAMP-001 | The system shall allow registration of laboratory samples with a unique system-generated sample number | Must |
| LIMS-SAMP-002 | Sample types shall include: raw_material, in_process, finished_product, stability, environmental, water, reference_standard | Must |
| LIMS-SAMP-003 | Sample registration shall capture: sample type, batch number, product (if applicable), specification (if applicable), required-by date, received date | Must |
| LIMS-SAMP-004 | Sample status lifecycle: registered → in_testing → pending_review → released / rejected / oos | Must |
| LIMS-SAMP-005 | Samples shall not be deleted; rejected or OOS samples shall be retained with full audit history | Must |
| LIMS-SAMP-006 | Chain of custody events (received, transferred, disposed) shall be tracked with timestamps and user attribution | Should |

### 3.3 Test Result Entry

| ID | Requirement | Priority |
|---|---|---|
| LIMS-RES-001 | Test results shall be recorded by analysts with the `lims.result.create` permission | Must |
| LIMS-RES-002 | Results shall capture: test name, result value (numeric or text), unit, method reference, analyst (authenticated user, server-resolved), entry timestamp (server UTC) | Must |
| LIMS-RES-003 | **Test results shall be append-only. Once submitted, a result entry is immutable.** | Must |
| LIMS-RES-004 | Corrections to results shall require submission of a new result entry with correction reason; the original result is retained and flagged as superseded | Must |
| LIMS-RES-005 | The system shall automatically compare numeric results against specification limits and flag as: within_specification, oot (out-of-trend), oos (out-of-specification) | Must |
| LIMS-RES-006 | OOT flagging shall be based on trend rules configurable per specification (e.g., Westgard rules) | Could |
| LIMS-RES-007 | OOS preliminary flagging shall occur automatically; a reviewer with `lims.result.review` permission shall confirm the OOS determination | Must |

### 3.4 OOS (Out-of-Specification) Investigation

| ID | Requirement | Priority |
|---|---|---|
| LIMS-OOS-001 | When a result is reviewed and confirmed as OOS, the system shall **automatically create a Phase 1 OOS investigation record** | Must |
| LIMS-OOS-002 | Phase 1 investigation shall cover: laboratory error review, analyst re-check, instrument verification. Conclusion: laboratory error found (invalidate result and retest) or no laboratory error (escalate to Phase 2) | Must |
| LIMS-OOS-003 | If no laboratory error is found in Phase 1, the system shall escalate to a Phase 2 full investigation, linked to a CAPA | Must |
| LIMS-OOS-004 | OOS investigations shall have their own workflow: open → phase_1_investigation → phase_2_investigation → closed / invalidated | Must |
| LIMS-OOS-005 | Result invalidation (laboratory error confirmed) shall require documentation of the error type and corrective action, plus e-signature from a QA reviewer | Must |
| LIMS-OOS-006 | OOS investigations shall trigger an immediate email notification to the QA team and laboratory manager | Must |
| LIMS-OOS-007 | All OOS investigation actions and conclusions shall be captured in the immutable audit trail | Must |

### 3.5 Laboratory Data Integrity Controls

| ID | Requirement | Priority |
|---|---|---|
| LIMS-DI-001 | The system shall prevent analysts from accessing raw results from other analysts before they have submitted their own result (blind analysis) | Could |
| LIMS-DI-002 | Mass result entry (copying a result across multiple samples) shall be logged as a separate audit event and require confirmation | Should |
| LIMS-DI-003 | Any audit trail query showing the same result value across multiple independent samples shall generate a data integrity alert | Could |
| LIMS-DI-004 | The system shall log all login attempts, failed logins, and session timeouts for laboratory users | Must |

---

## 4. Environmental Monitoring Requirements

### 4.1 Monitoring Locations

| ID | Requirement | Priority |
|---|---|---|
| EM-LOC-001 | The system shall maintain a registry of environmental monitoring locations with: code, name, GMP grade (A/B/C/D), room, building | Must |
| EM-LOC-002 | GMP grade classification shall follow EU GMP Annex 1 (Grade A: critical zone, B: background to A, C/D: clean areas) | Must |
| EM-LOC-003 | Monitoring locations shall have active/inactive status | Must |
| EM-LOC-004 | Each location shall have configurable alert limits and action limits per parameter | Must |

### 4.2 Alert and Action Limits

| ID | Requirement | Priority |
|---|---|---|
| EM-LIMIT-001 | Alert and action limits shall be configurable per location per parameter | Must |
| EM-LIMIT-002 | Parameters shall include at minimum: total_aerobic_count, total_yeast_mould, particle_0_5um, particle_5um, temperature, relative_humidity, differential_pressure | Must |
| EM-LIMIT-003 | Limits shall be based on EU GMP Annex 1 recommended levels by grade, with facility-specific tightening allowed | Must |
| EM-LIMIT-004 | Changes to alert and action limits shall require change control documentation and shall be fully audited | Must |

### 4.3 Result Entry and Classification

| ID | Requirement | Priority |
|---|---|---|
| EM-RES-001 | EM results shall be recorded by users with `env_monitoring.create` permission | Must |
| EM-RES-002 | Result entry shall capture: location, parameter, result value, unit, sampling date, sampled by (authenticated user), comments | Must |
| EM-RES-003 | Result entry timestamp (result_entered_at) shall be server-set in UTC at submission time | Must |
| EM-RES-004 | The system shall **automatically classify** each result against the location's configured limits: within_limits, alert, action, oot, oos | Must |
| EM-RES-005 | Classification shall be server-side and immutable; the operator cannot select a classification | Must |
| EM-RES-006 | Alert limit exceedances shall trigger email notification to the QA team | Must |
| EM-RES-007 | **Action limit exceedances shall trigger immediate email notification and prompt for deviation record creation** | Must |
| EM-RES-008 | EM results shall be retained with full audit trail permanently | Must |

### 4.4 Sampling Plans

| ID | Requirement | Priority |
|---|---|---|
| EM-PLAN-001 | The system shall support definition of sampling plans specifying: location, parameter, frequency, responsible party | Should |
| EM-PLAN-002 | Missing samples (scheduled but not recorded within the defined period) shall generate alert notifications | Should |

### 4.5 Trending and Reporting

| ID | Requirement | Priority |
|---|---|---|
| EM-TREND-001 | The system shall generate trend reports showing EM results over time per location and parameter | Must |
| EM-TREND-002 | The system shall calculate and display rolling averages with control chart limits (alert and action) | Should |
| EM-TREND-003 | Trend analysis shall identify upward trends that may indicate contamination risk before limits are exceeded | Could |
| EM-TREND-004 | Monthly EM summary reports shall be auto-generated and notified to the QA team | Should |
| EM-TREND-005 | Dashboard shall display: exceedances this month (alert / action), locations with missing samples, grade summary | Must |

---

## 5. EU GMP Annex 1 Compliance Matrix

| Annex 1 Clause | Requirement | System Implementation |
|---|---|---|
| 9.28 | EM programme for cleanrooms | EM location registry with GMP grades |
| 9.29 | Alert and action limits | Configurable per location per parameter |
| 9.30 | Classification of results | Auto-classification server-side, immutable |
| 9.31 | Investigation of exceedances | Action limit → automatic deviation prompt |
| 9.32 | Trend analysis | Trend reports and rolling averages |
| 9.35 | Records retained | Audit trail retained indefinitely |

---

## 6. Acceptance Criteria

### LIMS

| ID | Test | Expected Result |
|---|---|---|
| LIMS-AC-001 | Submit test result; check timestamp | Timestamp is server UTC; client-provided time rejected |
| LIMS-AC-002 | Attempt to edit submitted result | System returns 400/403 |
| LIMS-AC-003 | Submit OOS result; review as OOS | Phase 1 OOS investigation auto-created |
| LIMS-AC-004 | Submit OOS result; review as laboratory error | Investigation status → invalidated; e-sig required |
| LIMS-AC-005 | List samples with status_filter=oos | Returns only OOS samples |
| LIMS-AC-006 | Submit result within specification | Status remains in_specification; no investigation created |

### Environmental Monitoring

| ID | Test | Expected Result |
|---|---|---|
| EM-AC-001 | Record result exceeding action limit | Status = action; alert dispatched; deviation prompted |
| EM-AC-002 | Record result between alert and action limit | Status = alert; alert notification dispatched |
| EM-AC-003 | Record result within both limits | Status = within_limits; no notification |
| EM-AC-004 | Attempt to set result status manually | System ignores; server-side classification used |
| EM-AC-005 | Query results for Grade A location | Returns only Grade A results |
| EM-AC-006 | Change action limit without documentation | System requires change control reference |

---

## 7. Revision History

| Version | Date | Author | Summary |
|---|---|---|---|
| 1.0 | 2026-04-20 | GMP Platform Project Team | Initial draft |
