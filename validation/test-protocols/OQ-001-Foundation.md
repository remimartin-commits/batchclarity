# OQ-001 Operational Qualification — Foundation Layer

---

| Field | Value |
|---|---|
| Document ID | OQ-001 |
| Title | Operational Qualification — Foundation Layer |
| Version | 01 |
| Status | DRAFT |
| Date | 2026-04-21 |
| System | GMP Platform |
| Module | Foundation Layer |
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

This Operational Qualification (OQ) protocol establishes documented evidence that the GMP Platform Foundation Layer operates consistently and as intended throughout anticipated operating ranges. Execution of this protocol demonstrates that the core system services — authentication, role-based access control (RBAC), audit trail, electronic signatures (e-signatures), workflow engine, document versioning, notifications, and session management — function correctly, securely, and in compliance with applicable regulatory requirements.

This document is an execution-ready protocol. It must be completed in full by qualified personnel in the validated test environment prior to system release for GMP use.

### 1.2 Scope

This OQ covers the following Foundation Layer components of the GMP Platform:

| Component | Description |
|---|---|
| Authentication | Username/password login, MFA (TOTP), account lockout, session management |
| RBAC | Permission model, role assignment, site-scoping of permissions |
| Audit Trail | Immutable event log, field-level change capture, tamper evidence |
| Electronic Signatures | 21 CFR Part 11 and EU Annex 11 compliant e-signature capture and validation |
| Workflow Engine | State-machine-based workflow transitions, approval routing |
| Document Versioning | Version numbering, supersession, content hash integrity |
| Notifications | In-app and email notifications for assignments and events |
| Session Management | Timeout, concurrent session controls |
| Password Policy | Complexity rules, history enforcement, expiry |
| Timestamp Handling | UTC storage, timezone display |

**Out of Scope:** QMS, MES, LIMS, Equipment, Training, and Environmental Monitoring module-specific functions are covered in their respective OQ protocols (OQ-002 through OQ-006).

### 1.3 Regulatory Basis

This protocol is designed to satisfy the requirements of:

- 21 CFR Part 11 — Electronic Records; Electronic Signatures (FDA)
- EU GMP Annex 11 — Computerised Systems
- GAMP 5 (Second Edition) — A Risk-Based Approach to Compliant GxP Computerised Systems
- ICH Q9 — Quality Risk Management
- 21 CFR Part 211 — Current Good Manufacturing Practice for Finished Pharmaceuticals

---

## 2. References

| Reference ID | Document Title |
|---|---|
| URS-001 | User Requirements Specification — Foundation Layer |
| IQ-001 | Installation Qualification — Foundation Layer |
| SDD-001 | System Design Description — Foundation Layer |
| RA-001 | Risk Assessment — Foundation Layer |
| GMP-PLT-QMP-001 | Quality Management Plan — GMP Platform |
| 21 CFR Part 11 | Electronic Records; Electronic Signatures (FDA, 1997) |
| EU GMP Annex 11 | Computerised Systems (EMA, 2011) |
| GAMP 5 | A Risk-Based Approach to Compliant GxP Computerised Systems (ISPE, 2022) |
| ICH Q9 | Quality Risk Management |
| NIST SP 800-63B | Digital Identity Guidelines — Authentication |

---

## 3. Definitions and Abbreviations

| Term / Abbreviation | Definition |
|---|---|
| CAPA | Corrective and Preventive Action |
| CFR | Code of Federal Regulations |
| E-signature | Electronic signature as defined by 21 CFR Part 11 |
| GAMP | Good Automated Manufacturing Practice |
| GMP | Good Manufacturing Practice |
| IQ | Installation Qualification |
| MFA | Multi-Factor Authentication |
| MBR | Master Batch Record |
| OQ | Operational Qualification |
| PQ | Performance Qualification |
| RBAC | Role-Based Access Control |
| RPN | Risk Priority Number |
| SOD | Separation of Duties |
| TOTP | Time-based One-Time Password |
| URS | User Requirements Specification |
| UTC | Coordinated Universal Time |
| UUID | Universally Unique Identifier |

---

## 4. Prerequisites

All of the following prerequisites must be verified and documented before execution of this protocol commences. If any prerequisite is not met, execution must not proceed and the discrepancy must be documented.

| Prereq ID | Prerequisite | Verified By | Date | Initials |
|---|---|---|---|---|
| PRE-001 | IQ-001 (Installation Qualification — Foundation Layer) has been formally approved and all IQ deviations closed or risk-accepted | | | |
| PRE-002 | The test environment is a separate, controlled instance of the GMP Platform. It is not the production system. Environment details documented in the IQ. | | | |
| PRE-003 | Test environment database has been initialised with clean baseline data and no GMP production records are present | | | |
| PRE-004 | All test user accounts required for this protocol have been created as documented in Appendix A | | | |
| PRE-005 | Test environment system date/time is synchronised to a known, accurate NTP source and has been verified | | | |
| PRE-006 | Tester(s) executing this protocol have read and understood the protocol in full | | | |
| PRE-007 | Tester(s) have received training on GMP documentation practices (training records available) | | | |
| PRE-008 | The version of the GMP Platform under test matches the version documented in the IQ and in this protocol header | | | |
| PRE-009 | Direct database access credentials for audit log verification are available to the lead tester | | | |
| PRE-010 | A valid TOTP-compatible authenticator application is available and has been provisioned for the MFA test user account | | | |

**System Version Under Test:** ___________________________

**Test Environment URL:** ___________________________

**Database Host:** ___________________________

**Prerequisites Verified By:** ___________________________ Date: _______________

---

## 5. Test Cases

### Instructions for Execution

1. Execute each test case in the sequence listed unless otherwise noted.
2. Record all results contemporaneously — do not complete from memory after the fact.
3. If a test step cannot be completed as written, stop and raise a deviation immediately.
4. "Actual Result" must describe what actually occurred, not simply repeat the expected result.
5. Pass/Fail must be circled or initialled in ink if completed on paper. If completed electronically, the tester's e-signature applies.
6. Any deviation from expected results must be assigned a Deviation ID and handled per Section 6.

---

### TC-OQ-001: Login with Valid Credentials Succeeds

| Field | Detail |
|---|---|
| Test Case ID | TC-OQ-001 |
| Test Objective | Verify that a user with a valid, active account and correct credentials can successfully authenticate to the GMP Platform and access the home dashboard |
| URS Reference | URS-001-AUTH-001 |
| Risk Level | High |
| Prerequisites | Test user account "tester.oq001@gmpplatform.local" is active, password is known, MFA is disabled for this account |

