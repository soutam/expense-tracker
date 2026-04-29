# Start Backend and Frontend servers for Family Expense Tracker

$ROOT = $PSScriptRoot

Write-Host "Starting Backend (FastAPI on port 8000)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$ROOT\backend'; uvicorn app.main:app --reload --host 127.0.0.1 --port 8000" -WindowStyle Normal

Start-Sleep -Seconds 2

Write-Host "Starting Frontend (Vite on port 5173)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$ROOT\frontend'; npm run dev" -WindowStyle Normal

Write-Host ""
Write-Host "Servers started:" -ForegroundColor Green
Write-Host "  Backend  -> http://localhost:8000" -ForegroundColor White
Write-Host "  API Docs -> http://localhost:8000/docs" -ForegroundColor White
Write-Host "  Frontend -> http://localhost:5173" -ForegroundColor White
