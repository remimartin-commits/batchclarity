# User Requirement Specification
## URS-001 — GMP Platform Foundation Layer

| Field | Value |
|---|---|
| Document Number | URS-001 |
| Title | GMP Platform — Foundation Layer |
| Version | 1.0 |
| Status | Draft |
| Author | |
| Date | 2026-04-20 |
| Classification | GMP Critical |

---

## 1. Purpose

This URS defines the user requirements for the Foundation Layer of the GMP Platform — a unified, validated software system intended to replace multiple disparate GMP systems (TrackWise, Syncade, paper SOPs) with a single integrated platform.

The Foundation Layer provides shared services used by all functional modules: authentication, audit trail, electronic signatures, workflow engine, and document versioning.

---

## 2. Regulatory Framework

This system shall comply with:

- **21 CFR Part 11** — Electronic Records; Electronic Signatures (FDA)
- **EU GMP Annex 11** — Computerised Systems
- **GAMP 5** — A Risk-Based Approach to Compliant GxP Computerised Systems (Category 5 — Custom Software)
- **ICH Q10** — Pharmaceutical Quality System
- **21 CFR Part 211** — Current Good Manufacturing Practice for Finished Pharmaceuticals

---

## 3. User Requirements

### 3.1 Authentication & Access Control

| ID | Requirement | Priority |
|---|---|---|
| URS-001-AUTH-001 | The system shall authenticate users with a unique username and password | Mandatory |
| URS-001-AUTH-002 | Passwords shall be a minimum of 12 characters, containing uppercase, number, and special character | Mandatory |
| URS-001-AUTH-003 | The system shall lock accounts after 5 consecutive failed login attempts for a minimum of 30 minutes | Mandatory |
| URS-001-AUTH-004 | The system shall enforce a 30-minute inactivity session timeout | Mandatory |
| URS-001-AUTH-005 | The system shall prevent reuse of the last 12 passwords | Mandatory |
| URS-001-AUTH-006 | The system shall implement Role-Based Access Control (RBAC) | Mandatory |
| URS-001-AUTH-007 | User accounts shall be unique and not shared between individuals | Mandatory |
| URS-001-AUTH-008 | All login attempts (success and failure) shall be recorded in the audit trail | Mandatory |

### 3.2 Audit Trail (ALCOA+)

| ID | Requirement | Priority |
|---|---|---|
| URS-001-AUD-001 | The system shall maintain a secure, computer-generated audit trail for all GMP records | Mandatory |
| URS-001-AUD-002 | The audit trail shall record: who made the change, what was changed, the old value, the new value, and when (UTC) | Mandatory |
| URS-001-AUD-003 | Audit trail records shall not be modifiable or deletable by any user, including administrators | Mandatory |
| URS-001-AUD-004 | The timestamp for all audit events shall be set server-side in UTC and shall not be modifiable by the client | Mandatory |
| URS-001-AUD-005 | The audit trail shall be retained for a minimum of 10 years | Mandatory |
| URS-001-AUD-006 | Authorised users shall be able to search and export the audit trail | Mandatory |
| URS-001-AUD-007 | The reason for a change shall be captured where required by GMP | Mandatory |

### 3.3 Electronic Signatures (21 CFR Part 11)

| ID | Requirement | Priority |
|---|---|---|
| URS-001-ESIG-001 | Electronic signatures shall be legally binding and equivalent to handwritten signatures | Mandatory |
| URS-001-ESIG-002 | The system shall require password re-entry at the time of each signature (cannot be pre-signed) | Mandatory |
| URS-001-ESIG-003 | Each signature shall record: the full name of the signer, the date and time, and the meaning of the signature | Mandatory |
| URS-001-ESIG-004 | The record content shall be cryptographically hashed at the time of signing to detect tampering | Mandatory |
| URS-001-ESIG-005 | Electronic signature records shall be permanently linked to their associated GMP records | Mandatory |
| URS-001-ESIG-006 | Signatures shall not be transferable between individuals | Mandatory |
| URS-001-ESIG-007 | The system shall support configurable signature requirements per record type and state transition | Mandatory |

### 3.4 Workflow Engine

| ID | Requirement | Priority |
|---|---|---|
| URS-001-WF-001 | The system shall provide a configurable workflow engine for GMP record lifecycle management | Mandatory |
| URS-001-WF-002 | Workflows shall enforce valid state transitions only (no bypassing required steps) | Mandatory |
| URS-001-WF-003 | Required signatures and role authorisations shall be enforced before state transitions | Mandatory |
| URS-001-WF-004 | Due dates and SLA tracking shall be configurable per workflow state | Mandatory |
| URS-001-WF-005 | All state transitions shall be recorded in the audit trail | Mandatory |
| URS-001-WF-006 | The system shall issue notifications on workflow state changes | Desired |

### 3.5 Document Control

| ID | Requirement | Priority |
|---|---|---|
| URS-001-DOC-001 | The system shall maintain version-controlled GMP documents | Mandatory |
| URS-001-DOC-002 | Only one version of a document shall be in "effective" status at any time | Mandatory |
| URS-001-DOC-003 | Superseded document versions shall be archived and accessible but not editable | Mandatory |
| URS-001-DOC-004 | Document approval shall require electronic signature | Mandatory |
| URS-001-DOC-005 | New effective document versions shall automatically trigger training assignments | Desired |
| URS-001-DOC-006 | The effective date shall be set by the QA approver, not the document author | Mandatory |

### 3.6 System General

| ID | Requirement | Priority |
|---|---|---|
| URS-001-GEN-001 | The system shall be available 99.5% of the time during production hours | Mandatory |
| URS-001-GEN-002 | The system shall support multiple manufacturing sites | Mandatory |
| URS-001-GEN-003 | The system shall operate in validated DEV, UAT, and PROD environments | Mandatory |
| URS-001-GEN-004 | Data shall be backed up daily with verified restoration capability | Mandatory |
| URS-001-GEN-005 | The system shall support export of records in PDF format for regulatory submissions | Mandatory |

---

## 4. Out of Scope for Foundation Layer

- Functional QMS module (CAPA, deviations, change control) — URS-002
- MES module (batch records, recipes) — URS-003
- Equipment management module — URS-004
- Training management module — URS-005
- LIMS module — URS-006

---

## 5. Approval

| Role | Name | Signature | Date |
|---|---|---|---|
| Author | | | |
| QA Reviewer | | | |
| QA Approver | | | |
| IT/Systems Owner | | | |
