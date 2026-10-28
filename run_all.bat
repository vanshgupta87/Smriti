@echo off
title Smriti CDS - Launch All Services
cd /d "%~dp0"

echo =======================================================
echo   Smriti CDS - Starting Backend and Frontend
echo =======================================================

echo [1/2] Launching Backend Server in new window...
start "Smriti Backend (Port 8000)" cmd /k "%~dp0run_backend.bat"

echo [2/2] Launching Frontend Server in new window...
start "Smriti Frontend (Port 3000)" cmd /k "%~dp0run_frontend.bat"

echo.
echo =======================================================
echo   Both services are launching:
echo   - Backend:  http://127.0.0.1:8000
echo   - Frontend: http://localhost:3000
echo =======================================================
echo.
