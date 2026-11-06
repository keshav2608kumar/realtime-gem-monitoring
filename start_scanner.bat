@echo off
title GeM BidWatch - 24/7 Domestic Indian Scanner
color 0C
echo ============================================================
echo   GeM BidWatch - Live 24/7 Scanner (Bangalore Toner & Printer)
echo ============================================================
echo.
cd /d "%~dp0"
python local_scanner.py
pause
