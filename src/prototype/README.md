# Vorlese-App Prototyp

## Installation

1. Python-Umgebung erstellen und aktivieren:
```bash
python -m venv venv
venv\Scripts\activate  # Windows
```

2. Abhängigkeiten installieren:
```bash
pip install -r ../../requirements.txt
```

## Ausführung

```bash
python main.py
```

## Nutzung

1. Die App startet im Hintergrund mit einem Icon im System-Tray
2. Text markieren und in Zwischenablage kopieren (Strg+C)
3. Hotkeys verwenden:
   - **Strg+1**: Text auf Deutsch vorlesen
   - **Strg+2**: Text auf Englisch vorlesen  
   - **Strg+3**: Vorlesen pausieren/fortsetzen

## Konfiguration

Die Einstellungen befinden sich in `config/settings.json`:
- Hotkeys anpassen
- Stimmen ändern
- Sprechgeschwindigkeit einstellen

Rechtsklick auf Tray-Icon → "Einstellungen öffnen"

## Hinweise

- Dies ist ein Prototyp - Sicherheitsaspekte sind noch nicht implementiert
- Windows SAPI-Stimmen müssen installiert sein
- Text muss manuell in Zwischenablage kopiert werden (Strg+C)

## Thread-Management und Process-Cleanup

Die Anwendung verfügt über ein robustes Thread-Management-System, das sicherstellt, dass keine "Zombie"-Threads oder -Prozesse im Hintergrund laufen bleiben.

### Startup-Cleanup

Beim Start der Anwendung wird automatisch ein Cleanup durchgeführt:

1. **Process-Cleanup**: Alle vorherigen Instanzen der Anwendung werden beendet
2. **Thread-Cleanup**: Alle registrierten Speech-Threads werden bereinigt
3. **Lock-File-Management**: Ein Lock-File wird erstellt, um die aktuelle Instanz zu identifizieren

### Thread-Registry

Alle Speech-Threads werden in einer globalen Registry verwaltet:

- **Automatische Registrierung**: Neue Speech-Threads werden automatisch registriert
- **Automatische Deregistrierung**: Threads werden nach Abschluss automatisch entfernt
- **Force-Cleanup**: Möglichkeit, alle Threads zwangsweise zu beenden

### Verwendung

#### Normale Anwendung starten:
```bash
# Mit Batch-Datei (empfohlen)
start.bat

# Oder direkt mit Python
python main.py
```

#### Schneller Start (ohne Process-Cleanup):
```bash
# Mit Batch-Datei für schnellen Start
start_fast.bat

# Oder mit Umgebungsvariable
set VORLESE_SKIP_PROCESS_CLEANUP=1 && python main.py
```

#### Aggressiver Force-Kill Modus:
```bash
# Mit Batch-Datei für Force-Kill
start_force_kill.bat

# Oder mit Umgebungsvariable
set VORLESE_FAST_KILL=1 && python main.py
```

#### Console-Modus für Debugging:
```bash
set VORLESE_CONSOLE_MODE=1 && python main.py
```

#### Kombinierte Modi:
```bash
# Schnell + Console-Modus
set VORLESE_SKIP_PROCESS_CLEANUP=1 && set VORLESE_CONSOLE_MODE=1 && python main.py

# Force-Kill + Console-Modus
set VORLESE_FAST_KILL=1 && set VORLESE_CONSOLE_MODE=1 && python main.py
```

#### Programmatische Verwendung:
```python
from text_speaker_v2 import startup_cleanup, cleanup_all_speech_threads

# Beim Anwendungsstart
startup_cleanup()  # Bereinigt vorherige Instanzen und Threads

# Manueller Thread-Cleanup (falls erforderlich)
cleanup_all_speech_threads()
```

### Technische Details

- **Process-Erkennung**: Verwendet `psutil` zur Erkennung von Python-Prozessen mit `main.py`
- **Graceful Termination**: Versucht zunächst SIGTERM, dann SIGKILL falls nötig
- **Thread-Synchronisation**: Thread-sichere Registry mit Locks
- **Lock-File**: `vorlese_app.lock` zur Prozess-Identifikation

### Umgebungsvariablen

- **`VORLESE_CONSOLE_MODE=1`**: Startet die Anwendung im Konsolen-Modus statt System Tray
- **`VORLESE_SKIP_PROCESS_CLEANUP=1`**: Überspringt das Beenden vorheriger Instanzen (schnellerer Start)
- **`VORLESE_FAST_KILL=1`**: Verwendet aggressiven Force-Kill für vorherige Instanzen (sofortige Beendigung)

### Sicherheit

- **Timeout-basiert**: Threads haben Timeouts für graceful termination (1 Sekunde)
- **Exception-Handling**: Robuste Fehlerbehandlung für alle Cleanup-Operationen
- **Daemon-Threads**: Speech-Threads sind als Daemon-Threads konfiguriert
- **Optimierter Process-Cleanup**: Reduzierte Timeouts und bessere Fehlerbehandlung

## 🚀 Starten der Anwendung

### Aus VS Code (empfohlen):
1. **Launch Configuration verwenden:**
   - Drücken Sie `F5` oder gehen Sie zu "Run and Debug"
   - Wählen Sie "Vorlese-App (Console Mode)" oder "Vorlese-App (Fast Startup)"
   - Die App startet im integrierten Terminal

2. **Direkt im Terminal:**
   ```bash
   # Im VS Code Terminal
   python main.py
   ```
   **Hinweis:** Die App läuft im Hintergrund - Sie sehen die Ausgabe möglicherweise nicht sofort.

### Aus der Kommandozeile:

#### Normale Anwendung starten:
```bash
# Mit Batch-Datei (empfohlen)
start.bat

# Oder direkt mit Python
python main.py
```

### 🔧 Umgebungsvariablen

Die Anwendung unterstützt folgende Umgebungsvariablen:

- **`VORLESE_CONSOLE_MODE=1`**: Startet die Anwendung im Konsolen-Modus statt System Tray
- **`VORLESE_SKIP_PROCESS_CLEANUP=1`**: Überspringt das Beenden vorheriger Instanzen (schnellerer Start)
- **`VORLESE_FAST_KILL=1`**: Verwendet aggressiven Force-Kill für vorherige Instanzen (sofortige Beendigung)
- **`VORLESE_BATCH_MODE=1`**: Markiert Ausführung aus Batch-Datei (für Auto-Erkennung)

### 🤖 Intelligente Auto-Erkennung

Die Anwendung erkennt automatisch die Laufzeitumgebung:

- **VS Code/IDEs**: Automatisch Fast-Startup + Console-Modus
- **Batch-Dateien**: Respektiert Benutzer-Konfiguration
- **Terminal**: Normal-Modus mit Console-Ausgabe
- **Unbekannt**: Sicherer Fast-Modus