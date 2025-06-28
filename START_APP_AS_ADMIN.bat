@echo off
echo ============================================
echo    VorleseApp - Administrator Start
echo ============================================
echo.
echo Starting TTS application with admin privileges...
echo This is required for global hotkeys to work.
echo.

cd /d "%~dp0"
cd src\prototype

echo Current directory: %CD%
echo.
echo Starting application...
python main.py

echo.
echo Press any key to close this window...
pause >nul 