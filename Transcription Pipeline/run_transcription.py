#!/usr/bin/env python3
"""
run_transcription.py
--------------------
Batch-transcribe a folder of mixed (single-track) audio files into readable
Q/A transcripts, using WhisperX for transcription + word alignment + speaker
diarization (P1, P2, ...).

    python run_transcription.py --input "audio" --output "transcripts"

Each audio file becomes:
    <name>.docx   readable transcript, speakers labelled
    <name>.txt    same, with [mm:ss] timestamps
    <name>.srt    subtitles for video/audio editing
    <name>.json   raw diarized segments (re-format without re-running)

Accuracy tips are in README.md. Uses your GPU automatically if available
(NVIDIA CUDA, or AMD ROCm with the ROCm build of CTranslate2); otherwise CPU.
Diarization needs a free Hugging Face token (see README).
"""
import argparse, json, os, sys, glob, time

import qa_format

AUDIO_EXT = (".wav", ".mp3", ".m4a", ".flac", ".aac", ".ogg", ".mp4", ".wma")

# Fixed lead-in of the glossary initial_prompt. During silent stretches Whisper
# can echo this back as if it were speech (a hallucination); strip_prompt_echo()
# removes such echoes from the output.
GLOSSARY_LEAD = "Names and terms that appear include"


def load_dotenv():
    """Load KEY=VALUE lines from a local .env (next to this script, or cwd) into
    the environment. Keeps secrets out of the code and out of git."""
    here = os.path.dirname(os.path.abspath(__file__))
    for p in (os.path.join(here, ".env"), os.path.join(os.getcwd(), ".env")):
        if os.path.exists(p):
            for line in open(p, encoding="utf-8"):
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())


def load_glossary(path):
    """Read a glossary file (names/terms, one per line, '#' comments) into an
    initial_prompt string that biases Whisper toward correct spellings."""
    if not path or not os.path.exists(path):
        return None
    terms = []
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if line and not line.startswith("#"):
            terms.append(line)
    if not terms:
        return None
    return ("This is a podcast interview. " + GLOSSARY_LEAD + ": "
            + ", ".join(terms) + ".")


def strip_prompt_echo(segments, initial_prompt):
    """Remove Whisper's hallucinated echoes of the glossary prompt. On silent
    stretches Whisper sometimes emits the prompt lead-in ('Names and terms that
    appear include ...') as if it were speech. Trim that text from a segment;
    drop the segment if nothing real remains."""
    if not initial_prompt:
        return segments
    marker = GLOSSARY_LEAD.lower()
    out, dropped = [], 0
    for s in segments:
        txt = s.get("text") or ""
        i = txt.lower().find(marker)
        if i != -1:
            txt = txt[:i].rstrip(" ,.-\t")
        if txt.strip():
            s = dict(s); s["text"] = txt
            out.append(s)
        else:
            dropped += 1
    if dropped:
        print("  removed " + str(dropped) + " glossary-prompt hallucination segment(s)")
    return out


def transcribe_file(audio_path, model, align_cache, diarizer, device,
                    batch_size, min_spk, max_spk, language=None):
    import whisperx
    audio = whisperx.load_audio(audio_path)

    result = model.transcribe(audio, batch_size=batch_size, language=language)
    lang = result["language"]

    if lang not in align_cache:
        align_cache[lang] = whisperx.load_align_model(language_code=lang, device=device)
    a_model, a_meta = align_cache[lang]
    result = whisperx.align(result["segments"], a_model, a_meta, audio, device,
                            return_char_alignments=False)

    if diarizer is not None:
        dia_kwargs = {}
        if min_spk:
            dia_kwargs["min_speakers"] = min_spk
        if max_spk:
            dia_kwargs["max_speakers"] = max_spk
        diarize_segments = diarizer(audio, **dia_kwargs)
        result = whisperx.assign_word_speakers(diarize_segments, result)

    segs = [{"start": s.get("start", 0.0), "end": s.get("end", 0.0),
             "speaker": s.get("speaker", "UNKNOWN"), "text": s.get("text", "")}
            for s in result["segments"]]
    return segs, lang


