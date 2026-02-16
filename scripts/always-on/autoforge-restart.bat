@echo off
REM ============================================
REM   Restart AutoForge Server
REM ============================================

echo Restarting AutoForge...

REM Stop first
call "%~dp0autoforge-stop.bat"

REM Wait a moment for ports to free up
timeout /t 3 /nobreak >nul

REM Start again (hidden)
echo Starting AutoForge...
cscript //nologo "%~dp0autoforge-startup.vbs"

echo AutoForge restarted. Open http://localhost:8888
pause
