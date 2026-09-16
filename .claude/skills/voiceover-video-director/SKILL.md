---
name: voiceover-video-director
description: Turns a FINISHED voiceover recording plus its transcript into a fully edited video by running the pixabay-video-producer and AI-scene-generation workflows as one system instead of two separate tools. For every semantic beat of the voiceover (~3-5s each) it decides GENERATED (branded AI video/motion graphics for metaphors, abstractions, or moments that need the channel's visual identity), PIXABAY (real, non-AI stock footage when it genuinely and concretely matches the line), or HYBRID (real Pixabay footage composited with branded captions/stat callouts/graphics/character overlays) — then executes that decision and locks every cut to the voiceover's real timing. Use this whenever the user has an already-recorded voiceover/narration + transcript and wants a finished video built to it, asks to combine or unify the Pixabay skill with the AI/branded video-generation skill, wants a single edit plan mixing real and generated footage, or describes a documentary/explainer/YouTube edit that should use real footage where it strengthens the point and generated visuals where a metaphor or brand moment is needed. Do not use this to generate a video from a topic with no voiceover yet (that's the standalone video-producer skill's job) or for a plain b-roll montage with no per-beat format decision (use pixabay-video-producer alone for that).
---

# Voiceover Video Director

Orchestrates two capabilities as one pipeline: **pixabay-video-producer**
(this repo's `.claude/skills/pixabay-video-producer`, real non-AI stock
footage) and **branded AI scene generation** (whatever AI video/motion-graphics
workflow is set up for the channel — e.g. the `grim-margins-video-producer`
skill's prompt style and Remotion-style graphics conventions, or a connected
generation tool like BFL `generate_video` / VideoGen `generate_video_clip`).
Neither one decides the edit alone. This skill reads the voiceover, decides
*per beat* which capability should render that beat (or both, for HYBRID),
and produces one locked-to-audio shot list and one final render.

## Requirements

- The finished voiceover audio file, and its transcript. Timestamps make
  everything downstream far more accurate — see Step 1.
- `PIXABAY_API_KEY` set, and `ffmpeg`/`ffprobe` on PATH (same as
  pixabay-video-producer).
- A connected AI video-generation tool for GENERATED beats (BFL `generate_video`,
  VideoGen `generate_video_clip`/`prompt_to_video_clip`, or equivalent). If
  none is connected, still produce the full plan and the branded generation
  prompts, and say plainly that GENERATED beats need to be rendered
  elsewhere — don't silently substitute Pixabay footage for a beat you
  decided should be generated.
- A brand reference, if one exists for this channel (e.g. `claude/grim-margins-brand.md`
  or similar in the project). If nothing like that exists and the plan
  includes GENERATED or HYBRID beats, ask the user for the minimum needed —
  palette, tone, any recurring motif/character/logo asset — before producing
  those beats. Pure-PIXABAY plans don't need this at all.
- AI video generation typically costs real credits. Before generating more
  than a couple of clips, total up how many GENERATED beats the plan has and
  confirm with the user if that's a meaningful spend — the same courtesy
  grim-margins-video-producer's own budget check extends here.

## Workflow

### 1. Get real timing for the transcript

Precision here is what makes every later cut land exactly on the word it's
illustrating, so don't skip straight to guessing.

- **Transcript already has timestamps** (SRT, VTT, or a word/sentence JSON
  export from the TTS or an aligner): run
  `scripts/parse_transcript.py --input transcript.srt` → sentence-level JSON.
- **Plain text only, no timestamps**: run
  `scripts/estimate_timing.py --audio voiceover.mp3 --transcript script.txt`.
  This distributes the real audio duration across sentences by word count —
  it's an approximation (it doesn't know about pauses or emphasis), so treat
  the resulting cuts as a first pass and nudge any beat that clearly drifts
  once you scrub the assembled video.

### 2. Group sentences into visual beats

```bash
python3 scripts/build_beats.py --input sentences.json --target 4 --min 3 --max 5 --hard-cap 7
```

This merges short consecutive sentences toward ~4s and keeps a single long
sentence whole rather than cutting it mid-word. Beats flagged `long_beat`
(over the hard cap) are candidates for two visual cuts instead of one static
shot — decide that when you build the shot list in the next step.

### 3. Decide the format for every beat — the core judgment call

This step is yours to reason through, not a script's — read each beat's text
and picture what actually needs to be on screen. Use this as the decision
order, not a checklist to satisfy mechanically:

1. **Does this beat name or imply a concrete, filmable, real-world thing** —
   a place, an object, a generic action, a type of person doing a
   recognizable task? → **PIXABAY**. Search for it (Step 4). Only fall
   through to GENERATED if nothing suitable turns up.
2. **Is this beat abstract, a metaphor, a brand moment (a reveal, a
   recurring motif, a number that needs to *feel* like the channel), or a
   shot no camera could realistically get** (impossible angle,
   reconstruction of something with no footage, a process with no real
   people to film)? → **GENERATED**.
