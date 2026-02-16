' ============================================
'   AutoForge Silent Startup Script
' ============================================
'
' This VBS script launches AutoForge hidden (no terminal window).
'
' SETUP (one-time):
'   1. Press Win+R, type: shell:startup
'   2. Copy THIS FILE into that folder
'   3. Done. AutoForge now starts on every login.
'
' MANUAL START:
'   Double-click this file to start AutoForge silently.
'
' TO STOP:
'   Run autoforge-stop.bat or use Task Manager
'

Set WshShell = CreateObject("WScript.Shell")

' Get the directory this script is in
scriptDir = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)

' Run the batch file hidden (0 = hidden window, False = don't wait)
WshShell.Run """" & scriptDir & "\autoforge-service.bat""", 0, False