**Test Steps:**

| Step | Action | Expected Result |
|---|---|---|
| 1 | Navigate to the GMP Platform login URL in a supported web browser | Login page is displayed with username and password fields visible |
| 2 | Enter the username: `tester.oq001@gmpplatform.local` | Username is entered in the field without error |
| 3 | Enter the correct password for this account | Password is entered (masked) without error |
| 4 | Click the "Login" / "Sign In" button | System processes the authentication request |
| 5 | Observe the post-login page | User is redirected to the home dashboard. The user's full name is displayed in the navigation header. No error message is shown. |
| 6 | Query the audit log via the API or database: `SELECT * FROM audit_events WHERE actor_user_id = [user_id] AND event_type = 'LOGIN_SUCCESS' ORDER BY created_at DESC LIMIT 1` | An audit event of type LOGIN_SUCCESS is present with the correct user_id, timestamp (UTC), and client IP address |

**Expected Result:** User is authenticated and the home dashboard is displayed. An audit log entry for LOGIN_SUCCESS is present.

**Actual Result:**

_______________________________________________________________________________

_______________________________________________________________________________

**Pass / Fail:** ________ **Tester:** ___________________________ **Date:** _______________

**Comments:**

_______________________________________________________________________________

---

### TC-OQ-002: Login with Invalid Password Fails and Increments Lockout Counter

| Field | Detail |
|---|---|
| Test Case ID | TC-OQ-002 |
| Test Objective | Verify that submitting an incorrect password results in authentication failure and that the failed attempt counter is incremented in the system |
| URS Reference | URS-001-AUTH-002 |
| Risk Level | High |
| Prerequisites | Test user account "tester.oq002@gmpplatform.local" is active, MFA disabled. Current failed_attempt_count = 0 (verified via DB query) |

**Test Steps:**

| Step | Action | Expected Result |
|---|---|---|
| 1 | Navigate to the login page | Login page displayed |
| 2 | Enter username: `tester.oq002@gmpplatform.local` | Username entered |
| 3 | Enter an incorrect password (e.g., "WrongPassword123!") | Password field populated |
| 4 | Click the Login button | System returns an authentication error |
| 5 | Observe the error message displayed | A generic error message is shown (e.g., "Invalid username or password"). The message must NOT reveal whether the username or password was incorrect specifically. |
| 6 | Query the database: `SELECT failed_attempt_count FROM users WHERE email = 'tester.oq002@gmpplatform.local'` | The failed_attempt_count is now 1 |
| 7 | Query the audit log for a LOGIN_FAILURE event with this user's ID | An audit event of type LOGIN_FAILURE is present with the correct timestamp and reason |

**Expected Result:** Login is rejected with a generic error message. The failed attempt counter is incremented to 1. An audit log entry for LOGIN_FAILURE is created.

**Actual Result:**

_______________________________________________________________________________

_______________________________________________________________________________

**Pass / Fail:** ________ **Tester:** ___________________________ **Date:** _______________

**Comments:**

_______________________________________________________________________________

---

### TC-OQ-003: Account Locks After 5 Consecutive Failed Login Attempts

| Field | Detail |
|---|---|
| Test Case ID | TC-OQ-003 |
| Test Objective | Verify that an account is locked after 5 consecutive failed login attempts and that subsequent login attempts (even with the correct password) are rejected until unlocked by an administrator |
| URS Reference | URS-001-AUTH-003 |
| Risk Level | High |
| Prerequisites | Test user account "tester.oq003@gmpplatform.local" is active, MFA disabled, failed_attempt_count = 0 |

**Test Steps:**

| Step | Action | Expected Result |
|---|---|---|
| 1 | Attempt to log in with incorrect password (Attempt 1 of 5) | Authentication fails with generic error message |
| 2 | Repeat failed login attempt (Attempt 2 of 5) | Authentication fails |
| 3 | Repeat failed login attempt (Attempt 3 of 5) | Authentication fails |
| 4 | Repeat failed login attempt (Attempt 4 of 5) | Authentication fails |
| 5 | Repeat failed login attempt (Attempt 5 of 5) | Authentication fails. Query DB: `SELECT account_locked, failed_attempt_count FROM users WHERE email = 'tester.oq003@gmpplatform.local'` — account_locked = TRUE, failed_attempt_count = 5 |
| 6 | Attempt to log in with the **correct** password | Login is rejected. System displays a message indicating the account is locked (e.g., "Account locked. Please contact an administrator.") |
| 7 | Query the audit log for an ACCOUNT_LOCKED event | An ACCOUNT_LOCKED audit event is present with the correct timestamp |
| 8 | As an administrator, unlock the account via the admin console | Account unlocked successfully |
| 9 | Attempt to log in again with the correct password | Login succeeds |

**Expected Result:** After 5 failed attempts the account is locked. The correct password is also rejected while locked. An administrator can unlock the account. Audit log captures the lock event.

**Actual Result:**

_______________________________________________________________________________

_______________________________________________________________________________

**Pass / Fail:** ________ **Tester:** ___________________________ **Date:** _______________

**Comments:**

_______________________________________________________________________________

---

### TC-OQ-004: MFA TOTP Token Required When MFA is Enabled

| Field | Detail |
|---|---|
| Test Case ID | TC-OQ-004 |
| Test Objective | Verify that when MFA is enabled on a user account, authentication cannot be completed with username and password alone — a valid TOTP token must be provided |
| URS Reference | URS-001-AUTH-004, 21 CFR 11.200(a)(1) |
| Risk Level | High |
| Prerequisites | Test user account "tester.oq004.mfa@gmpplatform.local" is active and MFA (TOTP) is enabled. Authenticator app is provisioned for this account. |

**Test Steps:**

| Step | Action | Expected Result |
|---|---|---|
| 1 | Navigate to the login page | Login page displayed |
| 2 | Enter valid username and correct password | Credentials accepted |
| 3 | Click Login | System does not grant access. Instead, it presents a second authentication step requesting a TOTP code. |
| 4 | Observe the intermediate state | The page shows a field requesting the MFA code. The session is not yet authenticated. |
| 5 | Enter an **incorrect** TOTP code (e.g., "000000") | System rejects the code with an error message. Authentication is not completed. |
| 6 | Retrieve the current valid TOTP code from the provisioned authenticator app | Six-digit code obtained |
| 7 | Enter the valid TOTP code | System accepts the code |
| 8 | Observe the result | User is authenticated and redirected to the home dashboard |
| 9 | Query the audit log for MFA_CHALLENGE_SUCCESS event | Audit event present with correct user_id and timestamp |

