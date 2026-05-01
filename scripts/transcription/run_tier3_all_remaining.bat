@echo off
REM ── Tier 3 — ALL REMAINING Jeremy Miner videos ──────────────────────────────
REM Run AFTER Tier 2 is confirmed complete.
REM
REM Covers BEST Jeremy Miner - 7th Level Communications - NEPQ 3.0:
REM   - Jeremy Miner NEPQ Black Book Bundle (Modules 0-5 + Bonuses)  ~29 videos
REM   - NEPQ Training Calls (root + 2021 + 2022 subfolders)          ~60 videos
REM   - The Training (01. Cold Calling ... 53. Door-to-Door)         ~53 videos
REM
REM Total new: ~145 videos. Est. cost: ~$1.00-$1.50 depending on runtime.
REM Skip logic: already-done .mp3/.txt files are skipped automatically.

setlocal

set BEST=E:\AutoForge\Jeremy Miner\BEST Jeremy Miner - 7th Level Communications - NEPQ 3.0
set AUDIO_ROOT=E:\AutoForge\jeremy-audio
set SCRIPTS=%~dp0

echo.
echo ============================================================
echo  TIER 3 — Audio Extraction
echo ============================================================

echo [1/3] Extracting: NEPQ Black Book Bundle (Modules 0-5 + Bonuses)...
python "%SCRIPTS%extract_audio.py" "%BEST%\Jeremy Miner - NEPQ Black Book Bundle"

echo [2/3] Extracting: NEPQ Training Calls (2021 + 2022 + root)...
python "%SCRIPTS%extract_audio.py" "%BEST%\NEPQ Training Calls"

echo [3/3] Extracting: The Training (53 videos)...
python "%SCRIPTS%extract_audio.py" "%BEST%\The Training"

echo.
echo ============================================================
echo  TIER 3 — Deepgram Transcription (all new audio, skip done)
echo ============================================================
python "%SCRIPTS%transcribe_deepgram.py" "%AUDIO_ROOT%"

echo.
echo ============================================================
echo  TIER 3 — Consolidate
echo ============================================================
cd /d "%~dp0..\.."
python "%SCRIPTS%consolidate.py"

echo.
echo ============================================================
echo  TIER 3 COMPLETE. All Jeremy Miner videos transcribed.
echo ============================================================
pause
