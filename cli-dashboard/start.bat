@echo off
:: CLI Dashboard Launcher (Windows)
:: Starts the dashboard server and opens the browser

set SCRIPT_DIR=%~dp0
set PORT=9111
if defined DASHBOARD_PORT set PORT=%DASHBOARD_PORT%

echo.
echo   +=======================================+
echo   :         CLI Dashboard v0.1            :
echo   :     Zero SDK / Pure Claude Code       :
echo   +=======================================+
echo.
echo   Server: http://localhost:%PORT%
echo   Press Ctrl+C to stop
echo.

:: Check for dependencies
python -c "import fastapi" 2>nul
if errorlevel 1 (
    echo   Installing dependencies...
    pip install fastapi uvicorn
)

:: Start server
cd /d "%SCRIPT_DIR%"
python server.py