**Expected Result:** User cannot authenticate with credentials alone when MFA is enabled. A valid TOTP code is mandatory. Incorrect codes are rejected. Successful MFA authentication is logged.

**Actual Result:**

_______________________________________________________________________________

_______________________________________________________________________________

**Pass / Fail:** ________ **Tester:** ___________________________ **Date:** _______________

**Comments:**

_______________________________________________________________________________

---

### TC-OQ-005: User Without Permission Cannot Access Restricted Endpoint (403)

| Field | Detail |
|---|---|
| Test Case ID | TC-OQ-005 |
| Test Objective | Verify that the RBAC system correctly rejects API requests from authenticated users who do not possess the required permission for the requested resource, returning HTTP 403 Forbidden |
| URS Reference | URS-001-RBAC-001, 21 CFR 11.10(d) |
| Risk Level | High |
| Prerequisites | Test user "tester.oq005.readonly@gmpplatform.local" is active and assigned only the "Viewer" role, which does not include the permission "capa:approve". User is logged in and a valid session token is available. |

**Test Steps:**

| Step | Action | Expected Result |
|---|---|---|
| 1 | Authenticate as `tester.oq005.readonly@gmpplatform.local` and obtain a valid JWT/session token | Authentication succeeds |
| 2 | Using the API (e.g., curl or Postman), submit a POST request to `/api/v1/qms/capas/{capa_id}/approve` with the valid session token. Use a known CAPA ID in DRAFT status. | Request is processed by the server |
| 3 | Observe the HTTP response status code and body | HTTP 403 Forbidden is returned. Response body contains an error message such as `{"detail": "Insufficient permissions: capa:approve required"}` |
| 4 | Confirm the CAPA status has not changed | Query the CAPA record: status remains DRAFT, not APPROVED |
| 5 | Query the audit log | An ACCESS_DENIED audit event is recorded with the user ID, the requested resource, and the required permission |
| 6 | Repeat the same request as a user with the "QA Manager" role (who holds `capa:approve` permission) | HTTP 200 OK is returned and the CAPA is approved |

**Expected Result:** The unauthorised user receives HTTP 403. The resource is not modified. The access denial is logged. An authorised user can perform the same action successfully.

**Actual Result:**

_______________________________________________________________________________

_______________________________________________________________________________

**Pass / Fail:** ________ **Tester:** ___________________________ **Date:** _______________

**Comments:**

_______________________________________________________________________________

---

### TC-OQ-006: Role Assignment is Site-Scoped Correctly

| Field | Detail |
|---|---|
| Test Case ID | TC-OQ-006 |
| Test Objective | Verify that a user's role assignment is scoped to a specific site and that permissions granted at Site A do not grant accessto Site B resources |
| URS Reference | URS-001-RBAC-002 |
| Risk Level | High |
| Prerequisites | Two sites exist: "Site-Alpha" (ID: site-001) and "Site-Beta" (ID: site-002). User "tester.oq006@gmpplatform.local" is assigned the "Operator" role at Site-Alpha only. |

**Test Steps:**

| Step | Action | Expected Result |
|---|---|---|
| 1 | Authenticate as `tester.oq006@gmpplatform.local` | Authentication succeeds |
| 2 | Submit a GET request to `/api/v1/sites/site-001/batches` | HTTP 200 OK returned. Site-Alpha batch records are visible. |
| 3 | Submit a GET request to `/api/v1/sites/site-002/batches` | HTTP 403 Forbidden returned. Site-Beta records are not accessible. |
| 4 | Attempt to create a record under Site-Beta: POST `/api/v1/sites/site-002/batches` | HTTP 403 Forbidden returned |
| 5 | Verify audit log | An ACCESS_DENIED event is logged for the Site-Beta access attempts |

**Expected Result:** The user can access Site-Alpha resources but is blocked from Site-Beta resources. Site scoping is enforced at the API level.

**Actual Result:**

_______________________________________________________________________________

_______________________________________________________________________________

**Pass / Fail:** ________ **Tester:** ___________________________ **Date:** _______________

**Comments:**

_______________________________________________________________________________

---

### TC-OQ-007: Audit Log Entry Created on Record Create with All Required Fields Populated

| Field | Detail |
|---|---|
| Test Case ID | TC-OQ-007 |
| Test Objective | Verify that when any GMP record is created, a corresponding audit log entry is automatically generated and contains all fields required by 21 CFR Part 11 and EU Annex 11 |
| URS Reference | URS-001-AUDIT-001, 21 CFR 11.10(e) |
| Risk Level | Critical |
| Prerequisites | User "tester.oq007@gmpplatform.local" is authenticated and has permission to create CAPA records |

**Test Steps:**

| Step | Action | Expected Result |
|---|---|---|
| 1 | Authenticate as `tester.oq007@gmpplatform.local` | Authentication succeeds |
| 2 | Create a new CAPA record via POST `/api/v1/qms/capas` with all required fields populated. Note the returned record ID and creation timestamp. | HTTP 201 Created returned with the new CAPA record including its UUID |
| 3 | Query the audit log: `SELECT * FROM audit_events WHERE record_id = '[new_capa_uuid]' AND event_type = 'RECORD_CREATE'` | One audit event is returned |
| 4 | Verify the following fields are present and populated in the audit event: (a) event_id (UUID), (b) event_type = 'RECORD_CREATE', (c) record_type = 'CAPA', (d) record_id = [UUID of created CAPA], (e) actor_user_id = [UUID of tester.oq007], (f) actor_username = 'tester.oq007@gmpplatform.local', (g) created_at (UTC timestamp), (h) ip_address, (i) new_values (JSON representation of all created fields) | All listed fields are present and correctly populated |
| 5 | Verify that old_values is NULL or empty (no prior state for a new record) | old_values is NULL |
| 6 | Verify that the timestamp in created_at matches the creation time of the CAPA record (within 1 second) | Timestamps match within tolerance |

**Expected Result:** A single RECORD_CREATE audit event is created, containing all nine required fields, with no old_values and correct new_values representing the initial record state.

