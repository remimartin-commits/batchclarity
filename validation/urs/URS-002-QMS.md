# URS-002 — User Requirements Specification: Quality Management System (QMS)

| Field | Value |
|---|---|
| Document Number | URS-002 |
| Title | User Requirements Specification — Quality Management System |
| Version | 1.0 |
| Status | Draft |
| Author | GMP Platform Project Team |
| Review Date | 2027-04-01 |
| Classification | GAMP 5 Category 5 — Custom Software |
| Regulatory Basis | ICH Q10, EU GMP Annex 11, 21 CFR Part 11, ISO 9001 |

---

## 1. Introduction

### 1.1 Purpose

This document specifies the user requirements for the Quality Management System (QMS) module of the GMP Platform. It defines what the system shall do to support corrective and preventive actions (CAPAs), deviation management, and change control in compliance with ICH Q10 pharmaceutical quality systems.

### 1.2 Scope

This URS covers the following QMS sub-modules:
- CAPA Management (corrective and preventive actions)
- Deviation Management
- Change Control

Out of scope: supplier qualification, product complaints (future URS), and audit management (future URS).

### 1.3 Relationship to Other URSs

| URS | Module |
|---|---|
| URS-001 | GMP Platform Foundation (authentication, audit trail, e-signatures, workflow) |
| URS-002 | This document — Quality Management System |
| URS-003 | Manufacturing Execution System (MES) |
| URS-004 | Equipment Management and Training |
| URS-005 | LIMS and Environmental Monitoring |

---

## 2. Regulatory and Compliance Requirements

### 2.1 Applicable Regulations

| Regulation | Section | Requirement |
|---|---|---|
| EU GMP Annex 11 | Clause 9 | Audit trails for GMP-relevant data |
| EU GMP Annex 11 | Clause 12 | Electronic signatures for record approval |
| ICH Q10 | 3.2.2 | CAPA system as pharmaceutical quality system element |
| 21 CFR Part 11 | 11.10(e) | Audit trails capturing date, time, operator, change |
| 21 CFR Part 211 | 211.192 | Investigation of any unexplained discrepancy |
| ISO 9001:2015 | Clause 10.2 | Nonconformity and corrective action requirements |

### 2.2 Data Integrity Requirements (ALCOA+)

All QMS records shall be:

- **Attributable** — linked to the authenticated user who created or modified the record
- **Legible** — stored as structured data, human-readable at all times
- **Contemporaneous** — timestamps set server-side in UTC; no client-provided timestamps for audit events
- **Original** — original entries never deleted or overwritten; corrections create new audit entries
- **Accurate** — validated against business rules before acceptance
- **Complete** — all mandatory fields enforced; no partial saves without flagging
- **Consistent** — status transitions enforced by workflow engine; no direct status field writes
- **Enduring** — records retained per retention schedule; no hard deletes on GMP records
- **Available** — records retrievable within 3 seconds for standard queries

---

## 3. CAPA Management Requirements

### 3.1 CAPA Record Creation

| ID | Requirement | Priority |
|---|---|---|
| QMS-CAPA-001 | The system shall allow authenticated users with `qms.capa.create` permission to create new CAPA records | Must |
| QMS-CAPA-002 | Each CAPA shall be assigned a unique system-generated number in the format `CAPA-YYYY-NNNN` | Must |
| QMS-CAPA-003 | CAPA creation shall require: title, description, source type, risk level, and owner | Must |
| QMS-CAPA-004 | Risk level shall be one of: low, minor, major, critical | Must |
| QMS-CAPA-005 | Source type shall indicate the originating event: deviation, audit, complaint, self-inspection, trend, other | Must |
| QMS-CAPA-006 | The system shall allow linking a CAPA to a source record (e.g. a specific deviation ID) | Should |
| QMS-CAPA-007 | A due date shall be assignable at creation and modifiable until the CAPA is approved | Must |
| QMS-CAPA-008 | CAPA records shall support one or more action items with assigned owners and due dates | Must |

