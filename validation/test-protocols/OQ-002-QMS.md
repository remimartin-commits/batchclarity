# OQ-002 Operational Qualification — QMS Module

---

| Field | Value |
|---|---|
| Document ID | OQ-002 |
| Title | Operational Qualification — Quality Management System (QMS) Module |
| Version | 01 |
| Status | DRAFT |
| Date | 2026-04-21 |
| System | GMP Platform |
| Module | QMS (CAPA, Deviation, Change Control, Supplier Management, Risk Management) |
| Author | [Author Name] |
| Reviewer | [Reviewer Name] |
| Approver | [Approver Name] |

---

## Table of Contents

1. Purpose and Scope
2. References
3. Definitions and Abbreviations
4. Prerequisites
5. Test Cases
6. Acceptance Criteria
7. Deviation Handling
8. Signature Page

---

## 1. Purpose and Scope

### 1.1 Purpose

This Operational Qualification (OQ) protocol establishes documented evidence that the GMP Platform Quality Management System (QMS) Module operates consistently and as intended throughout anticipated operating ranges. This protocol verifies the functional behaviour of the following sub-modules: Corrective and Preventive Actions (CAPA), Deviations, Change Control, Supplier Management, and Risk Management.

Execution of this protocol demonstrates that QMS data entry, workflow routing, business rule enforcement, access controls, audit trail capture, and notifications function correctly and in compliance with applicable regulatory requirements.

### 1.2 Scope

This OQ covers the following QMS Module components:

| Sub-Module | Key Functions Under Test |
|---|---|
| CAPA | Record creation, workflow (Draft → Closed), overdue notifications, effectiveness check, access control |
| Deviation | Creation, classification (minor/major/critical), linkage to CAPA, audit trail |
| Change Control | Risk assessment mandatory fields, approval date logic, document linkage |
| Supplier Management | Supplier approval status rules, audit record dependency |
| Risk Management | RPN calculation, approval signature requirement, mandatory CAPA linkage for high RPN |
| Cross-Module Audit Trail | Field-level change capture across all QMS record types |

**Out of Scope:** Foundation Layer (authentication, RBAC, core audit trail) is covered in OQ-001. MES, LIMS, Equipment, Training, and Environmental Monitoring modules are covered in separate OQ protocols.

### 1.3 Regulatory Basis

- 21 CFR Part 11 — Electronic Records; Electronic Signatures (FDA)
- 21 CFR Part 820 — Quality System Regulation (FDA)
- EU GMP Annex 11 — Computerised Systems
- EU GMP Annex 15 — Qualification and Validation
- ICH Q9 — Quality Risk Management
- ISO 9001:2015 — Quality Management Systems Requirements
- GAMP 5 — A Risk-Based Approach to Compliant GxP Computerised Systems

---

## 2. References

| Reference ID | Document Title |
|---|---|
| URS-002 | User Requirements Specification — QMS Module |
| IQ-001 | Installation Qualification — Foundation Layer (prerequisite) |
| OQ-001 | Operational Qualification — Foundation Layer (prerequisite) |
| SDD-002 | System Design Description — QMS Module |
| RA-002 | Risk Assessment — QMS Module |
| GMP-PLT-QMP-001 | Quality Management Plan — GMP Platform |
| 21 CFR Part 11 | Electronic Records; Electronic Signatures |
| 21 CFR Part 820 | Quality System Regulation |
| EU GMP Annex 11 | Computerised Systems (EMA, 2011) |
| ICH Q9 | Quality Risk Management |
| GAMP 5 | A Risk-Based Approach to Compliant GxP Computerised Systems (ISPE, 2022) |

---

## 3. Definitions and Abbreviations

| Term / Abbreviation | Definition |
|---|---|
| CAPA | Corrective and Preventive Action |
| CC | Change Control |
| CFR | Code of Federal Regulations |
| E-signature | Electronic signature as defined by 21 CFR Part 11 |
| GAMP | Good Automated Manufacturing Practice |
| GMP | Good Manufacturing Practice |
| OOS | Out of Specification |
| OQ | Operational Qualification |
| QMS | Quality Management System |
| RBAC | Role-Based Access Control |
| RPN | Risk Priority Number (Probability × Severity × Detectability) |
| SOP | Standard Operating Procedure |
| URS | User Requirements Specification |

---

## 4. Prerequisites

All prerequisites must be verified before execution begins. Do not proceed if any prerequisite is unmet.

| Prereq ID | Prerequisite | Verified By | Date | Initials |
|---|---|---|---|---|
| PRE-001 | OQ-001 (Foundation Layer OQ) has been successfully executed and approved. All OQ-001 test cases passed. | | | |
| PRE-002 | IQ-001 approved and all IQ deviations closed or formally risk-accepted | | | |
| PRE-003 | Test environment is isolated from the production system and contains only test data | | | |
| PRE-004 | The following test user accounts have been created with the roles specified in Appendix A: QA Manager, QA Reviewer, Operator, Supplier Quality Manager, Risk Manager | | | |
| PRE-005 | At least one test Supplier record exists in the system with status "Pending" | | | |
| PRE-006 | At least one test Risk Assessment record exists in DRAFT status | | | |
| PRE-007 | Tester(s) have read this protocol in full and are trained on GMP documentation practices | | | |
| PRE-008 | The system version under test matches the approved IQ version | | | |
| PRE-009 | Direct database access is available for result verification | | | |
| PRE-010 | The notification (email) test server (e.g., Mailhog) is running and accessible | | | |

**System Version Under Test:** ___________________________

**Test Environment URL:** ___________________________