**Actual Result:**

_______________________________________________________________________________

_______________________________________________________________________________

**Pass / Fail:** ________ **Tester:** ___________________________ **Date:** _______________

**Comments:**

_______________________________________________________________________________

---

### TC-OQ-008: Audit Log Entry on Record Update Contains Old and New Values

| Field | Detail |
|---|---|
| Test Case ID | TC-OQ-008 |
| Test Objective | Verify that modifying a GMP record generates an audit log entry that captures both the previous (old) and new values of every changed field, enabling full reconstruction of the record's history |
| URS Reference | URS-001-AUDIT-002, 21 CFR 11.10(e), EU Annex 11 §9 |
| Risk Level | Critical |
| Prerequisites | An existing CAPA record (ID: [to be noted at runtime]) exists in DRAFT status with description "Initial description text". User has permission to edit CAPAs. |

**Test Steps:**

| Step | Action | Expected Result |
|---|---|---|
| 1 | Record the current description and status of the CAPA: `SELECT description, status FROM capas WHERE id = '[capa_id]'` | Description = "Initial description text", status = "DRAFT" |
| 2 | Submit a PATCH request to update the CAPA description to "Updated description after investigation findings" | HTTP 200 OK returned with updated record |
| 3 | Query the audit log: `SELECT * FROM audit_events WHERE record_id = '[capa_id]' AND event_type = 'RECORD_UPDATE' ORDER BY created_at DESC LIMIT 1` | One RECORD_UPDATE audit event is returned |
| 4 | Inspect the old_values JSON field | old_values contains `{"description": "Initial description text"}` |
| 5 | Inspect the new_values JSON field | new_values contains `{"description": "Updated description after investigation findings"}` |
| 6 | Verify that fields that were NOT changed are NOT listed in either old_values or new_values (delta-only capture) | Only the changed field (description) appears in old_values and new_values |
| 7 | Verify actor_user_id, timestamp, and ip_address are correct | All fields correctly populated |

**Expected Result:** The audit event captures exactly the changed fields with both old and new values. Unchanged fields are not included. Actor identity and timestamp are correct.

**Actual Result:**

_______________________________________________________________________________

_______________________________________________________________________________

**Pass / Fail:** ________ **Tester:** ___________________________ **Date:** _______________

**Comments:**

_______________________________________________________________________________

---

### TC-OQ-009: Audit Log Records Cannot Be Modified

| Field | Detail |
|---|---|
| Test Case ID | TC-OQ-009 |
| Test Objective | Verify that audit log records are immutable — no application user or API call can modify an existing audit log entry |
| URS Reference | URS-001-AUDIT-003, 21 CFR 11.10(e) |
| Risk Level | Critical |
| Prerequisites | At least one audit log entry exists. Direct database access is available. A known audit_event_id is recorded. |

**Test Steps:**

| Step | Action | Expected Result |
|---|---|---|
| 1 | Note an existing audit event ID from a prior test (e.g., from TC-OQ-007) | audit_event_id recorded |
| 2 | Attempt to update the audit event via the API: PATCH `/api/v1/audit/events/[audit_event_id]` with a modified actor_username | HTTP 405 Method Not Allowed or HTTP 403 Forbidden is returned. No audit modification endpoint should exist. |
| 3 | Attempt a direct SQL UPDATE on the audit_events table using the application's own database connection string: `UPDATE audit_events SET actor_username = 'tampered_user' WHERE id = '[audit_event_id]'` | The database user for the application must not have UPDATE privilege on audit_events. The query returns an error such as `ERROR: permission denied for table audit_events`. |
| 4 | Attempt the same UPDATE using a DBA-level connection | Document the result. If the DBA can update via direct DB access, this must be noted as a risk and a compensating control (e.g., database-level audit of DBA activity, WAL log review) must be documented. |
| 5 | Verify the audit event record is unchanged: `SELECT * FROM audit_events WHERE id = '[audit_event_id]'` | The record is unchanged |

**Expected Result:** The application API provides no endpoint to modify audit events. The application database user does not have UPDATE privileges on the audit_events table. The audit record is confirmed unchanged.

**Actual Result:**

_______________________________________________________________________________

_______________________________________________________________________________

**Pass / Fail:** ________ **Tester:** ___________________________ **Date:** _______________

**Comments:**

_______________________________________________________________________________

---

### TC-OQ-010: Audit Log Records Cannot Be Deleted

| Field | Detail |
|---|---|
| Test Case ID | TC-OQ-010 |
| Test Objective | Verify that audit log records cannot be deleted through the application API or by the application database user |
| URS Reference | URS-001-AUDIT-003, 21 CFR 11.10(e) |
| Risk Level | Critical |
| Prerequisites | At least one audit log entry exists. Known audit_event_id from a prior test. |

**Test Steps:**

| Step | Action | Expected Result |
|---|---|---|
| 1 | Attempt to delete an audit event via the API: DELETE `/api/v1/audit/events/[audit_event_id]` | HTTP 405 Method Not Allowed or HTTP 403 Forbidden. No delete endpoint exists or is accessible. |
| 2 | Attempt a direct SQL DELETE on the application database connection: `DELETE FROM audit_events WHERE id = '[audit_event_id]'` | The application database role does not hold DELETE privilege on audit_events. Query returns a permission denied error. |
| 3 | Confirm the audit event still exists: `SELECT COUNT(*) FROM audit_events WHERE id = '[audit_event_id]'` | COUNT = 1. Record still present. |

**Expected Result:** No mechanism exists to delete audit log records through the application or via the application's database user. The audit trail is confirmed intact.

**Actual Result:**

_______________________________________________________________________________

_______________________________________________________________________________

**Pass / Fail:** ________ **Tester:** ___________________________ **Date:** _______________

**Comments:**

_______________________________________________________________________________

---

### TC-OQ-011: Electronic Signature Captured with Correct Meaning, Timestamp, and Signer Name

| Field | Detail |
|---|---|
| Test Case ID | TC-OQ-011 |
| Test Objective | Verify that an electronic signature is correctly captured with the signer's full name, title/role, the meaning of the signature, and an accurate UTC timestamp, and that all these attributes are stored and retrievable |
| URS Reference | URS-001-ESIG-001, 21 CFR 11.50(a), 21 CFR 11.70 |
| Risk Level | Critical |
| Prerequisites | A CAPA record exists in "Pending Approval" status. User "qa.approver@gmpplatform.local" has the QA Manager role and the `capa:approve` permission. |

