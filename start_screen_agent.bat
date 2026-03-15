@echo off
title Screen Command Agent

:: Check for API key
if "%ANTHROPIC_API_KEY%"=="" (
    echo ==========================================
    echo   You need an Anthropic API key.
    echo.
    echo   Get one at: console.anthropic.com
    echo   Then run:
    echo     set ANTHROPIC_API_KEY=sk-ant-your-key-here
    echo   Or set it permanently in System Environment Variables.
    echo ==========================================
    echo.
    set /p ANTHROPIC_API_KEY="Paste your API key here: "
)

:: Install deps if needed
pip show anthropic >nul 2>&1 || pip install anthropic Pillow pynput

:: Run
echo Starting Screen Agent...
echo.
python "%~dp0screen_agent.py"
pause
