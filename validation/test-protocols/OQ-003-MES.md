# OQ-003 Operational Qualification — MES Module

---

| Field | Value |
|---|---|
| Document ID | OQ-003 |
| Title | Operational Qualification — Manufacturing Execution System (MES) Module |
| Version | 01 |
| Status | DRAFT |
| Date | 2026-04-21 |
| System | GMP Platform |
| Module | MES (Master Batch Records, Batch Execution, Material Management, Work Orders) |
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

This Operational Qualification (OQ) protocol establishes documented evidence that the GMP Platform Manufacturing Execution System (MES) Module operates consistently and as intended throughout anticipated operating ranges. Execution of this protocol demonstrates that Master Batch Record (MBR) creation, versioning, batch record generation, step execution, critical parameter monitoring, material dispensing, yield calculation, work order management, and batch release functions operate correctly and in compliance with applicable GMP and regulatory requirements.

### 1.2 Scope

This OQ covers the following MES Module components:

| Component | Key Functions Under Test |
|---|---|
| Master Batch Record (MBR) | Creation, version control, approval, lifecycle management |
| Batch Record | Generation from approved MBR, step execution, operator attribution, critical parameters |
| Material Management | Material lot dispensing, quantity tracking, tolerance enforcement |
| Work Orders | Quantity tracking, batch completion decrement |
| Batch Release | Completeness checks, dual e-signature, status controls |
| Audit Trail | Step-level entry logging with timestamp and operator identity |
| MBR Version Lock | Immutability of MBR version on batch record creation |
| Batch Numbering | Uniqueness enforcement per organisation |

**Out of Scope:** Foundation Layer (OQ-001), QMS Module (OQ-002), LIMS, Equipment, Training, and Environmental Monitoring modules are covered in separate protocols.

### 1.3 Regulatory Basis

- 21 CFR Part 211 Subpart F — Production and Process Controls (§211.100, §211.101, §211.105, §211.110)
- 21 CFR Part 211 Subpart J — Records and Reports (§211.186, §211.188)
- EU GMP Annex 11 — Computerised Systems
- EU GMP Part I Chapter 4 — Documentation
- EU GMP Part I Chapter 5 — Production
- 21 CFR Part 11 — Electronic Records; Electronic Signatures
- GAMP 5 — A Risk-Based Approach to Compliant GxP Computerised Systems

---

## 2. References

| Reference ID | Document Title |
|---|---|
| URS-003 | User Requirements Specification — MES Module |
| IQ-001 | Installation Qualification — Foundation Layer (prerequisite) |
| OQ-001 | Operational Qualification — Foundation Layer (prerequisite) |
| OQ-002 | Operational Qualification — QMS Module (informational reference) |
| SDD-003 | System Design Description — MES Module |
| RA-003 | Risk Assessment — MES Module |
| GMP-PLT-QMP-001 | Quality Management Plan — GMP Platform |
| 21 CFR Part 211 | Current Good Manufacturing Practice for Finished Pharmaceuticals |
| 21 CFR Part 11 | Electronic Records; Electronic Signatures |
| EU GMP Annex 11 | Computerised Systems (EMA, 2011) |
| GAMP 5 | A Risk-Based Approach to Compliant GxP Computerised Systems (ISPE, 2022) |

---

## 3. Definitions and Abbreviations

| Term / Abbreviation | Definition |
|---|---|
| API | Application Programming Interface |
| BR | Batch Record (executed record for a specific batch) |
| CoA | Certificate of Analysis |
| E-signature | Electronic signature per 21 CFR Part 11 |
| GMP | Good Manufacturing Practice |
| IQ | Installation Qualification |
| LIMS | Laboratory Information Management System |
| MBR | Master Batch Record (master template) |
| MES | Manufacturing Execution System |
| OOS | Out of Specification |
| OQ | Operational Qualification |
| QA | Quality Assurance |
| RBAC | Role-Based Access Control |
| RPN | Risk Priority Number |
| SOP | Standard Operating Procedure |
| UUID | Universally Unique Identifier |
| WO | Work Order |

---

## 4. Prerequisites

| Prereq ID | Prerequisite | Verified By | Date | Initials |
|---|---|---|---|---|
| PRE-001 | OQ-001 (Foundation Layer OQ) is approved and all test cases passed | | | |
| PRE-002 | IQ-001 is approved | | | |
| PRE-003 | Test environment is isolated and contains no GMP production data | | | |
| PRE-004 | The following test user accounts exist with the specified roles: Production Operator (mes:execute_step), QA Batch Reviewer (mes:release_batch), MBR Author (mes:create_mbr), MBR Approver (mes:approve_mbr) | | | |
| PRE-005 | At least one product is configured in the system with a material BOM (Bill of Materials) | | | |
| PRE-006 | At least three material lots are present in the inventory with known quantities | | | |
| PRE-007 | At least one Work Order is present in OPEN status with a planned quantity of 100 kg | | | |
| PRE-008 | Tester(s) have read this protocol in full and hold current GMP documentation training | | | |
| PRE-009 | Direct database access is available for result verification | | | |
| PRE-010 | The system version under test matches the IQ-approved version | | | |

**System Version Under Test:** ___________________________

**Test Environment URL:** ___________________________

**Prerequisites Verified By:** ___________________________ Date: _______________

---

## 5. Test Cases