**Test Steps:**

| Step | Action | Expected Result |
|---|---|---|
| 1 | Log in as `qa.approver@gmpplatform.local` | Authentication succeeds |
| 2 | Navigate to the CAPA record in Pending Approval status | CAPA record displayed correctly |
| 3 | Click the "Approve" action, which triggers the e-signature dialogue | An e-signature modal/dialogue is displayed requesting: (a) Password confirmation, (b) Signature meaning (pre-populated as "Approved" or selectable from a defined list) |
| 4 | Confirm the displayed signature meaning reads "Approved" and cannot be changed to an arbitrary free-text value | Signature meaning is from a controlled vocabulary; free text is not permitted |
| 5 | Enter the correct password for `qa.approver@gmpplatform.local` | Password entered |
| 6 | Click "Sign and Approve" | Signature is processed |
| 7 | Query the e-signatures table: `SELECT * FROM esignatures WHERE record_id = '[capa_id]' ORDER BY signed_at DESC LIMIT 1` | One e-signature record is returned containing: (a) signer_user_id, (b) signer_full_name = full name of qa.approver, (c) signer_title = job title/role, (d) meaning = "Approved", (e) signed_at = UTC timestamp, (f) record_id = CAPA UUID, (g) record_type = "CAPA" |
| 8 | Verify the signed_at timestamp is within 5 seconds of the current UTC time | Timestamp is accurate |

**Expected Result:** The e-signature record contains signer identity, meaning, and an accurate timestamp. All required 21 CFR Part 11 §11.50(a) attributes are present.

**Actual Result:**

_______________________________________________________________________________

_______________________________________________________________________________

**Pass / Fail:** ________ **Tester:** ___________________________ **Date:** _______________

**Comments:**

_______________________________________________________________________________

---

### TC-OQ-012: Electronic Signature Rejected if Wrong Password Entered

| Field | Detail |
|---|---|
| Test Case ID | TC-OQ-012 |
| Test Objective | Verify that an electronic signature attempt fails and the associated action is not executed if the user enters an incorrect password during the e-signature confirmation step |
| URS Reference | URS-001-ESIG-002, 21 CFR 11.200(a)(2) |
| Risk Level | Critical |
| Prerequisites | A CAPA record exists in "Pending Approval" status. User `qa.approver@gmpplatform.local` is logged in. |

**Test Steps:**

| Step | Action | Expected Result |
|---|---|---|
| 1 | Navigate to a CAPA record awaiting approval | CAPA displayed |
| 2 | Click "Approve" to trigger the e-signature dialogue | E-signature dialogue displayed |
| 3 | Enter an **incorrect** password | Password entered |
| 4 | Click "Sign and Approve" | System rejects the signature. Error message displayed: "Incorrect password. Signature not applied." or equivalent. |
| 5 | Verify the CAPA status has not changed | CAPA remains in "Pending Approval" status |
| 6 | Verify no e-signature record was created for this action | `SELECT COUNT(*) FROM esignatures WHERE record_id = '[capa_id]' AND meaning = 'Approved'` returns 0 (no records from this failed attempt) |
| 7 | Verify the audit log records an E_SIGNATURE_FAILURE event | ESIG_FAILURE audit event is present with user ID, record ID, and timestamp |

**Expected Result:** Incorrect password prevents signature application. The CAPA status is unchanged. No spurious e-signature record is created. The failure is audited.

**Actual Result:**

_______________________________________________________________________________

_______________________________________________________________________________

**Pass / Fail:** ________ **Tester:** ___________________________ **Date:** _______________

**Comments:**

_______________________________________________________________________________

---

### TC-OQ-013: Electronic Signature Content Hash Matches Record Content at Time of Signing

| Field | Detail |
|---|---|
| Test Case ID | TC-OQ-013 |
| Test Objective | Verify that the e-signature record stores a cryptographic hash of the record content at the time of signing and that this hash can be used to detect subsequent unauthorised modifications to the signed record |
| URS Reference | URS-001-ESIG-003, 21 CFR 11.70 |
| Risk Level | Critical |
| Prerequisites | A CAPA record that was signed in TC-OQ-011 is available. The e-signature record for this CAPA is accessible. |

**Test Steps:**

| Step | Action | Expected Result |
|---|---|---|
| 1 | Retrieve the e-signature record for the CAPA approved in TC-OQ-011 | E-signature record is retrieved, including the `content_hash` field |
| 2 | Retrieve the current content of the CAPA record (all fields that are included in the signed snapshot) via the API or database | Content retrieved |
| 3 | Compute the SHA-256 hash of the canonical serialisation of the CAPA content at sign time (using the same algorithm documented in SDD-001) | Computed hash value recorded |
| 4 | Compare the computed hash with the stored `content_hash` in the e-signature record | The hashes match identically |
| 5 | Directly modify a field in the CAPA record in the database (simulating a tamper attempt): `UPDATE capas SET description = 'TAMPERED CONTENT' WHERE id = '[capa_id]'` | Record updated directly in the database |
| 6 | Re-compute the hash of the tampered record content | New hash value is different from the stored e-signature content_hash |
| 7 | Use the application's hash verification endpoint (if available) or verify manually that the hashes no longer match | Mismatch is detected. The system reports the record has been modified after signing. |
| 8 | Restore the record to its original content: `UPDATE capas SET description = '[original description]' WHERE id = '[capa_id]'` | Record restored. Hashes match again. |

**Expected Result:** The content hash stored in the e-signature matches the record at time of signing. Any subsequent modification causes a detectable hash mismatch, demonstrating tamper evidence.

**Actual Result:**

_______________________________________________________________________________

_______________________________________________________________________________

**Pass / Fail:** ________ **Tester:** ___________________________ **Date:** _______________

**Comments:**

_______________________________________________________________________________

---

### TC-OQ-014: Workflow Transitions Follow Defined State Machine — Invalid Transitions Rejected

| Field | Detail |
|---|---|
| Test Case ID | TC-OQ-014 |
| Test Objective | Verify that the workflow engine enforces the defined state machine and rejects attempts to transition a record to a state that is not permitted from its current state |
| URS Reference | URS-001-WF-001 |
| Risk Level | High |
| Prerequisites | A CAPA record exists in "DRAFT" state. The defined CAPA state machine does not permit a direct transition from DRAFT to CLOSED. |

