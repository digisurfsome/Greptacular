@echo off
cd /d "%~dp0"
REM AutoForge UI Launcher for Windows
REM This script launches the web UI for the autonomous coding agent.
REM Now auto-syncs from main before starting to prevent stale UI bugs.

echo.
echo ====================================
echo   AutoForge UI
echo ====================================
echo.

REM Auto-sync: pull latest main so you never run stale/broken code
echo Syncing latest code from main...
git stash >nul 2>&1
git checkout main >nul 2>&1
git pull origin main >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [WARNING] Could not pull latest code - starting with local files
) else (
    echo [OK] Code is up to date
)
echo.

REM Kill any existing processes on port 8888
echo Cleaning up old processes...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8888" ^| findstr "LISTENING"') do (
    taskkill /F /PID %%a >nul 2>&1
)

REM Check if Python is available
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ERROR: Python not found in PATH
    echo Please install Python from https://python.org
    pause
    exit /b 1
)

REM Check if venv exists with correct activation script
if not exist "venv\Scripts\activate.bat" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate the virtual environment
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt --quiet

REM Run the Python launcher
python "%~dp0start_ui.py" %*
