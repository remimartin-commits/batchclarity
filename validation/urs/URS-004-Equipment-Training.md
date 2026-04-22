# URS-004 — User Requirements Specification: Equipment Management and Training

| Field | Value |
|---|---|
| Document Number | URS-004 |
| Title | User Requirements Specification — Equipment Management and Training |
| Version | 1.0 |
| Status | Draft |
| Author | GMP Platform Project Team |
| Review Date | 2027-04-01 |
| Classification | GAMP 5 Category 5 — Custom Software |
| Regulatory Basis | EU GMP Annex 11, EU GMP Chapter 3 (Premises & Equipment), EU GMP Chapter 2 (Personnel), 21 CFR Part 211, ISPE GAMP 5 |

---

## 1. Introduction

### 1.1 Purpose

This document specifies user requirements for two closely related GMP Platform modules:

1. **Equipment Management** — tracking equipment status, calibration, qualification (IQ/OQ/PQ), and preventive maintenance
2. **Training Management** — managing training curricula, assignments, competency records, and read-and-understood attestations

Both modules generate primary GMP records that must comply with EU GMP Annex 11 and the 21 CFR Part 11 electronic records/signatures requirements.

### 1.2 Scope

**Equipment Management:**
- Equipment registry
- Calibration management (scheduling, recording, certificate management)
- Qualification management (IQ/OQ/PQ/DQ/PV)
- Preventive and corrective maintenance recording
- Equipment status lifecycle

**Training Management:**
- Training curricula definition
- Assignment and scheduling
- Completion recording with e-signature read-and-understood
- Training matrix and competency reporting

---

## 2. Equipment Management Requirements

### 2.1 Equipment Registry

| ID | Requirement | Priority |
|---|---|---|
| EQ-REG-001 | The system shall maintain a central equipment registry for all GMP-relevant equipment | Must |
| EQ-REG-002 | Each equipment record shall include: unique equipment number, name, type, manufacturer, model, serial number, location, GMP criticality | Must |
| EQ-REG-003 | Equipment number shall be system-generated, unique, and immutable once assigned | Must |
| EQ-REG-004 | Equipment type shall be selectable from: instrument, process_equipment, utility, computer_system, facility | Must |
| EQ-REG-005 | Equipment records shall track site assignment | Must |
| EQ-REG-006 | Equipment status shall be one of: active, inactive, under_maintenance, out_of_service, calibration_overdue, quarantine | Must |
| EQ-REG-007 | Status changes shall require a reason and shall be audited | Must |
| EQ-REG-008 | Equipment records shall never be deleted; decommissioned equipment shall be marked inactive | Must |

### 2.2 Calibration Management

| ID | Requirement | Priority |
|---|---|---|
| EQ-CAL-001 | Each equipment record shall track whether calibration is required (calibration_required flag) | Must |
| EQ-CAL-002 | Calibration intervals shall be defined in months per equipment type | Must |
| EQ-CAL-003 | The system shall track calibration due date; status shall automatically flag as calibration_overdue when past due | Must |
| EQ-CAL-004 | Calibration records shall capture: calibration number (`CAL-YYYY-NNNN`), calibration date, next due date, performed by, external provider, result, certificate number, pass/fail | Must |
| EQ-CAL-005 | Calibration results shall be one of: as_found_in_tolerance, as_found_out_of_tolerance, adjusted_in_tolerance, failed | Must |
| EQ-CAL-006 | Out-of-tolerance calibrations shall automatically trigger a deviation record prompt | Must |
| EQ-CAL-007 | Calibration certificates shall be referenceable by number; file attachment shall be supported | Should |
| EQ-CAL-008 | The system shall notify equipment managers 30 days before calibration due date | Must |
| EQ-CAL-009 | Calibration history shall be retained indefinitely and be fully auditable | Must |

### 2.3 Qualification Management (IQ/OQ/PQ/DQ/PV)

| ID | Requirement | Priority |
|---|---|---|
| EQ-QUAL-001 | The system shall support recording of all qualification lifecycle stages: DQ, IQ, OQ, PQ, PV | Must |
| EQ-QUAL-002 | Qualification records shall include: qualification number, type, protocol reference, status, start date, completion date, approval date, approved by | Must |
| EQ-QUAL-003 | Qualification number format: `{TYPE}-YYYY-NNNN` (e.g. IQ-2026-0001) | Must |
| EQ-QUAL-004 | Qualification approval shall require an electronic signature with meaning "approved" | Must |
| EQ-QUAL-005 | Equipment qualification status shall reflect the most recent qualification result | Must |
| EQ-QUAL-006 | Requalification due dates shall be tracked and notified | Should |
| EQ-QUAL-007 | Qualification records shall be linked to validation documentation (protocol reference) | Must |

### 2.4 Preventive Maintenance

| ID | Requirement | Priority |
|---|---|---|
| EQ-MAINT-001 | The system shall record preventive and corrective maintenance activities | Must |
| EQ-MAINT-002 | Maintenance records shall include: maintenance number (`MAINT-YYYY-NNNN`), type, date performed, performed by, description, parts replaced, next due date | Must |
| EQ-MAINT-003 | Maintenance records shall be immutable once submitted | Must |
| EQ-MAINT-004 | Equipment placed under_maintenance status shall not appear as available in batch records | Should |

