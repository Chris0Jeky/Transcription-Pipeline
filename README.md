# From the Boys

Working repo for the "From the Boys" podcast project: tooling to transcribe
interview/discussion recordings into readable, speaker-separated transcripts,
plus an optional AI clean-up pass.

## What's in the repo
- **`Transcription Pipeline/`** - the workhorse (all code + docs):
  - `run_transcription.py` - WhisperX transcription + speaker diarization (P1/P2 or Q/A)
  - `qa_format.py` - builds the .docx/.txt/.srt outputs
  - `cleanup_with_claude.py` - optional AI pass: punctuate, fix easy errors, flag the rest
  - `glossary.txt` - names/terms to spell correctly (edit as you go)
  - `README.md` - full setup + usage (start here)
  - `run_windows.bat`, `requirements.txt`, `.env.example`

## What's NOT in the repo (ignored on purpose)
Audio, transcripts, and the highlighted transcripts are kept out of version
control (they're bulky and/or regenerable). The empty folders are preserved as
placeholders so the structure is clear:
- `AUDIO/` - put recordings here (git-ignored)
- `Transcripts/` - source + highlighted transcripts (git-ignored)
- `Transcripts_auto/` - pipeline output goes here (git-ignored)

Secrets live in `Transcription Pipeline/.env` (git-ignored). Copy `.env.example`
to `.env` and add your tokens.

## Quick start
See **`Transcription Pipeline/README.md`**. Short version: install the deps for
your machine, make sure `.env` has your `HF_TOKEN`, then run `run_windows.bat`.

## Claude Code setup
This repo is set up as a Claude Code project:
- `CLAUDE.md` - project context + working instructions, loaded each session.
- `.claude/settings.json` - shared settings: commit co-authored-by/attribution
  trailers are **off**, and the default permission mode is **bypassPermissions**
  (skips prompts). Note: bypass mode is meant for local/trusted use and is ignored
  by cloud sessions.
- `.claude/settings.local.json` - your personal overrides, git-ignored.
