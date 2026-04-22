# Audit — 2026-04-21 — Quality Gates and CI Automation

## GitHub Actions workflows present on disk
- .github/workflows/quality-gates.yml — CI on push/PR
- .github/workflows/docs-pages.yml — docs site deployment
- .github/workflows/chaos-weekly.yml — added 2026-04-23 (weekly chaos suite)

## Architecture boundary tests
backend/tests/test_architecture_boundaries.py
- test_no_lateral_module_imports(): AST walk to detect cross-module imports
- test_no_cross_module_foreign_keys(): regex ForeignKey("table.col") scan

Both tests use real Python tooling (ast module, re). Not decorative.

## Known gap in FK regex
Pattern: ForeignKey\("([^".]+)\.[^"]+"\)
Misses: alternative FK declaration styles (split across lines, schema-qualified names).
Mitigation: add SQLAlchemy metadata inspection test in future.

## Chaos suite (added 2026-04-23)
chaos.py — 5 deterministic scenarios:
1. Kill DB connection mid-batch
2. 10x query latency injection
3. Fill event bus to 10,000 messages
4. Corrupt 1-in-100 messages + dead-letter verification
5. App process crash + SQLite state recovery

Runs locally: python chaos.py
CI: .github/workflows/chaos-weekly.yml (Monday 03:00 UTC, blocks on failure)
Report: chaos/last-report.json

## Pre-commit hooks
.pre-commit-config.yaml present — assumed ruff + mypy (not audited in detail).
