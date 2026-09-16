#!/usr/bin/env python3
"""Group sentence-level timing into visual beats of ~3-5 seconds each.

A "beat" is one on-screen visual — the unit the rest of this skill assigns a
GENERATED/PIXABAY/HYBRID format to. Beats never split a sentence (that needs
word-level timestamps to do safely); instead consecutive short sentences are
merged toward the target duration, and a single sentence that already runs
long is kept whole and flagged so the visual plan can consider giving it two
cuts (e.g. an establishing shot then a closer one) instead of forcing an
unnaturally long static beat.

Usage:
    python3 build_beats.py --input sentences.json --target 4 --min 3 --max 5 --hard-cap 7
"""

import argparse
import json
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--input", required=True, help="Sentence-level JSON from parse_transcript.py / estimate_timing.py")
    parser.add_argument("--target", type=float, default=4.0, help="Ideal beat duration, seconds")
    parser.add_argument("--min", type=float, default=3.0, help="Don't merge past this without a reason")
    parser.add_argument("--max", type=float, default=5.0, help="Stop merging once a beat reaches this")
    parser.add_argument("--hard-cap", type=float, default=7.0,
                         help="A single sentence longer than target but under this stays its own beat unflagged; "
                              "beyond this it's flagged long_beat for manual splitting")
    args = parser.parse_args()

    with open(args.input, encoding="utf-8") as f:
        sentences = json.load(f)

    beats = []
    current_text, current_start, current_end = [], None, None

    def flush():
        if current_text:
            duration = current_end - current_start
            beats.append({
                "start": round(current_start, 3),
                "end": round(current_end, 3),
                "duration": round(duration, 3),
                "text": " ".join(current_text),
                "long_beat": duration > args.hard_cap,
            })

    for sentence in sentences:
        s_start, s_end, s_text = sentence["start"], sentence["end"], sentence["text"]
        s_duration = s_end - s_start

        if current_start is None:
            current_start, current_end, current_text = s_start, s_end, [s_text]
            continue

        merged_duration = s_end - current_start
        if (current_end - current_start) >= args.min and merged_duration > args.max:
            # Current beat is already long enough; start a new one rather than overshoot.
            flush()
            current_start, current_end, current_text = s_start, s_end, [s_text]
        else:
            current_end = s_end
            current_text.append(s_text)

    flush()

    long_beats = [b for b in beats if b["long_beat"]]
    if long_beats:
        print(f"NOTE: {len(long_beats)} beat(s) exceed {args.hard_cap}s and are flagged "
              f"long_beat=true — consider two visual cuts for these in the shot list.",
              file=sys.stderr)

    print(json.dumps(beats, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