**Test Steps:**

| Step | Action | Expected Result |
|---|---|---|
| 1 | Confirm the CAPA is in DRAFT state | CAPA status = DRAFT |
| 2 | Attempt to transition the CAPA directly to CLOSED by posting to the workflow endpoint: POST `/api/v1/qms/capas/[capa_id]/transitions` with body `{"target_state": "CLOSED"}` | HTTP 422 Unprocessable Entity or HTTP 400 Bad Request is returned |
| 3 | Inspect the response body | Error message indicates the transition is invalid (e.g., `{"detail": "Invalid transition: DRAFT → CLOSED is not permitted"}`) |
| 4 | Verify the CAPA status has not changed | CAPA remains in DRAFT status |
| 5 | Attempt a valid transition: DRAFT → IN_REVIEW | HTTP 200 OK returned. CAPA status is now IN_REVIEW. |
| 6 | Verify the state machine also rejects APPROVED → DRAFT (backwards transition) | HTTP 422 returned for the invalid backwards transition |

**Expected Result:** The workflow engine enforces the state machine. Invalid transitions are rejected with an informative error. Valid transitions succeed.

**Actual Result:**

_______________________________________________________________________________

_______________________________________________________________________________

**Pass / Fail:** ________ **Tester:** ___________________________ **Date:** _______________

**Comments:**

_______________________________________________________________________________

---

### TC-OQ-015: Signature-Required Workflow Transition Blocked if Signature is Pending

| Field | Detail |
|---|---|
| Test Case ID | TC-OQ-015 |
| Test Objective | Verify that a workflow transition configured to require an electronic signature cannot be completed via an API call that bypasses the signature step |
| URS Reference | URS-001-WF-002, URS-001-ESIG-004 |
| Risk Level | Critical |
| Prerequisites | A CAPA record is in IN_REVIEW status. The transition IN_REVIEW → APPROVED requires an e-signature. |

**Test Steps:**

| Step | Action | Expected Result |
|---|---|---|
| 1 | Attempt to transition the CAPA to APPROVED status without providing an e-signature: POST `/api/v1/qms/capas/[capa_id]/transitions` with body `{"target_state": "APPROVED"}` (no signature payload included) | HTTP 422 Unprocessable Entity is returned |
| 2 | Inspect the error response | Error indicates that an e-signature is required for this transition: `{"detail": "Electronic signature required for transition to APPROVED"}` |
| 3 | Verify the CAPA status has not changed | CAPA remains in IN_REVIEW |
| 4 | Now perform the transition correctly: submit the transition with the e-signature payload (password + meaning) | HTTP 200 OK returned. CAPA transitions to APPROVED. E-signature record created. |

**Expected Result:** A signature-gated transition cannot be bypassed. The transition only completes when a valid e-signature is provided as part of the same request.

**Actual Result:**

_______________________________________________________________________________

_______________________________________________________________________________

**Pass / Fail:** ________ **Tester:** ___________________________ **Date:** _______________

**Comments:**

_______________________________________________________________________________

---

### TC-OQ-016: Document Version Increments Correctly on New Version Creation

| Field | Detail |
|---|---|
| Test Case ID | TC-OQ-016 |
| Test Objective | Verify that when a new version of a controlled document is created from an existing approved version, the version number increments according to the defined versioning scheme (major.minor or sequential integer) |
| URS Reference | URS-001-DOC-001 |
| Risk Level | High |
| Prerequisites | A controlled document (SOP type) exists at version 01 (APPROVED status). |

**Test Steps:**

| Step | Action | Expected Result |
|---|---|---|
| 1 | Retrieve the current document: `SELECT id, version_number, status FROM documents WHERE id = '[doc_id]'` | version_number = 1 (or "01"), status = APPROVED |
| 2 | Create a new version of this document via POST `/api/v1/documents/[doc_id]/new-version` | HTTP 201 Created. New document version returned. |
| 3 | Check the version_number of the new document | version_number = 2 (or "02") — incremented by exactly 1 |
| 4 | Check the status of the new document version | Status = DRAFT (new version is always created as DRAFT) |
| 5 | Verify the parent_document_id of the new version points to the original document | parent_document_id = [original doc_id] |

**Expected Result:** A new DRAFT version is created with a version number exactly one higher than the current approved version.

**Actual Result:**

_______________________________________________________________________________

_______________________________________________________________________________

**Pass / Fail:** ________ **Tester:** ___________________________ **Date:** _______________

**Comments:**

_______________________________________________________________________________

---

### TC-OQ-017: Previous Document Version is Superseded When New Version is Approved

| Field | Detail |
|---|---|
| Test Case ID | TC-OQ-017 |
| Test Objective | Verify that upon approval of a new document version, the previously approved version is automatically set to SUPERSEDED status, ensuring only one version of a document is in APPROVED status at any time |
| URS Reference | URS-001-DOC-002 |
| Risk Level | High |
| Prerequisites | Continuing from TC-OQ-016: version 1 of the SOP is APPROVED. Version 2 is in DRAFT. |

**Test Steps:**

| Step | Action | Expected Result |
|---|---|---|
| 1 | Advance version 2 through the approval workflow until it reaches the "Pending Approval" state | Document version 2 is in Pending Approval |
| 2 | Approve version 2 with a valid e-signature | HTTP 200 OK. Version 2 status = APPROVED |
| 3 | Query version 1 status: `SELECT status FROM documents WHERE id = '[doc_v1_id]'` | Version 1 status = SUPERSEDED |
| 4 | Query to confirm only one APPROVED version of this document exists: `SELECT COUNT(*) FROM documents WHERE doc_family_id = '[family_id]' AND status = 'APPROVED'` | COUNT = 1 (version 2 only) |
| 5 | Verify an audit log entry records the status change of version 1 | RECORD_UPDATE audit event for doc_v1 shows status changed from APPROVED to SUPERSEDED |

**Expected Result:** Upon approval of version 2, version 1 is automatically set to SUPERSEDED. Only one version of a document is APPROVED at any time.

**Actual Result:**

_______________________________________________________________________________

_______________________________________________________________________________

**Pass / Fail:** ________ **Tester:** ___________________________ **Date:** _______________

**Comments:**

_______________________________________________________________________________

---

### TC-OQ-018: Document Content Hash Verifiable After Approval