3. **Does a real, concrete scene from case 1 still need something added to
   land the specific point** — the exact stat spoken, a branded stamp/label,
   a character or graphic the channel always uses, a caption calling out
   what to notice? → **HYBRID**: real Pixabay base + a branded layer on top.

A few worked examples:

| Voiceover line | Format | Why |
|---|---|---|
| "Rows of cars sit behind the impound lot's fence." | PIXABAY | Concrete, ordinary, exists as stock footage. |
| "The debt gets quietly passed down a chain nobody sees." | GENERATED | Abstract mechanism, needs a visual metaphor. |
| "That's eighty-five dollars a day, every day it sits there." | HYBRID | Real impound-lot footage + a `$85/day` stat callout burned in at the moment it's said. |
| "Here's who actually gets paid first." | GENERATED (or the channel's motion-graphics template) | A reveal/brand moment, not a literal scene. |

Never force a PIXABAY clip that's only vaguely on-topic just to avoid
generating — an on-topic but generic real shot is fine, a real shot that
contradicts or is unrelated to the line is worse than a well-directed
generated one.

### 4. Build the one shot list — this is the deliverable that makes it one system

Produce a single table (and save it as `shot_list.md`) covering every beat,
regardless of format — this is what keeps both capabilities working off the
same plan instead of two disconnected outputs:

| Beat | Time | Voiceover | Format | Visual | Source details |
|---|---|---|---|---|---|
| 001 | 00:00–00:04 | "Rows of cars sit behind the impound lot's fence." | PIXABAY | Chain-link fence, parked impounded cars, late afternoon | Search: `impound lot fence cars`; picked clip id 228847 |
| 002 | 00:04–00:09 | "That's eighty-five dollars a day, every day it sits there." | HYBRID | Same impound lot, `$85/DAY` stat burned in, counter ticking | Base: clip 228847 (reused, different trim) + `apply_overlay.py --stat-text "$85/DAY"` |
| 003 | 00:09–00:14 | "The debt gets quietly passed down a chain nobody sees." | GENERATED | Abstract chain-link of hands passing an envelope, dim warm light, dolly-in | Prompt below |

For GENERATED rows, write the full production prompt using the same
structure grim-margins-video-producer uses (Subject / Environment / Action /
Camera / Lighting / Realism / Mood / Duration / Aspect / Must NOT appear) so
output stays visually consistent even across different generation calls.

### 5. Resolve each beat's visual

- **PIXABAY beats**: use pixabay-video-producer's own scripts directly —
  `../pixabay-video-producer/scripts/pixabay_search.py` then
  `../pixabay-video-producer/scripts/download_clip.py` — with the query and
  duration from the shot list. Track used clip IDs across the whole video so
  the same footage doesn't repeat unless intentionally reused (as in the
  HYBRID example above, which is fine — it's the same establishing shot
  getting a graphic added, not a lazy repeat).
- **GENERATED beats**: submit the production prompt to the connected AI
  video tool. Generate a draft first if the tool supports it, confirm it
  matches the shot list entry, then finalize. Don't generate near-duplicate
  scenes for beats that read similarly — vary angle, environment, or action
  the way grim-margins-video-producer's own rules require, or reuse an
  already-generated clip with a different trim instead of making a new
  near-identical one.
- **HYBRID beats**: resolve the base the same way as a PIXABAY beat, then run
  `scripts/apply_overlay.py` on the downloaded clip with whatever combination
  of `--caption-text`, `--stat-text`, `--grade-color`, and `--overlay-image`
  the shot list calls for.

Each beat should end up as one local video file at least as long as its
`duration`, at the shot list's `file` path, ready for the manifest below.

### 6. Assemble, locked to the real voiceover

Build the beats manifest (each entry needs `start`, `end`, `duration`, and
now `file` pointing at the resolved clip from Step 5), then:

```bash
python3 scripts/assemble_from_beats.py \
  --beats beats_resolved.json \
  --narration voiceover.mp3 \
  --aspect 16:9 \
  --output final.mp4 \
  --music soundtrack.mp3 --music-volume 0.25   # omit --music if there isn't one
```

This normalizes and trims/loops each beat to its exact slot, concatenates
them in order, pads or trims the picture to match the narration's real
duration (the narration is the master clock — it never gets stretched or
time-compressed), mixes in the real voiceover, and — if a music bed was
given — ducks it under the narration with sidechain compression and
loudness-normalizes the mix.

### 7. QC before handing it over

- [ ] Every beat's visual actually matches what's being said at that moment
      (spot-check by scrubbing, not just reading the table)
- [ ] No beat runs longer than ~7s without a new visual element
- [ ] No two GENERATED beats look near-identical
- [ ] HYBRID overlays don't cover anything essential in the base footage
- [ ] Final duration matches the narration track exactly
- [ ] Pixabay clip credits noted (page URL + user) for anything used, same as
      pixabay-video-producer
- [ ] If the platform requires disclosing altered/synthetic content and any
      beat is GENERATED or HYBRID, flag that in the delivery notes

Deliver: `final.mp4`, `shot_list.md`, and a short note on which beats were
PIXABAY/GENERATED/HYBRID and why, so the decision is auditable, not just the
output.
