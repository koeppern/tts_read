@echo off
REM Force-kill startup script for Vorlese-App
REM Uses aggressive force-kill for previous instances

echo Starting Vorlese-App (Force-Kill Mode)...
echo This mode will aggressively terminate previous instances.
echo.

REM Set environment variables for force-kill mode
set VORLESE_BATCH_MODE=1
set VORLESE_FAST_KILL=1

REM Change to the script directory
cd /d "%~dp0"

REM Start the application
python main.py

pause 