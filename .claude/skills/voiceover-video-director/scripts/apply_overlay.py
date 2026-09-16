#!/usr/bin/env python3
"""Composite brand elements onto a real (Pixabay) clip for a HYBRID beat.

This is what makes a HYBRID beat different from a plain PIXABAY beat: the
realistic footage stays as-is, but a branded layer sits on top of it —
a caption/stat callout, a color grade toward the channel palette, and/or a
transparent logo/character/graphic overlay. All layers are optional; pass
only the ones this beat needs.

Usage:
    python3 apply_overlay.py --input scene.mp4 --output scene_hybrid.mp4 \
        --caption-text "EIGHTY-FIVE DOLLARS A DAY" --accent-color "#E63A2E" \
        --stat-text "$85/day" --grade-color "#E63A2E" --grade-strength 0.15 \
        --overlay-image character.png --overlay-position bottom-right
"""

import argparse
import shutil
import subprocess
import sys


def hex_to_ffmpeg_color(hex_color: str) -> str:
    return "0x" + hex_color.lstrip("#")


def run(cmd):
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed ({' '.join(cmd)}):\n{result.stdout}")
    return result.stdout


OVERLAY_POSITIONS = {
    "bottom-right": "W-w-40:H-h-40",
    "bottom-left": "40:H-h-40",
    "top-right": "W-w-40:40",
    "top-left": "40:40",
    "center": "(W-w)/2:(H-h)/2",
}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--caption-text", default=None, help="Subtitle-style line, bottom-safe area")
    parser.add_argument("--caption-color", default="#F2EFE6")
    parser.add_argument("--stat-text", default=None, help="Big accent-colored number/stat callout, e.g. $85/day")
    parser.add_argument("--accent-color", default="#E63A2E", help="Used for --stat-text")
    parser.add_argument("--font", default=None, help="Path to a .ttf/.otf; falls back to ffmpeg's default font if omitted")
    parser.add_argument("--grade-color", default=None, help="Hex color to tint shadows toward, for brand-consistent grading")
    parser.add_argument("--grade-strength", type=float, default=0.12, help="0-1, how strong the tint is")
    parser.add_argument("--overlay-image", default=None, help="Transparent PNG/WebM: logo, character, or graphic element")
    parser.add_argument("--overlay-position", choices=list(OVERLAY_POSITIONS), default="bottom-right")
    parser.add_argument("--overlay-scale-width", type=int, default=None, help="Resize overlay image to this width, keep aspect")
    args = parser.parse_args()

    if shutil.which("ffmpeg") is None:
        print("ffmpeg not found on PATH.", file=sys.stderr)
        sys.exit(1)

    inputs = ["-i", args.input]
    filter_chain = "[0:v]"
    filter_steps = []
    label_counter = 0

    def new_label():
        nonlocal label_counter
        label_counter += 1
        return f"v{label_counter}"

    current = "0:v"

    if args.grade_color:
        r = int(args.grade_color.lstrip("#")[0:2], 16) / 255
        g = int(args.grade_color.lstrip("#")[2:4], 16) / 255
        b = int(args.grade_color.lstrip("#")[4:6], 16) / 255
        s = args.grade_strength
        label = new_label()
        filter_steps.append(
            f"[{current}]colorbalance=rs={r*s:.3f}:gs={g*s:.3f}:bs={b*s:.3f}:"
            f"rm={r*s*0.5:.3f}:gm={g*s*0.5:.3f}:bm={b*s*0.5:.3f}[{label}]"
        )
        current = label

    font_opt = f":fontfile={args.font}" if args.font else ""

    if args.caption_text:
        label = new_label()
        escaped = args.caption_text.replace("'", r"\'").replace(":", r"\:")
        color = hex_to_ffmpeg_color(args.caption_color)
        filter_steps.append(
            f"[{current}]drawtext=text='{escaped}'{font_opt}:fontcolor={color}:fontsize=54:"
            f"box=1:boxcolor=0x121212@0.55:boxborderw=20:x=(w-text_w)/2:y=h-th-90[{label}]"
        )
        current = label

    if args.stat_text:
        label = new_label()
        escaped = args.stat_text.replace("'", r"\'").replace(":", r"\:")
        color = hex_to_ffmpeg_color(args.accent_color)
        filter_steps.append(
            f"[{current}]drawtext=text='{escaped}'{font_opt}:fontcolor={color}:fontsize=90:"
            f"borderw=3:bordercolor=0x000000:x=(w-text_w)/2:y=(h-text_h)/2[{label}]"
        )
        current = label

    map_video = f"[{current}]"

    if args.overlay_image:
        inputs += ["-i", args.overlay_image]
        overlay_input = "1:v"
        if args.overlay_scale_width:
            overlay_input_label = "ov_scaled"
            filter_steps.append(f"[1:v]scale={args.overlay_scale_width}:-1[{overlay_input_label}]")
            overlay_input = overlay_input_label
        pos = OVERLAY_POSITIONS[args.overlay_position]
        label = new_label()
        filter_steps.append(f"[{current}][{overlay_input}]overlay={pos}[{label}]")
        map_video = f"[{label}]"

    cmd = ["ffmpeg", "-y", *inputs]
    if filter_steps:
        cmd += ["-filter_complex", ";".join(filter_steps), "-map", map_video]
    else:
        cmd += ["-map", "0:v"]
    cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", args.output]

    run(cmd)
    print(args.output)


if __name__ == "__main__":
    main()
