$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$backendDir = Join-Path $repoRoot "backend"
$frontendDir = Join-Path $repoRoot "frontend"
$pythonExe = Join-Path $repoRoot ".venv\Scripts\python.exe"
$pidFile = Join-Path $repoRoot ".dev-pids.json"
$logDir = Join-Path $repoRoot ".dev-logs"

if (-not (Test-Path $pythonExe)) {
    throw "No existe el entorno virtual en $pythonExe"
}

if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir | Out-Null
}

function Test-PortInUse([int]$Port) {
    return [bool](Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue)
}

if (Test-PortInUse 8000) {
    throw "El puerto 8000 ya esta en uso. Cierra ese proceso antes de levantar backend."
}

if (Test-PortInUse 5173) {
    throw "El puerto 5173 ya esta en uso. Cierra ese proceso antes de levantar frontend."
}

$backendOut = Join-Path $logDir "backend.out.log"
$backendErr = Join-Path $logDir "backend.err.log"
$frontendOut = Join-Path $logDir "frontend.out.log"
$frontendErr = Join-Path $logDir "frontend.err.log"

if (Test-Path $backendOut) { Remove-Item $backendOut -Force }
if (Test-Path $backendErr) { Remove-Item $backendErr -Force }
if (Test-Path $frontendOut) { Remove-Item $frontendOut -Force }
if (Test-Path $frontendErr) { Remove-Item $frontendErr -Force }

$backendProc = Start-Process -FilePath $pythonExe `
    -ArgumentList @("-m", "uvicorn", "api.main_sqlite:app", "--host", "127.0.0.1", "--port", "8000") `
    -WorkingDirectory $backendDir `
    -RedirectStandardOutput $backendOut `
    -RedirectStandardError $backendErr `
    -PassThru

$frontendProc = Start-Process -FilePath "npm.cmd" `
    -ArgumentList @("run", "dev", "--", "--host", "127.0.0.1", "--port", "5173") `
    -WorkingDirectory $frontendDir `
    -RedirectStandardOutput $frontendOut `
    -RedirectStandardError $frontendErr `
    -PassThru

Start-Sleep -Seconds 2

$pids = [ordered]@{
    backend_pid = $backendProc.Id
    frontend_pid = $frontendProc.Id
    started_at = (Get-Date).ToString("s")
}

($pids | ConvertTo-Json -Depth 3) | Set-Content -Path $pidFile -Encoding UTF8

Write-Host "Backend PID: $($backendProc.Id)"
Write-Host "Frontend PID: $($frontendProc.Id)"
Write-Host "Backend URL: http://127.0.0.1:8000/docs"
Write-Host "Frontend URL: http://127.0.0.1:5173"
Write-Host "Logs: $logDir"
Write-Host "Para apagar ambos: powershell -ExecutionPolicy Bypass -File scripts/dev-down.ps1"