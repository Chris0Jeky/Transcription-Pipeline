@echo off
REM ==== From the Boys - transcription launcher (Windows) ====
REM 1) Make sure Transcription Pipeline\.env contains your HF_TOKEN (already set up).
REM 2) Edit the two folders below if needed, then double-click this file.

set INPUT=..\AUDIO
set OUTPUT=..\Transcripts_auto

REM On the laptop, "medium" is a good speed/accuracy balance. Use large-v3 if you have time.
REM P = label speakers P1/P2/... ; change to QA for Question/Answer.
python run_transcription.py --input "%INPUT%" --output "%OUTPUT%" --model medium --label-style P

echo.
echo Done. Optional AI clean-up (needs ANTHROPIC_API_KEY in .env):
echo    python cleanup_with_claude.py --input "%OUTPUT%"
pause
