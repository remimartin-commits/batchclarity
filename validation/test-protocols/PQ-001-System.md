# PQ-001 Performance Qualification — Full System

---

| Field | Value |
|---|---|
| Document ID | PQ-001 |
| Title | Performance Qualification — Full System |
| Version | 01 |
| Status | DRAFT |
| Date | 2026-04-21 |
| System | GMP Platform |
| Modules | All: QMS, MES, Equipment, Training, LIMS, Environmental Monitoring |
| Author | [Author Name] |
| Reviewer | [Reviewer Name] |
| Approver | [Approver Name] |

---

## Table of Contents

1. Purpose
2. Scope
3. References
4. Definitions and Abbreviations
5. Prerequisites
6. Test Approach
7. End-to-End Scenarios
8. Performance Criteria
9. Acceptance Criteria
10. Deviation Handling
11. Signature Page

---

## 1. Purpose

This Performance Qualification (PQ) protocol establishes documented evidence that the GMP Platform performs as intended under conditions simulating actual GMP use across all integrated modules. The PQ demonstrates that the system functions correctly when individual modules interact — data flows between modules, cross-module workflows complete end-to-end, and the system maintains data integrity, audit trail completeness, and regulatory compliance across the full operational lifecycle of pharmaceutical manufacturing and quality management activities.

The PQ is the final validation phase before the GMP Platform is released for use in a regulated (GMP) environment. It builds upon the Installation Qualification (IQ-001) and all Operational Qualifications (OQ-001 through OQ-006). Passing this PQ is a prerequisite for system go-live.

All scenarios in this protocol are executed using realistic pharmaceutical data and workflows that simulate the actual day-to-day activities of the target user organisation.

---

## 2. Scope

This PQ covers the following modules and their interactions:

| Module | Functions Exercised in PQ |
|---|---|
| Foundation Layer | Authentication, RBAC, audit trail, e-signatures, workflow engine, notifications |
| QMS — CAPA | CAPA creation, investigation, implementation, effectiveness check, closure |
| QMS — Deviation | Deviation raise, classification, investigation, linkage to CAPA |
| QMS — Change Control | Change request, risk assessment, approval, implementation |
| QMS — Risk Management | RPN calculation, CAPA linkage, approval |
| QMS — Supplier Management | Supplier audit, finding, corrective action, re-approval |
| MES | MBR approval, batch execution, material dispensing, yield, dual-sig release |
| Equipment | Equipment qualification, calibration schedule, out-of-calibration event |
| Training | SOP assignment, operator training completion, training record |
| LIMS | Sample receipt, testing, OOS investigation, result approval, CoA generation |
| Environmental Monitoring | Sampling plan, result entry, OOT detection, investigation |
| Stability | Stability study scheduling, T=12m result entry, OOS investigation |
| Audit Trail (cross-module) | End-to-end batch traceability for a regulatory inspection scenario |

**Out of Scope:** System infrastructure performance benchmarking (covered separately in a Load Test Report). Disaster recovery and backup/restore testing (covered in IT Qualification).

---

## 3. References

| Reference ID | Document Title |
|---|---|
| URS-001 through URS-007 | User Requirements Specifications — All Modules |
| IQ-001 | Installation Qualification — Foundation Layer |
| OQ-001 | Operational Qualification — Foundation Layer |
| OQ-002 | Operational Qualification — QMS Module |
| OQ-003 | Operational Qualification — MES Module |
| OQ-004 | Operational Qualification — Equipment Module |
| OQ-005 | Operational Qualification — Training Module |
| OQ-006 | Operational Qualification — LIMS and Environmental Monitoring Module |
| GMP-PLT-QMP-001 | Quality Management Plan — GMP Platform |
| RA-001 through RA-007 | Risk Assessments — All Modules |
| 21 CFR Part 11 | Electronic Records; Electronic Signatures |
| 21 CFR Part 211 | Current Good Manufacturing Practice for Finished Pharmaceuticals |
| 21 CFR Part 820 | Quality System Regulation |
| EU GMP Annex 11 | Computerised Systems (EMA, 2011) |
| EU GMP Annex 15 | Qualification and Validation |
| ICH Q9 | Quality Risk Management |
| ICH Q10 | Pharmaceutical Quality System |
| GAMP 5 | A Risk-Based Approach to Compliant GxP Computerised Systems (ISPE, 2022) |

---

## 4. Definitions and Abbreviations

| Term / Abbreviation | Definition |
|---|---|
| API | Application Programming Interface |
| BR | Batch Record |
| CAPA | Corrective and Preventive Action |
| CC | Change Control |
| CoA | Certificate of Analysis |
| EM | Environmental Monitoring |
| GMP | Good Manufacturing Practice |
| IQ | Installation Qualification |
| LIMS | Laboratory Information Management System |
| MBR | Master Batch Record |
| MES | Manufacturing Execution System |
| OOS | Out of Specification |
| OOT | Out of Trend |
| OQ | Operational Qualification |
| PQ | Performance Qualification |
| QA | Quality Assurance |
| QMS | Quality Management System |
| RBAC | Role-Based Access Control |
| RPN | Risk Priority Number |
| SOP | Standard Operating Procedure |
| URS | User Requirements Specification |
| UTC | Coordinated Universal Time |

---

## 5. Prerequisites

All prerequisites must be verified and documented before PQ execution begins. The PQ must not start until all OQs have been approved.

| Prereq ID | Prerequisite | Verified By | Date | Initials |
|---|---|---|---|---|
| PRE-001 | OQ-001 (Foundation Layer) is approved; all test cases PASSED | | | |
| PRE-002 | OQ-002 (QMS Module) is approved; all test cases PASSED | | | |
| PRE-003 | OQ-003 (MES Module) is approved; all test cases PASSED | | | |
| PRE-004 | OQ-004 (Equipment Module) is approved; all test cases PASSED | | | |
| PRE-005 | OQ-005 (Training Module) is approved; all test cases PASSED | | | |
| PRE-006 | OQ-006 (LIMS and EM Module) is approved; all test cases PASSED | | | |
| PRE-007 | PQ test environment has been freshly provisioned from IQ-verified build artefacts. The environment is confirmed to be isolated from production. | | | |
| PRE-008 | PQ Master Data has been loaded: products, materials, equipment, users, roles, SOPs, suppliers, stability study plans (see Appendix A — PQ Master Data Set) | | | |
| PRE-009 | All users required for PQ scenarios (see Appendix B — PQ User Accounts) are created and their roles are verified | | | |
| PRE-010 | The system's date/time is synchronised to an accurate NTP source. The current UTC time has been verified and documented. | | | |
| PRE-011 | A stopwatch or timing mechanism is available for response-time measurements in Section 8 | | | |
| PRE-012 | The test email/notification server is operational | | | |
| PRE-013 | Tester(s) have read this protocol in full and hold GMP documentation training | | | |

**System Version Under Test:** ___________________________

