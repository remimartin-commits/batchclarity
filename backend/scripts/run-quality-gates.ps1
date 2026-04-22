$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot | Split-Path -Parent
Set-Location $RepoRoot

if (-not (Test-Path ".\backend\.venv\Scripts\python.exe")) {
    throw "Missing backend\.venv. Run backend\scripts\setup-dev-env.ps1 first."
}

$python = ".\backend\.venv\Scripts\python.exe"

Write-Host "==> Formatting check (ruff format)..." -ForegroundColor Cyan
& $python -m ruff format --check backend
if ($LASTEXITCODE -ne 0) { throw "Formatting check failed." }

Write-Host "==> Lint (ruff)..." -ForegroundColor Cyan
& $python -m ruff check backend
if ($LASTEXITCODE -ne 0) { throw "Lint check failed." }

Write-Host "==> Type check (mypy strict)..." -ForegroundColor Cyan
& $python -m mypy --config-file pyproject.toml
if ($LASTEXITCODE -ne 0) { throw "Type check failed." }

Write-Host "==> Architecture tests..." -ForegroundColor Cyan
& $python -m pytest backend/tests/test_architecture_boundaries.py -q
if ($LASTEXITCODE -ne 0) { throw "Architecture tests failed." }

Write-Host "==> Quality gates passed." -ForegroundColor Green
