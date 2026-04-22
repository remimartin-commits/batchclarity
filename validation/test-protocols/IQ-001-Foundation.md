# IQ-001: Installation Qualification — GMP Platform Foundation

| Field | Value |
|---|---|
| **Document Number** | IQ-001 |
| **Title** | Installation Qualification — GMP Platform Foundation Infrastructure |
| **Version** | 1.0 |
| **Status** | Draft |
| **Classification** | GAMP 5 Category 5 — Configured/Custom Software |
| **Applicable Regulations** | 21 CFR Part 11, EU GMP Annex 11, ICH Q10, ISO 13485:2016 |
| **Author** | |
| **Reviewed By** | |
| **Approved By** | |
| **Approval Date** | |
| **Next Review Date** | |

---

## 1. Purpose

This Installation Qualification (IQ) protocol verifies that the GMP Platform has been installed in accordance with the approved design specifications, vendor recommendations, and applicable regulatory requirements. Successful execution of this protocol demonstrates that all infrastructure components are present, correctly configured, and ready to support Operational Qualification (OQ) activities.

This IQ covers the foundation layer shared by all modules:

- Runtime environment (Python, Node.js, Docker)
- Database server (PostgreSQL)
- Cache/message broker (Redis)
- Backend application (FastAPI)
- Frontend application (React/Vite)
- Authentication and security subsystems
- Audit trail infrastructure
- Electronic signature framework
- Alembic database migration tooling

---

## 2. Scope

**In Scope:**
- Server/container infrastructure verification
- Software version verification
- Database schema installation
- Security configuration baseline
- Environment variable and secrets configuration
- Network connectivity between services
- Application startup and health check verification

**Out of Scope:**
- Functional behaviour of individual GMP modules (covered in OQ-002 through OQ-008)
- Performance and load testing (covered in PQ-001)
- User training
- Business process validation

---

## 3. References

| Reference | Title |
|---|---|
| URS-001 | User Requirements Specification — Platform Foundation |
| URS-002 | User Requirements Specification — Quality Management System |
| URS-003 | User Requirements Specification — Manufacturing Execution System |
| URS-004 | User Requirements Specification — Equipment and Training |
| URS-005 | User Requirements Specification — LIMS and Environmental Monitoring |
| 21 CFR Part 11 | Electronic Records; Electronic Signatures — FDA |
| EU GMP Annex 11 | Computerised Systems — EMA |
| GAMP 5 | A Risk-Based Approach to Compliant GxP Computerised Systems |
| ICH Q10 | Pharmaceutical Quality System |

---

## 4. Prerequisites

The following must be completed before executing this protocol:

| # | Prerequisite | Verified By | Date |
|---|---|---|---|
| P-01 | Validation Plan approved and in effect | | |
| P-02 | Risk Assessment (RA-001) reviewed and approved | | |
| P-03 | Server hardware/VM provisioned and accessible | | |
| P-04 | Operating system installed and hardened per IT Security Policy | | |
| P-05 | Docker Engine 24.x or later installed | | |
| P-06 | Git repository cloned to target server | | |
| P-07 | `.env` file created with production values from approved template | | |
| P-08 | SSL/TLS certificates provisioned (production only) | | |
| P-09 | Backup and recovery procedures documented | | |

---

## 5. Roles and Responsibilities

| Role | Responsibility |
|---|---|
| Validation Engineer | Protocol execution, recording results |
| IT Administrator | Infrastructure setup, credential management |
| QA Manager | Protocol review, approval, deviation management |
| System Owner | Final sign-off |

---

## 6. Materials and Tools Required

| Tool | Version | Purpose |
|---|---|---|
| Docker Engine | ≥ 24.0 | Container runtime |
| Docker Compose | ≥ 2.20 | Multi-service orchestration |
| `curl` | any | HTTP health check verification |
| `psql` | ≥ 16 | PostgreSQL connectivity verification |
| `redis-cli` | ≥ 7 | Redis connectivity verification |
| Text editor | any | Configuration file inspection |
| Checksum utility (`sha256sum`) | any | Artefact integrity verification |