### Instructions for Execution

1. Execute test cases in order; some test cases build upon artefacts created in prior steps.
2. Record all results contemporaneously. Do not complete after the fact.
3. Deviations must be raised immediately using the Deviation Log in Section 7.
4. Actual Results must genuinely describe observed behaviour, not repeat expected results.

---

### TC-OQ-MES-001: Master Batch Record Creation with Version Control

| Field | Detail |
|---|---|
| Test Case ID | TC-OQ-MES-001 |
| Test Objective | Verify that a Master Batch Record (MBR) can be created with all mandatory fields, is assigned version 1 on initial creation, and is assigned a system-generated MBR number |
| URS Reference | URS-003-MBR-001 |
| Risk Level | High |
| Prerequisites | User with `mes:create_mbr` permission is authenticated. A product (Product Code: PROD-OQ-001) exists in the system. |

**Test Steps:**

| Step | Action | Expected Result |
|---|---|---|
| 1 | Attempt to create an MBR with the product_id field missing: POST `/api/v1/mes/mbrs` without product_id | HTTP 422. Validation error for product_id |
| 2 | Attempt to create an MBR with no steps defined | HTTP 422. Error: "At least one manufacturing step is required." |
| 3 | Create a complete MBR with: product_id, batch_size_kg = 100, yield_lower_limit = 90, yield_upper_limit = 105, and 5 manufacturing steps each with step_number, step_name, instructions, and is_critical = false/true as appropriate | HTTP 201 Created. MBR returned with UUID, system-generated MBR number (e.g., MBR-PROD-OQ-001-001), version_number = 1, status = DRAFT |
| 4 | Verify the database: `SELECT mbr_number, version_number, status, product_id, batch_size_kg FROM mbrs WHERE id = '[mbr_uuid]'` | All fields match input values. version_number = 1. status = DRAFT |
| 5 | Verify the 5 steps are created: `SELECT COUNT(*) FROM mbr_steps WHERE mbr_id = '[mbr_uuid]' ORDER BY step_number` | COUNT = 5. Steps are ordered by step_number. |
| 6 | Verify audit log RECORD_CREATE event | Audit event present for MBR creation with actor_user_id of the MBR author |

**Expected Result:** MBR is created in DRAFT status at version 1 with a system-generated number. All mandatory fields are validated. Audit log is created.

**Actual Result:**

_______________________________________________________________________________

_______________________________________________________________________________

**Pass / Fail:** ________ **Tester:** ___________________________ **Date:** _______________

**Comments:**

_______________________________________________________________________________

---

### TC-OQ-MES-002: MBR Cannot Be Executed Without Approved Status

| Field | Detail |
|---|---|
| Test Case ID | TC-OQ-MES-002 |
| Test Objective | Verify that a Batch Record cannot be created (i.e., an MBR cannot be "executed") unless the MBR is in APPROVED status |
| URS Reference | URS-003-MBR-002, 21 CFR 211.100(a) |
| Risk Level | Critical |
| Prerequisites | An MBR created in TC-OQ-MES-001 exists in DRAFT status (not yet approved) |

**Test Steps:**

| Step | Action | Expected Result |
|---|---|---|
| 1 | Confirm MBR status: `SELECT status FROM mbrs WHERE id = '[mbr_uuid]'` | status = DRAFT |
| 2 | Attempt to create a Batch Record from this DRAFT MBR: POST `/api/v1/mes/batch-records` with body `{"mbr_id": "[mbr_uuid]", "work_order_id": "[wo_uuid]", "batch_number": "BN-OQ-002-001"}` | HTTP 422 Unprocessable Entity. Error: "MBR must be in APPROVED status before a Batch Record can be created. Current status: DRAFT." |
| 3 | Confirm no batch record was created: `SELECT COUNT(*) FROM batch_records WHERE mbr_id = '[mbr_uuid]'` | COUNT = 0 |
| 4 | Advance the MBR through the approval workflow to APPROVED status (with required e-signature) | MBR status = APPROVED |
| 5 | Reattempt to create the Batch Record from the now-APPROVED MBR | HTTP 201 Created. Batch Record created. |

**Expected Result:** Batch Record creation from a non-APPROVED MBR is blocked. Once the MBR is approved, creation succeeds.

**Actual Result:**

_______________________________________________________________________________

_______________________________________________________________________________

**Pass / Fail:** ________ **Tester:** ___________________________ **Date:** _______________

**Comments:**

_______________________________________________________________________________

---

### TC-OQ-MES-003: Batch Record Created from Approved MBR Correctly Inherits All Steps

| Field | Detail |
|---|---|
| Test Case ID | TC-OQ-MES-003 |
| Test Objective | Verify that when a Batch Record is created from an Approved MBR, all steps defined in the MBR are reproduced in the Batch Record with the correct attributes (step number, name, instructions, is_critical, required parameters) and in the correct order |
| URS Reference | URS-003-BR-001 |
| Risk Level | Critical |
| Prerequisites | An APPROVED MBR with exactly 5 steps (step numbers 1–5) exists. Step 3 is marked is_critical = true with parameter_name = "Mixing Temperature", lower_limit = 60, upper_limit = 80, unit = "°C". |

**Test Steps:**

