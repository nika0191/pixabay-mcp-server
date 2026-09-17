#!/usr/bin/env python3
"""Transcribe a voiceover with word-level timestamps and align it to the
known script text, producing gap-filled sentence boundaries.

Why this exists: estimating each sentence's start/end by dividing total
audio duration proportionally to word count (sec_per_word = total_dur /
total_words) looks reasonable but drifts badly — real speech has uneven
pacing and pauses between sentences/paragraphs, so the error compounds
over a long voiceover (observed: up to ~13s drift by the middle of a
19-minute file). This script replaces that estimate with real ASR
word timestamps, so every downstream cut lines up with the actual audio.

Requires: pip install faster-whisper

Usage:
    python3 whisper_align.py --audio voiceover.mp3 --script script.json \
        --out sentence_spans.json

`script.json` is a JSON list of {"text": "..."} objects (or a plain list of
strings) — one per sentence, in narration order. The script's own sentence
segmentation is authoritative; Whisper is only used for timing, never for
re-splitting the text.

Output `sentence_spans.json`:
    {
      "sentences": [
        {"text": "...", "start": 0.0, "end": 7.44, "method": "whisper"},
        ...
      ],
      "spans": [[0.0, 8.84], [8.84, 10.54], ...]   # gap-filled, see below
    }

`spans` is what you actually build beats from: each sentence's span is
extended to the START of the NEXT sentence (last sentence extends to the
end of the audio file), so that beats built from spans have ZERO gaps and
their total duration exactly equals a narration slice pulled with
`ffmpeg -ss <span_start> -t <span_end - span_start>`. Building beats from
the raw (non-extended) `start`/`end` instead will silently produce a video
a few seconds SHORTER than its narration track — `-shortest` at mux time
then truncates the END of the audio. This bit the first version of this
skill and is why `spans` exists as a separate, pre-corrected field.
"""

import argparse
import difflib
import json
import re
import sys


def normalize_word(w):
    return re.sub(r"[^a-z0-9]", "", w.lower())


def transcribe(audio_path, model_size="small.en"):
    from faster_whisper import WhisperModel

    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    segments, _ = model.transcribe(audio_path, word_timestamps=True, language="en", vad_filter=False)
    words = []
    for seg in segments:
        for w in (seg.words or []):
            words.append({"word": w.word, "start": w.start, "end": w.end, "prob": w.probability})
    return words


def align(sentences, whisper_words):
    """Map each sentence's word range onto whisper word timestamps via a
    global sequence alignment on normalized tokens (tolerant of ASR
    mis-transcriptions, number formatting differences, etc.)."""
    transcript_words = []
    owner = []
    for si, s in enumerate(sentences):
        for w in s["text"].split():
            transcript_words.append(normalize_word(w))
            owner.append(si)

    whisper_norm = [normalize_word(w["word"]) for w in whisper_words]
    sm = difflib.SequenceMatcher(None, transcript_words, whisper_norm, autojunk=False)
    t2w = {}
    for block in sm.get_matching_blocks():
        for k in range(block.size):
            t2w[block.a + k] = block.b + k

    n = len(transcript_words)

    def nearest_match(ti):
        step = 0
        while 0 <= ti - step or ti + step < n:
            for cand in (ti - step, ti + step):
                if 0 <= cand < n and cand in t2w:
                    return t2w[cand]
            step += 1
            if step > 200:
                return None
        return None

    ranges = {}
    for si in range(len(sentences)):
        idxs = [i for i, o in enumerate(owner) if o == si]
        ranges[si] = (idxs[0], idxs[-1])

    out = []
    for si, s in enumerate(sentences):
        first_t, last_t = ranges[si]
        w_first = nearest_match(first_t)
        w_last = nearest_match(last_t)
        if w_first is None or w_last is None or w_last < w_first:
            print(f"WARNING: sentence {si} failed to align, needs manual check: {s['text'][:60]!r}", file=sys.stderr)
            out.append({"text": s["text"], "start": None, "end": None, "method": "fallback"})
        else:
            out.append({
                "text": s["text"],
                "start": round(whisper_words[w_first]["start"], 3),
                "end": round(whisper_words[w_last]["end"], 3),
                "method": "whisper",
            })
    return out


def build_spans(aligned, total_audio_duration):
    """Extend each sentence to the start of the next one (gap-filling)."""
    spans = []
    for i, s in enumerate(aligned):
        start = s["start"]
        end = aligned[i + 1]["start"] if i + 1 < len(aligned) else total_audio_duration
        spans.append([start, end])
    return spans


def audio_duration(path):
    import subprocess
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        stdout=subprocess.PIPE, text=True)
    return float(r.stdout.strip())


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--audio", required=True)
    p.add_argument("--script", required=True, help="JSON list of sentences (strings, or {\"text\":...} objects)")
    p.add_argument("--out", required=True)
    p.add_argument("--model", default="small.en", help="faster-whisper model size (small.en is a good speed/accuracy default)")
    p.add_argument("--cache-words", help="optional path to cache/reuse raw whisper word timestamps (skips re-transcribing on reruns)")
    args = p.parse_args()

    raw = json.load(open(args.script))
    sentences = [{"text": s} if isinstance(s, str) else s for s in raw]

    if args.cache_words:
        try:
            words = json.load(open(args.cache_words))
            print(f"reusing cached whisper words from {args.cache_words}", file=sys.stderr)
        except FileNotFoundError:
            words = transcribe(args.audio, args.model)
            json.dump(words, open(args.cache_words, "w"))
    else:
        words = transcribe(args.audio, args.model)

    aligned = align(sentences, words)
    fallback_count = sum(1 for a in aligned if a["method"] == "fallback")
    if fallback_count:
        print(f"WARNING: {fallback_count}/{len(aligned)} sentences failed alignment — fix manually before building beats", file=sys.stderr)

    total_dur = audio_duration(args.audio)
    spans = build_spans(aligned, total_dur)

    json.dump({"sentences": aligned, "spans": spans}, open(args.out, "w"), indent=2)
    print(f"aligned {len(aligned)} sentences, {fallback_count} fallbacks, total audio {total_dur:.2f}s -> {args.out}")


if __name__ == "__main__":
    main()
