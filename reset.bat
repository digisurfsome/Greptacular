@echo off
cd /d "%~dp0"
REM ============================================
REM   AutoForge Reset - Fix broken UI state
REM ============================================
REM
REM Run this when the UI is broken or showing
REM weird panels/bugs after agents made changes.
REM
REM What it does:
REM   1. Saves any local changes (git stash)
REM   2. Switches to main branch
REM   3. Pulls latest clean code from GitHub
REM   4. Nukes the old UI build
REM   5. Starts fresh (start_ui.bat auto-rebuilds)
REM ============================================

echo.
echo ====================================
echo   AutoForge Reset
echo ====================================
echo.

REM Step 1: Stash any local changes
echo [1/5] Saving local changes...
git stash >nul 2>&1

REM Step 2: Switch to main branch
echo [2/5] Switching to main branch...
git checkout main >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo WARNING: Could not switch to main, continuing on current branch...
)

REM Step 3: Pull latest from main
echo [3/5] Pulling latest code from GitHub...
git pull origin main
if %ERRORLEVEL% neq 0 (
    echo ERROR: Pull failed. You may need to resolve conflicts manually.
    pause
    exit /b 1
)

REM Step 4: Nuke old UI build so it forces a rebuild
echo [4/5] Clearing old UI build...
if exist "ui\dist" rmdir /s /q "ui\dist"

REM Step 5: Launch (start_ui.bat will auto-rebuild)
echo [5/5] Starting AutoForge...
echo.
call "%~dp0start_ui.bat" %*