| Step | Action | Expected Result |
|---|---|---|
| 1 | Create a Batch Record from the APPROVED MBR: POST `/api/v1/mes/batch-records` with mbr_id, work_order_id, and batch_number | HTTP 201 Created. Batch Record returned with UUID, batch_number, status = IN_PROGRESS. |
| 2 | Query the Batch Record steps: `SELECT step_number, step_name, is_critical, instructions FROM batch_record_steps WHERE batch_record_id = '[br_uuid]' ORDER BY step_number` | Exactly 5 steps returned, in order (step_number 1 through 5). Step names and instructions match the MBR verbatim. |
| 3 | Verify Step 3 is_critical = TRUE and has the correct critical parameter definition | Step 3 record has is_critical = TRUE, critical_parameter.name = "Mixing Temperature", lower = 60, upper = 80, unit = "°C" |
| 4 | Verify the batch record's mbr_id and mbr_version_number are recorded | `SELECT mbr_id, mbr_version_number FROM batch_records WHERE id = '[br_uuid]'` — mbr_id = the MBR UUID, mbr_version_number = the MBR version at time of creation |
| 5 | Count total steps: `SELECT COUNT(*) FROM batch_record_steps WHERE batch_record_id = '[br_uuid]'` | COUNT = 5 exactly |

**Expected Result:** All 5 MBR steps are inherited exactly by the Batch Record. Critical parameter definitions are preserved. The MBR version at time of creation is recorded on the Batch Record.

**Actual Result:**

_______________________________________________________________________________

_______________________________________________________________________________

**Pass / Fail:** ________ **Tester:** ___________________________ **Date:** _______________

**Comments:**

_______________________________________________________________________________

---

### TC-OQ-MES-004: Batch Step Entries Require Operator Attribution — Cannot Be Anonymous

| Field | Detail |
|---|---|
| Test Case ID | TC-OQ-MES-004 |
| Test Objective | Verify that each batch step entry is attributed to a specific authenticated user and that the system does not allow anonymous or unauthenticated step entry |
| URS Reference | URS-003-BR-002, 21 CFR 211.68, 21 CFR Part 11 |
| Risk Level | Critical |
| Prerequisites | A Batch Record in IN_PROGRESS status exists. Steps are in PENDING status. |

**Test Steps:**

| Step | Action | Expected Result |
|---|---|---|
| 1 | Attempt to submit a step entry without an authentication token: POST `/api/v1/mes/batch-records/[br_uuid]/steps/1/entry` without Authorization header | HTTP 401 Unauthorized |
| 2 | Authenticate as `operator.oq004@gmpplatform.local` and obtain a valid session token | Authentication succeeds |
| 3 | Submit Step 1 entry with actual values and comments: POST with body `{"actual_value": null, "comments": "Step completed without deviation", "status": "COMPLETE"}` | HTTP 200 OK. Step 1 is updated to COMPLETE status. |
| 4 | Query the step entry: `SELECT performed_by_user_id, performed_by_username, performed_at FROM batch_record_steps WHERE batch_record_id = '[br_uuid]' AND step_number = 1` | performed_by_user_id = UUID of operator.oq004. performed_by_username = 'operator.oq004@gmpplatform.local'. performed_at = UTC timestamp. |
| 5 | Verify the audit log records the step entry with the operator's user ID | Audit event RECORD_UPDATE for the batch record step, actor_user_id = operator.oq004 UUID |

**Expected Result:** Every step entry is attributed to the authenticated user. Anonymous entries are rejected with HTTP 401. The operator identity and timestamp are stored immutably.

**Actual Result:**

_______________________________________________________________________________

_______________________________________________________________________________

**Pass / Fail:** ________ **Tester:** ___________________________ **Date:** _______________

**Comments:**

_______________________________________________________________________________

---

### TC-OQ-MES-005: Critical Parameter Out of Range Flags the Step

| Field | Detail |
|---|---|
| Test Case ID | TC-OQ-MES-005 |
| Test Objective | Verify that when a critical parameter value is entered outside the defined limits (lower_limit or upper_limit), the step is automatically flagged as OUT_OF_RANGE and the batch record is flagged for QA review |
| URS Reference | URS-003-BR-003, 21 CFR 211.110(a) |
| Risk Level | Critical |
| Prerequisites | Step 3 of the Batch Record has is_critical = TRUE, lower_limit = 60, upper_limit = 80 for Mixing Temperature (°C). Step 3 is in PENDING status. |

**Test Steps:**

| Step | Action | Expected Result |
|---|---|---|
| 1 | Enter a critical parameter value within range (e.g., actual_value = 70°C): POST step 3 entry with actual_value = 70 | HTTP 200 OK. Step 3 status = COMPLETE. No flag raised. critical_parameter_status = IN_RANGE. |
| 2 | Reset step 3 to PENDING (or use a fresh batch record for this test). Enter a critical parameter value below the lower limit (actual_value = 55°C) | HTTP 200 OK. Step records actual_value = 55. critical_parameter_status = OUT_OF_RANGE. A QA review flag is raised on the batch record: `requires_qa_review = TRUE`. |
| 3 | Query the step: `SELECT actual_value, critical_parameter_status FROM batch_record_steps WHERE batch_record_id = '[br_uuid]' AND step_number = 3` | actual_value = 55, critical_parameter_status = OUT_OF_RANGE |
| 4 | Query the batch record: `SELECT requires_qa_review FROM batch_records WHERE id = '[br_uuid]'` | requires_qa_review = TRUE |
| 5 | Verify an alert notification is sent to the QA Batch Reviewer | In-app notification: "Critical parameter out of range in Batch Record [BN-XXX], Step 3: Mixing Temperature = 55°C (limit: 60–80°C). QA review required." |
| 6 | Enter a value above the upper limit (actual_value = 85°C) | Same behaviour: OUT_OF_RANGE flag, QA review flag, notification |

