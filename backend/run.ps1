# From backend folder:  .\run.ps1

$ErrorActionPreference = "Stop"
$here = $PSScriptRoot
Set-Location $here

$py = Join-Path $here ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) {
    $py = Join-Path (Split-Path $here -Parent) ".venv\Scripts\python.exe"
}
if (-not (Test-Path $py)) {
    Write-Error "No venv. Run: python -m venv .venv; .\.venv\Scripts\pip install -r requirements.txt"
}

& $py -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
