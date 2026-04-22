# GMP Platform — Windows Autonomous Cursor Setup
# Run this script ONCE in an elevated PowerShell (Run as Administrator).
# After running: Cursor will operate fully autonomously without UAC prompts.
#
# Usage:
#   Right-click PowerShell → Run as Administrator
#   cd "C:\Users\fella\OneDrive\Desktop\work\gmp-platform\scripts"
#   .\setup-windows-autonomous.ps1
#
# What this does:
#   1. Sets PowerShell execution policy (no script blocking)
#   2. Adds Windows Defender exclusions (no false-positive quarantines)
#   3. Grants full filesystem permissions on the project folder
#   4. Creates an elevated Cursor launch shortcut (no UAC prompt)
#   5. Disables UAC elevation prompts for admin actions (dev machine only)
#   6. Prints migration instructions for moving project off OneDrive

param(
    [string]$ProjectPath = "C:\Users\fella\OneDrive\Desktop\work\gmp-platform",
    [string]$LocalDevPath = "C:\Dev\gmp-platform",
    [string]$UserName = $env:USERNAME
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "  GMP Platform — Windows Autonomous Setup" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# ── STEP 1: PowerShell Execution Policy ──────────────────────────────────────
Write-Host "[1/6] Setting PowerShell execution policy..." -ForegroundColor Yellow
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope LocalMachine -Force
Write-Host "      Done. Scripts can now run without blocking." -ForegroundColor Green

# ── STEP 2: Windows Defender Exclusions ──────────────────────────────────────
Write-Host "[2/6] Adding Windows Defender exclusions..." -ForegroundColor Yellow

$exclusions = @(
    $ProjectPath,
    $LocalDevPath,
    "$env:LOCALAPPDATA\uv",
    "$env:LOCALAPPDATA\Programs\cursor",
    "$env:APPDATA\npm",
    "$env:APPDATA\npm-cache",
    "C:\Users\$UserName\.venv",
    "C:\Users\$UserName\AppData\Local\pypoetry",
    "C:\Program Files\nodejs",
    "C:\Program Files\Docker"
)

foreach ($path in $exclusions) {
    try {
        Add-MpPreference -ExclusionPath $path
        Write-Host "      Excluded: $path" -ForegroundColor Gray
    } catch {
        Write-Host "      Skipped (not found): $path" -ForegroundColor DarkGray
    }
}
Write-Host "      Done. Defender will not quarantine Python/Node processes." -ForegroundColor Green

# ── STEP 3: Grant full filesystem permissions on project folder ───────────────
Write-Host "[3/6] Granting full permissions on project folder..." -ForegroundColor Yellow
if (Test-Path $ProjectPath) {
    icacls $ProjectPath /grant "${UserName}:(OI)(CI)F" /T /Q
    Write-Host "      Done. $UserName has full control of $ProjectPath" -ForegroundColor Green
} else {
    Write-Host "      Skipped: $ProjectPath does not exist yet." -ForegroundColor DarkGray
}

# Also set up C:\Dev if it doesn't exist
if (-not (Test-Path "C:\Dev")) {
    New-Item -ItemType Directory -Path "C:\Dev" | Out-Null
    icacls "C:\Dev" /grant "${UserName}:(OI)(CI)F" /T /Q
    Write-Host "      Created C:\Dev with full permissions." -ForegroundColor Green
}

# ── STEP 4: Create elevated Cursor launch shortcut ───────────────────────────
Write-Host "[4/6] Creating elevated Cursor launch shortcut..." -ForegroundColor Yellow

# Find Cursor executable
$cursorPaths = @(
    "$env:LOCALAPPDATA\Programs\cursor\Cursor.exe",
    "$env:LOCALAPPDATA\cursor\Cursor.exe",
    "C:\Program Files\Cursor\Cursor.exe"
)

$cursorExe = $null
foreach ($p in $cursorPaths) {
    if (Test-Path $p) { $cursorExe = $p; break }
}

if ($cursorExe) {
    # Create a scheduled task that runs Cursor elevated without UAC prompt
    $taskName = "Cursor-GMP-Elevated"
    $action = New-ScheduledTaskAction `
        -Execute $cursorExe `
        -Argument "--new-window `"$LocalDevPath`""
    $settings = New-ScheduledTaskSettingsSet `
        -RunOnlyIfNetworkAvailable $false `
        -AllowStartIfOnBatteries $true `
        -DontStopIfGoingOnBatteries $true
    $principal = New-ScheduledTaskPrincipal `
        -UserId $env:USERNAME `
        -RunLevel Highest `
        -LogonType Interactive

    Register-ScheduledTask `
        -TaskName $taskName `
        -Action $action `
        -Settings $settings `
        -Principal $principal `
        -Force | Out-Null

    # Create desktop shortcut that triggers the scheduled task
    $desktopPath = [Environment]::GetFolderPath("Desktop")
    $shortcutPath = "$desktopPath\Cursor GMP (Admin).lnk"
    $wsh = New-Object -ComObject WScript.Shell
    $shortcut = $wsh.CreateShortcut($shortcutPath)
    $shortcut.TargetPath = "schtasks.exe"
    $shortcut.Arguments = "/run /tn `"$taskName`""
    $shortcut.WindowStyle = 7  # minimized
    $shortcut.Description = "Launch Cursor elevated for GMP platform (no UAC prompt)"
    $shortcut.Save()

    Write-Host "      Done. Use 'Cursor GMP (Admin)' shortcut on your Desktop." -ForegroundColor Green
    Write-Host "      Or run: Start-ScheduledTask -TaskName '$taskName'" -ForegroundColor Gray
} else {
    Write-Host "      WARNING: Cursor.exe not found. Install Cursor first." -ForegroundColor Red
    Write-Host "      Then re-run this script." -ForegroundColor Red
}

# ── STEP 5: Disable UAC elevation prompts (dev machine only) ─────────────────
Write-Host "[5/6] Configuring UAC for autonomous operation..." -ForegroundColor Yellow
Write-Host "      This disables UAC prompts for administrator-level actions." -ForegroundColor Gray
Write-Host "      ONLY appropriate for a dedicated development machine." -ForegroundColor Gray

$uacKey = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System"

# ConsentPromptBehaviorAdmin = 0 → Elevate without prompting
Set-ItemProperty -Path $uacKey -Name "ConsentPromptBehaviorAdmin" -Value 0
# PromptOnSecureDesktop = 0 → No secure desktop dim (faster)
Set-ItemProperty -Path $uacKey -Name "PromptOnSecureDesktop" -Value 0

Write-Host "      Done. A restart is required for UAC changes to take effect." -ForegroundColor Green

# ── STEP 6: OneDrive migration instructions ───────────────────────────────────
Write-Host "[6/6] OneDrive migration instructions..." -ForegroundColor Yellow
Write-Host ""
Write-Host "  IMPORTANT: Move the project off OneDrive to stop sync conflicts." -ForegroundColor Red
Write-Host "  OneDrive fights Cursor during rapid file writes (OSError 22)." -ForegroundColor Red
Write-Host "  The main.py already has a workaround patch — but the real fix is to move." -ForegroundColor Red
Write-Host ""
Write-Host "  Run these commands in a normal PowerShell after this script:" -ForegroundColor White
Write-Host ""
Write-Host "    xcopy `"$ProjectPath`" `"$LocalDevPath`" /E /I /H /Y" -ForegroundColor Cyan
Write-Host "    cd `"$LocalDevPath`"" -ForegroundColor Cyan
Write-Host "    git init" -ForegroundColor Cyan
Write-Host "    git add ." -ForegroundColor Cyan
Write-Host "    git commit -m `"feat(platform): initial commit — foundation HARDENED`"" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Then open Cursor from the 'Cursor GMP (Admin)' desktop shortcut." -ForegroundColor White
Write-Host "  It will open C:\Dev\gmp-platform elevated with no UAC prompts." -ForegroundColor White
Write-Host ""

# ── SUMMARY ──────────────────────────────────────────────────────────────────
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "  Setup Complete" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  ✅ PowerShell execution policy: RemoteSigned" -ForegroundColor Green
Write-Host "  ✅ Defender exclusions: project + uv + node + cursor" -ForegroundColor Green
Write-Host "  ✅ Filesystem permissions: full control granted" -ForegroundColor Green
if ($cursorExe) {
    Write-Host "  ✅ Elevated Cursor shortcut: Desktop → 'Cursor GMP (Admin)'" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  Cursor shortcut: SKIPPED (Cursor not found)" -ForegroundColor Yellow
}
Write-Host "  ✅ UAC prompts: disabled for admin actions" -ForegroundColor Green
Write-Host "  ⚠️  OneDrive migration: MANUAL STEP REQUIRED (see above)" -ForegroundColor Yellow
Write-Host ""
Write-Host "  RESTART REQUIRED for UAC changes to take effect." -ForegroundColor Red
Write-Host ""
