@echo off
REM ── Tier 1A Smoke Test — Folder #1 only ────────────────────────────────────
REM Stage 1: Extract audio
REM Stage 2: Transcribe with Deepgram
REM Stage 3: Consolidate
REM
REM Run from the repo root or this folder. Requires DEEPGRAM_API_KEY in .env

setlocal

set FOLDER1=E:\AutoForge\Jeremy Miner\JEREMY MAIN\05-The NEPQ Objection Obliteration Accelerator\04-Top 50 NEPQ Word-For-Word Objections
set AUDIO_ROOT=E:\AutoForge\jeremy-audio\04-Top 50 NEPQ Word-For-Word Objections
set SCRIPTS=%~dp0

echo.
echo ============================================================
echo  STAGE 1 — Audio Extraction
echo ============================================================
python "%SCRIPTS%extract_audio.py" "%FOLDER1%"
if %errorlevel% neq 0 (
    echo ERROR in Stage 1. Stopping.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo  STAGE 2 — Deepgram Transcription
echo ============================================================
python "%SCRIPTS%transcribe_deepgram.py" "%AUDIO_ROOT%"
if %errorlevel% neq 0 (
    echo ERROR in Stage 2. Stopping.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo  STAGE 3 — Consolidate
echo ============================================================
cd /d "%~dp0..\.."
python "%SCRIPTS%consolidate.py"

echo.
echo ============================================================
echo  SMOKE TEST COMPLETE. Review output above, then confirm.
echo ============================================================
pause
