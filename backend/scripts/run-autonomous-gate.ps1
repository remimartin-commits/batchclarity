$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$backendDir = Join-Path $repoRoot "backend"
$frontendDir = Join-Path $repoRoot "frontend"

Write-Host "==> Backend checks"
Set-Location $backendDir
& ".\scripts\run-checks.ps1"
if ($LASTEXITCODE -ne 0) {
  throw "Backend checks failed."
}

Write-Host "==> Generate documentation artifacts"
Set-Location $repoRoot
& ".\backend\.venv\Scripts\python.exe" ".\backend\scripts\generate-docs.py"
if ($LASTEXITCODE -ne 0) {
  throw "Documentation generation failed."
}

Write-Host "==> Frontend build"
Set-Location $frontendDir
npm run build
if ($LASTEXITCODE -ne 0) {
  throw "Frontend build failed."
}

Write-Host "==> Gate passed"