---

## 3. Training Management Requirements

### 3.1 Training Curricula

| ID | Requirement | Priority |
|---|---|---|
| TR-CUR-001 | The system shall support definition of training curricula as collections of training items | Must |
| TR-CUR-002 | Each curriculum shall have a unique code, name, description, and target roles list | Must |
| TR-CUR-003 | Curricula shall be flagged as mandatory or optional | Must |
| TR-CUR-004 | Retraining intervals shall be configurable per curriculum in months | Must |
| TR-CUR-005 | Curriculum items shall reference controlled documents (by document number) or describe standalone training content | Must |
| TR-CUR-006 | Curricula shall have active/inactive status; inactive curricula cannot be assigned | Must |

### 3.2 Training Assignment

| ID | Requirement | Priority |
|---|---|---|
| TR-ASGN-001 | Training coordinators shall be able to assign curricula to individual users or user groups | Must |
| TR-ASGN-002 | Assignments shall capture: curriculum, assignee, due date, assigned by (authenticated user, server-set) | Must |
| TR-ASGN-003 | Mandatory curricula shall support auto-assignment to all users with matching roles | Should |
| TR-ASGN-004 | The system shall send email notification to assignees when a new training is assigned | Must |
| TR-ASGN-005 | The system shall send reminder notifications 7 days before the assignment due date | Must |
| TR-ASGN-006 | Overdue training assignments (past due date, not completed) shall trigger escalation notifications | Must |

### 3.3 Training Completion and Read-and-Understood

| ID | Requirement | Priority |
|---|---|---|
| TR-COMP-001 | Training completion shall be recordable by the assignee or a training coordinator | Must |
| TR-COMP-002 | Completion records shall capture: method (classroom, e-learning, on_the_job, read_and_understood), date, score (where applicable), pass/fail | Must |
| TR-COMP-003 | The completion timestamp shall be server-set in UTC; no client-provided timestamps | Must |
| TR-COMP-004 | **Read-and-Understood attestation shall require an electronic signature with meaning "acknowledged"** from the assignee | Must |
| TR-COMP-005 | The electronic signature for R&U shall bind the user identity, document version, and timestamp cryptographically | Must |
| TR-COMP-006 | Once a training is completed with e-signature, the completion record shall be immutable | Must |
| TR-COMP-007 | The system shall track score thresholds; assignments with score below passing threshold shall remain in "failed" status | Should |

### 3.4 Training Records and Reporting

| ID | Requirement | Priority |
|---|---|---|
| TR-RPT-001 | A training matrix shall be available showing: employees vs. curricula, with completion status | Must |
| TR-RPT-002 | The system shall flag users whose mandatory training is overdue and restrict their authorisation in other modules | Should |
| TR-RPT-003 | Training records shall be retained for the duration of employment plus 7 years | Must |
| TR-RPT-004 | Dashboard shall show: overdue training count, expiring-soon count, compliance % by department | Must |

---

## 4. Cross-Module Integration Requirements

| ID | Requirement | Priority |
|---|---|---|
| CROSS-001 | Equipment calibration overdue status shall be visible in the batch record module; operators should see a warning when selecting overdue equipment | Should |
| CROSS-002 | Operators with overdue mandatory training shall receive a warning when attempting to execute batch record steps | Should |
| CROSS-003 | Qualification records shall be linkable to change control records that triggered requalification | Should |
| CROSS-004 | Document revision in Document Control shall auto-trigger re-assignment of Read-and-Understood for linked curricula | Could |

---

## 5. Acceptance Criteria

### Equipment

| ID | Test | Expected Result |
|---|---|---|
| EQ-AC-001 | Register equipment without name | System rejects with validation error |
| EQ-AC-002 | Record out-of-tolerance calibration | System prompts deviation creation; status set to calibration_overdue |
| EQ-AC-003 | Approve qualification without e-signature | System rejects with 401/403 |
| EQ-AC-004 | Query equipment with calibration_due < today | Returns equipment list with overdue flag |
| EQ-AC-005 | Attempt to delete equipment record | System returns 405 (method not allowed) |

### Training

| ID | Test | Expected Result |
|---|---|---|
| TR-AC-001 | Complete R&U training without e-signature | System rejects; signature required |
| TR-AC-002 | Complete R&U with wrong password | System returns 401; completion not recorded |
| TR-AC-003 | Complete R&U successfully | Completion record created with signature_id; timestamp is server UTC |
| TR-AC-004 | Attempt to modify completed R&U record | System returns 400/403 |
| TR-AC-005 | Assign curriculum to user; check notification | Email notification dispatched to assignee |
| TR-AC-006 | Run training matrix report | Returns grid of user vs. curriculum completion status |

---

## 6. Revision History

| Version | Date | Author | Summary |
|---|---|---|---|
| 1.0 | 2026-04-20 | GMP Platform Project Team | Initial draft |
