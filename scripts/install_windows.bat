@echo off
REM ==============================================================================
REM Copy Cat — Windows Startup Shortcut Installer
REM Automatically creates a shortcut to start_windows.vbs in the user's Startup folder.
REM ==============================================================================

setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
set "TARGET_VBS=%SCRIPT_DIR%start_windows.vbs"
set "STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "SHORTCUT=%STARTUP_FOLDER%\CopyCat.lnk"

echo [Copy Cat] Installing Windows startup shortcut...
echo   Target: %TARGET_VBS%
echo   Shortcut: %SHORTCUT%

powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%SHORTCUT%'); $s.TargetPath = '%TARGET_VBS%'; $s.WorkingDirectory = '%SCRIPT_DIR%..'; $s.Save()"

if %ERRORLEVEL% EQU 0 (
    echo [Copy Cat] Shortcut created successfully in Startup folder!
    echo [Copy Cat] Copy Cat will now run silently in the background on every login.
) else (
    echo [Copy Cat] Failed to create shortcut. Please copy start_windows.vbs to shell:startup manually.
)

pause