### 3.2 CAPA Lifecycle and Workflow

| ID | Requirement | Priority |
|---|---|---|
| QMS-CAPA-010 | CAPAs shall follow the configurable workflow: Draft → Under Review → Approved → WIP → Effectiveness Check → Closed | Must |
| QMS-CAPA-011 | Status transitions shall be enforced by the workflow engine; direct status field edits shall be rejected | Must |
| QMS-CAPA-012 | Transition from Under Review to Approved shall require an electronic signature with meaning "approved" | Must |
| QMS-CAPA-013 | Closure shall require an electronic signature with meaning "approved" from a QA Manager or Administrator | Must |
| QMS-CAPA-014 | The system shall enforce a 5-business-day approval SLA for CAPA action plans; overdue CAPAs shall be flagged and notified | Should |
| QMS-CAPA-015 | Cancelled and closed CAPAs shall be read-only; no further modifications permitted | Must |
| QMS-CAPA-016 | The system shall record the reason for any rejection or return-to-draft transition | Must |

### 3.3 CAPA Action Item Management

| ID | Requirement | Priority |
|---|---|---|
| QMS-CAPA-020 | Each action item shall have: description, assigned owner, due date, status | Must |
| QMS-CAPA-021 | Action items shall be individually completable with server-set completion timestamps | Must |
| QMS-CAPA-022 | The system shall support freezing action items (is_frozen flag) once the CAPA is approved, with a recorded freeze reason | Must |
| QMS-CAPA-023 | Frozen action items shall not be editable except by users with the `qms.capa.approve` permission | Must |

### 3.4 CAPA Effectiveness Verification

| ID | Requirement | Priority |
|---|---|---|
| QMS-CAPA-030 | CAPAs shall include an effectiveness criteria field populated before approval | Should |
| QMS-CAPA-031 | The system shall support an effectiveness check date, triggering a notification when due | Should |
| QMS-CAPA-032 | Closing a CAPA shall require documentation of effectiveness verification outcome | Should |

### 3.5 CAPA Audit Trail

| ID | Requirement | Priority |
|---|---|---|
| QMS-CAPA-040 | All creates, updates, status changes, and signature events on CAPA records shall be captured in the immutable audit trail | Must |
| QMS-CAPA-041 | Field-level changes shall record old value, new value, timestamp, and user identity | Must |
| QMS-CAPA-042 | The audit trail for a CAPA shall be viewable to authorised users from the CAPA detail screen | Must |

---

## 4. Deviation Management Requirements

### 4.1 Deviation Record Creation

| ID | Requirement | Priority |
|---|---|---|
| QMS-DEV-001 | The system shall allow authenticated users with `qms.deviation.create` to report new deviations | Must |
| QMS-DEV-002 | Each deviation shall be assigned a unique number in the format `DEV-YYYY-NNNN` | Must |
| QMS-DEV-003 | Deviation creation shall require: title, description, severity, detection date | Must |
| QMS-DEV-004 | Severity shall be one of: minor, major, critical | Must |
| QMS-DEV-005 | The system shall capture: detected by (server-resolved to authenticated user), detection date, detection location | Must |
| QMS-DEV-006 | Immediate containment actions shall be recordable at creation | Must |

### 4.2 Deviation Lifecycle

| ID | Requirement | Priority |
|---|---|---|
| QMS-DEV-010 | Deviations shall follow the workflow: Open → Under Investigation → Pending Review → Closed | Must |
| QMS-DEV-011 | Closure shall require an electronic signature from a QA Manager or Administrator | Must |
| QMS-DEV-012 | The system shall support linking a deviation to one or more CAPAs | Must |
| QMS-DEV-013 | Root cause shall be documented before submission for review | Should |

### 4.3 Deviation Reporting

