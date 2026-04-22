# User Requirement Specification
## URS-005 — Training Management Module

| Field | Value |
|---|---|
| Document Number | URS-005 |
| Title | GMP Platform — Training Management Module |
| Version | 1.0 |
| Status | Draft |
| Author | GMP Platform Project Team |
| Date | 2026-04-22 |
| Classification | GMP Critical |

---

## 1. Purpose

Define user requirements for training curriculum management, assignment tracking, and e-signature-based read-and-understood completion.

---

## 2. Regulatory Basis

- EU GMP Chapter 2
- EU GMP Annex 11
- 21 CFR Part 11
- GAMP 5

---

## 3. Functional Requirements

| ID | Requirement |
|---|---|
| URS-005-001 | The system shall manage curricula and curriculum items as controlled training content. |
| URS-005-002 | The system shall create user-specific training assignments with due dates. |
| URS-005-003 | The system shall expose “my assignments” and assignment status lifecycle (pending/overdue/completed). |
| URS-005-004 | Completion by read-and-understood shall require electronic signature with password re-authentication. |
| URS-005-005 | Completed assignment records shall be immutable and row-locked in the UI. |
| URS-005-006 | Overdue assignment checks shall trigger rule-based notifications. |

---

## 4. Acceptance Criteria

| ID | Test | Expected Result |
|---|---|---|
| URS-005-AC-001 | Create assignment with due date | Assignment is created and appears in assignee list. |
| URS-005-AC-002 | Complete assignment without signature password | System rejects completion. |
| URS-005-AC-003 | Complete assignment with valid read-and-understood e-sign | Assignment status changes to completed and row is locked. |
| URS-005-AC-004 | Run overdue training hook | Overdue status is set and rule notification is emitted. |

---

## 5. Traceability to Module Features

| Requirement IDs | Feature Mapping |
|---|---|
| URS-005-001 | `/api/v1/training/curricula` |
| URS-005-002,003 | `/api/v1/training/assignments`, `/api/v1/training/assignments/my` |
| URS-005-004,005 | `/api/v1/training/assignments/{id}/read-and-understood` + shared `ESignatureModal` |
| URS-005-006 | training overdue task hook + notification rule |

