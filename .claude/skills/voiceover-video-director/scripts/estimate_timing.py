#!/usr/bin/env python3
"""Estimate per-sentence timing for a PLAIN TEXT transcript with no timestamps.

Only use this when the real voiceover has no aligned transcript (no SRT/VTT,
no word-level JSON from the TTS/ASR tool that made it). It measures the
actual audio duration with ffprobe and distributes it across sentences in
proportion to each sentence's word count — it does NOT know where pauses or
emphasis actually land, so treat the output as approximate. If the source TTS
tool can export word/sentence timestamps (many can), prefer that and use
parse_transcript.py instead — this script exists as a fallback, not the
default path.

Usage:
    python3 estimate_timing.py --audio voiceover.mp3 --transcript script.txt
"""

import argparse
import json
import re
import shutil
import subprocess
import sys


def probe_duration(path: str) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )
    return float(out.stdout.strip())


def split_sentences(text: str):
    text = re.sub(r"\s+", " ", text).strip()
    # Split on sentence-ending punctuation, keeping it attached to the sentence.
    parts = re.split(r"(?<=[.!?])\s+", text)
    return [p.strip() for p in parts if p.strip()]


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--audio", required=True)
    parser.add_argument("--transcript", required=True, help="Plain text file, no timestamps")
    args = parser.parse_args()

    if shutil.which("ffprobe") is None:
        print("ffprobe not found on PATH.", file=sys.stderr)
        sys.exit(1)

    with open(args.transcript, encoding="utf-8") as f:
        text = f.read()

    sentences = split_sentences(text)
    if not sentences:
        print("No sentences found in transcript.", file=sys.stderr)
        sys.exit(1)

    total_duration = probe_duration(args.audio)
    word_counts = [max(len(s.split()), 1) for s in sentences]
    total_words = sum(word_counts)

    result = []
    cursor = 0.0
    for i, (sentence, words) in enumerate(zip(sentences, word_counts)):
        share = words / total_words
        duration = total_duration * share
        start = cursor
        end = total_duration if i == len(sentences) - 1 else cursor + duration
        result.append({"start": round(start, 3), "end": round(end, 3), "text": sentence})
        cursor = end

    print(f"WARNING: timings are estimated from word-count proportions, not real "
          f"speech timing — verify against the actual audio before locking the edit.",
          file=sys.stderr)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
