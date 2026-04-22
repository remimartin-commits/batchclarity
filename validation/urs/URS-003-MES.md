# URS-003 — User Requirements Specification: Manufacturing Execution System (MES)

| Field | Value |
|---|---|
| Document Number | URS-003 |
| Title | User Requirements Specification — Manufacturing Execution System |
| Version | 1.0 |
| Status | Draft |
| Author | GMP Platform Project Team |
| Review Date | 2027-04-01 |
| Classification | GAMP 5 Category 5 — Custom Software |
| Regulatory Basis | EU GMP Annex 11, EU GMP Part II, 21 CFR Part 11, 21 CFR Part 211, ICH Q7 |

---

## 1. Introduction

### 1.1 Purpose

This document specifies the user requirements for the Manufacturing Execution System (MES) module of the GMP Platform. The MES replaces paper-based batch records with a fully electronic system compliant with EU GMP and FDA current Good Manufacturing Practice (cGMP) requirements.

### 1.2 Scope

This URS covers:
- Product master data management
- Master Batch Record (MBR) authoring and approval
- Electronic Batch Record (EBR) creation and execution
- Batch release and rejection workflow
- In-process data capture with ALCOA+ compliance

Out of scope: ERP/SAP integration, materials management, scheduling (future phase).

### 1.3 Critical GMP Requirement

The MES is designated a **GMP-critical system** under ICH Q10. All batch records produced by the system are primary GMP records. The system must enforce:
- No back-filling of step execution times (Contemporaneous requirement)
- No editing of completed step data (Original requirement)
- All data entries attributed to the authenticated operator (Attributable requirement)
- Server-set timestamps only — no client-provided timestamps for audit events

---

## 2. Regulatory and Compliance Requirements

| Regulation | Section | Requirement |
|---|---|---|
| EU GMP Part I | Chapter 4 | Documentation — batch records as primary manufacturing records |
| EU GMP Annex 11 | Clause 7.1 | Data entered at time of activity |
| EU GMP Annex 11 | Clause 9 | Audit trails for GMP-critical data |
| 21 CFR Part 211 | §211.188 | Batch production and control records |
| 21 CFR Part 211 | §211.194 | Laboratory records (in-process testing) |
| 21 CFR Part 211 | §211.192 | Review of completed batch records |
| ICH Q7 | Section 6 | Production and in-process controls |
| ICH Q10 | 3.2.1 | Management of documents and records |

---

## 3. Product Master Data Requirements

| ID | Requirement | Priority |
|---|---|---|
| MES-PROD-001 | The system shall maintain a product master record for each manufactured product | Must |
| MES-PROD-002 | Product records shall include: name, unique code, product type, dosage form, strength | Must |
| MES-PROD-003 | Product records shall have an active/inactive flag; inactive products cannot be used in new MBRs | Must |
| MES-PROD-004 | Product code shall be unique across the system | Must |
| MES-PROD-005 | Product master changes shall be audited | Must |

---

## 4. Master Batch Record (MBR) Requirements

### 4.1 MBR Authoring

| ID | Requirement | Priority |
|---|---|---|
| MES-MBR-001 | The system shall allow creation of Master Batch Records linked to approved products | Must |
| MES-MBR-002 | Each MBR shall have a unique number in the format `MBR-PPPP-VVV` where PPPP is product code and VVV is version | Must |
| MES-MBR-003 | MBRs shall capture: batch size, batch size unit, yield min/max, process steps | Must |
| MES-MBR-004 | MBR steps shall include: step number (sequential), title, detailed instructions, criticality flag, signature requirement flag | Must |
| MES-MBR-005 | Each MBR step shall optionally define expected result / acceptance criteria | Must |
| MES-MBR-006 | MBR versioning shall be enforced; a new version must be created for any change to an approved MBR | Must |
| MES-MBR-007 | Superseded MBR versions shall be retained as read-only historical records | Must |

### 4.2 MBR Approval

| ID | Requirement | Priority |
|---|---|---|
| MES-MBR-010 | MBRs shall require electronic signature approval before use in production | Must |
| MES-MBR-011 | MBR approval shall require the `mes.mbr.approve` permission | Must |
| MES-MBR-012 | Only approved MBRs shall be selectable when creating a new batch record | Must |
| MES-MBR-013 | The approver shall be prevented from approving an MBR they authored (4-eyes principle) | Should |

---

## 5. Electronic Batch Record (EBR) Requirements

