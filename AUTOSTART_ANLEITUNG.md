# 🚀 VorleseApp - Autostart Einrichtung

## 📁 Verfügbare Dateien

Nach dem Aufräumen haben Sie jetzt nur noch **3 wichtige Dateien**:

1. **`VORLESE_AUTOSTART.bat`** - Hauptscript für Autostart
2. **`VorleseApp_AdminAutostart.vbs`** - VBScript für Admin-Rechte
3. **`START_MANUAL.bat`** - Für manuellen Test-Start

---

## ⚙️ Autostart einrichten

### Methode 1: Autostart-Ordner (EMPFOHLEN)

1. **Windows-Taste + R** drücken
2. **`shell:startup`** eingeben und Enter
3. Der **Autostart-Ordner** öffnet sich
4. **VorleseApp_AdminAutostart.vbs** in den Autostart-Ordner **kopieren**

```
C:\Users\[IhrName]\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\
```

### Methode 2: Task Scheduler (Erweitert)

1. **Taskplaner** öffnen (`Win + R` → `taskschd.msc`)
2. **"Einfache Aufgabe erstellen"**
3. **Name:** `VorleseApp Autostart`
4. **Trigger:** `Beim Anmelden`
5. **Aktion:** `Programm starten`
6. **Programm:** Pfad zu `VorleseApp_AdminAutostart.vbs`
7. **"Mit höchsten Rechten ausführen"** aktivieren

---

## 🔧 Was passiert beim Autostart?

1. **VBScript** wird ausgeführt
2. **UAC-Dialog** erscheint (Administrator-Rechte)
3. **VORLESE_AUTOSTART.bat** startet mit Admin-Rechten
4. **VorleseApp** läuft im Hintergrund (System Tray)
5. **Globale Hotkeys** sind sofort verfügbar:
   - **Strg+1** = Vorlesen (Action 0)
   - **Strg+2** = Vorlesen (Action 1)
   - **Strg+3** = Pause/Resume
   - **Strg+4** = Text-Fenster

---

## ⚠️ Wichtige Hinweise

### Administrator-Rechte
- **ERFORDERLICH** für globale Hotkeys
- UAC-Dialog wird **einmalig** beim Login angezeigt
- Nach Bestätigung läuft die App stumm im Hintergrund

### Fehlerbehandlung
- Script prüft automatisch alle Pfade
- Zeigt Fehlermeldungen bei Problemen
- Protokolliert Start/Stop-Zeiten

### Deaktivieren
- **Autostart-Datei** aus dem Startup-Ordner entfernen
- ODER Task im Taskplaner deaktivieren

---

## 🧪 Testen

### Vor Autostart-Einrichtung:
```cmd
# Manuell testen mit:
START_MANUAL.bat
```

### Nach Autostart-Einrichtung:
1. **Computer neu starten**
2. **UAC-Dialog bestätigen**
3. **Strg+1** testen (Text markieren und Hotkey drücken)
4. **System Tray** prüfen (VorleseApp-Icon)

---

## 📝 Zusätzliche Konfiguration

### Autostart ohne UAC (Erweitert)
Falls Sie das UAC-Dialog vermeiden möchten:
1. **Group Policy Editor** verwenden
2. **Task Scheduler** mit höchsten Rechten
3. **Lokale Sicherheitsrichtlinien** anpassen

⚠️ **Sicherheitshinweis:** Nicht empfohlen für normale Benutzer

---

## 🔧 Troubleshooting

### Problem: Hotkeys funktionieren nicht
- **Lösung:** Administrator-Rechte prüfen
- **Check:** `net session` in CMD ausführen

### Problem: App startet nicht
- **Lösung:** Pfade in VORLESE_AUTOSTART.bat prüfen
- **Check:** Python Installation verfügbar?

### Problem: UAC-Dialog nervt
- **Lösung:** Task Scheduler verwenden
- **Alternative:** Einmal bestätigen, dann läuft es still

---

## ✅ Erfolgreich eingerichtet!

Nach erfolgreicher Einrichtung:
- ✅ VorleseApp startet automatisch beim Login
- ✅ Läuft unsichtbar im System Tray
- ✅ Globale Hotkeys funktionieren sofort
- ✅ Keine manuelle Bedienung erforderlich

**Die VorleseApp ist jetzt vollständig automatisiert! 🎉** 