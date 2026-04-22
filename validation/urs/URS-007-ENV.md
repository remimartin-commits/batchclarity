# User Requirement Specification
## URS-007 — Environmental Monitoring Module

| Field | Value |
|---|---|
| Document Number | URS-007 |
| Title | GMP Platform — Environmental Monitoring Module |
| Version | 1.0 |
| Status | Draft |
| Author | GMP Platform Project Team |
| Date | 2026-04-22 |
| Classification | GMP Critical |

---

## 1. Purpose

Define user requirements for environmental monitoring location management, alert/action limit classification, and trend/notification controls.

---

## 2. Regulatory Basis

- EU GMP Annex 1
- EU GMP Annex 11
- 21 CFR Part 211
- 21 CFR Part 11

---

## 3. Functional Requirements

| ID | Requirement |
|---|---|
| URS-007-001 | The system shall maintain monitoring location records with GMP grade and site context. |
| URS-007-002 | The system shall support parameter-specific alert/action limits per location. |
| URS-007-003 | Result entry shall classify status server-side (normal/alert/action). |
| URS-007-004 | Alert limit exceedances shall be highlighted amber; action limit exceedances highlighted red. |
| URS-007-005 | Result entry endpoints shall record sampling metadata and comments. |
| URS-007-006 | Overdue trend review checks shall trigger rule-based notifications. |

---

## 4. Acceptance Criteria

| ID | Test | Expected Result |
|---|---|---|
| URS-007-AC-001 | Record result below alert limit | Status is normal/within_limits and no exceedance highlight. |
| URS-007-AC-002 | Record result above alert but below action | Status is alert and row is amber-highlighted. |
| URS-007-AC-003 | Record result above action limit | Status is action and row is red-highlighted. |
| URS-007-AC-004 | Run overdue review scheduler hook | Rule notification is emitted for overdue trend reviews. |

---

## 5. Traceability to Module Features

| Requirement IDs | Feature Mapping |
|---|---|
| URS-007-001 | `/api/v1/env-monitoring/locations` |
| URS-007-002 | `/api/v1/env-monitoring/locations/{id}/limits` |
| URS-007-003,005 | `/api/v1/env-monitoring/locations/{id}/results` |
| URS-007-004 | frontend `EnvMonitoringList` alert/action visual states |
| URS-007-006 | `check_overdue_monitoring_reviews` scheduler task |

