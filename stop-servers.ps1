# Stop Backend and Frontend servers for Family Expense Tracker

function Stop-Port {
    param([int]$Port, [string]$Label)

    $conn = netstat -ano | Select-String ":$Port\s" | Select-String "LISTENING"
    if ($conn) {
        $procId = ($conn -split '\s+')[-1]
        $proc = Get-Process -Id $procId -ErrorAction SilentlyContinue
        Write-Host "Stopping $Label (port $Port, PID $procId - $($proc.ProcessName))..." -ForegroundColor Yellow
        Stop-Process -Id $procId -Force
        Write-Host "  Stopped." -ForegroundColor Green
    } else {
        Write-Host "$Label (port $Port) is not running." -ForegroundColor Gray
    }
}

Stop-Port -Port 8000 -Label "Backend"
Stop-Port -Port 5173 -Label "Frontend"

Write-Host ""
Write-Host "All servers stopped." -ForegroundColor Green
