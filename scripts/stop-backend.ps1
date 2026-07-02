# Stop backend (uvicorn on port 8000):  .\scripts\stop-backend.ps1

$ErrorActionPreference = "SilentlyContinue"
$killed = @()

# 1) All python processes that run uvicorn (parent + reloader children)
Get-CimInstance Win32_Process -Filter "name='python.exe'" | ForEach-Object {
    if ($_.CommandLine -match "uvicorn|app\.main|spawn_main|multiprocessing\.spawn") {
        $killed += $_.ProcessId
        Write-Host "Stopping uvicorn PID $($_.ProcessId) (tree)..."
        taskkill /PID $_.ProcessId /F /T | Out-Null
    }
}

# 2) Whatever still listens on port 8000
$pids = @()
try {
    $pids = Get-NetTCPConnection -LocalPort 8000 -State Listen |
        Select-Object -ExpandProperty OwningProcess -Unique
}
catch { }

if (-not $pids) {
    $pids = netstat -ano | Select-String ":8000\s+.*LISTENING" | ForEach-Object {
        if ($_ -match "\s+(\d+)\s*$") { [int]$Matches[1] }
    } | Select-Object -Unique
}

foreach ($pid in $pids) {
    if ($pid -in $killed) { continue }
    Write-Host "Stopping port 8000 PID $pid (tree)..."
    taskkill /PID $pid /F /T | Out-Null
    $killed += $pid
}

Start-Sleep -Milliseconds 800

$alive = $false
try {
    $r = Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/health" -UseBasicParsing -TimeoutSec 2
    if ($r.StatusCode -eq 200) { $alive = $true }
}
catch { }

if ($alive) {
    Write-Host ""
    Write-Host "Server still answers on :8000. Options:" -ForegroundColor Yellow
    Write-Host "  - Close the terminal window where you started uvicorn"
    Write-Host "  - PyCharm: red Stop button on the Run tab"
    Write-Host "  - Last resort (kills ALL python.exe):"
    Write-Host "      taskkill /F /IM python.exe"
}
elseif ($killed.Count -eq 0) {
    Write-Host "Nothing found on port 8000 / uvicorn." -ForegroundColor Green
}
else {
    Write-Host "Backend stopped." -ForegroundColor Green
}
