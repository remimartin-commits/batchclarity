# GMP Platform — rebuild venv, install deps, run Alembic, optional start API
# Run from PowerShell:  cd ...\gmp-platform\backend ; .\scripts\setup-dev-env.ps1

$ErrorActionPreference = "Stop"
$BackendRoot = Split-Path -Parent $PSScriptRoot
Set-Location $BackendRoot

Write-Host "==> Backend root: $BackendRoot" -ForegroundColor Cyan

function Remove-DirectoryHard {
    param([string]$TargetPath)
    if (-not (Test-Path -LiteralPath $TargetPath)) { return }
    $full = (Resolve-Path -LiteralPath $TargetPath).Path
    Write-Host "    (removing: $full)" -ForegroundColor DarkGray
    # Clear read-only / system bits (helps OneDrive + venv)
    cmd /c "attrib -r -s -h `"$full\*`" /s /d" 2>$null | Out-Null
    # Robocopy mirror from an empty folder deletes contents reliably on Windows
    $empty = Join-Path $env:TEMP "gmp_empty_$(Get-Random)"
    New-Item -ItemType Directory -Path $empty -Force | Out-Null
    try {
        & robocopy $empty $full /MIR /R:1 /W:1 /NFL /NDL /NJH /NJS /NP | Out-Null
    } finally {
        Remove-Item -LiteralPath $empty -Force -Recurse -ErrorAction SilentlyContinue
    }
    Remove-Item -LiteralPath $full -Force -Recurse -ErrorAction SilentlyContinue
}

# 1) Stop anything locking the venv (broad net — safe on dev machines)
$names = @("python", "pythonw", "uvicorn")
foreach ($n in $names) {
    Get-Process -Name $n -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
}
cmd /c "taskkill /F /IM python.exe /T 2>nul & taskkill /F /IM pythonw.exe /T 2>nul" | Out-Null
Start-Sleep -Seconds 2

# 2) Remove old .venv (plain rmdir often fails on site-packages under OneDrive)
if (Test-Path ".venv") {
    Write-Host "==> Removing .venv ..." -ForegroundColor Yellow
    $ErrorActionPreference = "Continue"
    try {
        Remove-DirectoryHard -TargetPath ".venv"
    } catch { }
    $ErrorActionPreference = "Stop"
    if (Test-Path ".venv") {
        Write-Host ""
        Write-Host "Could not delete .venv (files still locked). Try:" -ForegroundColor Red
        Write-Host "  - Close Cursor/VS Code and any other terminals using this project" -ForegroundColor White
        Write-Host "  - Pause OneDrive sync for this folder (or exit OneDrive briefly)" -ForegroundColor White
        Write-Host "  - Then delete the folder manually in Explorer: $BackendRoot\.venv" -ForegroundColor White
        throw "Remove .venv manually, then re-run this script."
    }
}

# 3) Create venv (Python 3.12)
Write-Host "==> Creating virtual environment (py -3.12) ..." -ForegroundColor Cyan
& py -3.12 -m venv .venv
if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    throw "Failed to create .venv. Is 'py -3.12' installed? Try: winget install Python.Python.3.12"
}

$py = ".\.venv\Scripts\python.exe"
# Console scripts (Windows): `python -m alembic` fails on some installs — use alembic.exe
$alembicExe = ".\.venv\Scripts\alembic.exe"
$uvicornExe = ".\.venv\Scripts\uvicorn.exe"

# 4) Bootstrap pip + install requirements
Write-Host "==> Installing dependencies ..." -ForegroundColor Cyan
& $py -m ensurepip --upgrade
& $py -m pip install --upgrade pip setuptools wheel
& $py -m pip install -r requirements.txt

# 5) Load DATABASE_URL from .env if present (Alembic reads env in env.py)
if (Test-Path ".env") {
    Get-Content ".env" | ForEach-Object {
        if ($_ -match '^\s*DATABASE_URL\s*=\s*(.+)\s*$') {
            $val = $Matches[1].Trim().Trim('"').Trim("'")
            [System.Environment]::SetEnvironmentVariable("DATABASE_URL", $val, "Process")
        }
    }
}
if (-not $env:DATABASE_URL) {
    Write-Host "WARNING: DATABASE_URL not set. Create backend\.env with DATABASE_URL=postgresql+asyncpg://..." -ForegroundColor Yellow
    Write-Host "         Skipping Alembic. After .env is ready, run:" -ForegroundColor Yellow
    Write-Host "         .\.venv\Scripts\alembic.exe revision --autogenerate -m foundation_layer_v1" -ForegroundColor Gray
    Write-Host "         .\.venv\Scripts\alembic.exe upgrade head" -ForegroundColor Gray
} else {
    if (-not (Test-Path $alembicExe)) {
        throw "alembic.exe not found after pip install. Run: $py -m pip install alembic"
    }
    Write-Host "==> Running Alembic migrations ..." -ForegroundColor Cyan
    & $alembicExe revision --autogenerate -m "foundation_layer_v1"
    & $alembicExe upgrade head
}

Write-Host ""
Write-Host "==> Done. Start the API with:" -ForegroundColor Green
Write-Host "    .\.venv\Scripts\uvicorn.exe app.main:app --reload" -ForegroundColor White
Write-Host "    Then open http://127.0.0.1:8000/health" -ForegroundColor White