**Prerequisites Verified By:** ___________________________ Date: _______________

---

## 5. Test Cases

### Instructions for Execution

1. Execute test cases in the listed order unless a specific dependency is noted.
2. All results must be recorded contemporaneously during execution.
3. Any deviation from expected results must be documented immediately and handled per Section 7.
4. "Actual Result" must be a genuine description of what occurred.
5. Database queries must be pasted verbatim as executed, and results must be recorded.

---

### TC-OQ-QMS-001: CAPA Creation with All Required Fields

| Field | Detail |
|---|---|
| Test Case ID | TC-OQ-QMS-001 |
| Test Objective | Verify that a CAPA record can be created with all mandatory fields and that the system validates the presence of all required fields, rejecting submissions with missing mandatory data |
| URS Reference | URS-002-CAPA-001 |
| Risk Level | High |
| Prerequisites | User with `capa:create` permission is authenticated |

**Test Steps:**

| Step | Action | Expected Result |
|---|---|---|
| 1 | Attempt to create a CAPA with the title field empty: POST `/api/v1/qms/capas` with body omitting the `title` field | HTTP 422 Unprocessable Entity. Error: `{"detail": [{"loc": ["body", "title"], "msg": "field required"}]}` |
| 2 | Attempt to create a CAPA with the `root_cause_category` field empty | HTTP 422. Field-level validation error for root_cause_category |
| 3 | Attempt to create a CAPA with the `due_date` field missing | HTTP 422. Field-level validation error for due_date |
| 4 | Create a CAPA with all mandatory fields populated: title, description, root_cause_category, due_date, priority, assigned_to_user_id | HTTP 201 Created. CAPA record returned with a system-generated CAPA number (e.g., "CAPA-2026-0001"), UUID, and status = DRAFT |
| 5 | Verify the CAPA number follows the defined numbering convention | CAPA number format matches the configured pattern (e.g., CAPA-YYYY-NNNN) |
| 6 | Query the database: `SELECT * FROM capas WHERE id = '[new_capa_uuid]'` | All mandatory fields are populated. created_at isa UTC timestamp. created_by_user_id matches the authenticated user. |
| 7 | Verify an audit log RECORD_CREATE event was generated | Audit event of type RECORD_CREATE exists for this CAPA UUID |

**Expected Result:** CAPA creation fails with meaningful field-level errors when mandatory fields are absent. When all fields are present, a CAPA is created in DRAFT status with a system-generated number. An audit log entry is created.

**Actual Result:**

_______________________________________________________________________________

_______________________________________________________________________________

**Pass / Fail:** ________ **Tester:** ___________________________ **Date:** _______________

**Comments:**

_______________________________________________________________________________

---

### TC-OQ-QMS-002: CAPA Workflow — Full Lifecycle (Draft → In Review → Approved → WIP → Effectiveness Check → Closed)

| Field | Detail |
|---|---|
| Test Case ID | TC-OQ-QMS-002 |
| Test Objective | Verify that a CAPA can progress through all defined workflow states in the correct sequence, and that each state transition is recorded and audited |
| URS Reference | URS-002-CAPA-002 |
| Risk Level | High |
| Prerequisites | A CAPA record (CAPA-OQ-002-TC002) exists in DRAFT status. Users with appropriate roles for each transition are available: QA Reviewer (capa:review), QA Approver (capa:approve), Operator (capa:implement), QA Manager (capa:close) |

**Test Steps:**

| Step | Action | Expected Result |
|---|---|---|
| 1 | Transition the CAPA from DRAFT to IN_REVIEW: POST transition with target_state = IN_REVIEW as the assigned user | HTTP 200 OK. CAPA status = IN_REVIEW. Audit event RECORD_UPDATE with old_status = DRAFT, new_status = IN_REVIEW. |
| 2 | Transition the CAPA from IN_REVIEW to APPROVED: provide valid e-signature as QA Reviewer | HTTP 200 OK. CAPA status = APPROVED. E-signature record created with meaning = "Reviewed and Approved". |
| 3 | Transition the CAPA from APPROVED to WORK_IN_PROGRESS (WIP): as the assigned implementer | HTTP 200 OK. CAPA status = WORK_IN_PROGRESS |
| 4 | Transition the CAPA from WIP to EFFECTIVENESS_CHECK: as the implementer, providing completion evidence | HTTP 200 OK. CAPA status = EFFECTIVENESS_CHECK. Effectiveness check due date is automatically populated (verify it is [closure_date + configured days] from closure). |
| 5 | Transition from EFFECTIVENESS_CHECK to CLOSED: as QA Manager, providing e-signature and effectiveness outcome | HTTP 200 OK. CAPA status = CLOSED. E-signature present with meaning = "Effectiveness Verified and Closed". |
| 6 | Query the full state history: `SELECT status, changed_at, changed_by_user_id FROM capa_state_history WHERE capa_id = '[capa_uuid]' ORDER BY changed_at ASC` | Six state change records are returned in order: DRAFT, IN_REVIEW, APPROVED, WORK_IN_PROGRESS, EFFECTIVENESS_CHECK, CLOSED |
| 7 | Verify the CAPA cannot be re-opened or further transitioned once CLOSED | POST transition with any target_state from CLOSED returns HTTP 422 |

**Expected Result:** The CAPA progresses through all six states. Each transition is logged with actor and timestamp. The closed state is terminal. E-signatures are captured at approval and closure.

**Actual Result:**

_______________________________________________________________________________

_______________________________________________________________________________

**Pass / Fail:** ________ **Tester:** ___________________________ **Date:** _______________

**Comments:**

_______________________________________________________________________________

---

