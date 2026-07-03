# From the Boys - Automated Transcription Pipeline

Turns a folder of recordings into readable transcripts with the speakers
separated (P1, P2, ... or Question / Answer), then an optional AI pass that
punctuates, fixes obvious errors, and flags anything uncertain for you to check.

Two steps:

1. `run_transcription.py` - WhisperX: speech-to-text + word alignment + speaker
   diarization. Outputs `.docx`, `.txt`, `.srt`, `.json` per recording.
2. `cleanup_with_claude.py` *(optional)* - sends the transcript to Claude to
   punctuate, fix mis-heard words/names from context + the glossary, and produce
   a `.FLAGS.txt` list of timestamps to verify by ear. This is the "every easy
   win automatically, flag the rest" step.

---

## Quick answers (read me first)

**How long does it take?** Depends entirely on hardware:

| Setup | ~Speed | 1 hr of audio | 5 hrs of audio |
|-------|--------|---------------|----------------|
| NVIDIA GPU (CUDA) | ~10-30x realtime | ~2-6 min | ~10-30 min |
| AMD RX 9070 XT (ROCm) | ~5-15x realtime* | ~5-12 min | ~25-60 min |
| Strong desktop CPU (large-v3) | ~0.5-1.5x realtime | ~1-2 hrs | overnight |
| Laptop CPU (Intel Ultra 5 125H) | slower still | use `--model medium` | overnight+ |

\* AMD figures are estimates; ROCm Whisper is newer and less battle-tested than CUDA.

**Is the 9070 XT worth it?** Yes - it will be far faster than either CPU. The
catch: the Whisper/WhisperX stack is built around NVIDIA CUDA, and AMD needs a
special ROCm build of one component (CTranslate2). It's doable (see Track B) but
budget ~1-2 hrs of one-time setup. If you want results tonight with zero driver
pain, run the CPU track overnight, or rent a cloud NVIDIA GPU for an hour.

**Higher accuracy?** Yes, and it's already built in:
- `--model large-v3` (default) is the most accurate open model.
- `glossary.txt` feeds names/terms to Whisper so it stops writing "Middlesaise"
  for "Middlesex" and "Jellie Cacamba" for "Jely Kikamba". Add names as you go.
- The Claude cleanup pass fixes the rest and flags what it can't.
- Proper diarization (needs the token below) gives real P1/P2 speaker labels.

**The Hugging Face token - how hard?** ~5 minutes, free. You have to do it (it's
tied to your login), but here are the exact steps in Track 3 below. I can't create
it for you, but everything else is set up and ready.

---

## Step 1 setup - pick ONE track for your machine

### Track A - CPU only (simplest, works on any machine, slow)
```bat
python -m venv venv
venv\Scripts\activate
pip install torch                       REM CPU build
pip install whisperx python-docx anthropic
```
Run with a smaller model for reasonable speed on the laptop:
`--model medium` (or `small`).

### Track B - AMD RX 9070 XT (ROCm) - fastest on your desktop
The 9070 XT (gfx1201) is supported by ROCm 7.2. WhisperX needs the ROCm build of
CTranslate2. The most reliable route today is **WSL2 (Ubuntu) or native Ubuntu**;
native-Windows ROCm for this stack is newer and rougher.

Confirmed-working combo (early 2026): ROCm 7.2 + PyTorch 2.8 (ROCm build) +
CTranslate2-rocm 4.1 + faster-whisper 1.2.1 + WhisperX 3.7.4.
```bash
# inside Ubuntu / WSL2 with ROCm 7.2 installed:
pip install torch --index-url https://download.pytorch.org/whl/rocm6.2
pip install ctranslate2-rocm            # from the ROCm CTranslate2 build (see link)
pip install whisperx python-docx anthropic
```
Links to follow if a step fails:
- WhisperX on AMD ROCm (Ubuntu guide): https://github.com/m-bain/whisperX/discussions/1364
- ROCm build of CTranslate2: https://github.com/ROCm/CTranslate2
- If ROCm is a hassle: **whisper.cpp with Vulkan** transcribes fast on the 9070 XT
  cross-platform, but has no built-in diarization (you'd lose easy P1/P2).

### Track C - Cloud NVIDIA GPU (fastest overall, small cost)
Rent a GPU by the hour (e.g. RunPod / Vast) or a Colab GPU, then use Track A's
commands but with the CUDA torch build. A few hours of audio ≈ a few minutes +
a few dollars. Good if you want it done fast without touching drivers.

Also install **ffmpeg** on any track (Windows: `winget install Gyan.FFmpeg`).

---

## Step 2 setup - Hugging Face token (needed for speaker diarization)
1. Sign up / log in at https://huggingface.co
2. Settings -> Access Tokens -> **New token** (type: Read). Copy it.
3. Open these two pages and click **Agree/Accept** to the conditions:
   - https://huggingface.co/pyannote/speaker-diarization-3.1
   - https://huggingface.co/pyannote/segmentation-3.0
4. Give it to the pipeline: put it in `run_windows.bat`, or run
   `set HF_TOKEN=hf_xxxx` (Windows) / `export HF_TOKEN=hf_xxxx` (Linux),
   or pass `--hf-token hf_xxxx`.

---

## Running it

Put recordings in a folder (subfolders are searched), then:
```bat
python run_transcription.py --input "..\AUDIO" --output "..\Transcripts_auto" --model large-v3 --label-style P
```
Or just edit and double-click **run_windows.bat**.

Useful flags:
| Flag | Purpose |
|------|---------|
| `--label-style P` | P1/P2/... (default). Use `QA` for Question/Answer. |
| `--model medium` | faster, less accurate (good for CPU). |
| `--min-speakers 2 --max-speakers 2` | tell it how many voices (big reliability win on 1-1 interviews). |
| `--glossary glossary.txt` | names/terms to spell correctly (edit this file!). |
| `--reformat-only` | rebuild docs from existing `.json` (instant, no GPU). |

### Optional cleanup pass (your "easy wins + flag the rest" idea)
```bat
pip install anthropic
set ANTHROPIC_API_KEY=sk-ant-xxxx          REM from https://console.anthropic.com
python cleanup_with_claude.py --input "..\Transcripts_auto"
```
For each transcript this writes `<name>.cleaned.docx`, `<name>.cleaned.txt`, and
`<name>.FLAGS.txt` (timestamps to check by ear). `{{word?}}` marks an uncertain
guess in the text.

---

## Files here
- `run_transcription.py` - the transcription + diarization pipeline.
- `qa_format.py` - builds the docx/txt/srt and does the P / Q-A labelling.
- `cleanup_with_claude.py` - optional AI clean-up + flagging pass.
- `glossary.txt` - names/terms to improve spelling (edit freely).
- `requirements.txt`, `run_windows.bat`, `README.md`.

## Notes / honest limitations
- Speaker labels come from voice diarization; it's good but not perfect,
  especially in lively group chats. Verify labels on important quotes.
- The AI cleanup fixes clear errors and flags doubts - it won't invent content,
  but always sanity-check flagged spots against the audio.
- Names are the most common error; keeping `glossary.txt` updated helps a lot.
