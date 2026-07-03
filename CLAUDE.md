# CLAUDE.md - From the Boys

Context and working instructions for Claude Code sessions in this repo.

## What this project is
"From the Boys" is a podcast/research project (Middlesex University) exploring
what it's like to be a boy / young man today: social media, friendship and peer
pressure, school and exams, masculinity, emotions and mental health, family,
music and culture, and money/class/status. Recordings are interviews and group
discussions with teenage boys, plus guests (e.g. Jely Kikamba, a youth worker;
Dr Alex Blower, a researcher). This repo holds the tooling that turns recordings
into transcripts and supporting documents.

## Repo layout
- `Transcription Pipeline/` - the workhorse. Start with its `README.md`.
  - `run_transcription.py` - WhisperX: transcribe + word-align + diarize (P1/P2 or Q/A).
  - `qa_format.py` - builds `.docx` / `.txt` / `.srt` from diarized segments.
  - `cleanup_with_claude.py` - optional AI pass: punctuate, fix easy errors, and
    write a `.FLAGS.txt` of timestamps to check by ear.
  - `glossary.txt` - names/terms that Whisper mishears (keep this updated).
  - `.env` - secrets (HF_TOKEN, optional ANTHROPIC_API_KEY). NEVER commit.
- `AUDIO/`, `Transcripts/`, `Transcripts_auto/` - content, git-ignored (only
  `.gitkeep` placeholders are tracked, to preserve structure).
- Root `README.md`, `git_setup.md`, `setup_git.bat` - repo + git setup.

## Hardware / how transcription is run
- Primary machine is a laptop (Intel Ultra 5 125H, CPU-only): use `--model medium`
  (or `small`) for reasonable speed. `large-v3` is more accurate but slow on CPU.
- A desktop with an AMD RX 9070 XT exists for heavier runs; AMD needs the ROCm
  build of CTranslate2 (see `Transcription Pipeline/README.md`, Track B). The
  Whisper stack is CUDA-first, so AMD is more setup.
- Diarization needs a Hugging Face token in `.env` (already configured locally).

## Typical workflow
1. Drop recordings in `AUDIO/` (subfolders are fine).
2. `python run_transcription.py --input ..\AUDIO --output ..\Transcripts_auto --model medium --label-style P`
   (or double-click `run_windows.bat`).
3. Optional: `python cleanup_with_claude.py --input ..\Transcripts_auto` to tidy
   and flag uncertain spots. Then a human listens to flagged timestamps and fixes.
4. When names are misheard, add them to `glossary.txt` and re-run.

## Conventions (please follow)
- Secrets live only in `.env`; never hard-code or commit tokens/keys.
- Do not commit audio, transcripts, highlighted docs, or `.docx`/`.mp3`/`.wav`
  (already covered by `.gitignore`). Keep content out of version control.
- Keep names/terms in `glossary.txt` accurate - it's the cheapest accuracy win.
- Transcripts aim to separate the question-asker from answerers; perfect
  per-person identity is a bonus, not a requirement.
- Prose/output style for this project: concise and direct; no em dashes.

## Git
- Co-authored-by / "Generated with Claude Code" trailers are disabled
  (`.claude/settings.json`).
- Personal settings go in `.claude/settings.local.json` (git-ignored).
- Keep the GitHub repo private unless there's a reason not to.