### TC-OQ-QMS-003: CAPA Cannot Skip Workflow States

| Field | Detail |
|---|---|
| Test Case ID | TC-OQ-QMS-003 |
| Test Objective | Verify that the CAPA workflow engine prevents state-skipping — a CAPA in DRAFT cannot jump directly to CLOSED, APPROVED, or EFFECTIVENESS_CHECK |
| URS Reference | URS-002-CAPA-003 |
| Risk Level | High |
| Prerequisites | A new CAPA record exists in DRAFT status |

**Test Steps:**

| Step | Action | Expected Result |
|---|---|---|
| 1 | Attempt to transition a DRAFT CAPA directly to APPROVED | HTTP 422 returned. Error: invalid transition DRAFT → APPROVED |
| 2 | Attempt to transition a DRAFT CAPA directly to WORK_IN_PROGRESS | HTTP 422 returned. Error: invalid transition DRAFT → WORK_IN_PROGRESS |
| 3 | Attempt to transition a DRAFT CAPA directly to EFFECTIVENESS_CHECK | HTTP 422 returned |
| 4 | Attempt to transition a DRAFT CAPA directly to CLOSED | HTTP 422 returned |
| 5 | Attempt to transition a DRAFT CAPA directly to IN_REVIEW | HTTP 200 OK — this is the only valid transition from DRAFT |
| 6 | Verify CAPA remains in DRAFT after all failed attempts (except step 5) | Status is IN_REVIEW only after step 5; all prior attempts left the CAPA in DRAFT |

**Expected Result:** All invalid direct transitions from DRAFT are rejected with HTTP 422. Only DRAFT → IN_REVIEW is accepted.

**Actual Result:**

_______________________________________________________________________________

_______________________________________________________________________________

**Pass / Fail:** ________ **Tester:** ___________________________ **Date:** _______________

**Comments:**

_______________________________________________________________________________

---

### TC-OQ-QMS-004: Overdue CAPA Notification Sent

| Field | Detail |
|---|---|
| Test Case ID | TC-OQ-QMS-004 |
| Test Objective | Verify that when a CAPA's due date passes and the CAPA has not been closed, the assigned user and their manager receive an overdue notification |
| URS Reference | URS-002-CAPA-004 |
| Risk Level | Medium |
| Prerequisites | A CAPA record exists with due_date set to yesterday (i.e., the CAPA is overdue). The assigned user is `assignee.oq004@gmpplatform.local`. The scheduled notification job has run (or can be triggered manually for testing). |

**Test Steps:**

| Step | Action | Expected Result |
|---|---|---|
| 1 | Confirm the CAPA's due_date is in the past: `SELECT due_date, status FROM capas WHERE id = '[capa_uuid]'` | due_date < CURRENT_DATE, status ≠ CLOSED |
| 2 | Trigger the overdue notification job (or confirm it has run on schedule) | Job executes without error |
| 3 | Check in-app notifications for the assigned user | A notification of type CAPA_OVERDUE is present for this CAPA |
| 4 | Check the test email inbox for the assigned user | An email is received with subject "CAPA Overdue: [CAPA-XXXX]". Body includes CAPA ID, title, and due date. |
| 5 | Query the notifications table: `SELECT * FROM notifications WHERE record_id = '[capa_uuid]' AND type = 'CAPA_OVERDUE'` | At least one CAPA_OVERDUE notification record exists |
| 6 | Verify the CAPA is not automatically closed or modified by the notification job | CAPA status is unchanged |

**Expected Result:** The overdue notification job sends an in-app notification and email to the assigned user. The CAPA record is not modified by the notification process.

**Actual Result:**

_______________________________________________________________________________

_______________________________________________________________________________

**Pass / Fail:** ________ **Tester:** ___________________________ **Date:** _______________

**Comments:**

_______________________________________________________________________________

---

### TC-OQ-QMS-005: Deviation Creation and Classification (Minor / Major / Critical)

| Field | Detail |
|---|---|
| Test Case ID | TC-OQ-QMS-005 |
| Test Objective | Verify that a Deviation record can be created and classified with the correct severity classification (Minor, Major, or Critical) and that the classification is stored correctly |
| URS Reference | URS-002-DEV-001 |
| Risk Level | High |
| Prerequisites | User with `deviation:create` permission is authenticated |

**Test Steps:**

| Step | Action | Expected Result |
|---|---|---|
| 1 | Create a Deviation record with classification = MINOR | HTTP 201 Created. Deviation record returned with classification = MINOR and a system-generated deviation number (e.g., DEV-2026-0001) |
| 2 | Create a Deviation record with classification = MAJOR | HTTP 201 Created. Deviation record with classification = MAJOR |
| 3 | Create a Deviation record with classification = CRITICAL | HTTP 201 Created. Deviation record with classification = CRITICAL |
| 4 | Attempt to create a Deviation with an invalid classification value (e.g., "SEVERE") | HTTP 422 Unprocessable Entity. Error indicates the value must be one of: MINOR, MAJOR, CRITICAL |
| 5 | Verify that a CRITICAL deviation automatically creates a high-priority notification for the QA Manager | In-app notification exists for QA Manager: "Critical Deviation [DEV-XXXX] requires immediate attention" |
| 6 | Verify audit log records the creation of each deviation | Three RECORD_CREATE audit events exist, one per deviation |

**Expected Result:** Deviations can be created with all three classification levels. Invalid classifications are rejected. Critical deviations trigger immediate notifications.

**Actual Result:**

_______________________________________________________________________________

_______________________________________________________________________________

**Pass / Fail:** ________ **Tester:** ___________________________ **Date:** _______________