**Expected Result:** Out-of-range critical parameter values are flagged immediately on entry. The batch record is marked for mandatory QA review. An alert notification is generated.

**Actual Result:**

_______________________________________________________________________________

_______________________________________________________________________________

**Pass / Fail:** ________ **Tester:** ___________________________ **Date:** _______________

**Comments:**

_______________________________________________________________________________

---

### TC-OQ-MES-006: Batch Yield Calculated Correctly

| Field | Detail |
|---|---|
| Test Case ID | TC-OQ-MES-006 |
| Test Objective | Verify that the system correctly calculates batch yield as a percentage of the theoretical yield and that the yield is flagged if it falls outside the defined acceptable limits |
| URS Reference | URS-003-BR-004, 21 CFR 211.192 |
| Risk Level | High |
| Prerequisites | An MBR defines: batch_size_kg = 100, yield_lower_limit = 90%, yield_upper_limit = 105%. A Batch Record in IN_PROGRESS status exists from this MBR. |

**Test Steps:**

| Step | Action | Expected Result |
|---|---|---|
| 1 | Enter the actual yield for the batch: PATCH `/api/v1/mes/batch-records/[br_uuid]` with body `{"actual_yield_kg": 95}` | HTTP 200 OK |
| 2 | Query the calculated yield: `SELECT actual_yield_kg, theoretical_yield_kg, yield_percentage, yield_status FROM batch_records WHERE id = '[br_uuid]'` | theoretical_yield_kg = 100, actual_yield_kg = 95, yield_percentage = 95.0, yield_status = WITHIN_LIMITS |
| 3 | Update actual_yield_kg = 88 (below the 90% lower limit) | HTTP 200 OK. yield_percentage = 88.0. yield_status = BELOW_LOWER_LIMIT. A QA alert is generated. |
| 4 | Update actual_yield_kg = 107 (above the 105% upper limit) | HTTP 200 OK. yield_percentage = 107.0. yield_status = ABOVE_UPPER_LIMIT. QA alert generated. |
| 5 | Verify yield calculation formula: yield_percentage = (actual_yield_kg / theoretical_yield_kg) × 100 | Formula confirmed by comparing computed values with database values for all three test entries |
| 6 | Restore to a valid yield: actual_yield_kg = 95 | yield_percentage = 95.0, yield_status = WITHIN_LIMITS |

**Expected Result:** Yield percentage is correctly calculated. Values outside defined limits produce a status flag and QA alert. The formula is verified.

**Actual Result:**

_______________________________________________________________________________

_______________________________________________________________________________

**Pass / Fail:** ________ **Tester:** ___________________________ **Date:** _______________

**Comments:**

_______________________________________________________________________________

---

### TC-OQ-MES-007: Batch Record Cannot Be Released Without All Steps Completed

| Field | Detail |
|---|---|
| Test Case ID | TC-OQ-MES-007 |
| Test Objective | Verify that a Batch Record cannot be transitioned to RELEASED status unless all defined manufacturing steps are in COMPLETE or SKIPPED (with justification) status — no steps may remain in PENDING status |
| URS Reference | URS-003-BR-005, 21 CFR 211.188 |
| Risk Level | Critical |
| Prerequisites | A Batch Record in IN_PROGRESS status with 5 steps. Steps 1, 2, 4, 5 are marked COMPLETE. Step 3 remains PENDING. |

**Test Steps:**

| Step | Action | Expected Result |
|---|---|---|
| 1 | Confirm the incomplete step: `SELECT step_number, status FROM batch_record_steps WHERE batch_record_id = '[br_uuid]' ORDER BY step_number` | Steps 1, 2, 4, 5 = COMPLETE. Step 3 = PENDING. |
| 2 | Attempt to release the batch record: POST `/api/v1/mes/batch-records/[br_uuid]/transitions` with target_state = RELEASED | HTTP 422 returned. Error: "Cannot release batch record: Step 3 (Mixing) is not complete. All steps must be COMPLETE or SKIPPED before release." |
| 3 | Verify the batch record status remains IN_PROGRESS | status = IN_PROGRESS |
| 4 | Complete Step 3: POST step 3 entry with status = COMPLETE | Step 3 status = COMPLETE |
| 5 | Reattempt release (without e-signature to test completeness check independently) | HTTP 422 returned — now fails only on the missing dual e-signature, not on step completeness. Error message refers to e-signature requirement, not incomplete steps. |
| 6 | Verify no PENDING steps remain: `SELECT COUNT(*) FROM batch_record_steps WHERE batch_record_id = '[br_uuid]' AND status = 'PENDING'` | COUNT = 0 |

**Expected Result:** Release is blocked while any step is PENDING. Once all steps are COMPLETE, the completeness validation passes and the next blocker (e-signature) is correctly identified.

**Actual Result:**

_______________________________________________________________________________

_______________________________________________________________________________

**Pass / Fail:** ________ **Tester:** ___________________________ **Date:** _______________

