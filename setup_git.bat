@echo off
REM ===== Run this ONCE, from the FromTheBoys folder, to create the local git repo =====
cd /d "%~dp0"

git --version >nul 2>&1 || (echo Git is not installed. Get it from https://git-scm.com/download/win & pause & exit /b)

git init
git branch -M main
git add -A
git commit -m "Initial commit: From the Boys transcription pipeline"

echo.
echo ============================================================
echo Local repo created. Your audio/transcripts/.env are ignored.
echo To publish on GitHub:
echo   1) Create an EMPTY repo at https://github.com/new  (no README/.gitignore)
echo   2) git remote add origin https://github.com/YOURNAME/from-the-boys.git
echo   3) git push -u origin main
echo ============================================================
pause
