# Produktanforderungsdokument (PRD) - Feature "Folge-Text-Fenster"

## 1. Feature-Übersicht
Entwicklung eines neuen Features, das es dem Anwender ermöglicht, während des Vorlesens ein separates Fenster zu öffnen. In diesem Fenster wird der vorgelesene Text angezeigt, wobei das aktuell gesprochene Wort synchron hervorgehoben wird. Dies verbessert das Mitleseerlebnis und die Barrierefreiheit.

---

## 2. Detaillierte Anforderungen

### 2.1 Aktivierung & Fenster
*   **Neuer Hotkey**: In der `settings.json` wird ein neuer Shortcut definiert (z.B. `"showReadAlongWindow": "Ctrl+Shift+H"`), um das Folge-Text-Fenster zu öffnen oder in den Vordergrund zu bringen.
*   **Fenstergröße**: Das Fenster öffnet sich standardmäßig mit einer Größe von 75% der Bildschirmhöhe und -breite.
*   **Fensterdesign**: Weißer Hintergrund mit schwarzem Text für maximale Lesbarkeit.

### 2.2 Textanzeige und -hervorhebung
*   **Textinhalt**: Das Fenster zeigt den vollständigen Text an, der gerade vorgelesen wird.
*   **Live-Hervorhebung**: Das aktuell vorgelesene Wort wird in Echtzeit mit einem gelben Textmarker-Effekt (gelber Hintergrund, schwarzer Text) hervorgehoben.
*   **Synchronisation**: Die Hervorhebung bewegt sich Wort für Wort synchron zum Sprachausgabe-Fortschritt.

### 2.3 Scroll-Verhalten
*   **Automatisches Scrollen**: Der Text-Container scrollt automatisch mit, sodass das hervorgehobene Wort immer im sichtbaren Bereich des Fensters bleibt (z.B. vertikal zentriert).
*   **Manuelles Scrollen**: Sobald der Benutzer manuell mit dem Mausrad oder der Scroll-Leiste scrollt, wird das automatische Scrollen temporär deaktiviert.
*   **Re-Aktivierung des Auto-Scrolls**: Durch Drücken der **Leertaste** wird das automatische Scrollen reaktiviert und die Ansicht springt zurück zur Position des aktuell vorgelesenen Wortes.

### 2.4 Textgröße anpassen
*   Die Schriftgröße im Fenster kann dynamisch angepasst werden:
    *   **Tastatur**: `Strg` + `+` (Plus) zum Vergrößern, `Strg` + `-` (Minus) zum Verkleinern.
    *   **Maus**: `Strg` + **Mausrad scrollen** (hoch/runter) zum Vergrößern/Verkleinern.

### 2.5 Schließen des Fensters & Persistenz
*   Das Fenster kann mit folgenden Aktionen geschlossen werden:
    *   Standard-Fenster-Schaltfläche "Schließen".
    *   Tastenkombination `Alt` + `F4`.
    *   Tastenkombination `Strg` + `Q`.
    *   Tastenkombination `Strg` + `W`.
*   **Persistenz der Schriftgröße**: Beim Schließen des Fensters wird der zuletzt eingestellte Wert für die Schriftgröße in der `settings.json` gespeichert (z.B. unter einem neuen Schlüssel `"readAlongWindowFontSize": 18`). Beim nächsten Öffnen wird diese Schriftgröße wieder verwendet.

---

## 3. Konfiguration in `settings.json`

Die `settings.json` wird um folgende (beispielhafte) Einträge erweitert:

```json
{
  "hotkeys": {
    "deSpeak": "Ctrl+1",
    "enSpeak": "Ctrl+2",
    "pauseResume": "Ctrl+3",
    "showReadAlongWindow": "Ctrl+Shift+H"
  },
  "voices": {
    // ... bestehende Konfiguration
  },
  "readAlongWindow": {
    "fontSize": 18,
    "highlightColor": "yellow"
  },
  "startup": false
}
```

---

## 4. Anwendungsfälle (Use Cases)

*   **UC1: Konzentriertes Mitlesen**: Ein Benutzer lässt sich einen langen Artikel vorlesen. Er öffnet das Folge-Text-Fenster, um den Text visuell zu verfolgen und die Konzentration zu halten.
*   **UC2: Barrierefreiheit**: Ein Benutzer mit Sehschwäche vergrößert den Text auf eine für ihn angenehme Größe, um dem vorgelesenen Inhalt leichter folgen zu können.
*   **UC3: Nachschlagen im Text**: Während des Vorlesens scrollt der Benutzer im Text zurück, um eine vorherige Passage erneut zu lesen, ohne die Wiedergabe zu unterbrechen. Danach drückt er die Leertaste, um wieder zur aktuellen Vorleseposition zu springen.

---

## 5. Technische Hinweise

*   Die Implementierung erfordert eine UI-Bibliothek (z.B. Tkinter, PyQt, oder eine Web-basierte UI).
*   Die Synchronisation zwischen dem TTS-Engine-Fortschritt und der Texthervorhebung muss präzise sein. Die meisten TTS-Engines bieten Callbacks oder Events für Wortgrenzen (`word boundary events`).
*   Das Speichern der Konfiguration sollte atomar erfolgen, um Korruption der `settings.json` zu vermeiden.
