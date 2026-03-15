@echo off
setlocal

echo ========================================
echo   AutoForge Deploy Script
echo ========================================
echo.

:: Step 1: Update dev repo
echo [1/5] Updating dev repo...
cd /d "C:\Users\lober\GitHub\Greptacular - AutoForge Build\Greptacular"
if errorlevel 1 (
    echo ERROR: Dev repo not found!
    pause
    exit /b 1
)

git fetch origin main
git pull origin main --no-edit

:: Step 2: Check for feature branches to merge
echo.
echo [2/5] Checking for feature branches...
for /f "tokens=*" %%b in ('git branch -r --list "origin/claude/*" 2^>nul') do (
    echo Found: %%b
    set /p MERGE="Merge %%b? (y/n): "
    if /i "!MERGE!"=="y" (
        git merge %%b --no-edit
    )
)

:: Step 3: Build UI
echo.
echo [3/5] Building UI...
cd ui
call npm run build
if errorlevel 1 (
    echo ERROR: UI build failed!
    pause
    exit /b 1
)
cd ..

:: Step 4: Push to main
echo.
echo [4/5] Pushing to main...
git push origin main
if errorlevel 1 (
    echo ERROR: Push failed!
    pause
    exit /b 1
)

:: Step 5: Update live install
echo.
echo [5/5] Updating live install...
cd /d "C:\Users\lober\Greptacular"
git pull origin main --no-edit
if errorlevel 1 (
    echo ERROR: Live pull failed!
    pause
    exit /b 1
)

echo.
echo ========================================
echo   Deploy complete!
echo   Now restart start_ui.bat and Ctrl+Shift+R
echo ========================================
pause
