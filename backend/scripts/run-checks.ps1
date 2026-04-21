$ErrorActionPreference = "Stop"
$BackendRoot = Split-Path -Parent $PSScriptRoot
Set-Location $BackendRoot

Write-Host "==> Running strict quality gates..." -ForegroundColor Cyan
& .\scripts\run-quality-gates.ps1
if ($LASTEXITCODE -ne 0) {
    throw "Quality gates failed with exit code $LASTEXITCODE"
}

Write-Host "==> Checks passed." -ForegroundColor Green
