@echo off
REM Fast startup script for Vorlese-App
REM Skips process cleanup for faster startup

echo Starting Vorlese-App (Fast Mode)...
echo This mode skips process cleanup for faster startup.
echo.

REM Set environment variables for fast startup
set VORLESE_BATCH_MODE=1
set VORLESE_SKIP_PROCESS_CLEANUP=1

REM Change to the script directory
cd /d "%~dp0"

REM Start the application
python main.py

pause 