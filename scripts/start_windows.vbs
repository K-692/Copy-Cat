' ==============================================================================
' Windows Silent Background Startup Script for Copy Cat
' Starts the background keystroke listener via pythonw.exe without any console window.
' Place a shortcut to this script in your Windows Startup folder (shell:startup).
' ==============================================================================

Dim FSO, WshShell, ScriptDir, ProjectDir, PythonExe, MainPy

Set FSO = CreateObject("Scripting.FileSystemObject")
Set WshShell = CreateObject("WScript.Shell")

ScriptDir = FSO.GetParentFolderName(WScript.ScriptFullName)
ProjectDir = FSO.GetParentFolderName(ScriptDir)
MainPy = ProjectDir & "\main.py"

' Check if venv pythonw exists, else fallback to system pythonw
If FSO.FileExists(ProjectDir & "\venv\Scripts\pythonw.exe") Then
    PythonExe = """" & ProjectDir & "\venv\Scripts\pythonw.exe"""
Else
    PythonExe = "pythonw.exe"
End If

WshShell.CurrentDirectory = ProjectDir
WshShell.Run PythonExe & " """ & MainPy & """", 0, False
