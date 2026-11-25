<#
.SYNOPSIS
    Stops all DecentralID development processes (ports 8545, 8000, 5173).
#>

$ports = @(8545, 8000, 5173)

Write-Host "Stopping DecentralID development services..." -ForegroundColor Yellow

foreach ($port in $ports) {
    $processes = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique
    if ($processes) {
        foreach ($pidToKill in $processes) {
            try {
                $proc = Get-Process -Id $pidToKill -ErrorAction SilentlyContinue
                if ($proc) {
                    Write-Host "Stopping PID $pidToKill ($($proc.ProcessName)) on port $port..." -ForegroundColor Cyan
                    Stop-Process -Id $pidToKill -Force -ErrorAction SilentlyContinue
                }
            } catch {
                Write-Host "Could not stop PID $pidToKill: $_" -ForegroundColor Red
            }
        }
    } else {
        Write-Host "No process listening on port $port." -ForegroundColor Gray
    }
}

Write-Host "All DecentralID services stopped." -ForegroundColor Green