**Test Environment URL:** ___________________________

**PQ Execution Start Date/Time (UTC):** ___________________________

**Prerequisites Verified By:** ___________________________ Date: _______________

---

## 6. Test Approach

### 6.1 Scenario-Based Testing

Unlike the OQ (which tests individual functions in isolation), the PQ uses integrated end-to-end scenarios. Each scenario is a complete workflow that spans multiple modules, mimicking realistic pharmaceutical operations.

Testers execute the scenarios in the order presented. Some scenarios share artefacts (e.g., a batch record created in Scenario 1 is traced in Scenario 8). This is intentional — it tests that thesystem maintains referential integrity and audit trail continuity across the full lifecycle.

### 6.2 Data

PQ Master Data (Appendix A) must be loaded before execution begins. All data used is fictional but realistic: product names, lot numbers, and quantities are formatted as they would appear in real GMP use.

### 6.3 Execution Records

For each scenario step:
- Record the action taken and the exact system response observed.
- Note timestamps for any steps subject to performance criteria (Section 8).
- Capture screenshots or API response bodies as objective evidence where indicated.
- Any unexpected behaviour must be raised as a deviation immediately.

### 6.4 Evidence Collection

Objective evidence for each scenario must be retained:
- Screenshots of key screens (saved as: `PQ-001_Scenario[N]_Step[N]_[description].png`)
- API response JSON bodies (saved as: `PQ-001_Scenario[N]_Step[N]_api_response.json`)
- Database query results (copy-pasted into the protocol or an attached evidence document)

---

## 7. End-to-End Scenarios

---

### SCENARIO 1: New Product Introduction

**Scenario Title:** New Product Introduction — MBR to Batch Execution to LIMS Release to CoA

**Objective:** Demonstrate that introducing a new pharmaceutical product follows a controlled, fully documented process: the Master Batch Record is created and change-controlled, the first batch is executed against it, LIMS testing is completed and approved, and a Certificate of Analysis is generated.

**Modules Exercised:** Change Control (QMS), MBR (MES), Batch Record (MES), LIMS, CoA

**Personnel Required:** MBR Author, QA Manager, Production Operator, QA Batch Reviewer, LIMS Analyst, QA Lab Approver

---

#### Step 1.1 — Raise Change Control for New Product Introduction

| Field | Detail |
|---|---|
| Actor | QA Manager |
| Action | Create a Change Control record: Title = "Introduction of Product VERAPLEX-100 to manufacturing site", change_type = MAJOR,risk_description = "First-time manufacturing introduces risk of yield deviation and cross-contamination", risk_mitigation = "Dedicated equipment cleaning validated, operator training completed", risk_level = HIGH |
| Expected Result | Change Control record created in DRAFT status with CC number (e.g., CC-2026-0001). All risk fields are populated. |
| Actual Result | |
| Pass/Fail | |
| Tester/Date | |

#### Step 1.2 — Approve Change Control

| Field | Detail |
|---|---|
| Actor | QA Manager (Change Control Approver role) |
| Action | Advance the Change Control through the workflow: DRAFT → IN_REVIEW → APPROVED, providing e-signature at the approval step with meaning = "Change Approved" |
| Expected Result | Change Control status = APPROVED. E-signature record created. implementation_date set to a date ≥ approval_date. Audit trail records each state transition. |
| Actual Result | |
| Pass/Fail | |
| Tester/Date | |

#### Step 1.3 — Create and Approve Master Batch Record

| Field | Detail |
|---|---|
| Actor | MBR Author, then QA Manager |
| Action | Create an MBR for VERAPLEX-100: batch_size_kg = 200, yield_lower_limit = 92%, yield_upper_limit = 108%. Add 7 manufacturing steps. Step 4 is critical: "API Addition Temperature", lower = 55°C, upper = 75°C. Link the MBR to CC-2026-0001 via the document linkage function. Advance the MBR to APPROVED with e-signature. |
| Expected Result | MBR created (MBR-VER-001, version 1), status = APPROVED. MBR is linked to CC-2026-0001. E-signature captured. Change Control document list includes this MBR. |
| Actual Result | |
| Pass/Fail | |
| Tester/Date | |

#### Step 1.4 — Create Batch Record and Execute Manufacturing Steps

| Field | Detail |
|---|---|
| Actor | Production Operator |
| Action | Create a Batch Record from the approved MBR: batch_number = "VER-2026-B001", Work Order = WO-2026-001 (planned quantity 200 kg). Execute all 7 steps, entering values for each. For Step 4, enter actual_value = 65°C (within range). Enter actual_yield_kg = 189. |
| Expected Result | Batch Record created in IN_PROGRESS status. All 7 steps inherited from MBR v1. Step 4 critical parameter: actual_value = 65, critical_parameter_status = IN_RANGE. Yield = 189/200 = 94.5% — within 92–108% limits. yield_status = WITHIN_LIMITS. All steps status = COMPLETE. |
| Actual Result | |
| Pass/Fail | |
| Tester/Date | |

#### Step 1.5 — Dual E-Signature Release of Batch Record

| Field | Detail |
|---|---|
| Actor | Production Operator + QA Batch Reviewer |
| Action | Release the Batch Record using dual e-signature: Operator signs with meaning = "Manufactured by Operator", QA signs with meaning = "Released by QA" |
| Expected Result | Batch Record status = RELEASED. Two e-signature records present. released_at timestamp recorded in UTC. Work Order fulfilled_quantity incremented by 189 kg. |
| Actual Result | |
| Pass/Fail | |
| Tester/Date | |

#### Step 1.6 — Submit Samples to LIMS and Enter Test Results

| Field | Detail |
|---|---|
| Actor | LIMS Analyst |
| Action | Create a LIMS sample submission linked to batch VER-2026-B001. Enter test results for: Assay = 99.8% (specification 98.0–102.0%), Related Substances Total = 0.12% (limit ≤ 0.20%), Dissolution = 98% (limit ≥ 85%). All results are within specification. |
| Expected Result | LIMS sample record created and linked to the batch record. All three results entered. All results are flagged as WITHIN_SPEC. |
| Actual Result | |
| Pass/Fail | |
| Tester/Date | |

#### Step 1.7 — Approve Test Results and Generate CoA

| Field | Detail |
|---|---|
| Actor | QA Lab Approver |
| Action | Review and approve the LIMS results with e-signature (meaning = "Test Results Approved"). Generate the Certificate of Analysis for batch VER-2026-B001. |
| Expected Result | Results status = APPROVED. CoA generated as a PDF document containing: batch number, product name, product code, manufacturing date, expiry date, all test results with specifications, QA approver name, e-signature reference, and approval date. CoA document stored in the system and retrievable. |
| Actual Result | |
| Pass/Fail | |
| Tester/Date | |

#### Step 1.8 — Verify End-to-End Linkage

