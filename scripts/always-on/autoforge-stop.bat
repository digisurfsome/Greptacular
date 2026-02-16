@echo off
REM ============================================
REM   Stop AutoForge Server
REM ============================================
REM
REM Finds and kills the AutoForge uvicorn process
REM without killing other Python processes.
REM

echo Stopping AutoForge server...

REM Find and kill uvicorn processes on port 8888
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8888" ^| findstr "LISTENING"') do (
    echo Killing process on port 8888 (PID: %%a)
    taskkill /F /PID %%a >nul 2>&1
)

REM Also kill any remaining autoforge-service.bat processes
taskkill /F /FI "WINDOWTITLE eq autoforge-service*" >nul 2>&1

echo AutoForge server stopped.
pause