**Comments:**

_______________________________________________________________________________

---

### TC-OQ-QMS-006: Deviation Linked to CAPA Correctly

| Field | Detail |
|---|---|
| Test Case ID | TC-OQ-QMS-006 |
| Test Objective | Verify that a Deviation record can be linked to a CAPA record and that this linkage is bidirectional — the CAPA shows the associated deviation and vice versa |
| URS Reference | URS-002-DEV-002 |
| Risk Level | High |
| Prerequisites | A Deviation record (DEV-OQ-006) and a CAPA record (CAPA-OQ-006) both exist in the system |

**Test Steps:**

| Step | Action | Expected Result |
|---|---|---|
| 1 | Link the deviation to the CAPA: PATCH `/api/v1/qms/deviations/[dev_uuid]` with body `{"linked_capa_id": "[capa_uuid]"}` | HTTP 200 OK. Deviation record updated with linked_capa_id |
| 2 | Retrieve the deviation record: GET `/api/v1/qms/deviations/[dev_uuid]` | Response includes `linked_capa_id = [capa_uuid]` and a resolved `linked_capa` object with CAPA number and title |
| 3 | Retrieve the CAPA record: GET `/api/v1/qms/capas/[capa_uuid]` | Response includes a `linked_deviations` array containing the deviation's UUID and number |
| 4 | Verify the database linkage: `SELECT * FROM capa_deviation_links WHERE capa_id = '[capa_uuid]' AND deviation_id = '[dev_uuid]'` | One record exists in the link table |
| 5 | Verify the audit log records the linkage event on both the deviation and the CAPA | Audit RECORD_UPDATE events exist for both records, reflecting the link addition |
| 6 | Remove the link: PATCH `/api/v1/qms/deviations/[dev_uuid]` with body `{"linked_capa_id": null}` | HTTP 200 OK. Link removed. Audit log records the removal. |

**Expected Result:** The deviation-CAPA link is bidirectional, persistent, and audited. The link can be added and removed.

**Actual Result:**

_______________________________________________________________________________

_______________________________________________________________________________

**Pass / Fail:** ________ **Tester:** ___________________________ **Date:** _______________

**Comments:**

_______________________________________________________________________________

---

### TC-OQ-QMS-007: Change Control Risk Assessment Fields Mandatory for Major Changes

| Field | Detail |
|---|---|
| Test Case ID | TC-OQ-QMS-007 |
| Test Objective | Verify that for a Change Control classified as MAJOR, the risk assessment fields (risk_description, risk_mitigation, risk_level) are mandatory and the system rejects submission without them |
| URS Reference | URS-002-CC-001 |
| Risk Level | High |
| Prerequisites | User with `change_control:create` permission is authenticated |

**Test Steps:**

| Step | Action | Expected Result |
|---|---|---|
| 1 | Attempt to create a Change Control with change_type = MAJOR, and omit all risk assessment fields | HTTP 422 returned. Errors list risk_description, risk_mitigation, and risk_level as required |
| 2 | Attempt to create a Change Control with change_type = MAJOR, providing risk_description only (omitting risk_mitigation and risk_level) | HTTP 422 returned. Errors list the two remaining missing fields |
| 3 | Create a Change Control with change_type = MAJOR and all three risk assessment fields populated | HTTP 201 Created. Change control record returned with all fields |
| 4 | Create a Change Control with change_type = MINOR, omitting all risk assessment fields | HTTP 201 Created. Risk assessment fields are optional for MINOR changes. No validation error. |
| 5 | Verify the database: `SELECT change_type, risk_description, risk_mitigation, risk_level FROM change_controls WHERE id = '[cc_uuid]'` | MAJOR change has all three risk fields populated. MINOR change has NULL values for risk fields. |

**Expected Result:** Risk assessment fields are mandatory for MAJOR change controls and optional for MINOR. The system enforces this at the API level.

**Actual Result:**

_______________________________________________________________________________

_______________________________________________________________________________

**Pass / Fail:** ________ **Tester:** ___________________________ **Date:** _______________

**Comments:**

_______________________________________________________________________________

---

### TC-OQ-QMS-008: Change Control Implementation Date Cannot Be Before Approval Date

| Field | Detail |
|---|---|
| Test Case ID | TC-OQ-QMS-008 |
| Test Objective | Verify that the system rejects a Change Control implementation_date that is earlier than the approval_date, preventing retrospective or back-dated change implementations |
| URS Reference | URS-002-CC-002 |
| Risk Level | High |
| Prerequisites | A Change Control record in APPROVED status exists. The approval_date is 2026-04-10. |

**Test Steps:**

| Step | Action | Expected Result |
|---|---|---|
| 1 | Attempt to set the implementation_date to 2026-04-09 (before approval_date): PATCH `/api/v1/qms/change-controls/[cc_uuid]` with body `{"implementation_date": "2026-04-09"}` | HTTP 422 returned. Error: "Implementation date (2026-04-09) cannot be before approval date (2026-04-10)." |
| 2 | Attempt to set the implementation_date to 2026-04-10 (same as approval_date) | HTTP 200 OK. Same-day implementation is permitted. |
| 3 | Attempt to set the implementation_date to 2026-04-20 (after approval_date) | HTTP 200 OK. Future implementation date accepted. |
| 4 | Confirm via database: `SELECT approval_date, implementation_date FROM change_controls WHERE id = '[cc_uuid]'` | approval_date = 2026-04-10, implementation_date = 2026-04-20 |

**Expected Result:** Implementation dates before the approval date are rejected. Same-day and future dates are accepted.

**Actual Result:**

_______________________________________________________________________________