| Field | Detail |
|---|---|
| Actor | QA Manager |
| Action | From the Batch Record VER-2026-B001, verify the following links are all navigable: (a) CC-2026-0001 (Change Control), (b) MBR-VER-001 v1 (Master Batch Record), (c) LIMS Sample and test results, (d) CoA document |
| Expected Result | All four linked objects are accessible from the Batch Record detail page. Each link resolves to the correct record. The complete product introduction trail is viewable in a single audit trail query. |
| Actual Result | |
| Pass/Fail | |
| Tester/Date | |

**Scenario 1 Outcome:** PASS / FAIL / DEVIATION

**Tester:** ___________________________ **Date:** _______________

---

### SCENARIO 2: Deviation to CAPA to Effectiveness Check

**Scenario Title:** Deviation on Batch → Investigation → CAPA → Implementation → Effectiveness Verification → Closure

**Objective:** Demonstrate that a manufacturing deviation is raised, classified, investigated, linked to a CAPA, the CAPA is implemented, and the system enforces the effectiveness check workflow before closure.

**Modules Exercised:** Deviation (QMS), CAPA (QMS), MES (batch reference), Notifications

**Personnel Required:** Production Operator, QA Investigator, QA Manager

---

#### Step 2.1 — Raise a Manufacturing Deviation

| Field | Detail |
|---|---|
| Actor | Production Operator |
| Action | Raise a Deviation during execution of a batch: Title = "Temperature excursion during API addition step, Batch VER-2026-B002", classification = MAJOR, description = "API addition temperature recorded at 81°C, exceeding upper limit of 75°C by 6°C for approximately 3 minutes. Operator error — temperature probe alarm acknowledged late.", linked_batch_record_id = [ID of a batch in the test environment], detection_date = today |
| Expected Result | Deviation record created (DEV-2026-0001), status = DRAFT. Classification = MAJOR. Batch record is linked. QA Manager receives a MAJOR Deviation notification. |
| Actual Result | |
| Pass/Fail | |
| Tester/Date | |

#### Step 2.2 — Classify and Investigate the Deviation

| Field | Detail |
|---|---|
| Actor | QA Investigator |
| Action | Advance deviation to IN_INVESTIGATION status. Complete the investigation section: root_cause = "Operator did not acknowledge temperature alarm within required 60-second window per SOP-PROD-014. Root cause: SOP training not completed for this operator on the updated version of SOP-PROD-014 (v3)." Immediate action: "Batch quarantined pending impact assessment. Impact on product quality assessed by QA — API bioavailability unaffected based on stability data." |
| Expected Result | Deviation status = IN_INVESTIGATION. Root cause and immediate action fields populated. Audit trail captures all field changes with investigator identity. |
| Actual Result | |
| Pass/Fail | |
| Tester/Date | |

#### Step 2.3 — Create and Link CAPA

| Field | Detail |
|---|---|
| Actor | QA Investigator |
| Action | Create a CAPA linked to DEV-2026-0001: Title = "Prevent recurrence of temperature excursion due to SOP training gaps", root_cause_category = TRAINING, priority = MAJOR, due_date = [90 days from today], assigned_to = QA Training Manager. Corrective action: "Mandatory re-training of all production operators on SOP-PROD-014 v3 within 30 days." Preventive action: "Implement mandatory SOP version training assignment for all future SOP updates before an operator can execute steps requiring that SOP." |
| Expected Result | CAPA created (CAPA-2026-0001), linked to DEV-2026-0001. Deviation record shows the linked CAPA. CAPA shows the linked deviation. |
| Actual Result | |
| Pass/Fail | |
| Tester/Date | |

#### Step 2.4 — Advance Deviation to Closed with CAPA Reference

| Field | Detail |
|---|---|
| Actor | QA Manager |
| Action | Advance thedeviation to CLOSED status, referencing the linked CAPA as the corrective action vehicle. Apply e-signature with meaning = "Deviation Investigated and Closed — CAPA Raised" |
| Expected Result | Deviation status = CLOSED. E-signature captured. Audit trail records closure. CAPA remains open (not affected by deviation closure). |
| Actual Result | |
| Pass/Fail | |
| Tester/Date | |

#### Step 2.5 — Implement CAPA and Advance to Effectiveness Check

| Field | Detail |
|---|---|
| Actor | QA Training Manager |
| Action | Advance the CAPA to APPROVED, then to WORK_IN_PROGRESS. Complete the implementation: enter implementation notes = "All 12 production operators completed SOP-PROD-014 v3 training as evidenced by training records TRN-2026-0045 through TRN-2026-0056. SOP version training assignment automation implemented per IT change ITC-2026-0003." Advance to EFFECTIVENESS_CHECK. |
| Expected Result | CAPA status = EFFECTIVENESS_CHECK. effectiveness_check_due_date = today + 60 days (MAJOR priority). Implementation notes recorded in the CAPA. Audit trail records each state transition. |
| Actual Result | |
| Pass/Fail | |
| Tester/Date | |

#### Step 2.6 — Verify Effectiveness and Close CAPA

| Field | Detail |
|---|---|
| Actor | QA Manager |
| Action | After the effectiveness check period, record the effectiveness outcome: "Review of the 90 days post-implementation shows zero temperature excursion events. SOP training completion rate is 100% for all production operators on all current SOP versions. Automated training assignment triggered correctly for 3 new SOP versions issued in this period. CAPA deemed effective." Advance CAPA to CLOSED with e-signature, meaning = "CAPA Effective and Closed". |
| Expected Result | CAPA status = CLOSED. Effectiveness outcome text is stored. E-signature captured with correct meaning. The full CAPA lifecycle (DRAFT → IN_REVIEW → APPROVED → WORK_IN_PROGRESS → EFFECTIVENESS_CHECK → CLOSED) is visible in the state history. All six states present in audit trail. |
| Actual Result | |
| Pass/Fail | |
| Tester/Date | |

**Scenario 2 Outcome:** PASS / FAIL / DEVIATION

**Tester:** ___________________________ **Date:** _______________

---

### SCENARIO 3: Equipment Qualification → Calibration Due → Out-of-Calibration → Impact Assessment

**Scenario Title:** Equipment Lifecycle — Qualification, Calibration Scheduling, OOC Event, and Impact Assessment

**Objective:** Demonstrate that equipment is qualified, calibration is scheduled and tracked, an out-of-calibration (OOC) event is detected and recorded, and the system triggers a mandatory impact assessment for batches potentially affected by the OOC period.

**Modules Exercised:** Equipment Module, QMS (Deviation/CAPA), MES (affected batch identification), Notifications

**Personnel Required:** Equipment Engineer, QA Manager, Production Supervisor

---

#### Step 3.1 — Create Equipment Record and Set Calibration Schedule