---

## 7. Test Cases

All test results must be recorded in Section 8. Any deviation from the expected result must be recorded on a Deviation Report before proceeding.

**Pass/Fail Criteria:**
- **Pass (P):** Observed result matches the expected result exactly.
- **Fail (F):** Observed result does not match expected result; raise deviation.
- **N/A:** Test case does not apply to this installation; document justification.

---

### IQ-TC-001 — Docker Engine Version

**Objective:** Verify Docker Engine meets the minimum version requirement.

**Procedure:**
```bash
docker --version
docker compose version
```

**Expected Result:**
- Docker Engine version ≥ 24.0.x
- Docker Compose version ≥ 2.20.x

| Field | Value |
|---|---|
| **Observed Docker Engine Version** | |
| **Observed Docker Compose Version** | |
| **Result (P/F/N/A)** | |
| **Executed By** | |
| **Date/Time** | |
| **Comments** | |

---

### IQ-TC-002 — Container Image Build

**Objective:** Verify all container images build without errors from the approved source code.

**Procedure:**
```bash
cd /path/to/gmp-platform
docker compose build --no-cache
```

**Expected Result:**
- Exit code 0
- Images `gmp-platform-backend` and `gmp-platform-frontend` created
- No `ERROR` lines in build output

| Field | Value |
|---|---|
| **Backend image SHA256** | |
| **Frontend image SHA256** | |
| **Build exit code** | |
| **Result (P/F/N/A)** | |
| **Executed By** | |
| **Date/Time** | |
| **Comments** | |

---

### IQ-TC-003 — Service Startup and Health Checks

**Objective:** Verify all four services (db, redis, backend, frontend) start and report healthy.

**Procedure:**
```bash
docker compose up -d
# Wait 60 seconds for startup
sleep 60
docker compose ps
```

**Expected Result:**
- All services show `Status: healthy` (db, redis, backend) or `running` (frontend)
- No services in `exited` or `restarting` state

| Service | Observed Status | Healthy |
|---|---|---|
| db | | |
| redis | | |
| backend | | |
| frontend | | |

| Field | Value |
|---|---|
| **Result (P/F/N/A)** | |
| **Executed By** | |
| **Date/Time** | |
| **Comments** | |

---

### IQ-TC-004 — Backend Health Endpoint

**Objective:** Verify the backend health endpoint returns the expected response.

**Procedure:**
```bash
curl -s http://localhost:8000/health | python3 -m json.tool
```

**Expected Result:**
```json
{
  "status": "ok",
  "version": "<current version>",
  "environment": "<configured environment>",
  "modules": ["auth", "documents", "qms", "mes", "equipment", "training", "env_monitoring", "lims"]
}
```

| Field | Value |
|---|---|
| **HTTP Status Code** | |
| **`status` field** | |
| **`version` field** | |
| **`modules` count** | |
| **All 8 modules present** | Y / N |
| **Result (P/F/N/A)** | |
| **Executed By** | |
| **Date/Time** | |
| **Comments** | |

---

### IQ-TC-005 — Scheduler Status Endpoint

**Objective:** Verify APScheduler is running and the `overdue_checks` job is registered.

**Procedure:**
```bash
curl -s http://localhost:8000/health/scheduler | python3 -m json.tool
```

**Expected Result:**
- `scheduler_running` is `true`
- `jobs` array contains exactly one entry with `id = "overdue_checks"`
- `next_run` is a valid ISO-8601 timestamp

| Field | Value |
|---|---|
| **`scheduler_running`** | |
| **Number of jobs** | |
| **`overdue_checks` job present** | Y/ N |
| **`next_run` populated** | Y / N |
| **Result (P/F/N/A)** | |
| **Executed By** | |
| **Date/Time** | |
| **Comments** | |

---

### IQ-TC-006 — PostgreSQL Connectivity and Schema