_______________________________________________________________________________

**Pass / Fail:** ________ **Tester:** ___________________________ **Date:** _______________

**Comments:**

_______________________________________________________________________________

---

### TC-OQ-QMS-009: Document in Change Control Linked Correctly

| Field | Detail |
|---|---|
| Test Case ID | TC-OQ-QMS-009 |
| Test Objective | Verify that a controlled document (SOP) can be linked to a Change Control record and that the linkage creates a traceable connection between the document revision and the change |
| URS Reference | URS-002-CC-003 |
| Risk Level | Medium |
| Prerequisites | A Change Control record and a controlled SOP document (version 2, DRAFT) both exist |

**Test Steps:**

| Step | Action | Expected Result |
|---|---|---|
| 1 | Link the SOP to the Change Control: POST `/api/v1/qms/change-controls/[cc_uuid]/documents` with body `{"document_id": "[doc_uuid]", "link_type": "REVISED_DOCUMENT"}` | HTTP 201 Created. Link record returned. |
| 2 | Retrieve the Change Control: GET `/api/v1/qms/change-controls/[cc_uuid]` | Response includes a `linked_documents` array with the SOP document UUID, title, version, and link type |
| 3 | Retrieve the document: GET `/api/v1/documents/[doc_uuid]` | Response includes `linked_change_controls` array with the CC number |
| 4 | Verify the database link: `SELECT * FROM change_control_document_links WHERE change_control_id = '[cc_uuid]' AND document_id = '[doc_uuid]'` | One record exists |
| 5 | Verify an attempt to link the same document twice returns an appropriate error | HTTP 409 Conflict returned |

**Expected Result:** Document-CC linkage is created, bidirectional, and prevents duplicate entries.

**Actual Result:**

_______________________________________________________________________________

_______________________________________________________________________________

**Pass / Fail:** ________ **Tester:** ___________________________ **Date:** _______________

**Comments:**

_______________________________________________________________________________

---

### TC-OQ-QMS-010: Supplier Status Cannot Be Set to Approved Without an Audit Record

| Field | Detail |
|---|---|
| Test Case ID | TC-OQ-QMS-010 |
| Test Objective | Verify that a Supplier record cannot be set to APPROVED status unless at least one completed Supplier Audit record exists and is linked to the supplier |
| URS Reference | URS-002-SUP-001 |
| Risk Level | High |
| Prerequisites | A Supplier record (SUPP-OQ-010) exists with status = PENDING. No audit records are linked to this supplier. |

**Test Steps:**

| Step | Action | Expected Result |
|---|---|---|
| 1 | Confirm the supplier has no linked audit records: `SELECT COUNT(*) FROM supplier_audits WHEREsupplier_id = '[supp_uuid]' AND status = 'COMPLETED'` | COUNT = 0 |
| 2 | Attempt to set the supplier status to APPROVED: PATCH `/api/v1/qms/suppliers/[supp_uuid]` with body `{"status": "APPROVED"}` | HTTP 422 returned. Error: "Supplier cannot be approved without at least one completed audit record." |
| 3 | Verify supplier status remains PENDING in the database | status = PENDING |
| 4 | Create and complete a supplier audit record linked to this supplier: POST `/api/v1/qms/supplier-audits` and then transition to COMPLETED | Audit record created and status = COMPLETED |
| 5 | Reattempt to set supplier status to APPROVED | HTTP 200 OK. Supplier status = APPROVED. |
| 6 | Verify audit log records the status change | RECORD_UPDATE audit event: old_status = PENDING, new_status = APPROVED |

**Expected Result:** Supplier approval is blocked without a completed audit. Once a completed audit exists, approval succeeds.

**Actual Result:**

_______________________________________________________________________________

_______________________________________________________________________________

**Pass / Fail:** ________ **Tester:** ___________________________ **Date:** _______________

**Comments:**

_______________________________________________________________________________

---

### TC-OQ-QMS-011: Risk RPN Calculated Correctly (Probability × Severity × Detectability)

| Field | Detail |
|---|---|
| Test Case ID | TC-OQ-QMS-011 |
| Test Objective | Verify that the system correctly calculates the Risk Priority Number (RPN) as the product of Probability, Severity, and Detectability scores, and stores the calculated value in the risk assessment record |
| URS Reference | URS-002-RISK-001, ICH Q9 |
| Risk Level | High |
| Prerequisites | User with `risk:create` permission is authenticated. A Risk Assessment record is being created. |

**Test Steps:**

| Step | Action | Expected Result |
|---|---|---|
| 1 | Create a Risk Assessment with: probability = 3, severity = 5, detectability = 4 | HTTP 201 Created. Record returned. |
| 2 | Verify the calculated RPN field: `SELECT rpn, probability, severity, detectability FROM risk_assessments WHERE id = '[risk_uuid]'` | rpn = 60 (3 × 5 × 4). probability = 3, severity = 5, detectability = 4. |
| 3 | Update the risk record with: probability = 7, severity = 8, detectability = 6 | HTTP 200 OK |
| 4 | Verify the recalculated RPN | rpn = 336 (7 × 8 × 6) |
| 5 | Update with: probability = 10, severity = 10, detectability = 10 | HTTP 200 OK. rpn = 1000 (maximum possible) |
| 6 | Attempt to enter a probability value > 10: probability = 11 | HTTP 422 returned. Error: probability must be between 1 and 10. |
| 7 | Attempt to enter a severity value of 0 | HTTP 422 returned. Error: severity must be between 1 and 10. |

**Expected Result:** The system automatically calculates RPN = Probability × Severity × Detectability. All score values are constrained to 1–10. The RPN is recalculated whenever any component score changes.

