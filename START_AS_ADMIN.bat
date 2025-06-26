@echo off
echo ========================================
echo    TTS Vorlese-App (Administrator)
echo ========================================
echo.
echo Startet die Anwendung mit Administrator-Rechten
echo fuer globale Hotkey-Funktionalitaet.
echo.
echo Hotkeys:
echo   STRG+1 = Deutsche Sprachausgabe
echo   STRG+2 = Englische Sprachausgabe  
echo   STRG+3 = Pause/Fortsetzen
echo.
echo ========================================
echo.

cd /d "%~dp0"
py -3 src/prototype/main.py

echo.
echo Anwendung beendet. Druecken Sie eine Taste...
pause >nul 