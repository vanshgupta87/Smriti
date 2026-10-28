@echo off
title Smriti CDS - FastAPI Backend Server (Port 8000)
cd /d "%~dp0"

echo =======================================================
echo   Smriti CDS Research Engine - Backend Launcher
echo =======================================================

set PYTHON_CMD=

if exist "%~dp0.venv311\Scripts\python.exe" (
    set "PYTHON_CMD=%~dp0.venv311\Scripts\python.exe"
    echo [OK] Using virtual environment: .venv311
    goto :found_python
)

if exist "%~dp0.venv\Scripts\python.exe" (
    set "PYTHON_CMD=%~dp0.venv\Scripts\python.exe"
    echo [OK] Using virtual environment: .venv
    goto :found_python
)

where python >nul 2>nul
if %errorlevel% equ 0 (
    set "PYTHON_CMD=python"
    echo [OK] Using system Python on PATH
    goto :found_python
)

echo [ERROR] No Python executable found in .venv311, .venv, or system PATH!
echo Please ensure your Python virtual environment is installed.
pause
exit /b 1

:found_python
echo [INFO] Starting Uvicorn backend on http://127.0.0.1:8000 ...
"%PYTHON_CMD%" -m uvicorn backend.app:app --reload --host 0.0.0.0 --port 8000
pause
