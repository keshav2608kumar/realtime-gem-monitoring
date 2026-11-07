@echo off
title GeM BidWatch — Live Web Dashboard
color 0B
echo ============================================================
echo   Starting GeM BidWatch Executive Web Dashboard...
echo ============================================================
echo.
cd /d "%~dp0backend"
start http://localhost:8000/dashboard
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
pause
