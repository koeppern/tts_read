' =================================================================
' VorleseApp - Administrator Autostart VBScript
' =================================================================
' Dieses Script startet VORLESE_AUTOSTART.bat mit Admin-Rechten
' ohne ein sichtbares Konsolenfenster zu zeigen.
' =================================================================

On Error Resume Next

' Pfad zur Batch-Datei ermitteln
Dim fso, scriptPath, batchPath
Set fso = CreateObject("Scripting.FileSystemObject")
scriptPath = fso.GetParentFolderName(WScript.ScriptFullName)
batchPath = scriptPath & "\VORLESE_AUTOSTART.bat"

' Prüfen ob Batch-Datei existiert
If Not fso.FileExists(batchPath) Then
    WScript.Echo "FEHLER: VORLESE_AUTOSTART.bat nicht gefunden in: " & batchPath
    WScript.Quit 1
End If

' UAC-Dialog anzeigen und mit Admin-Rechten starten
Dim shell
Set shell = CreateObject("Shell.Application")

' Batch-Datei mit Administrator-Rechten ausführen
' runas = Administrator-Rechte anfordern
' 1 = Fenster normal anzeigen (kann auf 0 geändert werden für versteckt)
shell.ShellExecute batchPath, "", scriptPath, "runas", 0

' Cleanup
Set shell = Nothing
Set fso = Nothing

' Script beenden
WScript.Quit 0 