#!/usr/bin/env python3
"""Search Pixabay for real (non-AI) stock video clips for one storyboard scene.

Reads PIXABAY_API_KEY from the environment. Prints a JSON array of candidate
clips to stdout, ranked by how well they fit the requested orientation and
minimum duration, best first.

Usage:
    python3 pixabay_search.py --query "city traffic night" --orientation vertical \
        --min-duration 4 --per-page 10
"""

import argparse
import json
import sys
import urllib.parse
import urllib.request
import urllib.error

API_URL = "https://pixabay.com/api/videos/"

# Pixabay's native rendition sizes, largest first. We pick the largest
# rendition available so ffmpeg has enough resolution to crop to the target
# aspect ratio without upscaling artifacts, unless --max-width caps it.
RENDITIONS = ["large", "medium", "small", "tiny"]


def pick_rendition(video_sizes: dict, max_width: int | None):
    candidates = [video_sizes[r] for r in RENDITIONS if r in video_sizes]
    if max_width:
        fitting = [c for c in candidates if c["width"] <= max_width]
        if fitting:
            return fitting[0]
    return candidates[0] if candidates else None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", required=True, help="Search terms (English works best on Pixabay)")
    parser.add_argument("--orientation", choices=["all", "horizontal", "vertical"], default="all")
    parser.add_argument("--video-type", choices=["all", "film", "animation"], default="film",
                         help="'film' = real footage. Use 'all' only if animation is acceptable.")
    parser.add_argument("--category", default=None)
    parser.add_argument("--min-duration", type=float, default=0.0,
                         help="Drop clips shorter than this many seconds")
    parser.add_argument("--per-page", type=int, default=30,
                         help="How many raw results to fetch before client-side orientation filtering (3-200). "
                              "Pixabay has no server-side orientation filter, so fetch generously.")
    parser.add_argument("--max-width", type=int, default=None,
                         help="Cap the picked rendition's width, e.g. 1920")
    parser.add_argument("--allow-ai-generated", action="store_true",
                         help="By default AI-generated Pixabay clips are excluded so footage stays realistic")
    parser.add_argument("--top", type=int, default=5, help="How many ranked candidates to return")
    args = parser.parse_args()

    api_key = __import__("os").environ.get("PIXABAY_API_KEY")
    if not api_key:
        print(json.dumps({"error": "PIXABAY_API_KEY environment variable is not set"}), file=sys.stderr)
        sys.exit(1)

    params = {
        "key": api_key,
        "q": args.query[:100],
        "video_type": args.video_type,
        "safesearch": "true",
        "per_page": str(max(3, min(200, args.per_page))),
        "order": "popular",
    }
    if args.orientation != "all":
        # Pixabay's video API has no orientation param; we infer it after the
        # fact from width/height and filter client-side.
        pass
    if args.category:
        params["category"] = args.category

    url = f"{API_URL}?{urllib.parse.urlencode(params)}"
    try:
        with urllib.request.urlopen(url, timeout=20) as resp:
            data = json.load(resp)
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        print(json.dumps({"error": f"Pixabay API error {e.code}: {body}"}), file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(json.dumps({"error": f"Network error contacting Pixabay: {e}"}), file=sys.stderr)
        sys.exit(1)

    hits = data.get("hits", [])
    candidates = []
    for hit in hits:
        if hit.get("isAiGenerated") and not args.allow_ai_generated:
            continue
        if hit.get("isLowQuality"):
            continue
        if hit.get("duration", 0) < args.min_duration:
            continue

        rendition = pick_rendition(hit.get("videos", {}), args.max_width)
        if not rendition:
            continue

        width, height = rendition["width"], rendition["height"]
        orientation = "vertical" if height > width else ("square" if height == width else "horizontal")
        if args.orientation != "all" and orientation != args.orientation:
            continue

        candidates.append({
            "id": hit["id"],
            "page_url": hit.get("pageURL"),
            "tags": hit.get("tags"),
            "duration": hit.get("duration"),
            "orientation": orientation,
            "width": width,
            "height": height,
            "download_url": rendition["url"],
            "thumbnail_url": rendition.get("thumbnail"),
            "user": hit.get("user"),
            "user_url": hit.get("userURL"),
            "views": hit.get("views"),
        })

    # Rank: prefer exact orientation match (already filtered), then clips
    # whose duration is closest to (but not much shorter than) what's needed,
    # then popularity (views) as a tiebreaker.
    candidates.sort(key=lambda c: (-(c["duration"] >= args.min_duration), c["duration"], -c["views"]))
    candidates.sort(key=lambda c: -c["views"])

    print(json.dumps(candidates[: args.top], indent=2))


if __name__ == "__main__":
    main()
