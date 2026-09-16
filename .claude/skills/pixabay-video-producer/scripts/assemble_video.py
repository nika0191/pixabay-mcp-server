#!/usr/bin/env python3
"""Assemble downloaded Pixabay clips into one finished video with ffmpeg.

Takes a JSON manifest describing each scene's local video file and how long
it should play, normalizes every clip to one resolution/frame rate/aspect
ratio (cropping to fill, never stretching), joins them with a hard cut or a
crossfade, and optionally muxes in a soundtrack/voiceover.

Manifest format (list of scenes, in order):
    [
      {"file": "clip1.mp4", "duration": 4},
      {"file": "clip2.mp4", "duration": 3.5}
    ]

Usage:
    python3 assemble_video.py --manifest manifest.json --aspect 9:16 \
        --output final.mp4 --transition crossfade --transition-duration 0.5 \
        --audio voiceover.mp3
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile

PRESET_ASPECTS = {
    "9:16": (1080, 1920),
    "16:9": (1920, 1080),
    "1:1": (1080, 1080),
    "4:5": (1080, 1350),
}


def resolve_resolution(aspect: str):
    if aspect in PRESET_ASPECTS:
        return PRESET_ASPECTS[aspect]
    if "x" in aspect.lower():
        w, h = aspect.lower().split("x")
        return int(w), int(h)
    raise ValueError(f"Unknown --aspect '{aspect}'. Use 9:16, 16:9, 1:1, 4:5, or WIDTHxHEIGHT.")


def run(cmd):
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed ({' '.join(cmd)}):\n{result.stdout}")
    return result.stdout


def probe_duration(path: str) -> float:
    out = run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
               "-of", "default=noprint_wrappers=1:nokey=1", path])
    return float(out.strip())


def normalize_clip(src: str, duration: float, width: int, height: int, fps: int, out_path: str):
    src_duration = probe_duration(src)
    vf = f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height},setsar=1,fps={fps}"
    if src_duration < duration:
        # Loop the source so short clips can still cover a longer scene.
        cmd = ["ffmpeg", "-y", "-stream_loop", "-1", "-i", src, "-t", str(duration),
               "-vf", vf, "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", out_path]
    else:
        cmd = ["ffmpeg", "-y", "-i", src, "-t", str(duration),
               "-vf", vf, "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", out_path]
    run(cmd)


def concat_cut(normalized: list, output: str, fps: int):
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        for path in normalized:
            f.write(f"file '{os.path.abspath(path)}'\n")
        list_path = f.name
    try:
        run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_path,
             "-r", str(fps), "-c:v", "libx264", "-pix_fmt", "yuv420p", output])
    finally:
        os.unlink(list_path)


def concat_crossfade(normalized: list, durations: list, output: str, transition_duration: float):
    inputs = []
    for path in normalized:
        inputs += ["-i", path]

    filters = []
    cumulative = durations[0]
    last_label = "0"
    for i in range(1, len(normalized)):
        offset = max(cumulative - transition_duration, 0)
        out_label = f"v{i}"
        filters.append(
            f"[{last_label}][{i}]xfade=transition=fade:duration={transition_duration}:offset={offset:.3f}[{out_label}]"
        )
        cumulative = cumulative + durations[i] - transition_duration
        last_label = out_label

    filter_complex = ";".join(filters)
    cmd = ["ffmpeg", "-y", *inputs, "-filter_complex", filter_complex,
           "-map", f"[{last_label}]", "-c:v", "libx264", "-pix_fmt", "yuv420p", output]
    run(cmd)


def mux_audio(video_path: str, audio_path: str, output: str, fade_out: float = 1.0):
    video_duration = probe_duration(video_path)
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-stream_loop", "-1", "-i", audio_path,
        "-filter_complex",
        f"[1:a]atrim=0:{video_duration},afade=t=out:st={max(video_duration - fade_out, 0):.3f}:d={fade_out}[aout]",
        "-map", "0:v", "-map", "[aout]",
        "-c:v", "copy", "-c:a", "aac", "-shortest", output,
    ]
    run(cmd)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--manifest", required=True, help="JSON file: [{file, duration}, ...]")
    parser.add_argument("--aspect", default="9:16", help="9:16, 16:9, 1:1, 4:5, or WIDTHxHEIGHT")
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--transition", choices=["cut", "crossfade"], default="cut")
    parser.add_argument("--transition-duration", type=float, default=0.5)
    parser.add_argument("--audio", default=None, help="Optional music/voiceover track to mux over the final cut")
    parser.add_argument("--output", required=True)
    parser.add_argument("--workdir", default=None, help="Where to put normalized intermediate clips (default: temp dir)")
    args = parser.parse_args()

    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        print("ffmpeg/ffprobe not found on PATH. Install ffmpeg first.", file=sys.stderr)
        sys.exit(1)

    with open(args.manifest) as f:
        scenes = json.load(f)
    if not scenes:
        print("Manifest is empty.", file=sys.stderr)
        sys.exit(1)

    width, height = resolve_resolution(args.aspect)
    workdir = args.workdir or tempfile.mkdtemp(prefix="pixabay_assemble_")
    os.makedirs(workdir, exist_ok=True)

    normalized_paths = []
    durations = []
    for i, scene in enumerate(scenes):
        out_path = os.path.join(workdir, f"norm_{i:03d}.mp4")
        normalize_clip(scene["file"], float(scene["duration"]), width, height, args.fps, out_path)
        normalized_paths.append(out_path)
        durations.append(float(scene["duration"]))
        print(f"Normalized scene {i+1}/{len(scenes)}: {scene['file']}", file=sys.stderr)

    concatenated = os.path.join(workdir, "concatenated.mp4") if args.audio else args.output
    if args.transition == "crossfade" and len(normalized_paths) > 1:
        concat_crossfade(normalized_paths, durations, concatenated, args.transition_duration)
    else:
        concat_cut(normalized_paths, concatenated, args.fps)

    if args.audio:
        mux_audio(concatenated, args.audio, args.output)

    print(json.dumps({"output": args.output, "resolution": f"{width}x{height}", "scenes": len(scenes)}))


if __name__ == "__main__":
    main()
