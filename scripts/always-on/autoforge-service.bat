@echo off
REM ============================================
REM   AutoForge Always-On Server (Windows 10)
REM ============================================
REM
REM This script starts AutoForge as a persistent background process.
REM It runs hidden (no terminal window) and auto-restarts on crash.
REM
REM To install as auto-start on boot:
REM   1. Press Win+R, type: shell:startup
REM   2. Copy "autoforge-startup.vbs" into that folder
REM   3. That's it. AutoForge starts every time you log in.
REM
REM To stop: Open Task Manager > find "python" > End Task
REM   Or run: taskkill /F /IM python.exe (kills ALL python processes)
REM   Better: use autoforge-stop.bat
REM

cd /d "%~dp0\..\.."

REM Activate venv
call venv\Scripts\activate.bat

REM Start server with auto-restart on crash
:restart_loop
echo [%date% %time%] Starting AutoForge server...
python start_ui.py --port 8888

REM If we get here, the server exited
echo [%date% %time%] Server exited. Restarting in 5 seconds...
timeout /t 5 /nobreak >nul
goto restart_loop
