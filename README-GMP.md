# GMP Platform — Regulatory & Validation README

> **Path A — GMP Compliance Platform**
> Replace TrackWise. Replace Syncade. Replace LIMS. One validated system.
> Built to 21 CFR Part 11 / EU Annex 11 / GAMP 5 Category 5 from day one.

---

## What This Is

A modular, audit-ready pharmaceutical quality management platform that replaces
the patchwork of legacy GMP systems in small-to-mid-size pharma and biotech companies.

| Legacy System | This Platform Replaces | Module |
|---|---|---|
| TrackWise / MasterControl | QMS — CAPA, deviation, change control | `qms` |
| Syncade / Werum PAS-X | MES / EBR — batch records, process steps | `mes` |
| LabWare / LIMS | LIMS — stability, in-process, OOS investigations | `lims` |
| Pilgrim / eTQ | Document control, SOPs, change management | `core/documents` |
| ComplianceWire / Veeva Vault | Training records, qualification tracking | `training` |
| Blue Mountain RAM | Equipment calibration, maintenance scheduling | `equipment` |
| MODA / envista | Environmental monitoring, excursions | `env_monitoring` |

---

## Regulatory Compliance Built In

### 21 CFR Part 11 — Electronic Records & Signatures
- Every record mutation writes an immutable `AuditEvent` (append-only)
- Electronic signatures require re-authentication — no session reuse
- All timestamps stored as UTC in `audit_events.occurred_at`
- Audit trail covers who, what, when, system, IP address

### EU Annex 11 — Computerised Systems
- Data integrity enforced at database layer (not application layer)
- Backup and recovery procedures documented in IQ/OQ protocols
- Access controls tied to RBAC permission codes (`qms:capa:approve`, `mes:batch:release`, etc.)

### GAMP 5 Category 5 — Custom Software
- User Requirements Specification (URS) written before each module build
- Installation Qualification (IQ) and Operational Qualification (OQ) protocols in `validation/`
- Every module must reach VALIDATED tier before production use

### ALCOA+ Implementation
| Principle | Where Enforced |
|---|---|
| **A**ttributable | `created_by_id`, `performed_by_id` on every table |
| **L**egible | Structured JSON audit events, no free-text mutation logs |
| **C**ontemporaneous | `created_at` auto-set at INSERT, never settable via API |
| **O**riginal | Append-only audit trail, no UPDATE/DELETE on audit_events |
| **A**ccurate | FK integrity at DB level, schema validation at API layer |
| **C**omplete | `site_id` mandatory on all records; missing data = validation error |
| **C**onsistent | Status flags updated by scheduler, never stale |
| **E**nduring | Soft-delete only — no hard DELETE on GMP records |
| **A**vailable | Paginated export API; audit trail always queryable |

---

## Module Tier System

Each module progresses through four validated tiers before production use:

```
SKELETON → FUNCTIONAL → HARDENED → VALIDATED
```

| Tier | Meaning |
|---|---|
| SKELETON | Models + router exist. Not usable in production. |
| FUNCTIONAL | Core workflows complete, tests pass, notifications wired. |
| HARDENED | Edge cases handled, performance reviewed, auth/CORS locked. |
| VALIDATED | URS written, IQ/OQ executed, migration tested on prod copy. |

See `registry.json` for current module tiers.

---

## Architecture

```
gmp-platform/
├── backend/
│   ├── app/
│   │   ├── core/           ← Foundation (auth, audit, notify, esig, docs, integration)
│   │   └── modules/        ← Business modules (qms, mes, lims, equipment, training, env_monitoring)
│   ├── alembic/            ← All database migrations
│   └── tests/              ← Architecture boundary tests + integration tests
├── chaos.py                ← Deterministic chaos suite (5 scenarios)
├── BUILDING_RULES.md       ← Master specification (Cursor reads this every session)
├── TASK_QUEUE.md           ← Live build backlog
├── registry.json           ← Module tier registry
└── validation/             ← IQ/OQ protocols
```

### Architecture Boundaries (Enforced by CI)

- **No cross-module imports** — modules communicate via hook registry only
- **No cross-module foreign keys** — references stored as `String(36)` identifiers
- **No direct CRUD across module lines** — use events, not service calls
- Violations detected by `backend/tests/test_architecture_boundaries.py` at every PR

---

## Integration Strategy

**REPLACE these systems** (build native):
- QMS, MES/EBR, LIMS, Document Control, Training Management
- Equipment Calibration, Environmental Monitoring, ELN, SPC, Serialization

**INTEGRATE with these systems** (never replace):
- DCS/SCADA (DeltaV, Siemens) — read-only historian data into MES
- CDS instruments (Empower, Chromeleon) — read-only results into LIMS
- ERP financial layer (SAP, Oracle) — sync materials, batches, sites
- Environmental sensor hardware — real-time push into env_monitoring
- Regulatory submission systems (Veeva Vault, XEVMPD) — submit-only

All external calls go through `core/integration/` — never hardcoded in module code.

---

## Scale Plan

| Phase | Users | Sites | DB | Status |
|---|---|---|---|---|
| Phase 1 | <100 | 1 | PostgreSQL, single instance | Buildable now |
| Phase 2 | 100-300 | 1-3 | PgBouncer, read replicas | Needs TASK-007, TASK-010 |
| Phase 3 | 300-1000 | Multi-site | Partitioned tables, distributed scheduler | Major work |

**Known scale blockers (address before go-live):**
- Connection pool must be configured (TASK-007)
- High-volume tables must be partitioned by date (TASK-010)
- APScheduler must be guarded with PostgreSQL advisory lock (TASK-008)

---

## Running the Platform

```bash
# Development
cd backend
uv run uvicorn app.main:app --reload

# Run tests
uv run pytest backend/tests/

# Run chaos suite
uv run python chaos.py

# Generate audit report
uv run python scripts/generate_audit_report.py
```

---

## Autonomous Build Loop

This platform is built by Cursor (AI coding agent) under supervision of Matrix Agent.

- Cursor reads `BUILDING_RULES.md`, `TASK_QUEUE.md`, `.cursorrules` every session
- Cursor picks the highest-priority PENDING task and works through it
- Every 3 days, Matrix Agent reviews `audit/reports/YYYY-MM-DD-audit.json`
- Cursor escalates (BLOCKED status) on any GMP compliance decision it cannot resolve

See `SESSION_STARTER_TEMPLATE.md` for the exact prompt to start a Cursor session.

---

*Maintained by: Matrix Agent*
*Build loop: Cursor (autonomous) + Matrix Agent (3-day review cycle)*
*Regulatory scope: 21 CFR Part 11, EU Annex 11, GAMP 5 Category 5, ICH Q10*