**Objective:** Verify the PostgreSQL database is reachable and all expected tables are created.

**Procedure:**
```bash
docker compose exec db psql -U gmp_user -d gmp_platform -c "\dt"
```

**Expected Result:**
The following tables must be present (minimum set):

| Table | Present (Y/N) |
|---|---|
| `users` | |
| `roles` | |
| `permissions` | |
| `user_sessions` | |
| `password_histories` | |
| `sites` | |
| `audit_events` | |
| `electronic_signatures` | |
| `signature_requirements` | |
| `workflow_definitions` | |
| `workflow_states` | |
| `workflow_transitions` | |
| `workflow_instances` | |
| `workflow_history_entries` | |
| `document_types` | |
| `documents` | |
| `document_versions` | |
| `notification_templates` | |
| `notification_logs` | |
| `capas` | |
| `capa_actions` | |
| `deviations` | |
| `change_controls` | |
| `products` | |
| `master_batch_records` | |
| `batch_records` | |
| `batch_record_steps` | |
| `equipment` | |
| `calibration_records` | |
| `qualification_records` | |
| `maintenance_records` | |
| `training_curricula` | |
| `training_assignments` | |
| `training_completions` | |
| `monitoring_locations` | |
| `alert_limits` | |
| `monitoring_results` | |
| `samples` | |
| `test_results` | |
| `oos_investigations` | |

| Field | Value |
|---|---|
| **Total tables found** | |
| **All expected tables present** | Y / N |
| **Result (P/F/N/A)** | |
| **Executed By** | |
| **Date/Time** | |
| **Comments** | |

---

### IQ-TC-007 — Redis Connectivity

**Objective:** Verify Redis is reachable and responding to PING.

**Procedure:**
```bash
docker compose exec redis redis-cli ping
docker compose exec redis redis-cli info server | grep redis_version
```

**Expected Result:**
- `PING` returns `PONG`
- Redis version ≥ 7.0

| Field | Value |
|---|---|
| **PING response** | |
| **Redis version** | |
| **Result (P/F/N/A)** | |
| **Executed By** | |
| **Date/Time** | |
| **Comments** | |

---

### IQ-TC-008 — Python Runtime Version

**Objective:** Verify the backend container is running the approved Python version.

**Procedure:**
```bash
docker compose exec backend python --version
```

**Expected Result:**
- Python 3.12.x

| Field | Value |
|---|---|
| **Observed Python version** | |
| **Result (P/F/N/A)** | |
| **Executed By** | |
| **Date/Time** | |
| **Comments** | |

---

### IQ-TC-009 — Required Python Packages Installed

**Objective:** Verify all required Python packages are installed at the correct versions.

**Procedure:**
```bash
docker compose exec backend pip list --format=columns | grep -E "fastapi|sqlalchemy|alembic|asyncpg|pydantic|python-jose|passlib|cryptography|apscheduler"
```

**Expected Result — Minimum versions:**

| Package | Required Version | Observed Version | Match |
|---|---|---|---|
| fastapi | 0.115.0 | | |
| SQLAlchemy | 2.0.35 | | |
| alembic | 1.13.3 | | |
| asyncpg | 0.29.0 | | |
| pydantic | 2.9.2 | | |
| python-jose | 3.3.0 | | |
| passlib | 1.7.4 | | |
| cryptography | 43.0.1 | | |
| APScheduler | 3.10.4 | | |

| Field | Value |
|---|---|
| **All packages present at required versions** | Y / N |
| **Result (P/F/N/A)** | |
| **Executed By** | |
| **Date/Time** | |
| **Comments** | |

---

### IQ-TC-010 — Environment Variable Configuration

**Objective:** Verify all required environment variables are set and non-empty in the backend container.

**Procedure:**
```bash
docker compose exec backend env | grep -E "DATABASE_URL|SECRET_KEY|ENVIRONMENT|REDIS_URL"
```