| Field | Detail |
|---|---|
| Actor | Equipment Engineer |
| Action | Create an Equipment record: equipment_id = "EQ-SCALE-001", description = "Precision balance — 200 kg capacity", equipment_type = BALANCE, location = "Production Suite 3", calibration_frequency_days = 90, next_calibration_due = [90 days from today]. Set status = QUALIFIED. |
| Expected Result | Equipment record created with all fields. status = QUALIFIED. next_calibration_due is set. A calibration reminder notification will be scheduled for 14 days before due date. |
| Actual Result | |
| Pass/Fail | |
| Tester/Date | |

#### Step 3.2 — Simulate Calibration Due and Completion

| Field | Detail |
|---|---|
| Actor | Equipment Engineer |
| Action | Manually set next_calibration_due to today (simulating that calibration is now due). Confirm a calibration-due notification is present for the Equipment Engineer and QA Manager. Record a new calibration event: calibration_date = today, calibrated_by = "Calibration Services Ltd", certificate_number = "CERT-CS-2026-1234", result = PASS, next_calibration_due = today + 90 days. |
| Expected Result | Calibration event recorded. Equipment status remains QUALIFIED. next_calibration_due updated to today + 90 days. Notification marked as resolved/read. |
| Actual Result | |
| Pass/Fail | |
| Tester/Date | |

#### Step 3.3 — Record an Out-of-Calibration Event

| Field | Detail |
|---|---|
| Actor | Equipment Engineer |
| Action | Create a new Calibration Event for EQ-SCALE-001 with result = FAIL: calibration_date = today, reason = "Balance found reading 2.3% high across the full measurement range. Calibration certificate suspended by external calibrator." Set equipment status to OUT_OF_CALIBRATION. |
| Expected Result | Calibration event recorded with result = FAIL. Equipment status = OUT_OF_CALIBRATION. Equipment Engineer and QA Manager receive immediate OUT_OF_CALIBRATION alert notification. |
| Actual Result | |
| Pass/Fail | |
| Tester/Date | |

#### Step 3.4 — Impact Assessment for Batches Manufactured During OOC Period

| Field | Detail |
|---|---|
| Actor | QA Manager |
| Action | Query the system for all Batch Records that used EQ-SCALE-001 during the period between the last PASS calibration and the OOC event discovery: GET `/api/v1/equipment/[eq_uuid]/affected-batches?start_date=[last_pass_date]&end_date=[ooc_discovery_date]`. For each affected batch, raise a Deviation linked to the batch and to EQ-SCALE-001. |
| Expected Result | The system returns a list of all batch records where EQ-SCALE-001 was used in the OOC window. Each affected batch is traceable. Deviations are raised referencing each affected batch and the OOC equipment event. |
| Actual Result | |
| Pass/Fail | |
| Tester/Date | |

#### Step 3.5 — Return Equipment to Service

| Field | Detail |
|---|---|
| Actor | Equipment Engineer |
| Action | Record a new calibration: result = PASS, certificate = "CERT-CS-2026-1235". Advance equipment status from OUT_OF_CALIBRATION to QUALIFIED. |
| Expected Result | Equipment status = QUALIFIED. Calibration history shows the sequence: PASS → FAIL → PASS. The OOC period is documented in the audit trail with exact timestamps. |
| Actual Result | |
| Pass/Fail | |
| Tester/Date | |

**Scenario 3 Outcome:** PASS / FAIL / DEVIATION

**Tester:** ___________________________ **Date:** _______________

---

### SCENARIO 4: SOP Revision → Training Assignment → Operator Completion → Batch Execution with New SOP Version

**Scenario Title:** SOP Lifecycle and Training Compliance Before Batch Execution

**Objective:** Demonstrate that when an SOP is revised, training assignments are automatically generated for all affected roles, operators complete training, and the system enforces training completion as a prerequisite for batch execution against the new SOP version.

**Modules Exercised:** Document Management (Foundation), Training Module, MES (Batch Record gating)

**Personnel Required:** QA Document Controller, QA Manager, Production Operator, Training Administrator

---

#### Step 4.1 — Revise SOP and Create New Version

| Field | Detail |
|---|---|
| Actor | QA Document Controller |
| Action | Create a new version of SOP-PROD-014 "API Addition Temperature Control Procedure" — currently at version 3 (APPROVED). Create version 4 in DRAFT: update the instructions to include a new mandatory 60-second temperature equilibration wait before addition. Advance version 4 to APPROVED with e-signature. Confirm version 3 is now SUPERSEDED. |
| Expected Result | SOP-PROD-014 v4 status = APPROVED. v3 status = SUPERSEDED. Only one APPROVED version exists. E-signature with meaning = "Approved for GMP Use" captured. Audit trail records supersession of v3. |
| Actual Result | |
| Pass/Fail | |
| Tester/Date | |

#### Step 4.2 — Automatic Training Assignment on SOP Approval