**Actual Result:**

_______________________________________________________________________________

_______________________________________________________________________________

**Pass / Fail:** ________ **Tester:** ___________________________ **Date:** _______________

**Comments:**

_______________________________________________________________________________

---

### TC-OQ-QMS-012: Risk Assessment Requires Approval E-Signature Before Closing

| Field | Detail |
|---|---|
| Test Case ID | TC-OQ-QMS-012 |
| Test Objective | Verify that a Risk Assessment cannot be transitioned to CLOSED status without a valid electronic signature from an authorised approver |
| URS Reference | URS-002-RISK-002, 21 CFR 11.50 |
| Risk Level | High |
| Prerequisites | A Risk Assessment record exists in REVIEWED status, ready for approval |

**Test Steps:**

| Step | Action | Expected Result |
|---|---|---|
| 1 | Attempt to close the risk assessment without providing an e-signature: POST transition with target_state = CLOSED, no signature payload | HTTP 422 returned. Error: "Electronic signature required to close a Risk Assessment." |
| 2 | Attempt to close the risk assessment with an incorrect password in the e-signature payload | HTTP 401 or HTTP 422 returned. Error indicates signature authentication failed. Risk assessment is not closed. |
| 3 | Close the risk assessment with a valid e-signature from an authorised Risk Manager | HTTP 200 OK. Status = CLOSED. E-signature record created with meaning = "Risk Accepted and Closed". |
| 4 | Verify the e-signature record: `SELECT * FROM esignatures WHERE record_id = '[risk_uuid]' AND meaning = 'Risk Accepted and Closed'` | One e-signature record is present with correct signer identity and timestamp |

**Expected Result:** The Risk Assessment closure is gated by a valid e-signature. Attempts without or with incorrect signatures fail.

**Actual Result:**

_______________________________________________________________________________

_______________________________________________________________________________

**Pass / Fail:** ________ **Tester:** ___________________________ **Date:** _______________

**Comments:**

_______________________________________________________________________________

---

### TC-OQ-QMS-013: High-Risk Item (RPN > 100) Triggers Mandatory CAPA Linkage

| Field | Detail |
|---|---|
| Test Case ID | TC-OQ-QMS-013 |
| Test Objective | Verify that the system prevents a Risk Assessment with RPN > 100 from being approved or closed unless at least one CAPA record is linked to it |
| URS Reference | URS-002-RISK-003, ICH Q9 §3 |
| Risk Level | High |
| Prerequisites | A Risk Assessment record exists with RPN = 150 (e.g., P=5, S=6, D=5). No CAPAs are linked. |

**Test Steps:**

| Step | Action | Expected Result |
|---|---|---|
| 1 | Confirm the RPN is > 100: `SELECT rpn FROM risk_assessments WHERE id = '[risk_uuid]'` | rpn = 150 |
| 2 | Confirm no CAPAs are linked: `SELECT COUNT(*) FROM risk_capa_links WHERE risk_id = '[risk_uuid]'` | COUNT = 0 |
| 3 | Attempt to transition the risk assessment to APPROVED | HTTP 422 returned. Error: "Risk assessments with RPN > 100 require at least one linked CAPA before approval." |
| 4 | Create a CAPA record and link it to this risk assessment: POST `/api/v1/qms/risk-assessments/[risk_uuid]/capas` with body `{"capa_id": "[capa_uuid]"}` | HTTP 201 Created. Link established. |
| 5 | Reattempt to transition to APPROVED (with e-signature if required) | HTTP 200 OK. Risk assessment transitions to APPROVED. |
| 6 | Verify a risk assessment with RPN = 80 (≤ 100) can be approved without a linked CAPA | HTTP 200 OK for the low-RPN risk assessment. No CAPA required. |

**Expected Result:** Risk assessments with RPN > 100 cannot be approved without a linked CAPA. RPN ≤ 100 assessments can be approved without this requirement.

**Actual Result:**

_______________________________________________________________________________

_______________________________________________________________________________

**Pass / Fail:** ________ **Tester:** ___________________________ **Date:** _______________

**Comments:**

_______________________________________________________________________________

---

### TC-OQ-QMS-014: Audit Trail Captures All Field Changes in QMS Module

| Field | Detail |
|---|---|
| Test Case ID | TC-OQ-QMS-014 |
| Test Objective | Verify that all field-level changes across all QMS record types (CAPA, Deviation, Change Control, Supplier, Risk Assessment) generate audit log entries with old and new values |
| URS Reference | URS-002-AUDIT-001, 21 CFR 11.10(e) |
| Risk Level | Critical |
| Prerequisites | Records exist for each QMS entity type. Tester has edit permissions for each. |

**Test Steps:**

| Step | Action | Expected Result |
|---|---|---|
| 1 | Update the description field of a CAPA record | Audit RECORD_UPDATE event created for the CAPA with old_values.description and new_values.description |
| 2 | Update the classification field of a Deviation record | Audit RECORD_UPDATE event created for the Deviation with old_values.classification and new_values.classification |
| 3 | Update the risk_level field of a Change Control | Audit RECORD_UPDATE event created for the Change Control with old_values.risk_level and new_values.risk_level |
| 4 | Update the status field of a Supplier record | Audit RECORD_UPDATE event created for the Supplier with old and new status values |
| 5 | Update the detectability score on a Risk Assessment | Audit RECORD_UPDATE event created with old_values.detectability, new_values.detectability, and the resulting RPN change |
| 6 | Verify that for each audit event: actor_user_id, actor_username, timestamp, record_id, record_type, old_values, and new_values are all populated | All required fields present in all five audit events |
| 7 | Verify the audit events appear in the QMS module's audit log view in the UI | The UI correctly displays all five audit events with human-readable field names and values |

