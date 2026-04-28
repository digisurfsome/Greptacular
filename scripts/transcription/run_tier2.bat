@echo off
REM ── Tier 2 — Run ONLY after Tier 1 confirmed complete ───────────────────────
REM Folders: 03-Black Book Bundle (video subfolders), 05-Bonus Content,
REM          05-5 Traits, 06-B2B
REM PDFs in 03 (Questions, Diffusing Objections) are skipped — no videos.

setlocal

set BASE=E:\AutoForge\Jeremy Miner\JEREMY MAIN
set SCRIPTS=%~dp0

echo.
echo ============================================================
echo  TIER 2 — Audio Extraction
echo ============================================================

REM 03-Black Book Bundle — only the Kickstart Crash Course has videos
echo [1/5] Extracting: NEPQ Kickstart Crash Course...
python "%SCRIPTS%extract_audio.py" "%BASE%\03-The NEPQ Black Book Bundle\02-The NEPQ Kickstart Crash Course"

REM 03-Black Book Bundle — 7 Figure Call Vault (2 ts + 1 mp4 + 1 mp3)
echo [2/5] Extracting: 7 Figure Call Vault...
python "%SCRIPTS%extract_audio.py" "%BASE%\03-The NEPQ Black Book Bundle\04-The 7 Figure Call Vault"

REM 03-Black Book Bundle — Bonuses (1 ts)
echo [3/5] Extracting: Black Book Bonuses...
python "%SCRIPTS%extract_audio.py" "%BASE%\03-The NEPQ Black Book Bundle\05-Bonuses"

REM 05 Objection Accelerator — Bonus Content (4 videos)
echo [4/5] Extracting: Objection Accelerator Bonus Content...
python "%SCRIPTS%extract_audio.py" "%BASE%\05-The NEPQ Objection Obliteration Accelerator\02-Bonus Content"

REM 05 Objection Accelerator — 5 Traits (1 video)
echo [4b/5] Extracting: 5 Traits To Become Legendary...
python "%SCRIPTS%extract_audio.py" "%BASE%\05-The NEPQ Objection Obliteration Accelerator\03-5 Traits To Become Legendary"

REM 06-B2B (5 videos)
echo [5/5] Extracting: B2B...
python "%SCRIPTS%extract_audio.py" "%BASE%\06-B2B"

echo.
echo ============================================================
echo  TIER 2 — Deepgram Transcription (all new audio at once)
echo ============================================================
python "%SCRIPTS%transcribe_deepgram.py" "E:\AutoForge\jeremy-audio"

echo.
echo ============================================================
echo  TIER 2 — Consolidate
echo ============================================================
cd /d "%~dp0..\.."
python "%SCRIPTS%consolidate.py"

echo.
echo ============================================================
echo  TIER 2 COMPLETE.
echo ============================================================
pause
