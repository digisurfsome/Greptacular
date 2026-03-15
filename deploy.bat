@echo off
setlocal enabledelayedexpansion

echo ========================================
echo   AutoForge Auto-Deploy (hands-free)
echo ========================================
echo.

:: Step 1: Kill any running AutoForge server
echo [1/4] Stopping running servers...
taskkill /f /im python.exe 2>nul
taskkill /f /im node.exe 2>nul
timeout /t 2 /nobreak >nul

:: Step 2: Pull latest main on live install
echo [2/4] Pulling latest to live install...
cd /d "C:\Users\lober\Greptacular"
if errorlevel 1 (
    echo ERROR: Live install not found at C:\Users\lober\Greptacular
    echo Press any key to exit...
    pause >nul
    exit /b 1
)
git stash 2>nul
git checkout main 2>nul
git pull origin main --no-edit
if errorlevel 1 (
    echo WARN: Pull failed, retrying in 3s...
    timeout /t 3 /nobreak >nul
    git pull origin main --no-edit
)

:: Step 3: Clean and rebuild UI
echo [3/4] Rebuilding UI...
if exist "ui\dist" rmdir /s /q "ui\dist"

:: Step 4: Restart server
echo [4/4] Starting AutoForge...
start "" "C:\Users\lober\Greptacular\start_ui.bat"

echo.
echo ========================================
echo   Done! AutoForge is starting up.
echo   Do Ctrl+Shift+R in browser to refresh.
echo ========================================
timeout /t 5
