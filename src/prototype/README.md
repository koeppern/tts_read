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