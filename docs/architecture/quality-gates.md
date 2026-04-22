# Quality Gates

This project enforces automated quality gates locally and in CI.

## What is enforced

- Formatting: `ruff format --check backend`
- Lint: `ruff check backend`
- Type safety (strict): `mypy --config-file pyproject.toml`
- Architecture boundaries: `pytest backend/tests/test_architecture_boundaries.py -q`

Any failure exits non-zero and blocks commit/push workflows.

## Local setup (one-time)

From repo root:

```powershell
.\backend\scripts\setup-dev-env.ps1
.\backend\.venv\Scripts\python.exe -m pip install -r .\backend\requirements.txt
.\backend\.venv\Scripts\python.exe -m pre_commit install
```

## Run all quality gates locally

From repo root:

```powershell
.\backend\scripts\run-quality-gates.ps1
```

## Pre-commit behavior

- Config file: `.pre-commit-config.yaml`
- Installed via: `pre-commit install`
- Runs on every commit:
  - Ruff formatter
  - Ruff lint
  - Mypy strict type check
  - Architecture tests

If any check fails, commit is blocked.

## GitHub Actions behavior

- Workflow: `.github/workflows/quality-gates.yml`
- Trigger: every push to `main`
- Runs the same checks as local gate script.

If any check fails, the workflow fails and blocks merge policies that require passing checks.