| Field | Detail |
|---|---|
| Test Case ID | TC-OQ-018 |
| Test Objective | Verify that upon document approval, a cryptographic hash of the document content (file or structured data) is stored and can be used to verify document integrity post-approval |
| URS Reference | URS-001-DOC-003, EU Annex 11 §7.1 |
| Risk Level | High |
| Prerequisites | A document has just been approved in TC-OQ-017. The document record includes a content_hash field. |

**Test Steps:**

| Step | Action | Expected Result |
|---|---|---|
| 1 | Retrieve the approved document record including its content_hash | content_hash field is populated with a non-null SHA-256 hex string |
| 2 | Download the document file content via GET `/api/v1/documents/[doc_v2_id]/download` | Document file downloaded |
| 3 | Compute the SHA-256 hash of the downloaded file using: `(Get-FileHash -Path <file> -Algorithm SHA256).Hash` | Hash value computed |
| 4 | Compare the computed hash with the stored content_hash | Hashes are identical |
| 5 | Simulate a tamper: replace one byte in the downloaded file and recompute its hash | The computed hash no longer matches the stored content_hash |

**Expected Result:** The stored content hash matches the approved document. Any modification to the document is detectable via hash mismatch.

**Actual Result:**

_______________________________________________________________________________

_______________________________________________________________________________

**Pass / Fail:** ________ **Tester:** ___________________________ **Date:** _______________

**Comments:**

_______________________________________________________________________________

---

### TC-OQ-019: Notification Sent When Record is Assigned to a User

| Field | Detail |
|---|---|
| Test Case ID | TC-OQ-019 |
| Test Objective | Verify that when a GMP record (e.g., a CAPA task) is assigned to a user, that user receives an in-application notification and, if configured, an email notification |
| URS Reference | URS-001-NOTIF-001 |
| Risk Level | Medium |
| Prerequisites | User "assignee.oq019@gmpplatform.local" exists and has email notifications enabled. A CAPA record exists in DRAFT status. |

**Test Steps:**

| Step | Action | Expected Result |
|---|---|---|
| 1 | As a manager, assign the CAPA to `assignee.oq019@gmpplatform.local` via PATCH `/api/v1/qms/capas/[capa_id]` with body `{"assigned_to_user_id": "[assignee_uuid]"}` | HTTP 200 OK. CAPA updated with assignee. |
| 2 | Log in as `assignee.oq019@gmpplatform.local` | Authentication succeeds |
| 3 | Check the in-application notification bell/icon | The notification count is ≥ 1. Clicking the icon shows a notification: "CAPA [CAPA-XXXX] has been assigned to you" with a link to the record. |
| 4 | Mark the notification as read | Notification is marked as read. Count decrements. |
| 5 | Check the email inbox for `assignee.oq019@gmpplatform.local` (using the test mail server or mailhog) | An email is received with subject containing "CAPA Assignment" or similar. The email body includes the CAPA ID, title, and a link to the record. |
| 6 | Query the notifications table: `SELECT * FROM notifications WHERE user_id = '[assignee_uuid]' AND record_id = '[capa_id]' ORDER BY created_at DESC LIMIT 1` | Notification record is present with correct user_id, record_id, type = ASSIGNMENT, is_read = TRUE |

**Expected Result:** The assigned user receives an in-app notification and an email. The notification record is stored in the database.

**Actual Result:**

_______________________________________________________________________________

_______________________________________________________________________________

**Pass / Fail:** ________ **Tester:** ___________________________ **Date:** _______________

**Comments:**

_______________________________________________________________________________

---

### TC-OQ-020: Session Expires After Configured Timeout Period

| Field | Detail |
|---|---|
| Test Case ID | TC-OQ-020 |
| Test Objective | Verify that an authenticated user session is automatically invalidated after the configured inactivity timeout period, requiring re-authentication |
| URS Reference | URS-001-AUTH-005, 21 CFR 11.200(a)(3) |
| Risk Level | High |
| Prerequisites | The session timeout is configured to 15 minutes (900 seconds) in the test environment. This can be temporarily reduced to 2 minutes (120 seconds) for testing purposes — document any configuration change made. |

**Test Steps:**

| Step | Action | Expected Result |
|---|---|---|
| 1 | Confirm and document the current session timeout configuration value | Timeout value: _______ seconds |
| 2 | If required for testing efficiency, temporarily set the session timeout to 2 minutes in the system configuration | Configuration updated. Change documented. |
| 3 | Log in as `tester.oq020@gmpplatform.local` | Authentication succeeds. Session token obtained. |
| 4 | Take no action for the duration of the configured timeout period (wait) | Session is idle |
| 5 | After the timeout has elapsed, submit an authenticated API request using the original session token: GET `/api/v1/profile` | HTTP 401 Unauthorized is returned. Response body: `{"detail": "Session expired. Please log in again."}` |
| 6 | Attempt to navigate to a protected page in the UI | User is redirected to the login page |
| 7 | Restore the original timeout configuration if changed in step 2 | Configuration restored. Change documented. |

**Expected Result:** After the timeout period, the session is invalidated. Further requests with the expired token return HTTP 401 and the user is required to re-authenticate.

**Actual Result:**

_______________________________________________________________________________

_______________________________________________________________________________

**Pass / Fail:** ________ **Tester:** ___________________________ **Date:** _______________

**Comments:**

_______________________________________________________________________________

---

### TC-OQ-021: Password Complexity Rules Enforced

| Field | Detail |
|---|---|
| Test Case ID | TC-OQ-021 |
| Test Objective | Verify that the system enforces defined password complexity requirements and rejects passwords that do not meet the policy |
| URS Reference | URS-001-AUTH-006 |
| Risk Level | High |
| Prerequisites | Password policy configured as: minimum 12 characters, at least 1 uppercase, 1 lowercase, 1 digit, 1 special character. A test user account exists that can have its password changed. |

**Test Steps:**

| Step | Action | Expected Result |
|---|---|---|
| 1 | Document the current password policy from system configuration | Policy documented: min length = ___, uppercase required = ___, etc. |
| 2 | Attempt to set a password that is too short (e.g., "Short1!"): POST `/api/v1/users/[user_id]/change-password` | HTTP 422 returned. Error: "Password must be at least 12 characters long." |
| 3 | Attempt a password with no uppercase letter (e.g., "alllowercase123!"): | HTTP 422 returned. Error indicates missing uppercase character. |
| 4 | Attempt a password with no digit (e.g., "NoDigitsHere!!!!"): | HTTP 422 returned. Error indicates missing numeric character. |
| 5 | Attempt a password with no special character (e.g., "NoSpecialChar123"): | HTTP 422 returned. Error indicates missing special character. |
| 6 | Set a password that meets all requirements (e.g., "ValidP@ssw0rd#2026"): | HTTP 200 OK. Password updated successfully. |
| 7 | Verify the user can log in with the new password | Login succeeds |

