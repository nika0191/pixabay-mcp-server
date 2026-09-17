#!/usr/bin/env python3
"""Download one Pixabay video rendition to a local file, with retries.

Usage:
    python3 download_clip.py --url https://cdn.pixabay.com/... --output scene1.mp4
"""

import argparse
import sys
import time
import urllib.request
import urllib.error


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--retries", type=int, default=3)
    args = parser.parse_args()

    last_error = None
    for attempt in range(1, args.retries + 1):
        try:
            # cdn.pixabay.com returns 403 for the default urllib user agent.
            request = urllib.request.Request(args.url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(request, timeout=60) as response, open(args.output, "wb") as out_file:
                out_file.write(response.read())
            print(args.output)
            return
        except (urllib.error.URLError, TimeoutError) as e:
            last_error = e
            time.sleep(min(2 ** attempt, 8))

    print(f"Failed to download {args.url} after {args.retries} attempts: {last_error}", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
