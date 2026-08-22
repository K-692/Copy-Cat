@echo off
REM ==============================================================================
REM Copy Cat — Windows Startup Shortcut Uninstaller
REM Removes the Copy Cat shortcut from the user's Startup folder.
REM ==============================================================================

set "STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "SHORTCUT=%STARTUP_FOLDER%\CopyCat.lnk"

echo [Copy Cat] Removing Windows startup shortcut...

if exist "%SHORTCUT%" (
    del /f /q "%SHORTCUT%"
    echo [Copy Cat] Startup shortcut removed successfully.
) else (
    echo [Copy Cat] No shortcut found at %SHORTCUT%.
)

pause
