---
name: pixabay-video-producer
description: Builds a finished video, reel, short, or ad from a script/topic using REAL, non-AI-generated stock footage sourced live from Pixabay — not text-to-video generation. Searches Pixabay per scene, filters out AI-generated and low-quality hits, downloads the real clips, and assembles them with ffmpeg into a vertical (9:16), horizontal (16:9), or square cut with optional crossfades and a music/voiceover track. Use this whenever the user wants a video/reel/short/montage/ad made from real or realistic stock footage, explicitly mentions Pixabay, wants footage that is NOT AI-generated, or hands over a script/storyboard/list of scenes to turn into a video. Also trigger for Russian phrasing like "смонтируй ролик из реальных/реалистичных кадров", "сделай видео с пиксабей", "собери ролик из настоящих кадров", "нужны реалистичные кадры для видео". Do not use this for AI video generation (that's a different tool/skill) or for a single one-off image/clip lookup with no assembly involved.
---

# Pixabay Video Producer

Turns a script or topic into a finished MP4 built entirely from real Pixabay
footage. The point of this skill is realism: every clip is checked against
Pixabay's `isAiGenerated` flag and rejected if it's synthetic, so the output
is genuine stock footage, not a generative-video result.

## Requirements

- `PIXABAY_API_KEY` environment variable set to a valid Pixabay API key (free
  at https://pixabay.com/api/docs/). If it's missing, ask the user for one —
  don't guess or reuse a key from an unrelated project.
- `ffmpeg` and `ffprobe` on PATH. If missing, install them (e.g.
  `apt-get install -y ffmpeg`) before continuing, or tell the user to.
- Outbound network access to `pixabay.com` and `cdn.pixabay.com`.

## Workflow

### 1. Pin down the brief

The user will usually describe the video in plain language ("видео про кофе,
3 сцены", "a 20s reel about morning runs"). From that, and by asking when it's
genuinely ambiguous, establish:

- **The scenes**: a short list of shots, each with what should be visible and
  roughly how long it plays. If the user gives you a script/voiceover instead
  of explicit scenes, split it into natural visual beats yourself (aim for
  3-6 second scenes — long enough to read as a shot, short enough to keep
  the montage moving).
- **Aspect ratio**: ask if not stated. Vertical `9:16` for Reels/Shorts/TikTok
  is the most common default to suggest, `16:9` for YouTube/presentations,
  `1:1` or `4:5` for feed posts.
- **Transition style**: hard cuts (default, punchier) or crossfades (softer,
  better for calm/ambient content). Ask only if it matters for the tone.
- **Audio**: does the user have a music/voiceover file to lay under the
  footage? Pixabay clips are downloaded silent by design (their built-in
  ambience rarely matches a soundtrack), so audio is always a separate,
  optional file passed in at assembly time.

Don't over-interview — if the brief is clear and low-stakes, make a
reasonable call (e.g. default to hard cuts, 4s/scene) and mention what you
chose rather than blocking on it.

### 2. Turn each scene into a Pixabay search

Pixabay's index is strongest in English, so translate/derive concise English
keywords per scene even if the conversation is in another language (e.g. a
scene about "утренняя пробежка в парке" searches best as `morning jogging
park`). Prefer concrete, visual nouns over abstract ones — "steaming coffee
cup" beats "cozy morning".

Run the search helper for each scene:

```bash
python3 scripts/pixabay_search.py \
  --query "steaming coffee cup" \
  --orientation vertical \
  --min-duration 4 \
  --top 5
```

This already excludes AI-generated and low-quality hits. It returns ranked
JSON candidates with `id`, `download_url`, `duration`, `tags`, `page_url`,
and `user`. Pick the best match per scene, and **track which `id`s you've
already used** so the same clip doesn't repeat across scenes in one video —
if the top result is a repeat, take the next one down.

If nothing suitable comes back (empty list), broaden the query (drop a
modifier, try a synonym) before giving up on a scene.

### 3. Download the chosen clips

```bash
python3 scripts/download_clip.py --url "<download_url>" --output work/scene_01.mp4
```

Keep them in one working directory per project so paths line up with the
manifest in the next step.

### 4. Build the manifest and assemble

Write a JSON manifest listing the downloaded files in scene order with each
one's intended on-screen duration (seconds):

```json
[
  {"file": "work/scene_01.mp4", "duration": 4},
  {"file": "work/scene_02.mp4", "duration": 3.5},
  {"file": "work/scene_03.mp4", "duration": 4}
]
```

Then assemble:

```bash
python3 scripts/assemble_video.py \
  --manifest work/manifest.json \
  --aspect 9:16 \
  --transition cut \
  --output work/final.mp4
```

Add `--transition crossfade --transition-duration 0.5` for softer cuts, and
`--audio work/soundtrack.mp3` if the user supplied (or asked for) music or a
voiceover — it will be looped/trimmed to the video's length with a 1s fade
out at the end. `--aspect` also accepts `16:9`, `1:1`, `4:5`, or a raw
`WIDTHxHEIGHT`. Clips shorter than their scene duration are looped rather
than frozen or stretched, and every clip is cropped (never squeezed) to fill
the target frame.

### 5. Attribution and delivery

Pixabay's license doesn't require attribution, but it's good practice and
takes no effort — write a short `credits.txt` next to the output listing
each clip's `page_url` and `user` from the search results. Then hand the
finished MP4 to the user (send the file if the environment supports it) and
mention the aspect ratio, length, and transition style you used, plus
anything you had to guess.

## Notes and limits

- Respect Pixabay's API terms: cache/reuse results instead of re-querying
  the same search repeatedly, and stay under 100 requests/60s.
- `search_videos`/`get_video_by_id` from this repo's own MCP server
  (`src/index.ts`) expose the same underlying API if an MCP connection is
  preferred over the bundled script — either path hits the same endpoint and
  the same `isAiGenerated` field is present in its raw JSON output, but the
  MCP tools don't pre-filter it, so re-apply that filter yourself if you use
  them instead of `pixabay_search.py`.
- If a scene's best available footage is still a poor match, say so rather
  than silently forcing an unrelated clip in — a slightly generic but
  on-topic shot beats a literal but jarring mismatch.