**Expected Result:**
- `DATABASE_URL` — set, starts with `postgresql+asyncpg://`
- `SECRET_KEY` — set, non-default value in production (≥ 32 characters)
- `ENVIRONMENT` — set to `production` (or `staging` for pre-prod)
- `REDIS_URL` — set, starts with `redis://`

| Variable | Set (Y/N) | Value Valid (Y/N) |
|---|---|---|
| `DATABASE_URL` | | |
| `SECRET_KEY` | | |
| `ENVIRONMENT` | | |
| `REDIS_URL` | | |

| Field | Value |
|---|---|
| **All variables configured** | Y / N |
| **SECRET_KEY is non-default** | Y / N |
| **Result (P/F/N/A)** | |
| **Executed By** | |
| **Date/Time** | |
| **Comments** | |

---

### IQ-TC-011 — Authentication Endpoint Reachability

**Objective:** Verify the authentication endpoint is reachable and returns the correct schema error (not a 404 or 500).

**Procedure:**
```bash
curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Expected Result:**
- HTTP 422 (Unprocessable Entity — correct, means endpoint exists and validates input)
- Not 404 (would indicate routing misconfiguration)
- Not 500 (would indicate application startup error)

| Field | Value |
|---|---|
| **HTTP Status Code** | |
| **Result (P/F/N/A)** | |
| **Executed By** | |
| **Date/Time** | |
| **Comments** | |

---

### IQ-TC-012 — API Documentation Accessibility (DEBUG Mode Only)

**Objective:** Verify OpenAPI documentation is accessible in development/staging environments.

**Applicability:** Only execute when `ENVIRONMENT` is not `production`.

**Procedure:**
```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/docs
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/redoc
```

**Expected Result:**
- Both return HTTP 200

| Field | Value |
|---|---|
| `/api/docs` HTTP status** | |
| `/api/redoc` HTTP status** | |
| **Result (P/F/N/A)** | |
| **Executed By** | |
| **Date/Time** | |
| **Comments** | |

---

### IQ-TC-013 — Database Migration Tooling (Alembic)

**Objective:** Verify Alembic is correctly configured and can connect to the database.

**Procedure:**
```bash
docker compose exec backend alembic current
docker compose exec backend alembic history --verbose
```

**Expected Result:**
- `alembic current` returns without error (shows current revision or `<base>`)
- `alembic history` returns without connection error

| Field | Value |
|---|---|
| **`alembic current` exit code** | |
| **Connection errors** | Y / N |
| **Result (P/F/N/A)** | |
| **Executed By** | |
| **Date/Time** | |
| **Comments** | |

---

### IQ-TC-014 — Audit Trail Table Immutability Constraint

**Objective:** Verify the `audit_events` table has no UPDATE or DELETE triggers that would allow modification of records (append-only enforcement).

**Procedure:**
```bash
docker compose exec db psql -U gmp_user -d gmp_platform -c \
  "SELECT trigger_name, event_manipulation FROM information_schema.triggers WHERE event_object_table = 'audit_events';"
```

**Expected Result:**
- Query executes without error
- No `UPDATE` or `DELETE` event triggers are present on `audit_events`
- (INSERT triggers for timestamps are acceptable)

| Field | Value |
|---|---|
| **UPDATE triggers on audit_events** | Count: |
| **DELETE triggers on audit_events** | Count: |
| **Result (P/F/N/A)** | |
| **Executed By** | |
| **Date/Time** | |
| **Comments** | |

---

### IQ-TC-015 — Seed Data Installation (Reference Data)

**Objective:** Verify reference data (roles, permissions, document types, workflow definitions) has been loaded by the seed script.

**Procedure:**
```bash
# Run seed script
docker compose exec backend python scripts/seed.py

# Verify key reference counts
docker compose exec db psql -U gmp_user -d gmp_platform -c \
  "SELECT 'roles' as tbl, count(*) from roles
   UNION ALL SELECT 'permissions', count(*) from permissions
   UNION ALL SELECT 'document_types', count(*) from document_types
   UNION ALL SELECT 'workflow_definitions', count(*) from workflow_definitions
   UNION ALL SELECT 'notification_templates', count(*) from notification_templates;"
