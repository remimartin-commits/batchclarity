# User Requirement Specification
## URS-004 — Equipment Management Module

| Field | Value |
|---|---|
| Document Number | URS-004 |
| Title | GMP Platform — Equipment Management Module |
| Version | 1.0 |
| Status | Draft |
| Author | GMP Platform Project Team |
| Date | 2026-04-22 |
| Classification | GMP Critical |

---

## 1. Purpose

Define user requirements for equipment lifecycle management, including equipment registry, calibration, qualification, and maintenance controls.

---

## 2. Regulatory Basis

- EU GMP Chapter 3
- EU GMP Annex 11
- 21 CFR Part 211
- 21 CFR Part 11

---

## 3. Functional Requirements

| ID | Requirement |
|---|---|
| URS-004-001 | The system shall maintain unique, immutable equipment identifiers. |
| URS-004-002 | The system shall enforce status transitions with reason capture and audit logging. |
| URS-004-003 | The system shall record calibration events and next due dates. |
| URS-004-004 | The system shall flag overdue calibrations and expose overdue state in APIs/UI. |
| URS-004-005 | The system shall store qualification history for IQ/OQ/PQ-type records. |
| URS-004-006 | The system shall store preventive/corrective maintenance records as immutable entries. |
| URS-004-007 | Calibration due checks shall trigger rule-based notifications. |

---

## 4. Acceptance Criteria

| ID | Test | Expected Result |
|---|---|---|
| URS-004-AC-001 | Create equipment record | Record created with unique ID and audit event. |
| URS-004-AC-002 | Record overdue calibration | Calibration is marked overdue and visible in schedule. |
| URS-004-AC-003 | Run calibration scheduler hook | Rule notification is emitted for overdue/due-soon inventory. |
| URS-004-AC-004 | Attempt invalid status transition | System rejects request with validation error. |

---

## 5. Traceability to Module Features

| Requirement IDs | Feature Mapping |
|---|---|
| URS-004-001,002 | `/api/v1/equipment` + `/api/v1/equipment/{id}/status` |
| URS-004-003,004,007 | `/api/v1/equipment/{id}/calibrations` + calibration due task hook |
| URS-004-005 | `/api/v1/equipment/{id}/qualifications` |
| URS-004-006 | `/api/v1/equipment/{id}/maintenance` |

