<#
.SYNOPSIS
    Build the SotDL RPG Recorder .exe locally using PyInstaller.

.DESCRIPTION
    Reads the version from desktop-app/app/__version__.py, runs PyInstaller
    with build.spec, and reports the output location.

.EXAMPLE
    .\scripts\build.ps1
#>

$ErrorActionPreference = "Stop"

# ── Read version ────────────────────────────────────────────────
$versionFile = Join-Path $PSScriptRoot "..\desktop-app\app\__version__.py"
$versionLine = Get-Content $versionFile | Where-Object { $_ -match '__version__' }
$version = ($versionLine -replace '.*"(.+)".*', '$1')
Write-Host "`n🎮  Building SotDL RPG Recorder v$version" -ForegroundColor Cyan
Write-Host "─────────────────────────────────────────" -ForegroundColor DarkGray

# ── Install deps if needed ──────────────────────────────────────
$env:PYTHON_KEYRING_BACKEND = "keyring.backends.null.NullKeyring"
Write-Host "`n📦  Checking dependencies..." -ForegroundColor Yellow
pip install -q -r (Join-Path $PSScriptRoot "..\requirements.txt") 2>&1 | Out-Null
pip install -q -r (Join-Path $PSScriptRoot "..\desktop-app\requirements.txt") 2>&1 | Out-Null

# ── Build ───────────────────────────────────────────────────────
Write-Host "`n🔨  Running PyInstaller..." -ForegroundColor Yellow
Push-Location (Join-Path $PSScriptRoot "..\desktop-app")
try {
    pyinstaller build.spec --noconfirm 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "`n❌  Build failed!" -ForegroundColor Red
        exit 1
    }
} finally {
    Pop-Location
}

# ── Report ──────────────────────────────────────────────────────
$distDir = Join-Path $PSScriptRoot "..\desktop-app\dist"
$exe = Get-ChildItem -Path $distDir -Filter "*.exe" -Recurse | Select-Object -First 1

if ($exe) {
    Write-Host "`n✅  Build successful!" -ForegroundColor Green
    Write-Host "    Output: $($exe.FullName)" -ForegroundColor White
    Write-Host "    Size:   $([math]::Round($exe.Length / 1MB, 1)) MB" -ForegroundColor White
    Write-Host "`n📋  To release:" -ForegroundColor Cyan
    Write-Host "    1. git add -A && git commit -m 'release: v$version'" -ForegroundColor Gray
    Write-Host "    2. git tag v$version" -ForegroundColor Gray
    Write-Host "    3. git push && git push --tags" -ForegroundColor Gray
    Write-Host "    → GitHub Actions will create the release automatically`n" -ForegroundColor Gray
} else {
    Write-Host "`n⚠️  Build completed but .exe not found in dist/" -ForegroundColor Yellow
}
