@echo off
REM =================================================================
REM  VorleseApp - Autostart Script für Windows-Systemstart
REM =================================================================
REM  Diese Datei startet die VorleseApp automatisch beim Systemstart
REM  mit Administrator-Rechten für globale Hotkeys.
REM =================================================================

echo.
echo [%DATE% %TIME%] VorleseApp Autostart wird ausgefuehrt...
echo.

REM Administrator-Rechte prüfen
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo WARNUNG: Keine Administrator-Rechte erkannt!
    echo Die globalen Hotkeys funktionieren eventuell nicht korrekt.
    echo.
)

REM Zum Projektverzeichnis wechseln
cd /d "%~dp0"

REM Prüfen ob src/prototype existiert
if not exist "src\prototype" (
    echo FEHLER: src\prototype Verzeichnis nicht gefunden!
    echo Aktuelles Verzeichnis: %CD%
    pause
    exit /b 1
)

cd src\prototype

REM Prüfen ob main.py existiert
if not exist "main.py" (
    echo FEHLER: main.py nicht gefunden!
    echo Aktuelles Verzeichnis: %CD%
    pause
    exit /b 1
)

REM Prüfe und beende vorherige Instanzen
echo [%DATE% %TIME%] Pruefe auf vorherige VorleseApp-Instanzen...
tasklist /FI "IMAGENAME eq python.exe" /FO CSV | findstr /C:"main.py" >nul 2>&1
if %errorLevel% equ 0 (
    echo Vorherige VorleseApp-Instanzen gefunden - beende diese...
    
    REM Setze delayed expansion für Variablen in Schleifen
    setlocal EnableDelayedExpansion
    
    REM Beende alle Python-Prozesse die main.py ausführen (für VorleseApp)
    for /f "tokens=2 delims=," %%i in ('tasklist /FI "IMAGENAME eq python.exe" /FO CSV ^| findstr /C:"main.py"') do (
        set "pid=%%i"
        set "pid=!pid:"=!"
        echo Beende Prozess ID: !pid!
        taskkill /PID !pid! /F >nul 2>&1
    )
    
    REM Kurz warten bis Prozesse beendet sind
    timeout /t 2 /nobreak >nul 2>&1
    echo Vorherige Instanzen beendet.
    
    endlocal
) else (
    echo Keine vorherigen Instanzen gefunden.
)

REM Umgebungsvariablen für Autostart setzen
set VORLESE_AUTOSTART=1
set VORLESE_BATCH_MODE=1
set VORLESE_KILL_PREVIOUS=1

REM Stille Ausführung für Autostart (keine Pause am Ende)
echo [%DATE% %TIME%] Starte VorleseApp...
echo Hotkeys: Strg+1, Strg+2 (Vorlesen), Strg+3 (Pause), Strg+4 (Fenster)
echo.

REM Python-App starten
python main.py

REM Falls die App unerwartet beendet wird, protokollieren
echo [%DATE% %TIME%] VorleseApp wurde beendet (Exit Code: %ERRORLEVEL%)

REM Für Autostart: Nicht pausieren, sofort beenden
exit /b %ERRORLEVEL% 