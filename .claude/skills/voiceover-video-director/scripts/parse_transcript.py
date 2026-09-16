#!/usr/bin/env python3
"""Turn a timestamped transcript (SRT, VTT, or JSON) into sentence-level timing.

Output is always the same shape regardless of input format — a JSON array
on stdout:

    [{"start": 0.0, "end": 2.4, "text": "The impound lot charges a daily fee."}, ...]

Supported inputs:
- .srt  — standard SubRip subtitles
- .vtt  — WebVTT
- .json — either sentence-level [{"start","end","text"}, ...] (passed through
  after validation) or word-level [{"start","end","word"}, ...] (merged into
  sentences on ., !, ? boundaries)

If the transcript has no timestamps at all, use estimate_timing.py instead.

Usage:
    python3 parse_transcript.py --input voiceover.srt
"""

import argparse
import json
import re
import sys


def parse_srt_time(t: str) -> float:
    t = t.strip().replace(",", ".")
    h, m, s = t.split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


def parse_vtt_time(t: str) -> float:
    t = t.strip()
    parts = t.split(":")
    if len(parts) == 3:
        h, m, s = parts
    else:
        h = "0"
        m, s = parts
    return int(h) * 3600 + int(m) * 60 + float(s)


def parse_srt(text: str):
    blocks = re.split(r"\n\s*\n", text.strip())
    out = []
    for block in blocks:
        lines = [l for l in block.splitlines() if l.strip()]
        if len(lines) < 2:
            continue
        time_line_idx = 1 if re.match(r"^\d+$", lines[0].strip()) else 0
        time_line = lines[time_line_idx]
        m = re.match(r"([\d:,.]+)\s*-->\s*([\d:,.]+)", time_line)
        if not m:
            continue
        start, end = parse_srt_time(m.group(1)), parse_srt_time(m.group(2))
        content = " ".join(lines[time_line_idx + 1:]).strip()
        if content:
            out.append({"start": start, "end": end, "text": content})
    return out


def parse_vtt(text: str):
    text = re.sub(r"^WEBVTT.*?\n", "", text.strip(), flags=re.DOTALL)
    blocks = re.split(r"\n\s*\n", text.strip())
    out = []
    for block in blocks:
        lines = [l for l in block.splitlines() if l.strip()]
        time_line = next((l for l in lines if "-->" in l), None)
        if not time_line:
            continue
        m = re.match(r"([\d:.]+)\s*-->\s*([\d:.]+)", time_line)
        if not m:
            continue
        start, end = parse_vtt_time(m.group(1)), parse_vtt_time(m.group(2))
        idx = lines.index(time_line)
        content = " ".join(lines[idx + 1:]).strip()
        if content:
            out.append({"start": start, "end": end, "text": content})
    return out


def merge_words_into_sentences(words):
    sentences = []
    buf_text, buf_start = [], None
    for w in words:
        if buf_start is None:
            buf_start = w["start"]
        buf_text.append(w["word"])
        if re.search(r"[.!?]$", w["word"].strip()):
            sentences.append({"start": buf_start, "end": w["end"], "text": " ".join(buf_text).strip()})
            buf_text, buf_start = [], None
    if buf_text:
        sentences.append({"start": buf_start, "end": words[-1]["end"], "text": " ".join(buf_text).strip()})
    return sentences


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--input", required=True)
    args = parser.parse_args()

    with open(args.input, encoding="utf-8") as f:
        raw = f.read()

    if args.input.lower().endswith(".srt"):
        result = parse_srt(raw)
    elif args.input.lower().endswith(".vtt"):
        result = parse_vtt(raw)
    elif args.input.lower().endswith(".json"):
        data = json.loads(raw)
        if data and "word" in data[0]:
            result = merge_words_into_sentences(data)
        else:
            for item in data:
                if "start" not in item or "end" not in item or "text" not in item:
                    print(f"Malformed entry, expected start/end/text: {item}", file=sys.stderr)
                    sys.exit(1)
            result = data
    else:
        print("Unsupported extension. Use .srt, .vtt, or .json (or use estimate_timing.py "
              "for a plain-text transcript with no timestamps).", file=sys.stderr)
        sys.exit(1)

    if not result:
        print("No timed segments found in the transcript.", file=sys.stderr)
        sys.exit(1)

    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
