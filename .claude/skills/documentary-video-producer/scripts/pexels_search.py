#!/usr/bin/env python3
"""Search Pexels for real video footage. Mirrors the sibling
pixabay-video-producer skill's pixabay_search.py output shape so both
sources can feed the same downstream pipeline (download_clip.py from that
skill works unchanged against Pexels download URLs too).

Why a second source at all: Pixabay's library is strong for generic
lifestyle/nature footage but thin for niche topics (e.g. searches for
"ambulance economics"-adjacent scenes like "family reviewing medical bill"
returned mostly off-topic results). Pexels' catalog skews more toward
editorial/documentary-style footage and filled those gaps significantly in
practice — worth querying both and picking whichever result actually
matches, rather than forcing a mediocre Pixabay hit.

Requires PEXELS_API_KEY (free at https://www.pexels.com/api/). Note the
default urllib User-Agent gets a Cloudflare 403 from Pexels' API exactly
like Pixabay's CDN does — this script and download_clip.py both already
send a browser-like User-Agent to work around it.

Usage:
    python3 pexels_search.py --query "family reviewing bill" --per-page 6 --top 4
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

API_URL = "https://api.pexels.com/videos/search"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", required=True)
    parser.add_argument("--orientation", choices=["all", "landscape", "portrait", "square"], default="landscape")
    parser.add_argument("--min-duration", type=float, default=0.0)
    parser.add_argument("--per-page", type=int, default=15)
    parser.add_argument("--top", type=int, default=5)
    args = parser.parse_args()

    api_key = os.environ.get("PEXELS_API_KEY")
    if not api_key:
        print(json.dumps({"error": "PEXELS_API_KEY not set"}), file=sys.stderr)
        sys.exit(1)

    params = {"query": args.query, "per_page": str(min(80, args.per_page))}
    if args.orientation != "all":
        params["orientation"] = args.orientation
    url = f"{API_URL}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"Authorization": api_key, "User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.load(resp)
    except urllib.error.HTTPError as e:
        print(json.dumps({"error": f"Pexels API error {e.code}: {e.read().decode(errors='replace')}"}), file=sys.stderr)
        sys.exit(1)

    candidates = []
    for v in data.get("videos", []):
        if v.get("duration", 0) < args.min_duration:
            continue
        files = sorted(v["video_files"], key=lambda f: -(f.get("width") or 0))
        hd = next((f for f in files if (f.get("width") or 0) <= 1920 and f.get("file_type") == "video/mp4"), files[0] if files else None)
        if not hd:
            continue
        candidates.append({
            "id": v["id"],
            "page_url": v["url"],
            "duration": v.get("duration"),
            "width": hd["width"], "height": hd["height"],
            "download_url": hd["link"],
            "user": v["user"]["name"], "user_url": v["user"]["url"],
        })
    print(json.dumps(candidates[: args.top], indent=2))


if __name__ == "__main__":
    main()
