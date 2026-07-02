# From repo root:  .\scripts\start-backend.ps1
# Do NOT paste this file into the terminal - run the file only.

$ErrorActionPreference = "Stop"
$BackendDir = (Resolve-Path (Join-Path $PSScriptRoot "..\backend")).Path
Set-Location $BackendDir

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created backend\.env - edit DATABASE_URL" -ForegroundColor Yellow
}

$Python = Join-Path $BackendDir ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    $RootVenv = (Join-Path (Split-Path $BackendDir -Parent) ".venv\Scripts\python.exe")
    if (Test-Path $RootVenv) {
        $Python = $RootVenv
        Write-Host "Using CRM\.venv" -ForegroundColor Cyan
    }
    else {
        python -m venv (Join-Path $BackendDir ".venv")
        & (Join-Path $BackendDir ".venv\Scripts\pip.exe") install -r requirements.txt
        $Python = Join-Path $BackendDir ".venv\Scripts\python.exe"
    }
}

Write-Host "Backend: $BackendDir" -ForegroundColor Green
# /T in stop-backend.ps1 kills the reloader tree; Ctrl+C alone often leaves a child on Windows.
& $Python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
