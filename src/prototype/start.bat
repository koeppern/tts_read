@echo off
REM Standard startup script for Vorlese-App
REM Includes process cleanup for safety

echo Starting Vorlese-App...
echo.

REM Set batch mode flag for auto-detection
set VORLESE_BATCH_MODE=1

REM Change to the script directory
cd /d "%~dp0"

REM Start the application
python main.py

pause 