**Expected Result:** All non-compliant passwords are rejected with specific error messages. Only a password meeting all complexity criteria is accepted.

**Actual Result:**

_______________________________________________________________________________

_______________________________________________________________________________

**Pass / Fail:** ________ **Tester:** ___________________________ **Date:** _______________

**Comments:**

_______________________________________________________________________________

---

### TC-OQ-022: All Timestamps Stored in UTC and Displayed Correctly in Local Timezone

| Field | Detail |
|---|---|
| Test Case ID | TC-OQ-022 |
| Test Objective | Verify that all system timestamps are stored in UTC in the database and are displayed to users in their configured local timezone without data loss or ambiguity |
| URS Reference | URS-001-GENERAL-001, EU Annex 11 §12.1 |
| Risk Level | High |
| Prerequisites | Two test user accounts configured with different timezones: User A = UTC+0 (London), User B = UTC+8 (Singapore). A shared audit log entry is available. |

**Test Steps:**

| Step | Action | Expected Result |
|---|---|---|
| 1 | Create a record (e.g., a CAPA note) as User A at a known UTC time. Note the exact UTC time. | Record created. UTC creation time recorded: ______ UTC |
| 2 | Query the database directly: `SELECT created_at, pg_typeof(created_at) FROM audit_events WHERE ... ORDER BY created_at DESC LIMIT 1` | The stored value is a UTC timestamp (TIMESTAMPTZ). The raw value matches the observed creation time. |
| 3 | Log in as User A (UTC+0) and navigate to the record | The displayed timestamp matches the UTC time (e.g., "21 Apr 2026 10:30:00 UTC+0") |
| 4 | Log in as User B (UTC+8) and navigate to the same record | The displayed timestamp shows the UTC time converted to UTC+8 (e.g., "21 Apr 2026 18:30:00 SGT"). The absolute point in time is the same. |
| 5 | Confirm no timezone ambiguity: check that a timestamp during a daylight-saving-time transition is displayed with explicit offset (e.g., "+01:00" not just "BST") | Timezone offset is explicit and unambiguous |

**Expected Result:** All timestamps are stored as UTC in the database. The application correctly converts and displays timestamps in each user's configured local timezone. No ambiguity exists.

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
| AC-001 | All 22 test cases (TC-OQ-001 through TC-OQ-022) have been executed and recorded with a result of PASS |
| AC-002 | All test case Actual Results fields are completed contemporaneously during execution |
| AC-003 | All tester signatures and dates are present for each test case |
| AC-004 | Any deviations observed during testing have been documented and assigned a Deviation ID per Section 6 |
| AC-005 | All deviations have been assessed and resolved (or formally risk-accepted) prior to OQ approval |
| AC-006 | The protocol has been reviewed and approved by the Reviewer and Approver listed in Section 8 |

**Overall OQ Outcome:** PASS / FAIL / CONDITIONAL PASS (circle one)

**Summary of Outcome:**

_______________________________________________________________________________

_______________________________________________________________________________

---

## 7. Deviation Handling

### 7.1 Definition

A deviation is any departure from the expected result defined in a test case, including:
- Unexpected system behaviour
- An error message different from expected
- A test step that cannot be executed as written due to a system issue
- A prerequisite that cannot be satisfied

### 7.2 Deviation Procedure

1. Stop execution of the affected test case immediately upon observing a deviation.
2. Record "FAIL" or "DEVIATION" in the Pass/Fail field of the affected test case.
3. Complete the Comments field with a full description of what was observed.
4. Raise a formal Deviation Record using the Deviation Log below.
5. Do not proceed to the next test case until the deviation has been assessed and a disposition has been recorded by the lead tester.
6. Deviations must not be erased or corrected — use a single strikethrough if correction is needed, with initials and date.

### 7.3 Deviation Log

| Dev ID | TC Reference | Description of Deviation | Date Observed | Observed By | Impact Assessment | Disposition | Disposition By | Date Closed |
|---|---|---|---|---|---|---|---|---|
| DEV-001 | | | | | | | | |
| DEV-002 | | | | | | | | |
| DEV-003 | | | | | | | | |
| DEV-004 | | | | | | | | |
| DEV-005 | | | | | | | | |

**Disposition Options:**
- **Resolved** — root cause identified and corrected; test case re-executed and passed
- **Risk Accepted** — deviation assessed as having no impact on GMP compliance or system fitness for purpose (justification required)
- **Open** — under investigation; OQ approval is blocked until closed

---

## 8. Signature Page

This protocol has been prepared, reviewed, and approved in accordance with the GMP Platform Quality Management Plan (GMP-PLT-QMP-001).

### 8.1 Protocol Author

By signing below, the Author confirms that this protocol has been written in accordance with applicable regulatory requirements and internal procedures, and is suitable for execution.

| Field | Detail |
|---|---|
| Name (Print) | |
| Title | |
| Department | |
| Signature | |
| Date | |

---

### 8.2 Protocol Reviewer

By signing below, the Reviewer confirms that this protocol has been reviewed for technical accuracy, regulatory compliance, and completeness, and is approved for execution.

| Field | Detail |
|---|---|
| Name (Print) | |
| Title | |
| Department | |
| Signature | |
| Date | |

---

### 8.3 Protocol Approver

By signing below, the Approver (must be QA or delegate) authorises this protocol for execution.

| Field | Detail |
|---|---|
| Name (Print) | |
| Title | |
| Department | |
| Signature | |
| Date | |

---

### 8.4 Execution Completion Signature

By signing below, the Lead Tester confirms that all test cases have been executed as written (or deviations documented), all results recorded contemporaneously, and the protocol is complete and ready for QA review.

| Field | Detail |
|---|---|
| Name (Print) | |
| Title | |
| Signature | |
| Date of Completion | |
| Protocol Outcome | PASS / FAIL / CONDITIONAL PASS |

---

*End of OQ-001 Operational Qualification — Foundation Layer*

*Document ID: OQ-001 | Version: 01 | GMP Platform | 2026-04-21*
