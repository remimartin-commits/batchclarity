# User Requirement Specification
## URS-006 — LIMS Module

| Field | Value |
|---|---|
| Document Number | URS-006 |
| Title | GMP Platform — LIMS Module |
| Version | 1.0 |
| Status | Draft |
| Author | GMP Platform Project Team |
| Date | 2026-04-22 |
| Classification | GMP Critical |

---

## 1. Purpose

Define user requirements for laboratory sample management, test result capture, OOS handling, and automated quality escalation.

---

## 2. Regulatory Basis

- EU GMP Chapter 6
- EU GMP Annex 11
- 21 CFR Part 211.192 / 211.194
- 21 CFR Part 11
- FDA OOS Guidance

---

## 3. Functional Requirements

| ID | Requirement |
|---|---|
| URS-006-001 | The system shall register samples with unique sample numbers and lifecycle status. |
| URS-006-002 | The system shall store test results as append-only records. |
| URS-006-003 | Results marked OOS shall be visibly highlighted and traceable in UI/API. |
| URS-006-004 | OOS result capture shall automatically trigger QMS deviation creation. |
| URS-006-005 | Open OOS investigations older than threshold shall trigger scheduler notifications. |
| URS-006-006 | LIMS lists and detail pages shall support result entry and review workflows. |

---

## 4. Acceptance Criteria

| ID | Test | Expected Result |
|---|---|---|
| URS-006-AC-001 | Create sample and add non-OOS result | Result saved, no deviation auto-created. |
| URS-006-AC-002 | Add OOS result | Result saved and QMS deviation is auto-created. |
| URS-006-AC-003 | List sample results with OOS rows | OOS rows are highlighted and include deviation linkage UI. |
| URS-006-AC-004 | Run open OOS scheduler hook | Rule notification is emitted for stale investigations. |

---

## 5. Traceability to Module Features

| Requirement IDs | Feature Mapping |
|---|---|
| URS-006-001 | `/api/v1/lims/samples` |
| URS-006-002,003 | `/api/v1/lims/samples/{id}/results` |
| URS-006-004 | `lims.services.record_test_result` -> `qms.services.create_deviation_from_oos` |
| URS-006-005 | `check_open_oos_investigations` scheduler task |
| URS-006-006 | frontend `SampleList` and `SampleDetail` pages |

