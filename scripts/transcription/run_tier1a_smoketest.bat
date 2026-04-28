@echo off
REM ── Tier 1A Smoke Test — 01-Common Objections (53 videos) ───────────────────
REM Stage 1: Extract audio
REM Stage 2: Transcribe with Deepgram
REM Stage 3: Consolidate
REM
REM Run from the repo root or this folder. Requires DEEPGRAM_API_KEY in .env
REM NOTE: 04-Top 50 folder is a PDF only — no videos. Real Tier 1A = 01-Common Objections.

setlocal

set FOLDER1=E:\AutoForge\Jeremy Miner\JEREMY MAIN\05-The NEPQ Objection Obliteration Accelerator\01-Common Objections
set AUDIO_ROOT=E:\AutoForge\jeremy-audio
set SCRIPTS=%~dp0

echo.
echo ============================================================
echo  STAGE 1 — Audio Extraction (53 videos, .mp4 + .ts)
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