| Field | Detail |
|---|---|
| Actor | System (automated) / Training Administrator (verify) |
| Action | Upon approval of SOP-PROD-014 v4, the system should automatically assign trainingtasks to all users in the "Production Operator" and "Production Supervisor" roles (per the SOP's configured affected_roles). Verify the training assignments have been created. |
| Expected Result | Training assignment records are created for every user with the Production Operator or Production Supervisor role. Each assignment references SOP-PROD-014 v4. Assignment status = PENDING. Notification sent to each assignee: "New training required: SOP-PROD-014 v4." |
| Actual Result | |
| Pass/Fail | |
| Tester/Date | |

#### Step 4.3 — Operator Completes Training

| Field | Detail |
|---|---|
| Actor | Production Operator (`operator.pq004@gmpplatform.local`) |
| Action | Log in as the operator. Navigate to the training section and view the pending training assignment for SOP-PROD-014 v4. Read the SOP content (rendered inline or linked). Complete the training acknowledgement: e-sign with meaning = "I confirm I have read and understood SOP-PROD-014 Version 4" and complete any associated quiz (if configured). |
| Expected Result | Training record status = COMPLETED. Training record stores: operator user_id, SOP document_id, SOP version 4, completion_date (UTC), e-signature reference. Training assignment status = COMPLETED. |
| Actual Result | |
| Pass/Fail | |
| Tester/Date | |

#### Step 4.4 — Verify Batch Execution is Gated on Training Completion

| Field | Detail |
|---|---|
| Actor | Production Operator |
| Action | Use a test MBR that references SOP-PROD-014 v4 as a required SOP. Attempt to execute a step in a Batch Record as an operator who has NOT yet completed training on v4 (use a second operator account with pending training). |
| Expected Result | The system blocks step entry: HTTP 422 or UI error: "Operator [name] has not completed required training: SOP-PROD-014 v4. Training must be completed before executing this step." The step remains PENDING. |
| Actual Result | |
| Pass/Fail | |
| Tester/Date | |

#### Step 4.5 — Trained Operator Can Execute the Step

| Field | Detail |
|---|---|
| Actor | Production Operator (`operator.pq004@gmpplatform.local` — trained) |
| Action | As the trained operator (training completed in step 4.3), execute the same step in the Batch Record |
| Expected Result | Step executes successfully. Step entry record includes the operator's user_id and the training record reference (or the system confirms training was verified at time of execution). |
| Actual Result | |
| Pass/Fail | |
| Tester/Date | |

**Scenario 4 Outcome:** PASS / FAIL / DEVIATION

**Tester:** ___________________________ **Date:** _______________

---

### SCENARIO 5: Environmental Monitoring OOT → Investigation → Root Cause → CAPA

**Scenario Title:** Environmental Monitoring Out-of-Trend Result Leading to Investigation and CAPA

**Objective:** Demonstrate that an Environmental Monitoring result flagged as Out-of-Trend (OOT) triggers an investigation workflow, root cause is documented, and a CAPA is raised and linked to the EM event.

**Modules Exercised:** Environmental Monitoring Module, QMS (Deviation/CAPA), Notifications

**Personnel Required:** EM Analyst, Microbiologist, QA Manager

---

#### Step 5.1 — Enter Environmental Monitoring Result

| Field | Detail |
|---|---|
| Actor | EM Analyst |
| Action | Record an EM sample result for sampling location "Grade B Filling Room — Sample Point 3": sample_date = today, organism_count_cfu = 8 CFU/m³. The alert limit for Grade B is 5 CFU/m³ and the action limit is 10 CFU/m³. The result of 8 exceeds the alert limit. |
| Expected Result | EM result recorded. result_status = OOT_ALERT (between alert and action limit). Microbiologist and QA Manager receive OOT alert notification. |
| Actual Result | |
| Pass/Fail | |
| Tester/Date | |

#### Step 5.2 — Initiate OOT Investigation

| Field | Detail |
|---|---|
| Actor | Microbiologist |
| Action | From the OOT EM result, initiate an OOT Investigation record. Record initial assessment: "Elevated count observed at Sample Point 3. No concurrent manufacturing. HVAC maintenance performed 2 days prior in adjacent corridor. Organism identification initiated (cultures in progress)." |
| Expected Result | OOT Investigation record created and linked to the EM sample result. Status = IN_INVESTIGATION. Audit trail records the creation. |
| Actual Result | |
| Pass/Fail | |
| Tester/Date | |

#### Step 5.3 — Document Root Cause

| Field | Detail |
|---|---|
| Actor | Microbiologist |
| Action | Update the investigation: organism_identified = "Staphylococcus epidermidis". root_cause = "HVAC filter in corridor maintenance bay was left open for 45 minutes during maintenance, allowing non-classified air ingress. The filter was replaced and the area re-cleaned. Environmental monitoring data for the preceding 6 months reviewed — no previous exceedances at this location." |
| Expected Result | Root cause and organism identification fields populated. Investigation updated in the audit trail. |
| Actual Result | |
| Pass/Fail | |
| Tester/Date | |

#### Step 5.4 — Raise and Link CAPA

| Field | Detail |
|---|---|
| Actor | QA Manager |
| Action | Create a CAPA linked to the OOT investigation: Title = "Prevent HVAC filter ingress during maintenance activities", root_cause_category = FACILITY_MAINTENANCE, priority = MAJOR. Corrective action: "Issue immediate SOP update for HVAC maintenance to require mandatory barrier installation before filter access." Preventive action: "Quarterly HVAC maintenance training review for facilities team." Link the CAPA to the OOT investigation record. |
| Expected Result | CAPA created and linked to the OOT investigation. Investigation record shows linked_capa_id. CAPA shows linked EM investigation reference. |
| Actual Result | |
| Pass/Fail | |
| Tester/Date | |

#### Step 5.5 — Close Investigation

| Field | Detail |
|---|---|
| Actor | QA Manager |
| Action | Close the OOT investigation with e-signature: meaning = "OOT Investigation Closed — CAPA Raised and Implementation Underway". Confirm the EM result's impact_assessment = "Isolated event; no patient risk; no affected batches in filling room on the day of sampling; CAPA raised." |
| Expected Result | Investigation status = CLOSED. E-signature captured. Impact assessment documented. |
| Actual Result | |
| Pass/Fail | |
| Tester/Date | |

**Scenario 5 Outcome:** PASS / FAIL / DEVIATION

**Tester:** ___________________________ **Date:** _______________

---

### SCENARIO 6: Supplier Re-Qualification Audit → Finding → Corrective Action → Re-Approval

**Scenario Title:** Supplier Re-Qualification — Audit Finding to Corrective Action to Re-Approval

**Objective:** Demonstrate the complete supplier re-qualification workflow: a re-qualification audit is conducted, a finding is recorded, the supplier responds with a corrective action, and the supplier is re-approved only after the corrective action is verified.

**Modules Exercised:** Supplier Management (QMS), CAPA (QMS), Notifications

**Personnel Required:** Supplier Quality Manager, QA Manager

---

#### Step 6.1 — Create Supplier Re-Qualification Audit

| Field | Detail |
|---|---|
| Actor | Supplier Quality Manager |
| Action | Create a Supplier Audit record for Supplier "PharmRaw Co Ltd" (status = APPROVED): audit_type = RE_QUALIFICATION, audit_date = today, auditor = "Supplier Quality Manager". Begin the audit (status = IN_PROGRESS). |
| Expected Result | Supplier audit record created. Status = IN_PROGRESS. Supplier record shows a pending re-qualification audit. |
| Actual Result | |
| Pass/Fail | |
| Tester/Date | |

#### Step 6.2 — Record Audit Finding

| Field | Detail |
|---|---|
| Actor | Supplier Quality Manager |
| Action | Add an Audit Finding to the audit: finding_category = MAJOR, description = "Documented procedure SQM-014 for raw material testing not updated following changes to Ph. Eur. 7th edition specifications in 2024. Testing performed against superseded acceptance criteria for identity testing (IR spectra method updated in Ph. Eur. 10.5). No OOS results have been generated from this gap, but the procedural non-compliance represents a systemic quality management failure." |
| Expected Result | Finding record created and linked to the audit. QA Manager receives a notification of a MAJOR supplier finding. |
| Actual Result | |
| Pass/Fail | |
| Tester/Date | |

#### Step 6.3 — Supplier Status Set to Conditional Approval

| Field | Detail |
|---|---|
| Actor | QA Manager |
| Action | Complete the audit (status = COMPLETED, overall_result = CONDITIONAL_PASS). Update supplier status from APPROVED to CONDITIONALLY_APPROVED with a note: "Conditional approval pending resolution of major finding from re-qualification audit AUD-2026-0003. Current materials in inventory pre-approved and may continue to be used pending CAPA closure within 60 days." |
| Expected Result | Supplier status = CONDITIONALLY_APPROVED. Audit status = COMPLETED. Audit result = CONDITIONAL_PASS. The finding is documented with its corrective action timeline. |
| Actual Result | |
| Pass/Fail | |
| Tester/Date | |

#### Step 6.4 — Supplier Corrective Action and Closure

| Field | Detail |
|---|---|
| Actor | Supplier Quality Manager |
| Action | Create a CAPA for the supplier finding: "PharmRaw Co Ltd to update SQM-014 to current Ph. Eur. 10.5 IR method." Receive supplier response: "SQM-014 Rev 5 updated and validated. Retrospective review of all identity tests for past 12 months completed — all results confirmed acceptable against Ph. Eur. 10.5. Certificate of compliance provided." Record corrective action as COMPLETE. Close the CAPA. |
| Expected Result | CAPA is closed with effectiveness evidence. Supplier corrective action is documented and linked to the audit finding. |
| Actual Result | |
| Pass/Fail | |
| Tester/Date | |

#### Step 6.5 — Re-Approve Supplier

| Field | Detail |
|---|---|
| Actor | QA Manager |
| Action | Re-approve the supplier: update status from CONDITIONALLY_APPROVED to APPROVED. Apply e-signature: meaning = "Supplier Re-Approved Following Major Finding Resolution". |
| Expected Result | Supplier status = APPROVED. E-signature captured. Supplier audit history shows the full sequence: prior APPROVED, CONDITIONALLY_APPROVED (with finding), re-APPROVED (after CAPA). The complete re-qualification trail is audited. |
| Actual Result | |
| Pass/Fail | |
| Tester/Date | |

**Scenario 6 Outcome:** PASS / FAIL / DEVIATION

**Tester:** ___________________________ **Date:** _______________

---

### SCENARIO 7: Stability Study → OOS Result at T=12 Months → OOS Investigation → Regulatory Notification

**Scenario Title:** Stability Study OOS Event — Investigation and Regulatory Notification Workflow

**Objective:** Demonstrate that a stability study is managed in the system, an Out-of-Specification (OOS) result at the 12-month time point triggers a mandatory OOS investigation, root cause is documented, and the system supports the generation of a regulatory notification record.

**Modules Exercised:** Stability Module, LIMS (stability sample testing), QMS (Deviation/CAPA), Document Management

**Personnel Required:** LIMS Stability Analyst, QA Manager, Regulatory Affairs Manager

---

#### Step 7.1 — Confirm Stability Study is Active and T=12 Month Samples Due

| Field | Detail |
|---|---|
| Actor | LIMS Stability Analyst |
| Action | Navigate to the Stability module and locate the stability study for product VERAPLEX-100 batch VER-2026-B001 (created in Scenario 1). Confirm the T=12 month time point is scheduled and samples have been pulled. The T=12 month due date = 12 months after the manufacturing date entered in the system. |
| Expected Result | Stability study exists for VER-2026-B001. T=12 month time point status = SAMPLES_PULLED. The analyst is assigned to enter the results. A notification was sent to the analyst when the T=12 time point became due. |
| Actual Result | |
| Pass/Fail | |
| Tester/Date | |

#### Step 7.2 — Enter T=12 Month Test Results Including OOS

| Field | Detail |
|---|---|
| Actor | LIMS Stability Analyst |
| Action | Enter the T=12 month stability results: Assay = 96.2% (specification 98.0–102.0%) — OOS (below lower limit), Related Substances Total = 0.18% (limit ≤ 0.20%) — within specification, Dissolution = 95% (limit ≥ 85%) — within specification |
| Expected Result | Results recorded. Assay result of 96.2% is flagged OOS_FAIL (below 98.0% limit). The system immediately generates an OOS alert to the QA Manager and LIMS Supervisor. The stability time point status = OOS_DETECTED. |
| Actual Result | |
| Pass/Fail | |
| Tester/Date | |

#### Step 7.3 — Initiate Phase 1 OOS Investigation (Laboratory Investigation)

| Field | Detail |
|---|---|
| Actor | LIMS Stability Analyst |
| Action | Create an OOS Investigation record linked to the failed assay result. Phase 1 (laboratory phase): "Chromatographic data reviewed. Analyst qualification confirmed current. Reference standard confirmed in-date. System suitability passed. Calculation reviewed and confirmed correct. No laboratory error identified. Phase 1 investigation complete — OOS result confirmed as genuine." |
| Expected Result | OOS Investigation record created and linked to the stability result. Phase 1 status = COMPLETE. Result confirmed as genuine OOS. |
| Actual Result | |
| Pass/Fail | |
| Tester/Date | |

#### Step 7.4 — Phase 2 OOS Investigation (Full Investigation)

| Field | Detail |
|---|---|
| Actor | QA Manager |
| Action | Initiate Phase 2 investigation. Document findings: "Review of manufacturing batch record VER-2026-B001 shows all critical parameters within specification at time of manufacture. API source lot (LOT-API-001) retrospective review shows no issues. Stability storage conditions confirmed consistent throughout T=0 to T=12 (temperature chart data attached). Conclusion: genuine degradation of active substance, rate exceeding original accelerated study prediction. Potential formulation robustness issue. Product may have shorter shelf life than initially assigned." |
| Expected Result | Phase 2 investigation documented. Root cause = FORMULATION_STABILITY_INSUFFICIENT. Impact assessment completed. |
| Actual Result | |
| Pass/Fail | |
| Tester/Date | |

#### Step 7.5 — Create Regulatory Notification Record

| Field | Detail |
|---|---|
| Actor | Regulatory Affairs Manager |
| Action | Create a Regulatory Notification record linked to the OOS investigation: notification_type = EMA_VARIATION, subject = "Proposed reduction in shelf life for VERAPLEX-100 from 36 months to 24 months based on T=12 stability failure", target_authority = "EMA / MHRA", required_submission_date = [90 days from today]. Attach the OOS investigation report document. |
| Expected Result | Regulatory Notification record created, linked to the OOS investigation. Status = DRAFT. Submission due date is populated. A reminder notification is scheduled for 30 days before the submission due date. |
| Actual Result | |
| Pass/Fail | |
| Tester/Date | |

#### Step 7.6 — Link CAPA for Formulation Improvement

| Field | Detail |
|---|---|
| Actor | QA Manager |
| Action | Create a CAPA linked to the OOS investigation: "Initiate formulation development programme to improve VERAPLEX-100 active substance stability." Priority = CRITICAL. Link the CAPA to the OOS investigation record and to the Regulatory Notification record. |
| Expected Result | CAPA created and linked to both the OOS investigation and the Regulatory Notification. All three records are navigable from each other. |
| Actual Result | |
| Pass/Fail | |
| Tester/Date | |

**Scenario 7 Outcome:** PASS / FAIL / DEVIATION

**Tester:** ___________________________ **Date:** _______________

---

### SCENARIO 8: Full Audit Trail Review — Regulatory Inspector Scenario

**Scenario Title:** Simulated Regulatory Inspection — Full Batch Traceability Review

**Objective:** Simulate a regulatory inspector reviewing the complete life history of batch VER-2026-B001 — from raw material receipt through manufacturing, QC release, and all associated quality events. Demonstrate that the GMP Platform provides a complete, unbroken, and readily accessible audit trail satisfying 21 CFR Part 11 and EU Annex 11 requirements for data integrity.

**Modules Exercised:** All modules (read-only regulatory review scenario)

**Personnel Required:** QA Manager (acting as regulatory liaison), Read-only Regulatory Reviewer account

**Important Note:** This scenario is primarily a read and verification exercise. No new records are created. All artefacts were created during Scenarios 1–7 and prior OQ tests. The Regulatory Reviewer account must have read-only access to all modules.

---

#### Step 8.1 — Identify the Batch and Access Its Record

| Field | Detail |
|---|---|
| Actor | Regulatory Reviewer |
| Action | Navigate to the MES Batch Records module. Search for batch VER-2026-B001. Open the batch record detail page. |
| Expected Result | Batch record VER-2026-B001 is found within 5 seconds of search submission (see Performance Criteria, Section 8). The detail page displays: batch number, product name, product code, manufacturing date, batch size, actual yield, yield percentage, released date, dual e-signature references (Operator + QA), current status = RELEASED. |
| Actual Result | |
| Response Time (measured): ___ seconds | Pass/Fail: |
| Tester/Date | |

#### Step 8.2 — Trace Raw Material Lot Provenance

| Field | Detail |
|---|---|
| Actor | Regulatory Reviewer |
| Action | From the batch record, navigate to the Dispensing Events section. Identify all material lots used in VER-2026-B001. For each lot, navigate to the material lot record and verify: lot number, supplier name, Certificate of Analysis, receipt date, and incoming QC test result status. |
| Expected Result | All dispensed material lots are listed with full traceability. For LOT-API-001: supplier = PharmRaw Co Ltd, CoA attached and accessible, receipt date documented, incoming QC status = RELEASED. No lots were dispensed from a rejected or quarantined status. |
| Actual Result | |
| Pass/Fail | |
| Tester/Date | |

#### Step 8.3 — Review Manufacturing Step Audit Trail

| Field | Detail |
|---|---|
| Actor | Regulatory Reviewer |
| Action | Navigate to the Batch Record Audit Trail view. Filter for record_type = BATCH_RECORD_STEP. Review each step entry: confirm that every step has a performed_by_user_id, performed_at timestamp (UTC), and the entered values. Confirm the critical parameter step (Step 4) shows actual_value = 65°C and critical_parameter_status = IN_RANGE. |
| Expected Result | The complete audit trail for all 7 batch steps is visible. Each entry shows: operator identity (not anonymous), exact UTC timestamp, and entered values. The audit log entry for Step 4 is present and unambiguous. |
| Actual Result | |
| Pass/Fail | |
| Tester/Date | |

#### Step 8.4 — Verify E-Signatures on Batch Release

| Field | Detail |
|---|---|
| Actor | Regulatory Reviewer |
| Action | Navigate to the E-Signatures section for batch VER-2026-B001. Review the two release signatures. For each signature, verify: signer full name, signer job title, meaning of signature, timestamp (UTC), and that both signatures are from different users. |
| Expected Result | Two e-signature records are displayed. Operator signature: meaning = "Manufactured by Operator", signer = [Operator name and title], timestamp = [release date]. QA signature: meaning = "Released by QA", signer = [QA Reviewer name and title], timestamp = [release date]. Both signers are different individuals. No way to delete or modify these records. |
| Actual Result | |
| Pass/Fail | |
| Tester/Date | |

#### Step 8.5 — Review LIMS Results and CoA

| Field | Detail |
|---|---|
| Actor | Regulatory Reviewer |
| Action | From the batch record, navigate to the linked LIMS results. View all QC test results. Navigate to the CoA generated in Scenario 1, Step 1.7. Review the CoA for completeness. |
| Expected Result | LIMS results visible with all three tests (Assay, Related Substances, Dissolution) showing results and specifications. All results are within specification. CoA contains: batch number, product, manufacturing date, all test results, QA approver name and signature reference, and approval date. CoA is accessible and can be downloaded (PDF). |
| Actual Result | |
| Pass/Fail | |
| Tester/Date | |

#### Step 8.6 — Review Associated Quality Events

| Field | Detail |
|---|---|
| Actor | Regulatory Reviewer |
| Action | From the batch record or from a cross-module search, identify all quality events associated with VER-2026-B001: (a) DEV-2026-0001 (temperature excursion deviation from Scenario 2), (b) The associated CAPA (CAPA-2026-0001), (c) OOS investigation from Scenario 7 (T=12 month stability). |
| Expected Result | All three quality events are traceable from the batch record. Each event is accessible, shows its current status (CLOSED, CLOSED, and [status at time of PQ execution]). The linkage between the batch record and each quality event is persistent and unambiguous. |
| Actual Result | |
| Pass/Fail | |
| Tester/Date | |

#### Step 8.7 — Verify Audit Log Completeness and Immutability

| Field | Detail |
|---|---|
| Actor | Regulatory Reviewer / QA Manager |
| Action | Query the audit log for all events associated with VER-2026-B001 across all record types: `SELECT event_type, record_type, record_id, actor_username, created_at FROM audit_events WHERE record_id IN (SELECT id FROM batch_records WHERE batch_number = 'VER-2026-B001') OR record_id IN (SELECT id FROM batch_record_steps WHERE batch_record_id IN (SELECT id FROM batch_records WHERE batch_number = 'VER-2026-B001')) ORDER BY created_at`. Count the total number of audit events. Verify there are no gaps in the timeline. |
| Expected Result | A complete, chronological audit log is returned covering: batch record creation, all step entries, yield entry, release signature events, and LIMS linkage. No gaps in the timeline. Timestamps are all in UTC. Actor identities are present for every event. The Regulatory Reviewer account cannot modify or delete any audit event. |
| Total audit events for VER-2026-B001: _______ | |
| Actual Result | |
| Pass/Fail | |
| Tester/Date | |

#### Step 8.8 — Verify Change Control Linkage and MBR Version

| Field | Detail |
|---|---|
| Actor | Regulatory Reviewer |
| Action | From VER-2026-B001, navigate to the linked MBR (MBR-VER-001 v1). From the MBR, navigate to the linked Change Control (CC-2026-0001). Verify the complete trail: CC approved → MBR created and approved → Batch executed against MBR v1 → Batch released → LIMS tested → CoA issued. |
| Expected Result | The full product introduction trail is navigable from a single starting point (the batch record or the change control). All links resolve correctly. The system provides a coherent, unbroken chain of custody from change approval to CoA. |
| Actual Result | |
| Pass/Fail | |
| Tester/Date | |

**Scenario 8 Outcome:** PASS / FAIL / DEVIATION

**Tester:** ___________________________ **Date:** _______________

---

## 8. Performance Criteria

The following performance criteria must be met during PQ execution. Response times must be measured and recorded using a stopwatch or browser developer tools (network tab). All measurements are taken in the PQ test environment under normal (single-user) load.

| PC ID | Criterion | Requirement | Measured Value | Pass/Fail |
|---|---|---|---|---|
| PC-001 | Standard search query (e.g., search batch records by batch number) returns results | < 2 seconds | | |
| PC-002 | Individual record load time (e.g., loading a Batch Record detail page) | < 2 seconds | | |
| PC-003 | Audit log query for a single record's event history (up to 500 events) | < 2 seconds | | |
| PC-004 | Electronic signature processing time (from submission to confirmation) | < 3 seconds | | |
| PC-005 | Audit log write latency — time from record creation/update to the audit event appearing in the auditlog | < 100 milliseconds | | |
| PC-006 | CoA PDF generation time | < 10 seconds | | |
| PC-007 | Notification delivery (in-app notification appears after triggering event) | < 5 seconds | | |
| PC-008 | MBR-to-Batch-Record creation (batch record generated from approved MBR with 10 steps) | < 5 seconds | | |

### Performance Measurement Methodology

- **PC-001 to PC-003, PC-006 to PC-008:** Measured using a stopwatch from the moment the "submit" action is taken to the moment the result is fully displayed on screen.
- **PC-004:** Measured from the moment the "Sign" button is clicked (password entered) to the moment the success confirmation is displayed.
- **PC-005:** Measured using database query timing: record a row creation time (`NOW()` in PostgreSQL) immediately before the API call, then query the audit_events table until the event appears. Latency = event.created_at - record_creation_time.

**Performance measurements are advisory in the single-user PQ environment.** Values significantly exceeding criteria must be documented as deviations and investigated. Load testing under concurrent user conditions is conducted separately.

---

## 9. Acceptance Criteria

This PQ is considered successfully completed when ALL of the following criteria are met:

| Criterion | Requirement |
|---|---|
| AC-001 | All 8 scenarios have been executed to completion with all steps recorded |
| AC-002 | All scenario step Pass/Fail determinations are PASS (or any FAILs are recorded as deviations and resolved) |
| AC-003 | All performance criteria (PC-001 through PC-008) are met, or deviations are raised and assessed |
| AC-004 | All Actual Results fields are completed contemporaneously by the executing tester |
| AC-005 | All tester signatures and dates are present for each scenario |
| AC-006 | All deviations observed have been documented in the Deviation Log with Deviation IDs |
| AC-007 | All deviations have been resolved or formally risk-accepted prior to PQ approval |
| AC-008 | The complete audit trail for batch VER-2026-B001 (Scenario 8) has been reviewed and confirmed complete and immutable |
| AC-009 | No scenario step resulted in data integrity failure (e.g., records missing from audit trail, e-signatures not captured, cross-module links broken) |
| AC-010 | The protocol has been reviewed and approved by the Reviewer and Approver listed in Section 11 |

**Overall PQ Outcome:** PASS / FAIL / CONDITIONAL PASS (circle one)

**Summary of Outcome:**

_______________________________________________________________________________

_______________________________________________________________________________

_______________________________________________________________________________

**System Release Recommendation:** Based on the PQ outcome, the GMP Platform is / is not (circle one) recommended for release to a GMP environment.

**Conditional release conditions (if applicable):**

_______________________________________________________________________________

_______________________________________________________________________________

---

## 10. Deviation Handling

### 10.1 Definition

A PQ deviation is any scenario step that produces a result different from the expected result, any performance criterion that is not met, any data integrity issue observed, or any step that cannot be executed as written.

### 10.2 Deviation Procedure

1. Stop execution of the affected scenario step immediately upon observing a deviation.
2. Record FAIL or DEVIATION in the Pass/Fail field of the affected step.
3. Fully describe the observed behaviour in the Actual Result field.
4. Assign a Deviation ID and complete the Deviation Log entry below.
5. Assess the impact on GMP compliance and system fitness for purpose.
6. Do not erase or obscure any prior entry — strike through with initials and date.
7. The PQ cannot be approved until all deviations are Resolved or Risk Accepted.

### 10.3 Deviation Log

| Dev ID | Scenario/Step | Description of Deviation | Date Observed | Observed By | GMP Impact | Disposition | Disposition By | Date Closed |
|---|---|---|---|---|---|---|---|---|
| DEV-001 | | | | | | | | |
| DEV-002 | | | | | | | | |
| DEV-003 | | | | | | | | |
| DEV-004 | | | | | | | | |
| DEV-005 | | | | | | | | |
| DEV-006 | | | | | | | | |
| DEV-007 | | | | | | | | |
| DEV-008 | | | | | | | | |
| DEV-009 | | | | | | | | |
| DEV-010 | | | | | | | | |

**Disposition Options:** Resolved (re-test passed) | Risk Accepted (with documented justification) | Open (PQ approval blocked)

---

## 11. Signature Page

This protocol has been prepared, reviewed, and approved in accordance with the GMP Platform Quality Management Plan (GMP-PLT-QMP-001).

### 11.1 Protocol Author

By signing below, the Author confirms that this protocol has been written in accordance with applicable regulatory requirements and internal procedures, and is suitable for execution.

| Field | Detail |
|---|---|
| Name (Print) | |
| Title | |
| Department | |
| Signature | |
| Date | |

---

### 11.2 Protocol Reviewer

By signing below, the Reviewer confirms that this protocol has been reviewed for technical accuracy, regulatory compliance, and completeness across all integrated modules, and is approved for execution.

| Field | Detail |
|---|---|
| Name (Print) | |
| Title | |
| Department | |
| Signature | |
| Date | |

---

### 11.3 Protocol Approver

By signing below, the Approver (must be QA or delegate with authority over all GxP computerised system validation) authorises this protocol for execution. The Approver acknowledges that a passing PQ is the final prerequisite for system go-live.

| Field | Detail |
|---|---|
| Name (Print) | |
| Title | |
| Department | |
| Signature | |
| Date | |

---

### 11.4 Execution Completion and System Release Recommendation

By signing below, the Lead Tester confirms that all scenarios have been executed as written (or deviations documented), all results are recorded contemporaneously, the performance criteria have been measured and recorded, and the PQ is complete and ready for QA final review and approval.

| Field | Detail |
|---|---|
| Name (Print) | |
| Title | |
| Signature | |
| Date of Completion | |
| Protocol Outcome | PASS / FAIL / CONDITIONAL PASS |
| System Recommended for GMP Release | YES / NO / CONDITIONAL |

---

### 11.5 QA Final Approval for System Release

By signing below, the Head of Quality (or delegate) confirms that the PQ has been reviewed in its entirety including all deviations and their dispositions, and authorises the GMP Platform for release into the validated GMP environment.

| Field | Detail |
|---|---|
| Name (Print) | |
| Title | Head of Quality / QA Director |
| Department | Quality Assurance |
| Signature | |
| Date | |
| GMP Platform Version Released | |
| Effective Date of GMP Use | |

---

*End of PQ-001 Performance Qualification — Full System*

*Document ID: PQ-001 | Version: 01 | GMP Platform | 2026-04-21*
