@echo off
title Smriti CDS - Next.js Frontend (Port 3000)
cd /d "%~dp0frontend"

echo =======================================================
echo   Smriti CDS Clinical Command Center - Frontend Launcher
echo =======================================================

echo [INFO] Starting Next.js Dev Server on http://localhost:3000 ...
npm run dev
pause