def main():
    load_dotenv()
    ap = argparse.ArgumentParser(description="Batch diarized transcription (WhisperX).")
    ap.add_argument("--input", required=True, help="folder with audio files (searched recursively)")
    ap.add_argument("--output", required=True, help="folder for transcripts")
    ap.add_argument("--model", default="large-v3",
                    help="whisper model (default large-v3; use 'medium' or 'small' on CPU for speed)")
    ap.add_argument("--language", default=None,
                    help="force language code (e.g. 'en'). Default: auto-detect per file. "
                         "Forcing 'en' avoids mis-detection on noisy/quiet intros.")
    ap.add_argument("--device", default=None, help="cuda / cpu (auto-detected if omitted)")
    ap.add_argument("--compute-type", default=None,
                    help="float16 (GPU) / int8 (CPU). Auto if omitted.")
    ap.add_argument("--batch-size", type=int, default=8)
    ap.add_argument("--hf-token", default=os.environ.get("HF_TOKEN"),
                    help="Hugging Face token (or set HF_TOKEN env var)")
    ap.add_argument("--glossary", default="glossary.txt",
                    help="file of names/terms to improve spelling accuracy (default glossary.txt)")
    ap.add_argument("--min-speakers", type=int, default=None)
    ap.add_argument("--max-speakers", type=int, default=None)
    ap.add_argument("--diarize-model", default="pyannote/speaker-diarization-community-1",
                    help="pyannote diarization pipeline (must be accepted on HuggingFace). "
                         "Default: speaker-diarization-community-1 (whisperx 3.8+ default). "
                         "Use pyannote/speaker-diarization-3.1 for the older gated model.")
    ap.add_argument("--no-diarize", action="store_true",
                    help="skip diarization: transcription only, no speaker labels, no HF token needed")
    ap.add_argument("--label-style", default="P", choices=["P", "QA"],
                    help="P = P1/P2/... ; QA = Question/Answer (interviewer auto-detected)")
    ap.add_argument("--no-timestamps", action="store_true")
    ap.add_argument("--reformat-only", action="store_true",
                    help="skip transcription; rebuild docs from existing .json files")
    args = ap.parse_args()

    os.makedirs(args.output, exist_ok=True)
    qa_format.LABEL_STYLE = args.label_style

    # ---- reformat-only path: no heavy deps or audio needed ----
    if args.reformat_only:
        jsons = sorted(glob.glob(os.path.join(args.output, "*.json")))
        if not jsons:
            print("No .json segment files found in " + args.output)
            sys.exit(1)
        for jp in jsons:
            segs = json.load(open(jp, encoding="utf-8"))
            stem = os.path.splitext(jp)[0]
            name = os.path.basename(stem)
            info = qa_format.process(segs, stem, title=name,
                                     meta="Reformatted from saved segments",
                                     timestamps=not args.no_timestamps)
            print("  reformatted " + name + ": " + str(info))
        return

    files = sorted(f for f in glob.glob(os.path.join(args.input, "**", "*"), recursive=True)
                   if f.lower().endswith(AUDIO_EXT))
    if not files:
        print("No audio files found in " + args.input)
        sys.exit(1)
    print("Found " + str(len(files)) + " audio file(s).")

    import torch, whisperx
    device = args.device or ("cuda" if torch.cuda.is_available() else "cpu")
    compute_type = args.compute_type or ("float16" if device == "cuda" else "int8")
    print("Device: " + device + "  |  compute_type: " + compute_type + "  |  model: " + args.model)
    if not args.no_diarize and not args.hf_token:
        print("ERROR: a Hugging Face token is required for diarization. "
              "Pass --hf-token or set HF_TOKEN, or use --no-diarize. See README.md.")
        sys.exit(2)

    initial_prompt = load_glossary(args.glossary)
    if initial_prompt:
        print("Glossary loaded (" + args.glossary + ") - biasing spellings.")
    # condition_on_previous_text=False stops the glossary prompt from carrying
    # across windows and looping. Any echo that still slips through is removed
    # from the output by strip_prompt_echo() below.
    asr_options = {"condition_on_previous_text": False}
    if initial_prompt:
        asr_options["initial_prompt"] = initial_prompt

    model = whisperx.load_model(args.model, device, compute_type=compute_type,
                                asr_options=asr_options)
    diarizer = None
    if not args.no_diarize:
        try:
            from whisperx.diarize import DiarizationPipeline
        except Exception:
            from whisperx import DiarizationPipeline
        print("Diarization model: " + args.diarize_model)
        diarizer = DiarizationPipeline(model_name=args.diarize_model,
                                       token=args.hf_token, device=device)
    else:
        print("Diarization disabled (--no-diarize): transcription only, single speaker label.")
    align_cache = {}

    for i, audio_path in enumerate(files, 1):
        name = os.path.splitext(os.path.basename(audio_path))[0]
        stem = os.path.join(args.output, name)
        print("\n[" + str(i) + "/" + str(len(files)) + "] " + os.path.basename(audio_path))
        t0 = time.time()
        try:
            segs, lang = transcribe_file(audio_path, model, align_cache, diarizer,
                                         device, args.batch_size,
                                         args.min_speakers, args.max_speakers,
                                         args.language)
        except Exception as e:
            print("  FAILED: " + str(e))
            continue
        segs = strip_prompt_echo(segs, initial_prompt)
        json.dump(segs, open(stem + ".json", "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        meta = ("Auto-transcribed (" + args.model + ", lang=" + str(lang) + "). "
                + ("Diarization skipped - single speaker label."
                   if args.no_diarize else
                   "Speaker labels from diarization - verify against audio for key quotes."))
        info = qa_format.process(segs, stem, title=name, meta=meta,
                                 timestamps=not args.no_timestamps)
        dur = round(time.time() - t0)
        print("  done in " + str(dur) + "s - " + str(info["turns"]) + " turns, "
              + str(info.get("n_speakers", "?")) + " speaker(s)")

    print("\nAll files processed. Outputs in: " + args.output)
    print("Next: optional AI clean-up ->  python cleanup_with_claude.py --input \""
          + args.output + "\"")


if __name__ == "__main__":
    main()