**Expected Result:** Every field change across all QMS entity types generates a complete audit log entry with old and new values, actor identity, and timestamp.

**Actual Result:**

_______________________________________________________________________________

_______________________________________________________________________________

**Pass / Fail:** ________ **Tester:** ___________________________ **Date:** _______________

**Comments:**

_______________________________________________________________________________

---

### TC-OQ-QMS-015: User Without QA Role Cannot Approve a CAPA

| Field | Detail |
|---|---|
| Test Case ID | TC-OQ-QMS-015 |
| Test Objective | Verify that only users assigned a role that includes the `capa:approve` permission can perform the CAPA approval action, and that users with other roles (including Operator and Supplier Quality Manager) are blocked |
| URS Reference | URS-002-RBAC-001, 21 CFR 11.10(d) |
| Risk Level | High |
| Prerequisites | A CAPA record is in IN_REVIEW status. User "operator.oq015@gmpplatform.local" has the Operator role only (no `capa:approve` permission). User "qa.manager.oq015@gmpplatform.local" has the QA Manager role (includes `capa:approve`). |

**Test Steps:**

| Step | Action | Expected Result |
|---|---|---|
| 1 | Authenticate as `operator.oq015@gmpplatform.local` | Authentication succeeds |
| 2 | Attempt to approve the CAPA: POST `/api/v1/qms/capas/[capa_uuid]/transitions` with target_state = APPROVED and e-signature payload | HTTP 403 Forbidden. Error: "Insufficient permissions: capa:approve required." |
| 3 | Verify the CAPA status has not changed | status = IN_REVIEW |
| 4 | Verify an ACCESS_DENIED audit event is recorded | Audit event present for this failed approval attempt |
| 5 | Authenticate as `qa.manager.oq015@gmpplatform.local` | Authentication succeeds |
| 6 | Approve the CAPA with a valid e-signature | HTTP 200 OK. CAPA status = APPROVED. |

**Expected Result:** Users without `capa:approve` permission are blocked from the approval action. Only QA-role users can approve CAPAs.

**Actual Result:**

_______________________________________________________________________________

_______________________________________________________________________________

**Pass / Fail:** ________ **Tester:** ___________________________ **Date:** _______________

**Comments:**

_______________________________________________________________________________

---

### TC-OQ-QMS-016: CAPA Effectiveness Check Due Date Calculated from Closure Date

| Field | Detail |
|---|---|
| Test Case ID | TC-OQ-QMS-016 |
| Test Objective | Verify that when a CAPA transitions to EFFECTIVENESS_CHECK status, the system automatically calculates and populates the effectiveness_check_due_date as a defined number of days after the closure (or implementation completion) date, based on the configured CAPA priority |
| URS Reference | URS-002-CAPA-005 |
| Risk Level | Medium |
| Prerequisites | The system is configured with the following effectiveness check intervals: CRITICAL = 30 days, MAJOR = 60 days, MINOR = 90 days after transition to EFFECTIVENESS_CHECK |

**Test Steps:**

| Step | Action | Expected Result |
|---|---|---|
| 1 | Transition a CAPA with priority = CRITICAL to EFFECTIVENESS_CHECK status (from WIP) | HTTP 200 OK. Status = EFFECTIVENESS_CHECK. Note the transition timestamp (T). |
| 2 | Retrieve the effectiveness_check_due_date: `SELECT effectiveness_check_due_date FROM capas WHERE id = '[capa_uuid_critical]'` | effectiveness_check_due_date = T + 30 days (within ±1 day tolerance for time-of-day differences) |
| 3 | Transition a MAJOR priority CAPA to EFFECTIVENESS_CHECK | HTTP 200 OK. |
| 4 | Retrieve the effectiveness_check_due_date for the MAJOR CAPA | effectiveness_check_due_date = T + 60 days |
| 5 | Transition a MINOR priority CAPA to EFFECTIVENESS_CHECK | HTTP 200 OK. |
| 6 | Retrieve the effectiveness_check_due_date for the MINOR CAPA | effectiveness_check_due_date = T + 90 days |
| 7 | Verify the effectiveness_check_due_date cannot be manually set to a date before the transition date | PATCH with effectiveness_check_due_date < transition_date returns HTTP 422 |

**Expected Result:** Effectiveness check due dates are automatically calculated per priority class. Manual back-dating is prevented.

**Actual Result:**

_______________________________________________________________________________

_______________________________________________________________________________

**Pass / Fail:** ________ **Tester:** ___________________________ **Date:** _______________

**Comments:**

_______________________________________________________________________________

---

### TC-OQ-QMS-017: Deviation Cannot Be Linked to a Non-Existent CAPA

| Field | Detail |
|---|---|
| Test Case ID | TC-OQ-QMS-017 |
| Test Objective | Verify that the system validates foreign key integrity when linking a Deviation to a CAPA — linking to a non-existent or deleted CAPA ID is rejected |
| URS Reference | URS-002-DEV-003 |
| Risk Level | Medium |
| Prerequisites | A Deviation record exists in DRAFT status |

**Test Steps:**

| Step | Action | Expected Result |
|---|---|---|
| 1 | Attempt to link the deviation to a fabricated/non-existent CAPA UUID: PATCH deviation with `{"linked_capa_id": "00000000-0000-0000-0000-000000000000"}` | HTTP 404 Not Found or HTTP 422 Unprocessable Entity. Error: "CAPA with ID 00000000-0000-0000-0000-000000000000 does not exist." |
| 2 | Verify the deviation's linked_capa_id field is still NULL | `SELECT linked_capa_id FROM deviations WHERE id = '[dev_uuid]'` returns NULL |
| 3 | Link to a valid, existing CAPA | HTTP 200 OK. Linkage established. |