### 5.1 Batch Record Creation

| ID | Requirement | Priority |
|---|---|---|
| MES-EBR-001 | The system shall create electronic batch records from approved MBR templates | Must |
| MES-EBR-002 | Batch records shall capture: batch number, selected MBR + version snapshot, actual batch size | Must |
| MES-EBR-003 | Batch number shall be unique; the system shall reject duplicate batch numbers | Must |
| MES-EBR-004 | All MBR steps shall be automatically pre-populated in the batch record at creation | Must |
| MES-EBR-005 | The MBR step instructions shall be frozen at the MBR version used; subsequent MBR changes shall not retroactively modify in-progress batch records | Must |

### 5.2 Step Execution

| ID | Requirement | Priority |
|---|---|---|
| MES-EBR-010 | Operators shall record step results directly in the system at time of execution | Must |
| MES-EBR-011 | Step execution timestamps shall be set server-side in UTC when the result is submitted | Must |
| MES-EBR-012 | **Back-filling of completed steps shall be explicitly prohibited.** Once a step has been marked as performed, the performed_at timestamp and performed_by_id shall be immutable | Must |
| MES-EBR-013 | The system shall record: performed_by (authenticated user), performed_at (server UTC), result_text, result_numeric (where applicable), pass/fail determination | Must |
| MES-EBR-014 | Critical steps (is_critical=True) shall require a pass/fail determination before proceeding | Must |
| MES-EBR-015 | Steps marked requires_signature=True in the MBR shall require an electronic signature with meaning "witnessed" to complete | Must |
| MES-EBR-016 | Failed critical steps shall automatically trigger a deviation record prompt | Should |

### 5.3 Batch Release

| ID | Requirement | Priority |
|---|---|---|
| MES-EBR-020 | Batch record release shall require the `mes.batch.release` permission | Must |
| MES-EBR-021 | Release shall require an electronic signature with meaning "approved" from a QA Manager or Administrator | Must |
| MES-EBR-022 | The release decision shall be one of: released, rejected | Must |
| MES-EBR-023 | Rejection shall require a documented reason | Must |
| MES-EBR-024 | Released batch records shall be read-only; no further modification permitted | Must |
| MES-EBR-025 | Rejected batches shall trigger an automatic deviation record | Should |
| MES-EBR-026 | The batch release date shall be server-set at the time of the release signature | Must |

---

## 6. Data Integrity and Audit Trail

| ID | Requirement | Priority |
|---|---|---|
| MES-AUDIT-001 | All batch record creation, step execution, and release events shall be captured in the immutable audit trail | Must |
| MES-AUDIT-002 | The audit trail shall include: user identity, timestamp (UTC), action, old value, new value for every field change | Must |
| MES-AUDIT-003 | Audit trail entries shall not be deletable or modifiable by any user including administrators | Must |
| MES-AUDIT-004 | The system shall retain batch records and their full audit trails for a minimum of 7 years post-batch release | Must |

---

## 7. Reporting Requirements

| ID | Requirement | Priority |
|---|---|---|
| MES-RPT-001 | Dashboard shall display: batches in progress, batches pending release, recent releases, batch rejection rate | Must |
| MES-RPT-002 | Batch records shall be filterable by product, status, date range, and release decision | Must |
| MES-RPT-003 | A batch record summary printout (PDF) shall be exportable for physical GMP record retention | Should |

---

## 8. Acceptance Criteria

| ID | Test | Expected Result |
|---|---|---|
| MES-AC-001 | Create batch record from unapproved MBR | System rejects with 400 |
| MES-AC-002 | Execute step; check performed_at | Timestamp is server UTC; client cannot specify time |
| MES-AC-003 | Re-submit completed step | System rejects with "Back-filling not permitted" |
| MES-AC-004 | Release batch without e-signature | System rejects with 401/403 |
| MES-AC-005 | Reject batch; verify reason captured | Reject reason stored; audit event created |
| MES-AC-006 | Attempt to edit released batch | System returns 400/403 |
| MES-AC-007 | Approve MBR; create batch; verify step count matches | EBR steps = MBR steps in same order |
| MES-AC-008 | Create batch with duplicate batch number | System returns 400 with unique constraint error |

---

## 9. Revision History

| Version | Date | Author | Summary |
|---|---|---|---|
| 1.0 | 2026-04-20 | GMP Platform Project Team | Initial draft |
