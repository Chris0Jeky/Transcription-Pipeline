@echo off
REM ==== From the Boys - transcription launcher (Windows) ====
REM Uses the dedicated virtual environment set up for this project. It lives
REM OUTSIDE OneDrive (in your user profile) so it is never sync-churned.
REM ffmpeg is put on PATH here so WhisperX can decode the audio.
REM
REM One-time step for speaker diarization: sign in at huggingface.co (as the
REM account whose token is in .env) and click "Agree" on
REM   https://huggingface.co/pyannote/speaker-diarization-community-1
REM Until that is accepted, add --no-diarize below to transcribe without labels.

set VENV=%USERPROFILE%\ftb-venv
set PY=%VENV%\Scripts\python.exe
set PATH=%LOCALAPPDATA%\Microsoft\WinGet\Links;%PATH%

set INPUT=..\AUDIO
set OUTPUT=..\Transcripts_auto

REM On the laptop, "medium" is a good speed/accuracy balance. Use large-v3 if you have time.
REM P = label speakers P1/P2/... ; change to QA for Question/Answer.
REM --language en forces English (avoids mis-detecting quiet/noisy intros as another language).
REM For 1-1 interviews, adding  --min-speakers 2 --max-speakers 2  improves diarization.
"%PY%" run_transcription.py --input "%INPUT%" --output "%OUTPUT%" --model medium --language en --label-style P

echo.
echo Done. Optional AI clean-up (needs ANTHROPIC_API_KEY in .env):
echo    "%PY%" cleanup_with_claude.py --input "%OUTPUT%"
pause