**Expected Result:** Non-existent CAPA references are rejected. Only valid, existing CAPAs can be linked.

**Actual Result:**

_______________________________________________________________________________

_______________________________________________________________________________

**Pass / Fail:** ________ **Tester:** ___________________________ **Date:** _______________

**Comments:**

_______________________________________________________________________________

---

### TC-OQ-QMS-018: QMS Module Search and Filter Returns Correct Results

| Field | Detail |
|---|---|
| Test Case ID | TC-OQ-QMS-018 |
| Test Objective | Verify that the QMS module search and filter functionality returns accurate results and that filters for status, date range, assigned user, and record type operate correctly |
| URS Reference | URS-002-GENERAL-001 |
| Risk Level | Medium |
| Prerequisites | At least 10 CAPA records exist in the test environment with varying statuses (DRAFT, IN_REVIEW, CLOSED), dates, and assigned users |

**Test Steps:**

| Step | Action | Expected Result |
|---|---|---|
| 1 | Search for all CAPAs with status = DRAFT: GET `/api/v1/qms/capas?status=DRAFT` | Only DRAFT CAPAs are returned. No CLOSED or IN_REVIEW records in the result set. |
| 2 | Search for CAPAs with status = CLOSED | Only CLOSED CAPAs returned |
| 3 | Search for CAPAs assigned to a specific user: GET `/api/v1/qms/capas?assigned_to_user_id=[user_uuid]` | Only CAPAs assigned to that user are returned |
| 4 | Search for CAPAs created within a date range: GET `/api/v1/qms/capas?created_after=2026-04-01&created_before=2026-04-30` | Only CAPAs created in April 2026 are returned |
| 5 | Search for CAPAs using a keyword in the title: GET `/api/v1/qms/capas?q=contamination` | Only CAPAs with "contamination" in the title or description are returned |
| 6 | Combine multiple filters: status = IN_REVIEW AND assigned_to = [user_uuid] | Results are correctly filtered by both criteria simultaneously |
| 7 | Verify pagination: GET `/api/v1/qms/capas?page=1&page_size=5` | Returns maximum 5 records. Response includes `total_count`, `page`, `page_size`, and `total_pages`. |

**Expected Result:** All filter combinations return accurate results. Pagination metadata is correct.

**Actual Result:**

_______________________________________________________________________________

_______________________________________________________________________________

**Pass / Fail:** ________ **Tester:** ___________________________ **Date:** _______________

**Comments:**

_______________________________________________________________________________

---

## 6. Acceptance Criteria

This OQ is considered successfully completed when ALL of the following criteria are met:

| Criterion | Requirement |
|---|---|
| AC-001 | All 18 test cases (TC-OQ-QMS-001 through TC-OQ-QMS-018) have been executed and recorded with a result of PASS |
| AC-002 | All test case Actual Results fields are completed contemporaneously |
| AC-003 | All tester signatures and dates are present for each executed test case |
| AC-004 | Any deviations observed have been documented with a Deviation ID |
| AC-005 | All deviations have been resolved or formally risk-accepted prior to OQ approval |
| AC-006 | The protocol has been reviewed and approved per Section 8 |

**Overall OQ Outcome:** PASS / FAIL / CONDITIONAL PASS (circle one)

**Summary of Outcome:**

_______________________________________________________________________________

_______________________________________________________________________________

---

## 7. Deviation Handling

### 7.1 Definition

A deviation is any departure from the expected result defined in a test case, including unexpected system behaviour, error messages different from specified, inability to execute a test step, or unmet prerequisites.

### 7.2 Deviation Procedure

1. Stop execution of the affected test case immediately.
2. Record FAIL or DEVIATION in the Pass/Fail field.
3. Describe the observation in the Comments field.
4. Raise a formal Deviation Record in the log below.
5. Assess impact before proceeding.
6. Do not erase or obscure any prior entry — use single strikethrough with initials and date.

### 7.3 Deviation Log

| Dev ID | TC Reference | Description of Deviation | Date Observed | Observed By | Impact Assessment | Disposition | Disposition By | Date Closed |
|---|---|---|---|---|---|---|---|---|
| DEV-001 | | | | | | | | |
| DEV-002 | | | | | | | | |
| DEV-003 | | | | | | | | |
| DEV-004 | | | | | | | | |
| DEV-005 | | | | | | | | |

**Disposition Options:** Resolved | Risk Accepted | Open

---

## 8. Signature Page

### 8.1 Protocol Author

| Field | Detail |
|---|---|
| Name (Print) | |
| Title | |
| Department | |
| Signature | |
| Date | |

### 8.2 Protocol Reviewer

| Field | Detail |
|---|---|
| Name (Print) | |
| Title | |
| Department | |
| Signature | |
| Date | |

### 8.3 Protocol Approver

| Field | Detail |
|---|---|
| Name (Print) | |
| Title | |
| Department | |
| Signature | |
| Date | |

### 8.4 Execution Completion Signature

| Field | Detail |
|---|---|
| Name (Print) | |
| Title | |
| Signature | |
| Date of Completion | |
| Protocol Outcome | PASS / FAIL / CONDITIONAL PASS |

---

*End of OQ-002 Operational Qualification — QMS Module*

*Document ID: OQ-002 | Version: 01 | GMP Platform | 2026-04-21*