**Comments:**

_______________________________________________________________________________

---

### TC-OQ-MES-008: Batch Release Requires Dual E-Signature (Operator + QA)

| Field | Detail |
|---|---|
| Test Case ID | TC-OQ-MES-008 |
| Test Objective | Verify that releasing a Batch Record to RELEASED status requires two distinct electronic signatures: one from the Production Operator role and one from the QA Batch Reviewer role, and that both signatures must come from different users |
| URS Reference | URS-003-BR-006, 21 CFR 11.50, 21 CFR 211.68 |
| Risk Level | Critical |
| Prerequisites | A Batch Record with all steps COMPLETE and a valid yield. No signatures have been applied. |

**Test Steps:**

| Step | Action | Expected Result |
|---|---|---|
| 1 | Attempt release with no e-signatures at all | HTTP 422. Error: "Batch release requires an Operator signature and a QA signature." |
| 2 | Provide only the Operator e-signature (correct password): POST release with operator_signature payload only | HTTP 422. Error: "QA signature is required to complete batch release." Batch record not released. |
| 3 | Attempt to provide both signatures from the same user (using the same user's credentials for both the Operator and QA signatures): POST release with both signature payloads using the same user | HTTP 422. Error: "Operator signature and QA signature must be from different users." |
| 4 | Provide both signatures from different users: Operator = `operator.oq008@gmpplatform.local`, QA = `qa.reviewer.oq008@gmpplatform.local` | HTTP 200 OK. Batch Record status = RELEASED. |
| 5 | Verify two e-signature records: `SELECT signer_user_id, meaning, role FROM esignatures WHERE record_id = '[br_uuid]' ORDER BY signed_at` | Two records returned: one with meaning = "Produced by Operator", one with meaning = "Released by QA". Different signer_user_ids. |
| 6 | Verify the batch record has RELEASED status and a released_at timestamp in the database | status = RELEASED, released_at is a non-null UTC timestamp |

**Expected Result:** Dual signature from two different users (Operator and QA) is enforced. Single-user dual-signing is blocked. Released status and both e-signature records are correctly stored.

**Actual Result:**

_______________________________________________________________________________

_______________________________________________________________________________

**Pass / Fail:** ________ **Tester:** ___________________________ **Date:** _______________

**Comments:**

_______________________________________________________________________________

---

### TC-OQ-MES-009: Work Order Quantity Decremented on Batch Completion

| Field | Detail |
|---|---|
| Test Case ID | TC-OQ-MES-009 |
| Test Objective | Verify that when a Batch Record is released, the Work Order's fulfilled_quantity is incremented by the batch's actual yield, and the Work Order's remaining_quantity is correspondingly decremented |
| URS Reference | URS-003-WO-001 |
| Risk Level | High |
| Prerequisites | A Work Order (WO-OQ-009) exists with planned_quantity = 200 kg and fulfilled_quantity = 0. A released Batch Record from TC-OQ-MES-008 has actual_yield_kg = 95. |

**Test Steps:**

| Step | Action | Expected Result |
|---|---|---|
| 1 | Query the Work Order before batch release: `SELECT planned_quantity, fulfilled_quantity, remaining_quantity FROM work_orders WHERE id = '[wo_uuid]'` | planned_quantity = 200, fulfilled_quantity = 0, remaining_quantity = 200 |
| 2 | Confirm the released Batch Record is linked to WO-OQ-009: `SELECT work_order_id, actual_yield_kg, status FROM batch_records WHERE id = '[br_uuid]'` | work_order_id = [wo_uuid], actual_yield_kg = 95, status = RELEASED |
| 3 | Query the Work Order after batch release | fulfilled_quantity = 95, remaining_quantity = 105 (200 - 95) |
| 4 | Release a second Batch Record against the same Work Order with actual_yield_kg = 100 | Second batch released |
| 5 | Query the Work Order again | fulfilled_quantity = 195, remaining_quantity = 5 |
| 6 | Verify the Work Order status when remaining_quantity is fulfilled: release a third batch with actual_yield_kg = 5 | fulfilled_quantity = 200, remaining_quantity = 0. Work Order status transitions to FULFILLED automatically. |

**Expected Result:** The Work Order fulfilled_quantity is incremented by each batch's actual yield. remaining_quantity decrements correspondingly. The Work Order closes when fully fulfilled.

**Actual Result:**

_______________________________________________________________________________

_______________________________________________________________________________

**Pass / Fail:** ________ **Tester:** ___________________________ **Date:** _______________

**Comments:**

_______________________________________________________________________________

---

### TC-OQ-MES-010: Material Lot Dispensed Against Work Order is Correctly Tracked

| Field | Detail |
|---|---|
| Test Case ID | TC-OQ-MES-010 |
| Test Objective | Verify that when a material lot is dispensed against a Batch Record, the dispensed quantity is recorded against the specific material lot and the lot's remaining balance is correctly decremented |
| URS Reference | URS-003-MAT-001, 21 CFR 211.101(c) |
| Risk Level | Critical |
| Prerequisites | Material Lot (LOT-API-001) exists with material = "Active Pharmaceutical Ingredient", available_quantity = 500 kg. A Batch Record in IN_PROGRESS status requires 80 kg of this API. |

**Test Steps:**

| Step | Action | Expected Result |
|---|---|---|
| 1 | Query material lot before dispensing: `SELECT material_code, available_quantity FROM material_lots WHERE lot_number = 'LOT-API-001'` | available_quantity = 500.0 kg |
| 2 | Record a dispensing event: POST `/api/v1/mes/batch-records/[br_uuid]/dispensing` with body `{"material_lot_id": "[lot_uuid]", "dispensed_quantity_kg": 80, "dispense_step_number": 1}` | HTTP 201 Created. Dispensing record created with UUID, batch_record_id, material_lot_id, dispensed_quantity_kg = 80, dispensed_at timestamp, dispensed_by_user_id. |
| 3 | Query material lot after dispensing: `SELECT available_quantity FROM material_lots WHERE lot_number = 'LOT-API-001'` | available_quantity = 420.0 kg (500 - 80) |
| 4 | Verify the dispensing record: `SELECT * FROM dispensing_events WHERE batch_record_id = '[br_uuid]'` | One record with correct material_lot_id, dispensed_quantity_kg = 80, and operator attribution |
| 5 | Verify audit log captures the dispensing event | Audit event DISPENSING_RECORDED with batch_record_id, lot_number, quantity, actor |
| 6 | Query to confirm bidirectional traceability: which batches used LOT-API-001? `SELECT batch_number FROM batch_records br JOIN dispensing_events de ON de.batch_record_id = br.id WHERE de.material_lot_id = '[lot_uuid]'` | The current batch number is returned in the query results |

**Expected Result:** Dispensing event is created with operator attribution and timestamp. Material lot available quantity is decremented. Full traceability exists in both directions.

**Actual Result:**

_______________________________________________________________________________

_______________________________________________________________________________

**Pass / Fail:** ________ **Tester:** ___________________________ **Date:** _______________

**Comments:**

_______________________________________________________________________________

---

### TC-OQ-MES-011: Batch Record Audit Trail Captures Every Step Entry with Timestamp

| Field | Detail |
|---|---|
| Test Case ID | TC-OQ-MES-011 |
| Test Objective | Verify that every step entry action on a Batch Record generates a corresponding audit log event capturing the step number, the entered values, the timestamp, and the operator identity |
| URS Reference | URS-003-AUDIT-001, 21 CFR 211.68(b), 21 CFR Part 11 |
| Risk Level | Critical |
| Prerequisites | A Batch Record in IN_PROGRESS status. Operator is authenticated. |

**Test Steps:**

| Step | Action | Expected Result |
|---|---|---|
| 1 | Execute Step 1 with actual_value = null and comments = "Step completed as per instructions" | HTTP 200 OK |
| 2 | Execute Step 2 with actual_value = "2.5 bar" and comments = "Pressure held within specification" | HTTP 200 OK |
| 3 | Execute Step 3 (critical) with actual_value = 72 (in range) | HTTP 200 OK |
| 4 | Query the audit log for all step entry events for this batch record: `SELECT event_type, record_id, new_values, actor_user_id, created_at FROM audit_events WHERE record_type = 'BATCH_RECORD_STEP' AND record_id IN (SELECT id FROM batch_record_steps WHERE batch_record_id = '[br_uuid]') ORDER BY created_at` | Three audit events returned, one per step entry. Each contains: step_number in new_values, performed_by_user_id, performed_at (UTC timestamp), the entered value |
| 5 | Verify that modifying a previously entered step value (if permitted by the system) generates a new RECORD_UPDATE audit event with the old and new values | If step value correction is allowed: audit event with old_values.actual_value and new_values.actual_value. If not allowed: the system returns HTTP 422 indicating the step cannot be re-entered. Either behaviour is acceptable provided it is consistent with URS-003. |
| 6 | Verify no audit events can be deleted for step entries | DELETE `/api/v1/audit/events/[step_audit_event_id]` returns HTTP 403 or 405 |

**Expected Result:** Every step entry generates a complete audit event with operator identity, timestamp, and data values. The audit trail is immutable.

**Actual Result:**

_______________________________________________________________________________

_______________________________________________________________________________

**Pass / Fail:** ________ **Tester:** ___________________________ **Date:** _______________

**Comments:**

_______________________________________________________________________________

---

### TC-OQ-MES-012: MBR Version Locked on Batch Record Creation — Cannot Change Mid-Batch

| Field | Detail |
|---|---|
| Test Case ID | TC-OQ-MES-012 |
| Test Objective | Verify that the MBR version referenced by a Batch Record is immutably locked at the time of Batch Record creation, and that a subsequent new version of the MBR does not affect an in-progress Batch Record |
| URS Reference | URS-003-MBR-003, 21 CFR 211.186(a) |
| Risk Level | Critical |
| Prerequisites | An APPROVED MBR at version 1 exists. A Batch Record has been created from it and is IN_PROGRESS. |

**Test Steps:**

| Step | Action | Expected Result |
|---|---|---|
| 1 | Note the MBR version referenced by the Batch Record: `SELECT mbr_version_number FROM batch_records WHERE id = '[br_uuid]'` | mbr_version_number = 1 |
| 2 | Create a new version (version 2) of the MBR and approve it | New MBR version 2 created and APPROVED. MBR version 1 is now SUPERSEDED. |
| 3 | Query the Batch Record's referenced MBR version again | mbr_version_number still = 1 (unchanged despite MBR version 2 being approved) |
| 4 | Query the Batch Record's step definitions | Steps still reflect the original MBR version 1 definitions, not version 2 |
| 5 | Attempt to update the Batch Record to reference MBR version 2: PATCH `/api/v1/mes/batch-records/[br_uuid]` with `{"mbr_version_number": 2}` | HTTP 422 or HTTP 403 returned. Error: "The MBR version of an in-progress Batch Record cannot be changed." |
| 6 | Verify the batch record mbr_version_number is still 1 after the failed update attempt | mbr_version_number = 1 |

**Expected Result:** The MBR version is locked on the Batch Record at creation. Subsequent MBR version changes do not affect in-progress batches. Manual override is blocked.

**Actual Result:**

_______________________________________________________________________________

_______________________________________________________________________________

**Pass / Fail:** ________ **Tester:** ___________________________ **Date:** _______________

**Comments:**

_______________________________________________________________________________

---

### TC-OQ-MES-013: Rejected Batch Cannot Be Changed to Released

| Field | Detail |
|---|---|
| TestCase ID | TC-OQ-MES-013 |
| Test Objective | Verify that a Batch Record that has been set to REJECTED status cannot be transitioned to RELEASED status, and that the rejected state is terminal |
| URS Reference | URS-003-BR-007, 21 CFR 211.192 |
| Risk Level | Critical |
| Prerequisites | A Batch Record exists in REJECTED status (it was rejected by QA during review). |

**Test Steps:**

| Step | Action | Expected Result |
|---|---|---|
| 1 | Confirm the batch record status: `SELECT status FROM batch_records WHERE id = '[br_uuid]'` | status = REJECTED |
| 2 | Attempt to transition to RELEASED: POST `/api/v1/mes/batch-records/[br_uuid]/transitions` with target_state = RELEASED | HTTP 422 returned. Error: "Invalid transition: REJECTED → RELEASED is not permitted. Rejected batches cannot be released." |
| 3 | Attempt to transition to IN_PROGRESS: target_state = IN_PROGRESS | HTTP 422 returned. Error: invalid transition from REJECTED |
| 4 | Attempt to transition to APPROVED: target_state = APPROVED | HTTP 422 returned |
| 5 | Verify the batch record status remains REJECTED after all failed transition attempts | status = REJECTED |
| 6 | Verify the audit log records all failed transition attempts | Audit events of type TRANSITION_FAILED recorded for each attempt |

**Expected Result:** REJECTED is a terminal state for Batch Records. All transitions from REJECTED are blocked. The audit trail records all failed attempts.

**Actual Result:**

_______________________________________________________________________________

_______________________________________________________________________________

**Pass / Fail:** ________ **Tester:** ___________________________ **Date:** _______________

**Comments:**

_______________________________________________________________________________

---

### TC-OQ-MES-014: Batch Number Unique Per Organisation

| Field | Detail |
|---|---|
| Test Case ID | TC-OQ-MES-014 |
| Test Objective | Verify that the system enforces uniqueness of batch numbers within an organisation and rejects attempts to create a Batch Record with a batch number that already exists for that organisation |
| URS Reference | URS-003-BR-008, 21 CFR 211.188 |
| Risk Level | High |
| Prerequisites | A Batch Record with batch_number = "BN-OQ-014-001" already exists in the system for Organisation ID = org-001. |

**Test Steps:**

| Step | Action | Expected Result |
|---|---|---|
| 1 | Confirm the existing batch record: `SELECT batch_number, organisation_id FROM batch_records WHERE batch_number = 'BN-OQ-014-001' AND organisation_id = 'org-001'` | One record is returned |
| 2 | Attempt to create a new Batch Record with the same batch_number = "BN-OQ-014-001" for org-001 | HTTP 409 Conflict. Error: "Batch number BN-OQ-014-001 already exists for this organisation." |
| 3 | Attempt to create the same batch number for a different organisation (org-002) | HTTP 201 Created. The batch number is unique within org-001 but may exist in org-002. (Cross-organisation uniqueness is not required.) |
| 4 | Create a Batch Record with a different batch number "BN-OQ-014-002" for org-001 | HTTP 201 Created. Unique batch number accepted. |
| 5 | Verify the database constraint: attempt a direct SQL INSERT with a duplicate batch_number and organisation_id | PostgreSQL unique constraint violation error returned |

**Expected Result:** Duplicate batch numbers within the same organisation are rejected at the API and database constraint levels. The same batch number can exist in different organisations.

**Actual Result:**

_______________________________________________________________________________

_______________________________________________________________________________

**Pass / Fail:** ________ **Tester:** ___________________________ **Date:** _______________

**Comments:**

_______________________________________________________________________________

---

### TC-OQ-MES-015: Dispensed Quantity Cannot Exceed Required Quantity by More Than 5% Tolerance

| Field | Detail |
|---|---|
| Test Case ID | TC-OQ-MES-015 |
| Test Objective | Verify that the system enforces a tolerance of ±5% on dispensed quantities relative to the BOM-specified required quantity, and rejects dispensing events that exceed the upper tolerance limit |
| URS Reference | URS-003-MAT-002, 21 CFR 211.101(c) |
| Risk Level | Critical |
| Prerequisites | A Batch Record references an MBR that specifies: Material = "Excipient-A", required_quantity_kg = 50. A material lot with sufficient available quantity exists. |

**Test Steps:**

| Step | Action | Expected Result |
|---|---|---|
| 1 | Calculate the tolerance limits: Lower = 50 × 0.95 = 47.5 kg. Upper = 50 × 1.05 = 52.5 kg. Document these values. | Lower limit = 47.5 kg, Upper limit = 52.5 kg |
| 2 | Attempt to dispense 52.5 kg (at the exact upper limit) | HTTP 201 Created. Dispensing accepted — within tolerance. |
| 3 | Attempt to dispense an additional 0.1 kg (taking the total over 52.5 kg) | HTTP 422 returned. Error: "Total dispensed quantity (52.6 kg) exceeds the maximum allowable quantity (52.5 kg = 50 kg + 5% tolerance). Dispensing rejected." |
| 4 | Attempt to dispense 47.5 kg (exact lower limit) | HTTP 201 Created. Accepted. (Under-dispensing is allowed at the lower bound; the batch cannot be released until the required minimum is met.) |
| 5 | Attempt to dispense 47.4 kg as the only dispensing event (below lower tolerance) and attempt batch release | Batch release blocked: dispensed quantity (47.4 kg) is below the minimum required (47.5 kg). Error message references the under-dispensing. |
| 6 | Verify an over-tolerance dispensing event generates a QA alert notification | In-app notification sent to QA Batch Reviewer when any over-tolerance attempt is made (even if rejected) |

**Expected Result:** Dispensing quantities are validated against the BOM requirement ±5%. Over-tolerance dispensing is rejected. The system enforces this at every dispensing event, not just at release.

**Actual Result:**

_______________________________________________________________________________

_______________________________________________________________________________

**Pass / Fail:** ________ **Tester:** ___________________________ **Date:** _______________

**Comments:**

_______________________________________________________________________________

---

### TC-OQ-MES-016: MBR Version History is Retrievable and Complete

| Field | Detail |
|---|---|
| Test Case ID | TC-OQ-MES-016 |
| Test Objective | Verify that the full version history of a Master Batch Record is retrievable, including all prior versions in SUPERSEDED status, and that each version's content is preserved and independently accessible |
| URS Reference | URS-003-MBR-004 |
| Risk Level | Medium |
| Prerequisites | An MBR family exists with three versions: v1 (SUPERSEDED), v2 (SUPERSEDED), v3 (APPROVED). All three were created during earlier test execution. |

**Test Steps:**

| Step | Action | Expected Result |
|---|---|---|
| 1 | Retrieve the MBR version history: GET `/api/v1/mes/mbrs/[mbr_family_id]/versions` | Three versions returned: v1 (SUPERSEDED), v2 (SUPERSEDED), v3 (APPROVED). Each with its UUID, version_number, status, created_at, and approved_at (if applicable). |
| 2 | Retrieve the content of version 1: GET `/api/v1/mes/mbrs/[mbr_v1_uuid]` | Version 1 content returned including all original steps. Steps from v1 may differ from v3. |
| 3 | Retrieve the content of version 3: GET `/api/v1/mes/mbrs/[mbr_v3_uuid]` | Version 3 content returned with its current step definitions |
| 4 | Verify that the content of v1 and v3 can differ (e.g., different step counts or instructions) | The responses are compared and any differences are document. Version history preserves each version independently. |
| 5 | Verify that a SUPERSEDED MBR cannot be used to create a new Batch Record | Attempt to create a Batch Record with mbr_id = [mbr_v1_uuid] (SUPERSEDED): HTTP 422 returned. Error: "MBR version 1 is SUPERSEDED and cannot be used for batch execution." |

**Expected Result:** Full version history is retrievable. Each version's content is independently accessible and preserved. Superseded versions cannot be used for new batch execution.

**Actual Result:**

_______________________________________________________________________________

_______________________________________________________________________________

**Pass / Fail:** ________ **Tester:** ___________________________ **Date:** _______________

**Comments:**

_______________________________________________________________________________

---

## 6. Acceptance Criteria

| Criterion | Requirement |
|---|---|
| AC-001 | All 16 test cases (TC-OQ-MES-001 through TC-OQ-MES-016) have been executed and recorded with a result of PASS |
| AC-002 | All Actual Results fields are completed contemporaneously |
| AC-003 | All tester signatures and dates are present for each test case |
| AC-004 | All deviations are documented with Deviation IDs |
| AC-005 | All deviations are resolved or formally risk-accepted before OQ approval |
| AC-006 | The protocol is reviewed and approved per Section 8 |

**Overall OQ Outcome:** PASS / FAIL / CONDITIONAL PASS (circle one)

**Summary of Outcome:**

_______________________________________________________________________________

_______________________________________________________________________________

---

## 7. Deviation Handling

### 7.1 Definition

A deviation is any departure from the expected result defined in a test case, including unexpected system behaviour, an error response different from expected, inability to execute a step as written, or an unmet prerequisite.

### 7.2 Deviation Procedure

1. Stop execution of the affected test case immediately.
2. Record FAIL or DEVIATION in the Pass/Fail field.
3. Document the observed behaviour fully in the Comments field.
4. Raise a formal Deviation Record in the log below.
5. Assess impact before proceeding to the next test case.

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

*End of OQ-003 Operational Qualification — MES Module*

*Document ID: OQ-003 | Version: 01 | GMP Platform | 2026-04-21*
