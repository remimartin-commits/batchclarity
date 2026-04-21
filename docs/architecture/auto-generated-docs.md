# Auto-Generated Documentation

This project auto-generates architecture and API documentation from source code.

## Generated outputs

- `docs/generated/openapi.json`
- `docs/generated/module-dependency-graph.md`
- `docs/generated/event-catalog.json`
- `docs/generated/event-catalog.md`
- `docs/generated/database-schema-by-module.md`
- `docs/site/index.html` (publishable static site)

## What is covered

1. API docs from endpoint definitions
   - FastAPI docs UI is exposed at `/docs` (and ReDoc at `/redoc`) in debug mode.
   - OpenAPI schema is generated to `docs/generated/openapi.json`.

2. Module dependency graph
   - Generated from import analysis in `backend/app/modules/**`.

3. Event catalog
   - Generated from in-code event publishers (`send_event(...)`) with producer paths.

4. Database schema per module
   - Generated from loaded SQLAlchemy metadata (models discovered through app startup imports).

## Regeneration

- Local build pipeline (`backend/scripts/run-autonomous-gate.ps1`) regenerates docs every build.
- CI quality gate (`.github/workflows/quality-gates.yml`) regenerates docs on every push to `main`.
- Pages deployment (`.github/workflows/docs-pages.yml`) regenerates and publishes docs/site on every push to `main`.

## Local command

From repository root:

```powershell
.\backend\.venv\Scripts\python.exe .\backend\scripts\generate-docs.py
```