| ID | Requirement | Priority |
|---|---|---|
| QMS-DEV-020 | The system shall provide list view of deviations filterable by status and severity | Must |
| QMS-DEV-021 | Deviations shall be reportable by product, batch, process area, and time period | Should |
| QMS-DEV-022 | Trend analysis across deviations shall be supported (frequency by severity and type over time) | Could |

---

## 5. Change Control Requirements

### 5.1 Change Control Record Creation

| ID | Requirement | Priority |
|---|---|---|
| QMS-CC-001 | The system shall allow users with `qms.change_control.create` to initiate change control records | Must |
| QMS-CC-002 | Each change control shall have a unique number in the format `CC-YYYY-NNNN` | Must |
| QMS-CC-003 | Change records shall capture: title, description, change type, change category, regulatory impact flag, validation required flag | Must |
| QMS-CC-004 | Change type shall include: process, equipment, material, computer_system, facility, supplier, document, other | Must |
| QMS-CC-005 | Change category shall be one of: minor, major, critical | Must |
| QMS-CC-006 | Regulatory impact assessment shall be mandatory for major and critical changes | Must |

### 5.2 Change Control Lifecycle

| ID | Requirement | Priority |
|---|---|---|
| QMS-CC-010 | Change controls shall follow the workflow: Draft → Pending Approval → Approved → Implementation → Closed | Must |
| QMS-CC-011 | Approval shall require an electronic signature with meaning "approved" from a QA Manager | Must |
| QMS-CC-012 | Rejected change controls shall be read-only with reason captured | Must |
| QMS-CC-013 | Where validation_required=True, the system shall enforce linkage to a validation record before closure | Could |
| QMS-CC-014 | Implementation date shall be recorded; changes to implementation date shall be audited | Must |

---

## 6. Notification Requirements

| ID | Requirement | Priority |
|---|---|---|
| QMS-NOTIF-001 | The system shall send email notification to the CAPA owner and QA team when a new CAPA is created | Must |
| QMS-NOTIF-002 | Overdue CAPAs (past due date, not closed) shall trigger daily escalation emails | Must |
| QMS-NOTIF-003 | CAPA approval shall trigger notification to the CAPA owner | Must |
| QMS-NOTIF-004 | New deviations shall trigger email to the QA team | Must |

---

## 7. Reporting and Search Requirements

| ID | Requirement | Priority |
|---|---|---|
| QMS-RPT-001 | The system shall provide paginated list views of all QMS record types with a default limit of 50 records | Must |
| QMS-RPT-002 | Lists shall support filtering by status, risk level, date range, and owner | Must |
| QMS-RPT-003 | Dashboard KPIs shall include: open CAPAs by risk level, overdue CAPAs, open deviations by severity, pending change controls | Must |
| QMS-RPT-004 | Export to CSV/Excel shall be supported for CAPA, deviation, and change control lists | Should |

---

## 8. Acceptance Criteria

| ID | Test | Expected Result |
|---|---|---|
| QMS-AC-001 | Create CAPA without required fields | System rejects with field-level validation errors |
| QMS-AC-002 | Approve CAPA without e-signature | System rejects; 401/403 returned |
| QMS-AC-003 | Attempt to modify a closed CAPA | System returns 400/403 |
| QMS-AC-004 | Create CAPA with source_type=deviation | Record created; linked deviation ID stored |
| QMS-AC-005 | Submit CAPA for review | Status transitions to under_review; audit event created |
| QMS-AC-006 | Sign CAPA with wrong password | System returns 401; signature not applied |
| QMS-AC-007 | List CAPAs with status_filter=approved | Returns only approved CAPAs |
| QMS-AC-008 | Create deviation and verify audit trail | AuditEvent record created with action=CREATE |
| QMS-AC-009 | Approve change control | Status transitions to Approved; e-signature record created |
| QMS-AC-010 | Verify CAPA number format | Format matches CAPA-YYYY-NNNN pattern |

---

## 9. Revision History

| Version | Date | Author | Summary |
|---|---|---|---|
| 1.0 | 2026-04-20 | GMP Platform Project Team | Initial draft |
