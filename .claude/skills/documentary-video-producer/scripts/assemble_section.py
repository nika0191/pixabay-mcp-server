#!/usr/bin/env python3
"""Assemble a beat order (real clips + rendered graphic clips) into one
crossfaded video, normalizing every source to a common resolution/fps first.

Usage:
    python3 assemble_section.py order.json workdir/ out_video.mp4 [crossfade_seconds]

`order.json` is a list of `[path, duration, offset]` triples in playback
order (offset is the seek-in point for real clips, 0.0 for rendered
graphics). Sources shorter than their requested slot are looped
(`-stream_loop -1`), never frozen or stretched.

## The crossfade duration-compensation trap

ffmpeg's `xfade` filter does NOT add duration — each transition of length T
overlaps two clips and the combined output is T seconds SHORTER than the sum
of the two clips' own lengths. Chain N clips with N-1 crossfades of length T
and the final video is `sum(durations) - (N-1)*T` seconds long — silently
shorter than the narration track you're about to mux against it, which
`-shortest` at mux time will then truncate from the END.

Fix (already applied in `build()` below): extend every clip's REQUESTED
duration by `crossfade` seconds, except the last clip in the sequence, before
normalizing. This makes `sum(extended_durations) - (N-1)*crossfade` exactly
equal `sum(original_durations)` again. Verify by comparing
`ffprobe`'d final video duration against a `ffprobe`'d narration slice
extracted for the same span BEFORE muxing — don't only check that the FINAL
muxed file's duration looks reasonable, since `-shortest` will make it match
whichever track is shorter and hide a truncation. This exact mistake shipped
once in this skill's development (checking post-mux duration instead of
narration-vs-video pre-mux) and cost several re-deliveries.

## GEN (rendered graphic) clips specifically

Graphic clips must have been recorded with at least
`requested_duration + crossfade` seconds of real content (see
record_graphics.py's BUFFER) — normalize() will loop a too-short graphic,
which repeats its reveal animation instead of holding still, and looks
broken. This script does not check that for you; verify before running it
(compare each GEN beat's needed duration — including the crossfade
extension for non-last beats — against the rendered clip's own ffprobe
duration).
"""

import json
import subprocess
import os
import sys

W, H, FPS = 1920, 1080, 30


def run(cmd):
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"FAILED: {' '.join(cmd)}\n{r.stdout}")


def normalize(src, dur, out, offset=0.0, loop_if_short=True):
    vf = f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,fps={FPS}"
    probe = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                             "-of", "default=noprint_wrappers=1:nokey=1", src],
                            stdout=subprocess.PIPE, text=True)
    src_dur = float(probe.stdout.strip() or 0)
    if loop_if_short and (src_dur - offset) < dur:
        run(["ffmpeg", "-y", "-stream_loop", "-1", "-ss", str(offset), "-i", src, "-t", str(dur),
             "-vf", vf, "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", out])
    else:
        run(["ffmpeg", "-y", "-ss", str(offset), "-i", src, "-t", str(dur),
             "-vf", vf, "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", out])


def concat_crossfade(norm_paths, durations, out_video, transition=0.35):
    inputs = []
    for p in norm_paths:
        inputs += ["-i", p]
    filters = []
    cumulative = durations[0]
    last_label = "0:v"
    for i in range(1, len(norm_paths)):
        offset = max(cumulative - transition, 0)
        out_label = f"v{i}"
        filters.append(f"[{last_label}][{i}:v]xfade=transition=fade:duration={transition}:offset={offset:.3f}[{out_label}]")
        cumulative = cumulative + durations[i] - transition
        last_label = out_label
    filter_complex = ";".join(filters)
    cmd = ["ffmpeg", "-y", *inputs, "-filter_complex", filter_complex,
           "-map", f"[{last_label}]", "-c:v", "libx264", "-pix_fmt", "yuv420p", out_video]
    run(cmd)


def build(order, workdir, out_video, crossfade=0.35):
    os.makedirs(workdir, exist_ok=True)
    norm_paths = []
    durations = []
    n = len(order)
    for i, item in enumerate(order):
        path, dur = item[0], item[1]
        offset = item[2] if len(item) > 2 else 0.0
        # Compensate for the runtime xfade will eat at each transition — see
        # module docstring. Every clip but the last plays `crossfade` seconds
        # longer than its nominal slot.
        actual_dur = dur + crossfade if (crossfade and i < n - 1) else dur
        out = f"{workdir}/n_{i:03d}.mp4"
        normalize(path, actual_dur, out, offset)
        norm_paths.append(out)
        durations.append(actual_dur)
        print(f"{i+1}/{n} {actual_dur:.2f}s @{offset:.2f} <- {path}")
    if crossfade:
        concat_crossfade(norm_paths, durations, out_video, transition=crossfade)
    else:
        listp = f"{workdir}/list.txt"
        with open(listp, "w") as f:
            for p in norm_paths:
                f.write(f"file '{os.path.abspath(p)}'\n")
        run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", listp, "-r", str(FPS),
             "-c:v", "libx264", "-pix_fmt", "yuv420p", out_video])
    print("VIDEO:", out_video)


if __name__ == "__main__":
    section_file = sys.argv[1]
    workdir = sys.argv[2]
    out_video = sys.argv[3]
    crossfade = float(sys.argv[4]) if len(sys.argv) > 4 else 0.35
    order = json.load(open(section_file))
    build(order, workdir, out_video, crossfade=crossfade)
