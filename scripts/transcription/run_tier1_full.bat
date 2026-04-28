@echo off
REM ── Tier 1 Full Run (after smoke test confirmed) ────────────────────────────
REM Tier 1A folder #2 + Tier 1B folders 3 & 4
REM Run ONLY after smoke test is confirmed good.

setlocal

set FOLDER2=E:\AutoForge\Jeremy Miner\JEREMY MAIN\05-The NEPQ Objection Obliteration Accelerator\01-Common Objections
set FOLDER3=E:\AutoForge\Jeremy Miner\JEREMY MAIN\01-Intro to NEPQ Selling
set FOLDER4=E:\AutoForge\Jeremy Miner\JEREMY MAIN\02-The Power of NEPQ

set AUDIO2=E:\AutoForge\jeremy-audio\01-Common Objections
set AUDIO3=E:\AutoForge\jeremy-audio\01-Intro to NEPQ Selling
set AUDIO4=E:\AutoForge\jeremy-audio\02-The Power of NEPQ

set SCRIPTS=%~dp0

echo.
echo ============================================================
echo  EXTRACTING — Tier 1A folder #2
echo ============================================================
python "%SCRIPTS%extract_audio.py" "%FOLDER2%"

echo.
echo ============================================================
echo  EXTRACTING — Tier 1B folder #3
echo ============================================================
python "%SCRIPTS%extract_audio.py" "%FOLDER3%"

echo.
echo ============================================================
echo  EXTRACTING — Tier 1B folder #4
echo ============================================================
python "%SCRIPTS%extract_audio.py" "%FOLDER4%"

echo.
echo ============================================================
echo  TRANSCRIBING — Tier 1A folder #2
echo ============================================================
python "%SCRIPTS%transcribe_deepgram.py" "%AUDIO2%"

echo.
echo ============================================================
echo  TRANSCRIBING — Tier 1B folder #3
echo ============================================================
python "%SCRIPTS%transcribe_deepgram.py" "%AUDIO3%"

echo.
echo ============================================================
echo  TRANSCRIBING — Tier 1B folder #4
echo ============================================================
python "%SCRIPTS%transcribe_deepgram.py" "%AUDIO4%"

echo.
echo ============================================================
echo  CONSOLIDATING all sections
echo ============================================================
cd /d "%~dp0..\.."
python "%SCRIPTS%consolidate.py"

echo.
echo ============================================================
echo  TIER 1 COMPLETE. Report and stop — no Tier 2 without OK.
echo ============================================================
pause
