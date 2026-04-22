# GMP Platform

Unified GMP Facility Management Platform — replaces TrackWise, Syncade, paper SOPs, and other manufacturing systems with a single validated application.

**Regulatory compliance:** 21 CFR Part 11 · EU Annex 11 · GAMP 5 Category 5 · ICH Q10

---

## Modules

| Module | Status | Replaces |
|---|---|---|
| Foundation (Auth, Audit, E-Sig, Workflow, Docs) | ✅ Built | Shared infrastructure |
| QMS (CAPA, Deviation, Change Control) | ✅ Built | TrackWise |
| MES (Master Batch Records, EBR) | ✅ Models built | Syncade / DeltaV |
| Equipment (Calibration, IQ/OQ/PQ, PM) | ✅ Models built | Paper-based systems |
| Training Management | ✅ Models built | Paper / LMS |
| Environmental Monitoring | 🔲 Pending | Paper-based |
| LIMS | 🔲 Pending | LabVantage / paper |

---

## Tech Stack

- **Backend:** Python 3.12 · FastAPI · SQLAlchemy 2.0 (async) · PostgreSQL 16
- **Frontend:** React 18 · TypeScript · Tailwind CSS · React Query · Zustand
- **Auth:** JWT (HS256) · bcrypt · 21 CFR Part 11 session management
- **E-Signatures:** Cryptographic JWT tokens · SHA-256 record hashing · password re-entry
- **Containerisation:** Docker · docker-compose

---

## Quick Start (Development)

### Prerequisites
- Docker Desktop
- Node.js 20+
- Python 3.12+

### 1. Start the database
```bash
docker-compose up db -d
```

### 2. Start the backend
```bash
cd backend
cp .env.example .env
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 3. Start the frontend
```bash
cd frontend
npm install
npm run dev
```

### 4. Or run everything with Docker
```bash
docker-compose up --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Generated Documentation (GitHub Pages)

- Docs site: `https://<github-username>.github.io/<repo-name>/`
- Generated from source on every push to `main` via `.github/workflows/docs-pages.yml`

---

## Project Structure

```
gmp-platform/
├── backend/
│   ├── app/
│   │   ├── core/               # Foundation layer (validated once)
│   │   │   ├── auth/           # Authentication, RBAC, sessions
│   │   │   ├── audit/          # Immutable audit trail (ALCOA+)
│   │   │   ├── esig/           # Electronic signatures (21 CFR Part 11)
│   │   │   ├── workflow/       # Configurable state machine engine
│   │   │   ├── documents/      # Version-controlled document control
│   │   │   └── notify/         # Notification engine
│   │   ├── modules/            # GMP functional modules
│   │   │   ├── qms/            # CAPA, Deviations, Change Control
│   │   │   ├── mes/            # Batch Records, MBR, Recipe Management
│   │   │   ├── equipment/      # Calibration, IQ/OQ/PQ, Maintenance
│   │   │   └── training/       # Training, Competency, Read & Understood
│   │   └── api/v1/             # API router
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/core/    # Layout, shared UI components
│   │   ├── pages/              # Page components per module
│   │   ├── stores/             # Zustand state (auth)
│   │   └── lib/                # API client
│   └── Dockerfile
├── validation/
│   ├── urs/                    # User Requirement Specifications
│   └── test-protocols/         # IQ/OQ/PQ test protocols
└── docker-compose.yml
```

---

## Validation Strategy

This system is built as **GAMP 5 Category 5 (Custom Software)**.

Validation documents are written alongside the code — not after:

| Document | Location | Status |
|---|---|---|
| URS-001 Foundation Layer | validation/urs/URS-001-Foundation.md | Draft |
| URS-002 QMS Module | validation/urs/URS-002-QMS.md | Pending |
| URS-003 MES Module | validation/urs/URS-003-MES.md | Pending |
| IQ Protocol — Foundation | validation/test-protocols/IQ-001.md | Pending |
| OQ Protocol — Foundation | validation/test-protocols/OQ-001.md | Pending |

---

## 21 CFR Part 11 Compliance Summary

| Requirement | Implementation |
|---|---|
| Unique user IDs | Enforced at DB level (unique constraint) |
| Password controls | Min 12 chars, complexity, 12-password history |
| Account lockout | 5 attempts → 30-min lockout |
| Session timeout | 30-min inactivity |
| Audit trail | Immutable append-only `audit_events` table |
| Old/new values | Captured on every field change |
| Electronic signatures | Password re-entry + SHA-256 record hash + JWT token |
| Signature meaning | Captured per signature (approved/reviewed/executed) |
| System access controls | RBAC — permission codes per module/resource/action |
