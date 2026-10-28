# Smriti CDS - PowerShell Service Launcher
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host "  Smriti CDS Research Engine - Development Launcher    " -ForegroundColor Cyan
Write-Host "=======================================================" -ForegroundColor Cyan

# Detect Python
$PythonExe = $null
if (Test-Path "$ScriptDir\.venv311\Scripts\python.exe") {
    $PythonExe = "$ScriptDir\.venv311\Scripts\python.exe"
    Write-Host "[OK] Detected virtual environment: .venv311" -ForegroundColor Green
} elseif (Test-Path "$ScriptDir\.venv\Scripts\python.exe") {
    $PythonExe = "$ScriptDir\.venv\Scripts\python.exe"
    Write-Host "[OK] Detected virtual environment: .venv" -ForegroundColor Green
} else {
    $PythonExe = "python"
    Write-Host "[OK] Using system python on PATH" -ForegroundColor Green
}

# Start backend in a new process
Write-Host "[INFO] Starting FastAPI Backend on http://127.0.0.1:8000..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$ScriptDir'; & '$PythonExe' -m uvicorn backend.app:app --reload --host 127.0.0.1 --port 8000"

# Start frontend in a new process
Write-Host "[INFO] Starting Next.js Frontend on http://localhost:3000..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$ScriptDir\frontend'; npm run dev"

Write-Host "`nAll services launched!" -ForegroundColor Green
Write-Host "Backend:  http://127.0.0.1:8000/docs" -ForegroundColor Cyan
Write-Host "Frontend: http://localhost:3000" -ForegroundColor Cyan
