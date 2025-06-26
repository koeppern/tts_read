# Produktanforderungsdokument (PRD)

## Anwendungstitel
**Vorlese-Hotkey-App für Windows**

## Zielsetzung
Entwicklung einer minimalistischen Windows-Anwendung, die es erlaubt, markierten Text per globalem Hotkey vorlesen zu lassen – in Deutsch oder Englisch, mit Pause-Funktion. Die App läuft im Hintergrund mit einem System-Tray-Icon und erlaubt einfache Konfiguration über eine JSON-Datei.

**Prototyp-Hinweis**: Diese Version ist als funktionsfähiger Prototyp konzipiert. Sicherheitsaspekte und erweiterte Fehlerbehandlung werden für die Produktivversion vorgesehen.

---

## 1. Zielgruppe
* Nutzer, die häufig Texte lesen und sich diese alternativ vorlesen lassen möchten
* Besonders nützlich für sehbeeinträchtigte Nutzer oder Anwender mit Fokus auf Accessibility
* Personen mit hohem Textaufkommen (z. B. Fachliteratur, Webseiten, PDFs)

---

## 2. Hauptfunktionen

### 2.1 Hotkey-gesteuertes Vorlesen
* **Strg+1**: markierten Text auf Deutsch vorlesen
* **Strg+2**: markierten Text auf Englisch vorlesen
* **Strg+3**: Vorlesen pausieren bzw. fortsetzen
* **Textauswahl wird per Zwischenablage übernommen**
* **Hinweis**: Die Sprachwahl erfolgt implizit über die konfigurierte Stimme - keine automatische Spracherkennung

### 2.2 Spracheinstellungen
* Jede Tastenkombination ist in der Konfigurationsdatei frei belegbar
* Pro Sprache ist ein Sprachmodul (SAPI-Stimme) samt Sprechgeschwindigkeit definierbar

### 2.3 System-Tray-Integration
* Platzhalter-Icon im Infobereich
* Rechtsklick-Menü:
  - „Einstellungen öffnen“ → öffnet `settings.json` im Texteditor
  - „Beenden“ → beendet Anwendung sofort

### 2.4 Konfigurierbarkeit
* Konfigurationsdatei `settings.json` im gleichen Ordner wie die EXE-Datei
* Beispielstruktur:
  ```json
  {
    "hotkeys": {
      "deSpeak": "Ctrl+1",
      "enSpeak": "Ctrl+2",
      "pauseResume": "Ctrl+3"
    },
    "voices": {
      "Ctrl+1": {
        "engine": "SAPI",
        "voice": "Microsoft Hedda",
        "rate": 1.0
      },
      "Ctrl+2": {
        "engine": "SAPI",
        "voice": "Microsoft David",
        "rate": 1.0
      }
    },
    "startup": false
  }
  ```

---

## 3. Architektur

### 3.1 Komponenten
* **Hotkey-Listener** (z. B. via `keyboard`- oder `pynput`-Lib)
* **Clipboard-Reader**: liest aktuellen Text aus Zwischenablage
* **TextSpeaker-Interface**:
  ```python
  class TextSpeaker:
      def speak(self, text: str, lang: str, rate: float): ...
      def pause(self): ...
      def resume(self): ...
      def stop(self): ...
  ```
* **SAPI-Implementierung** (z. B. via `pyttsx3`)
* **SettingsManager**: lädt `settings.json`, bietet Zugriff auf konfigurierbare Parameter
* **TrayIconService** (z. B. via `pystray`)
* **MainLoop**: zentrale Event-Schleife

---

## 4. Startverhalten

* Anwendung wird manuell gestartet (Standard)
* Optional: Autostart per Windows Registry (`startup: true` in der Config)

---

## 5. Use Cases

### UC1 – Deutsches Vorlesen
* Benutzer markiert Text, drückt Strg+1 → Text wird auf Deutsch vorgelesen

### UC2 – Englisches Vorlesen
* Benutzer markiert Text, drückt Strg+2 → Text wird auf Englisch vorgelesen

### UC3 – Pausieren und Fortsetzen
* Benutzer drückt Strg+3 → Vorlesen wird pausiert oder fortgesetzt

### UC4 – Konfiguration anpassen
* Benutzer klickt im Tray mit rechts → „Einstellungen öffnen“  
* Ändert `settings.json`  
* Speichert Datei → Änderungen gelten nach einem Neustart oder Re-Init

---

## 6. Technische Anforderungen

* Betriebssystem: Windows 10 oder höher
* Keine Adminrechte für Betrieb
* Tray-Icon sichtbar im Overflow-Menü
* Anwendung speichert keine Daten dauerhaft
* Ressourcenverbrauch minimal (< 100 MB RAM, < 2% CPU)

---

## 7. Fehlerverhalten

* Keine Stimme gefunden → Fehlermeldung im Tray oder Log
* Zwischenablage leer → keine Aktion
* Fehlerhafte `settings.json` → Fallback auf Defaults

---

## 8. Ausblick / Erweiterungsideen

* Unterstützung weiterer Stimmen oder Sprachausgabe-Engines (z. B. Azure TTS)
* GUI-Editor für Einstellungen
* Speicherung von zuletzt gelesenen Texten (optional)
* Audio-Ausgabe auf alternative Geräte umleiten (z. B. Bluetooth-Box)

---

## 9. Icon & Branding

* Platzhalter-Icon im PNG-Format (Dateiname: `icon.png`)
* Im Release später durch angepasstes App-Icon ersetzbar

---

## 10. Lizenzierung & Verteilung

* Lizenz: MIT oder Apache 2.0 (TBD)
* Verteilung: Portable EXE oder Installer (NSIS oder InnoSetup)

---
