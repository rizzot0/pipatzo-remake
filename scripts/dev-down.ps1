$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$pidFile = Join-Path $repoRoot ".dev-pids.json"

if (-not (Test-Path $pidFile)) {
    Write-Host "No hay archivo de PIDs (.dev-pids.json). Nada que detener."
    exit 0
}

$pids = Get-Content $pidFile -Raw | ConvertFrom-Json

function Stop-IfRunning([int]$Pid, [string]$Name) {
    if (-not $Pid) {
        return
    }

    $proc = Get-Process -Id $Pid -ErrorAction SilentlyContinue
    if ($proc) {
        Stop-Process -Id $Pid -Force
        Write-Host "$Name detenido (PID $Pid)"
    } else {
        Write-Host "$Name no estaba corriendo (PID $Pid)"
    }
}

Stop-IfRunning -Pid $pids.backend_pid -Name "Backend"
Stop-IfRunning -Pid $pids.frontend_pid -Name "Frontend"

Remove-Item $pidFile -Force
Write-Host "Entorno de desarrollo detenido."