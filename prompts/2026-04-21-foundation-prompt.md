# Prompt Record — 2026-04-21 — Foundation Layer Build

## Context
First full build session on the GMP platform. Agent was asked to build the foundation
layer from scratch covering all shared services.

## Prompt (reconstructed)
Build the foundation layer for a unified GMP facility management platform.
Modular monolith. One database, shared by all modules, but with strict module boundaries.

Foundation must cover:
- Auth/RBAC (User, Role, Permission, JWT sessions, password history)
- Immutable Audit Trail (AuditEvent — append-only, no updates/deletes)
- Electronic Signatures (ElectronicSignature — requires re-authentication, not session reuse)
- Workflow Engine (WorkflowDefinition, WorkflowState, WorkflowInstance, history)
- Document Versioning (Document, DocumentVersion — version-controlled, approval-gated)
- Notifications (NotificationTemplate, NotificationRule, NotificationLog)
- Integration (IntegrationConnector, DataFeed, EventLog)

Regulatory: 21 CFR Part 11, EU Annex 11, GAMP 5 Category 5, ALCOA+.
Stack: Python 3.12, FastAPI, SQLAlchemy 2.x async, PostgreSQL.

## Output produced
- backend/app/core/auth/models.py — User, Role, Permission, UserSession, PasswordHistory, Site
- backend/app/core/audit/models.py — AuditEvent (append-only)
- backend/app/core/esig/models.py — ElectronicSignature, SignatureRequirement
- backend/app/core/workflow/models.py — WorkflowDefinition, WorkflowState, WorkflowTransition,
  WorkflowInstance, WorkflowHistoryEntry
- backend/app/core/documents/models.py — DocumentType, Document, DocumentVersion
- backend/app/core/notify/models.py — NotificationTemplate, NotificationRule, NotificationLog
- backend/app/core/integration/models.py — IntegrationConnector, IntegrationDataFeed, IntegrationEventLog
- backend/app/core/database.py — async engine, Base, async_session_factory
- backend/app/main.py — FastAPI app with lifespan, APScheduler, CORS, model imports
- backend/app/api/v1/router.py — aggregation router

## Key decisions made
- Windows/OneDrive OSError errno 22 workaround in main.py (Pydantic plugin discovery)
- APScheduler run_overdue_checks every 6 hours
- CORS includes Minimax deployment URL for dev
- All module models imported with # noqa in main.py for SQLAlchemy discovery
