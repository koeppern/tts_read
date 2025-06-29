@echo off
REM =================================================================
REM  VorleseApp - Manueller Start (für Tests)
REM =================================================================

echo.
echo ============================================
echo    VorleseApp - Manueller Start
echo ============================================
echo.
echo Startet die VorleseApp zum Testen.
echo.
echo Hotkeys:
echo   Strg+1 = Vorlesen (Action 0)
echo   Strg+2 = Vorlesen (Action 1) 
echo   Strg+3 = Pause/Resume
echo   Strg+4 = Text-Fenster zeigen/verstecken
echo.
echo Hinweis: Für globale Hotkeys sind Administrator-
echo         Rechte erforderlich!
echo.
echo ============================================
echo.

REM Zum Projektverzeichnis wechseln
cd /d "%~dp0"
cd src\prototype

REM Prüfe und beende vorherige Instanzen
echo Pruefe auf vorherige VorleseApp-Instanzen...
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
    echo.
    
    endlocal
) else (
    echo Keine vorherigen Instanzen gefunden.
    echo.
)

REM Umgebungsvariablen setzen
set VORLESE_MANUAL_START=1
set VORLESE_KILL_PREVIOUS=1

REM App starten
echo Starte VorleseApp...
python main.py

echo.
echo VorleseApp wurde beendet.
echo Drücken Sie eine Taste zum Schließen...
pause >nul 