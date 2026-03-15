@echo off
echo Starting AutoForge Deploy Agent...
echo It will watch for new commits and auto-deploy.
echo Close this window to stop it.
echo.
cd /d "C:\Users\lober\Greptacular"
python deploy_agent.py
pause
