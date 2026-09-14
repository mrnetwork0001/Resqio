#!/usr/bin/env python3
"""Check your narration recordings locally (faster-whisper, fully offline).

For each recordings/<id>.* this:
  1. verifies the take against its script line (an unbiased transcript, so a
     misnamed file or a skipped phrase shows up),
  2. times every word (a second pass hinted with the script line, so names
     like Resqio and NOAA come back spelled right for cue matching),
  3. finds the exact start of your first word and end of your last from the
     audio energy itself (Whisper often reports the first word at 0.00 s).

Writes recordings/alignment.json, which scripts/voiceover.mjs uses to trim
each take precisely and to sync on-screen reveals to your spoken words.

    python scripts/align_recordings.py
"""
import difflib
import json
import re
import subprocess
from pathlib import Path

import numpy as np
from faster_whisper import WhisperModel

ROOT = Path(__file__).resolve().parents[1]
REC = ROOT / "recordings"
EXTS = {".wav", ".m4a", ".mp3", ".aiff", ".aif", ".caf"}
VOCAB = "Resqio, NOAA, Strands Agents SDK, Amazon Bedrock AgentCore, mutual-aid."
SR = 16000
HOP = SR // 100  # 10 ms energy frames
NUMBER_WORDS = {"one", "two", "three", "four", "five", "ten", "twelve", "eighty", "hundred", "thousand", "point", "km"}
NAME_VARIANTS = {"resq": "resqio", "rescue": "resqio", "resko": "resqio", "reskio": "resqio", "reskyo": "resqio", "noah": "noaa"}


def words_for_compare(text: str) -> list[str]:
    out = []
    for tok in re.findall(r"[a-z]+|\d[\d.,]*", text.lower()):
        if tok[0].isdigit() or tok in NUMBER_WORDS:
            continue  # "1.2" vs "one point two": numbers are checked by ear, not by string
        out.append(NAME_VARIANTS.get(tok, tok))
    return out


def load_pcm(path: Path) -> np.ndarray:
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32)


def energy_db(pcm: np.ndarray) -> np.ndarray:
    n = len(pcm) // HOP
    frames = pcm[: n * HOP].reshape(n, HOP)
    frames = frames - frames.mean(axis=1, keepdims=True)  # drop DC offset / rumble bias
    return 20 * np.log10(np.sqrt(np.mean(frames ** 2, axis=1)) + 1e-9)


def speech_bounds(db: np.ndarray, w_start: float, w_first_end: float, w_last_start: float, w_end: float):
    """Exact speech start/end from energy, searched near Whisper's first/last word."""
    floor = float(np.percentile(db, 10))
    loud_level = max(floor + 15, float(np.percentile(db, 99)) - 30)
    soft_level = floor + 6
    loud = db > loud_level
    # Sustained energy (4 of 6 frames), so a lone mouth click or bump doesn't count.
    sustained = np.convolve(loud.astype(int), np.ones(6, int), mode="full")[5:] >= 4
    n = len(db)
    f = lambda secs: int(min(n - 1, max(0, round(secs * 100))))

    lo, hi = f(w_start - 0.6), f(w_first_end + 0.1)
    hits = np.flatnonzero(sustained[lo:hi + 1])
    start_i = lo + int(hits[0]) if len(hits) else f(w_start)
    back = 0
    while start_i > 0 and db[start_i - 1] > soft_level and back < 25:  # soft onset ("f", "h", "th")
        start_i, back = start_i - 1, back + 1

    lo, hi = f(w_last_start - 0.1), f(w_end + 0.8)
    hits = np.flatnonzero(sustained[lo:hi + 1])
    end_i = lo + int(hits[-1]) + 5 if len(hits) else f(w_end)
    fwd = 0
    while end_i < n - 1 and db[end_i + 1] > soft_level and fwd < 40:  # natural decay
        end_i, fwd = end_i + 1, fwd + 1
    return start_i / 100, min(n, end_i + 1) / 100, floor


def transcribe(model: WhisperModel, path: Path, prompt: str):
    segments, _ = model.transcribe(str(path), language="en", beam_size=5, word_timestamps=True,
                                   vad_filter=False, condition_on_previous_text=False, initial_prompt=prompt)
    return [w for seg in segments for w in (seg.words or [])]


def main() -> None:
    scenes = json.loads((ROOT / "narration.json").read_text())["scenes"]
    model = WhisperModel("small.en", device="cpu", compute_type="int8")
    alignment = {}
    print(f"{'id':4} {'match':>6} {'speech':>13} {'file':>6} {'cut':>6} {'floor':>6}  notes")
    for scene in scenes:
        sid = scene["id"]
        path = next((p for p in sorted(REC.glob(f"{sid}.*")) if p.suffix.lower() in EXTS), None)
        if path is None:
            print(f"{sid:4} MISSING")
            continue

        heard_words = transcribe(model, path, VOCAB)
        heard = " ".join(w.word.strip() for w in heard_words)
        timed = transcribe(model, path, scene["text"]) or heard_words
        expected_tokens = words_for_compare(scene["text"])
        ratio = difflib.SequenceMatcher(None, expected_tokens, words_for_compare(heard)).ratio()

        db = energy_db(load_pcm(path))
        dur = len(db) / 100
        start, end, floor = speech_bounds(db, timed[0].start, timed[0].end, timed[-1].start, timed[-1].end)

        notes = []
        if ratio < 0.9:
            heard_tokens = words_for_compare(heard)
            notes.append(f"differs: missing {[w for w in expected_tokens if w not in heard_tokens][:5]} "
                         f"extra {[w for w in heard_tokens if w not in expected_tokens][:5]}")
        pauses = [f"{a.end:.1f}s" for a, b in zip(timed, timed[1:]) if b.start - a.end > 1.0]
        if pauses:
            notes.append(f"long pause after {', '.join(pauses)}")

        alignment[sid] = {
            "file": path.name, "match": round(ratio, 3), "start": round(start, 3), "end": round(end, 3),
            "duration": round(dur, 3), "noise_floor_db": round(floor, 1), "heard": heard,
            "words": [{"w": w.word.strip(), "s": round(w.start, 3), "e": round(w.end, 3)} for w in timed],
        }
        print(f"{sid:4} {ratio:6.0%} {start:5.2f}-{end:5.2f}s {dur:6.2f} {start + dur - end:5.2f}s {floor:6.1f}  {'; '.join(notes)}")
    (REC / "alignment.json").write_text(json.dumps(alignment, indent=2) + "\n")
    print("\nwrote recordings/alignment.json\n")
    for sid, a in alignment.items():
        print(f"  {sid} heard: {a['heard']}")


if __name__ == "__main__":
    main()