```

**Expected Result:**

| Table | Expected Count | Observed Count | Match |
|---|---|---|---|
| `roles` | ≥ 8 | | |
| `permissions` | ≥ 44 | | |
| `document_types` | ≥ 12 | | |
| `workflow_definitions` | ≥ 5 | | |
| `notification_templates` | ≥ 15 | | |

| Field | Value |
|---|---|
| **Admin user created** | Y / N |
| **All counts meet minimum** | Y / N |
| **Result (P/F/N/A)** | |
| **Executed By** | |
| **Date/Time** | |
| **Comments** | |

---

### IQ-TC-016 — Container Restart Policy

**Objective:** Verify all services are configured with `restart: always` so they recover automatically after system reboot.

**Procedure:**
```bash
docker compose config | grep -A2 "restart:"
```

**Expected Result:**
- All four services (db, redis, backend, frontend) show `restart: always`

| Service | Restart Policy |
|---|---|
| db | |
| redis | |
| backend | |
| frontend | |

| Field | Value |
|---|---|
| **All services have restart: always** | Y / N |
| **Result (P/F/N/A)** | |
| **Executed By** | |
| **Date/Time** | |
| **Comments** | |

---

### IQ-TC-017 — Log Output Verification

**Objective:** Verify application logs are being written and contain no critical startup errors.

**Procedure:**
```bash
docker compose logs backend --tail=100 2>&1 | grep -iE "error|exception|traceback|critical"
```

**Expected Result:**
- Zero `ERROR`, `EXCEPTION`, `TRACEBACK`, or `CRITICAL` level messages
- Startup messages include: `Database tables verified/created` and `APScheduler started`

| Field | Value |
|---|---|
| **ERROR/CRITICAL messages found** | Count: |
| **Startup success messages present** | Y / N |
| **Result (P/F/N/A)** | |
| **Executed By** | |
| **Date/Time** | |
| **Comments** | |

---

### IQ-TC-018 — Data Volume Persistence Verification

**Objective:** Verify persistent volumes are mounted so data survivescontainer restarts.

**Procedure:**
```bash
docker volume ls | grep -E "postgres_data|redis_data"
docker volume inspect gmp-platform_postgres_data
docker volume inspect gmp-platform_redis_data
```

**Expected Result:**
- Both volumes exist
- `Mountpoint` is not empty
- `Driver` is `local` (or approved enterprise storage driver)

| Volume | Exists (Y/N) | Driver |
|---|---|---|
| `gmp-platform_postgres_data` | | |
| `gmp-platform_redis_data` | | |

| Field | Value |
|---|---|
| **Result (P/F/N/A)** | |
| **Executed By** | |
| **Date/Time** | |
| **Comments** | |

---

## 8. Test Execution Summary

| Test Case | Title | Result (P/F/N/A) | Deviation Ref |
|---|---|---|---|
| IQ-TC-001 | Docker Engine Version | | |
| IQ-TC-002 | Container Image Build | | |
| IQ-TC-003 | Service Startup and Health Checks | | |
| IQ-TC-004 | Backend Health Endpoint | | |
| IQ-TC-005 | Scheduler Status Endpoint | | |
| IQ-TC-006 | PostgreSQL Connectivity and Schema | | |
| IQ-TC-007 | Redis Connectivity | | |
| IQ-TC-008 | Python Runtime Version | | |
| IQ-TC-009 | Required Python Packages Installed | | |
| IQ-TC-010 | Environment Variable Configuration | | |
| IQ-TC-011 | Authentication Endpoint Reachability | | |
| IQ-TC-012 | API Documentation Accessibility | | |
| IQ-TC-013 | Database Migration Tooling | | |
| IQ-TC-014 | Audit Trail Immutability Constraint | | |
| IQ-TC-015 | Seed Data Installation | | |
| IQ-TC-016 | Container Restart Policy | | |
| IQ-TC-017 | Log Output Verification | | |
| IQ-TC-018 | Data Volume Persistence | | |

**Total:** _____ Pass &nbsp;&nbsp;|&nbsp;&nbsp; _____ Fail &nbsp;&nbsp;|&nbsp;&nbsp; _____ N/A

---

## 9. Deviations

Any deviation from expected results must be recorded here. No test case may be left in `Fail` status without an associated deviation report.

| Dev. # | Test Case | Description | Impact Assessment | Resolution | Closed By | Date |
|---|---|---|---|---|---|---|
| | | | | | | |

---

## 10. Acceptance Criteria

This IQ is considered successfully executed when ALL of the following conditions are met:

1. All applicable test cases result in **Pass** or **N/A** (justified).
2. All **Fail** results have documented deviations with approved resolutions.
3. No unresolved **Critical** or **High** severity deviations remain open.
4. All test cases have been executed by a qualified individual and witnessed/verified where required.
5. The completed protocol has been reviewed by QA and signed by the System Owner.

---

## 11. Conclusion

*(To be completed after protocol execution)*

**Overall IQ Result:** Pass / Fail / Conditionally Passed

**Summary of Findings:**

**Outstanding Actions:**

**Recommendation to proceed to OQ:** Yes / No / Conditional

---

## 12. Sign-Off

| Role | Name | Signature | Date |
|---|---|---|---|
| Validation Engineer (Executed) | | | |
| Validation Engineer (Reviewed) | | | |
| IT Administrator | | | |
| QA Manager | | | |
| System Owner (Approved) | | | |

---

## Appendix A — Regulatory Traceability Matrix

| IQ Test Case | URS Requirement | Regulation / Guidance |
|---|---|---|
| IQ-TC-001 | URS-001 §2.1 (Approved technology stack) | GAMP 5 §5.3 |
| IQ-TC-002 | URS-001 §2.1 | GAMP 5 §7.4 |
| IQ-TC-003 | URS-001 §2.4 (System availability) | EU GMP Annex 11 §1 |
| IQ-TC-004 | URS-001 §2.4 | EU GMP Annex 11 §11 |
| IQ-TC-005 | URS-001 §2.5 (Automated notifications) | EU GMP Annex 11 §13 |
| IQ-TC-006 | URS-001 §2.2 (Data storage and integrity) | 21 CFR Part 11 §11.10(b) |
| IQ-TC-007 | URS-001 §2.4 | EU GMP Annex 11 §1 |
| IQ-TC-008 | URS-001 §2.1 | GAMP 5 §5.3 |
| IQ-TC-009 | URS-001 §2.1 | GAMP 5 §5.3 |
| IQ-TC-010 | URS-001 §3.1 (Security configuration) | 21 CFR Part 11 §11.10(d) |
| IQ-TC-011 | URS-001 §3.1 (Authentication) | 21 CFR Part 11 §11.300 |
| IQ-TC-012 | URS-001 §2.3 (System documentation) | EU GMP Annex 11 §4 |
| IQ-TC-013 | URS-001 §2.2 (Data integrity) | 21 CFR Part 11 §11.10(b) |
| IQ-TC-014 | URS-001 §4.1 (Audit trail immutability) | 21 CFR Part 11 §11.10(e) |
| IQ-TC-015 | URS-001 §2.6 (System configuration) | EU GMP Annex 11 §4.8 |
| IQ-TC-016 | URS-001 §2.4 (System availability) | EU GMP Annex 11 §16 |
| IQ-TC-017 | URS-001 §4.1 (Audit trail) | 21 CFR Part 11 §11.10(e) |
| IQ-TC-018 | URS-001 §2.2 (Data backup) | EU GMP Annex 11 §17 |

---

## Appendix B — Document Revision History

| Version | Date | Author | Description |
|---|---|---|---|
| 1.0 | | | Initial draft |
