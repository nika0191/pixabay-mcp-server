#!/usr/bin/env python3
"""Render a list of HTML graphic cards to MP4 clips via headless Chromium.

Takes a JSON job list `[[beat_index, html_path, duration_seconds], ...]`
(the `gen_jobs` output of build_beats.flatten_to_order) and, for each one,
records `duration + BUFFER` seconds of the page as WEBM, then transcodes to
MP4 at `out_dir/<prefix>_b<index>.mp4`.

The BUFFER (default 2.0s) matters: assemble_section.py extends every beat's
requested duration by the crossfade length when building the final cut (see
that script's docstring), so the rendered clip must be at least
`duration + crossfade` long or normalize() will fall back to
`-stream_loop -1`, which repeats the card's reveal animation instead of
holding its settled end state — visually wrong for anything with motion.
2.0s of buffer covers any crossfade duration in normal use (0.2-0.6s) with
margin to spare; raise it if you're using longer transitions.

Requires the Playwright Python package AND a Chromium binary whose build
number matches what that package version expects. In sandboxed/managed
environments the pip-installed `playwright` version frequently does NOT
match a pre-staged system Chromium — if `playwright install` is unavailable
or fails, point `--chrome` at whatever Chromium binary IS present (e.g.
`/opt/pw-browsers/chromium-<rev>/chrome-linux/chrome`) and pass
`--no-sandbox` (default on) rather than trying to reconcile versions.

Usage:
    python3 record_graphics.py --jobs gen_jobs.json --out-dir graphics/ \
        --prefix s2 [--chrome /path/to/chromium] [--buffer 2.0]
"""

import argparse
import json
import os
import shutil
import subprocess


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--jobs", required=True, help="JSON list of [beat_index, html_path, duration]")
    p.add_argument("--out-dir", required=True)
    p.add_argument("--prefix", required=True, help="output filename prefix, files land at <out-dir>/<prefix>_b<index:03d>.mp4")
    p.add_argument("--chrome", default=None, help="path to a Chromium binary; omit to let Playwright pick its own")
    p.add_argument("--buffer", type=float, default=2.0)
    p.add_argument("--no-sandbox", dest="no_sandbox", action="store_true", default=True)
    args = p.parse_args()

    from playwright.sync_api import sync_playwright

    jobs = json.load(open(args.jobs))
    os.makedirs(args.out_dir, exist_ok=True)

    launch_kwargs = {}
    if args.chrome:
        launch_kwargs["executable_path"] = args.chrome
    if args.no_sandbox:
        launch_kwargs["args"] = ["--no-sandbox"]

    with sync_playwright() as p_ctx:
        browser = p_ctx.chromium.launch(**launch_kwargs)
        for idx, html_path, dur in jobs:
            record_dur = dur + args.buffer
            video_dir = os.path.join(args.out_dir, f"_vid_{args.prefix}_b{idx:03d}")
            os.makedirs(video_dir, exist_ok=True)
            context = browser.new_context(
                viewport={"width": 1920, "height": 1080},
                record_video_dir=video_dir,
                record_video_size={"width": 1920, "height": 1080},
            )
            page = context.new_page()
            page.goto(f"file://{os.path.abspath(html_path)}")
            page.wait_for_timeout(int(record_dur * 1000))
            video_path = page.video.path()
            context.close()
            out_mp4 = os.path.join(args.out_dir, f"{args.prefix}_b{idx:03d}.mp4")
            subprocess.run(
                ["ffmpeg", "-y", "-i", video_path, "-r", "30", "-c:v", "libx264", "-pix_fmt", "yuv420p", out_mp4],
                check=True, capture_output=True,
            )
            shutil.rmtree(video_dir)
            print(f"beat {idx}: recorded {record_dur:.2f}s -> {out_mp4}")
        browser.close()


if __name__ == "__main__":
    main()
