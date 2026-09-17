---
name: documentary-video-producer
description: Turns a real voiceover recording plus its transcript into a full narrated documentary-style video by alternating real, non-AI stock footage (sourced live from Pixabay and Pexels) with branded animated graphic cards (charts, stat reveals, comparisons, illustrated characters), all cut in soft crossfades and precisely synced to the actual spoken audio via word-level speech alignment (not estimated). Use this whenever the user hands over a voiceover audio file + script/transcript and wants a finished long-form explainer, essay, or documentary video built from it — especially when they want mostly real footage with occasional on-brand graphic moments, not an AI-generated visual for every line and not plain text on a black screen. Also trigger for Russian phrasing like "собери видео по озвучке", "сделай ролик из моей начитки и расшифровки", "смонтируй документалку по этому тексту". Distinct from pixabay-video-producer (that skill has no branded-graphics layer and uses word-count-estimated scene timing, not speech-aligned timing) — use pixabay-video-producer instead for a short reel/ad from a scene list with no voiceover-sync requirement.
---

# Documentary Video Producer

Builds a long-form narrated video (tested up to ~19 minutes) from a real
voiceover recording and its transcript: every cut is either real stock
footage (Pixabay + Pexels) or a branded animated graphic card, both timed
against the ACTUAL audio (via Whisper word-level alignment), never against
an estimate.

This is the accumulated, hard-won process from building a full 19-minute
documentary end to end — including two real production bugs (drifting
timing, and later a duration-truncation bug in the sync fix itself) that
required re-delivering several sections. Follow the verification steps
literally; they exist because skipping them shipped visibly-wrong video
more than once during development.

## Requirements

- `PIXABAY_API_KEY` and `PEXELS_API_KEY` (free at pixabay.com/api/docs and
  pexels.com/api). Ask the user for whichever is missing.
- `ffmpeg` / `ffprobe` on PATH.
- `pip install faster-whisper playwright` — and a Chromium binary Playwright
  can drive. If `playwright install` isn't available (common in sandboxed
  environments) or the pip package's expected browser build doesn't match
  what's pre-staged, find whatever Chromium binary IS present and pass it
  explicitly via `record_graphics.py --chrome <path>` rather than fighting
  version alignment.
- The voiceover as an audio file, and its transcript split into sentences
  (a JSON list of strings or the exact text with sentence-ending
  punctuation you can split on). If the user gives you a transcript
  without sentence boundaries, split it yourself with ordinary sentence
  punctuation — don't invent different wording.

## Workflow

### 1. Get the real timing first — before any beat planning

This is the step that matters most and the one it's tempting to skip.

```bash
python3 scripts/whisper_align.py --audio voiceover.mp3 --script sentences.json \
    --out sentence_spans.json --cache-words whisper_words_cache.json
```

Do **not** estimate sentence timing by dividing total duration proportionally
to word count. That approach drifted by as much as 13 seconds by the middle
of a 19-minute file in practice, because real speech has uneven pacing and
pauses between sentences that a word-count model doesn't account for — and
the resulting video looked increasingly out of sync with the narration the
further in you got, which is exactly the kind of defect a quick spot-check
of the first minute won't catch.

Use the `spans` field of the output (not the raw `start`/`end`), for every
downstream duration calculation. `spans` has already absorbed inter-sentence
gaps by extending each sentence to the start of the next one — see the
script's own docstring for why skipping this specifically causes a video
that's several seconds SHORTER than its narration, silently truncating the
end of the audio at mux time.

If any sentences report `"method": "fallback"` in the output, fix those
manually (re-check the transcript text matches what's actually said at that
point) before proceeding — don't build beats on an unaligned span.

### 2. Divide the transcript into sections

For anything more than a couple of minutes, work one section at a time
(sentence-index ranges, e.g. sentences 0-10, 11-55, ...) rather than
building the whole video in one pass — each section's beat plan, footage
search, graphics render, and assembly is independently checkpointable and
this is much easier to debug and redeliver piecemeal than one monolithic
build.

### 3. Plan beats per sentence, then per section

For each sentence in a section, decide real footage vs. a graphic, and how
many sub-cuts:

- **Pacing target**: a new shot roughly every 2-3 seconds. For a sentence
  under ~3.5s, one beat is fine. Longer sentences split into
  `round(duration / 2.6)` roughly-equal real-footage sub-cuts (see
  `build_beats.split_evenly`), each a genuinely different clip or a
  different offset into the same clip for continuous motion.
- **Graphic sync — the second hard lesson of this skill**: when a sentence
  gets a graphic beat, check whether the graphic's on-screen content
  (a stat, a quoted clause, a defined term) is what that WHOLE sentence is
  about. If so, make the graphic ONE beat spanning the entire sentence
  (`build_beats.whole_span`) — not an equal fraction of it. Splitting a
  sentence into "intro real footage, graphic, more real footage" when the
  graphic's number is what's being discussed for the whole sentence means
  the frame cuts away to unrelated b-roll while the narration is still
  mid-explanation of that exact number — a real, noticeable defect users
  will catch. If the graphic is a broader recap card summarizing ideas
  across several sentences instead, keep it at a brief, natural placement
  and let real footage carry the rest — don't stretch a recap card across
  everything it recaps, or it just sits there looking static for 15+
  seconds.
- **Real/graphics ratio**: default around 85% real footage / 15% graphics
  across a section, but this is a guideline, not a hard constraint — sync
  accuracy from the rule above wins when they conflict. A sentence-dense
  section (a string of one-stat-per-sentence financial figures, say) can
  legitimately land at 30-50% graphics; say so plainly when delivering
  rather than forcing cards to stay short just to protect the ratio.
- **Never repeat a stock clip anywhere in the whole video.** Maintain one
  running exclusion set (clip IDs already used, across ALL sections, both
  Pixabay and Pexels) and check every new pick against it before assigning.
  Reusing the same clip ID at two different, unrelated moments is a defect
  users notice immediately (a very recognizable ambulance-siren shot
  appearing twice was the specific complaint that established this rule).
  The one exception: consecutive sub-beats of the SAME sentence may reuse
  one clip at different seek offsets for continuous motion — that's a
  single shot playing longer, not a repeat.
- **Never plain text on a flat background.** Every graphic beat uses one of
  the templates in `scripts/templates.py` — each has an icon, a chart, a
  comparison layout, or an illustrated character, never bare typography.
- **Vary the graphic technique.** Don't use the same template twice in a
  row; spread the different templates (`stat_reveal`, `bar_chart`,
  `icon_flow`, `split_compare`, `stamp_reveal`, `timeline_year`,
  `line_chart`, `quiet_quote`, `kinetic_words`, `line_draw_stat`,
  `receipt_card`, `glow_number`, `character_scene`, `route_pair`) across a
  section so the same visual idea doesn't repeat. `kinetic_words` (words
  flying in sequentially), `glow_number` (pulsing rings behind a big
  figure), `receipt_card` (itemized breakdown), and `character_scene`
  (bobbing illustrated figure + floating prop icon) read as the most
  visually dynamic of the set — lean on them, not just `stat_reveal`,
  when a beat can support it.
- **Sensitive real events**: if the narration covers a real person's death,
  injury, or other tragedy, do NOT source stock footage that reenacts or
  dramatizes it. Use restrained factual graphics instead — a `quiet_quote`
  card for the key fact, `route_pair` for something like real distances
  involved, neutral establishing-shot stock footage (a building, a road, a
  map) rather than actors. This costs some of the section's real-footage
  ratio and that's the right trade.

### 4. Source real footage

Query both Pixabay and Pexels per concept (translate to concise, concrete
English visual nouns if the narration is in another language):

```bash
python3 ../pixabay-video-producer/scripts/pixabay_search.py --query "..." --per-page 10 --top 4
python3 scripts/pexels_search.py --query "..." --per-page 6 --top 4
```

Pixabay is stronger for generic lifestyle/nature shots; Pexels filled in
noticeably better for editorial/documentary-style or niche-topic footage in
practice. Query both when a concept is even slightly specific, and pick
whichever result is the better content match, not whichever source you
queried first. Filter every candidate ID against your running
already-used-clips set before selecting it, then download with
`../pixabay-video-producer/scripts/download_clip.py` (works for both
sources' CDN URLs — it already carries the browser User-Agent header both
Pixabay's CDN and Pexels' API need to avoid a Cloudflare/anti-bot 403).

### 5. Render the graphic beats

Write each GEN beat's HTML using the matching function from
`scripts/templates.py`, then render them all:

```bash
python3 scripts/record_graphics.py --jobs gen_jobs.json --out-dir graphics/ \
    --prefix s2 --chrome /path/to/chromium
```

### 6. Assemble the section

Build the `order.json` (`build_beats.flatten_to_order` output) and run:

```bash
python3 scripts/assemble_section.py order.json workdir/ section_video.mp4 0.35
```

**Before muxing, verify duration two ways, separately:**

```bash
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 section_video.mp4
# extract the matching narration slice using this section's span start/end from step 1
ffmpeg -y -i voiceover.mp3 -ss <span_start> -t <span_end_minus_start> -c:a libmp3lame -q:a 2 section_narration.mp3
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 section_narration.mp3
```

These two numbers should match to within ~0.1s. If the video is shorter,
you have a beat-duration bug upstream (almost always: beats were built from
raw `start`/`end` instead of gap-filled `spans`, or an order.json was
regenerated from corrected data but the OLD order.json was assembled by
mistake) — fix it and reassemble BEFORE muxing, not after. **Checking only
the final muxed file's duration is not sufficient** — `-shortest` at mux
time makes the final file match whichever of video/audio is shorter, which
looks like a successful, reasonable-length file even when several seconds
of narration were silently cut from the end. This exact mistake happened
once during this skill's own development (a stale, unregenerated `order.json`
got assembled after a timing fix, and the truncation wasn't caught until the
user reported it) — always do the pre-mux comparison above, every section,
even ones that "should" already be correct.

Then mux, compress for delivery, and send:

```bash
ffmpeg -y -i section_video.mp4 -i section_narration.mp3 -c:v copy -c:a aac -b:a 192k -shortest section_final.mp4
ffmpeg -y -i section_final.mp4 -vf scale=1280:720 -c:v libx264 -crf 30 -c:a aac -b:a 96k section_final_compressed.mp4
```

### 7. Deliver incrementally

Send each section as it's finished rather than batching the whole video —
long assemblies (a 100+ clip crossfade chain can take 30-60+ minutes of
wall-clock ffmpeg time) benefit from the user being able to react to a
section's style/pacing before you've built six more the same way. State any
ratio deviation or ethical-footage substitution plainly in the delivery
message so the user can weigh in rather than discovering it themselves.

## Common bugs already worked out (don't rediscover these)

- **cdn.pixabay.com and api.pexels.com both 403 the default `urllib`
  User-Agent** (Cloudflare/anti-bot). Fixed once, in `download_clip.py` and
  `pexels_search.py` — don't strip that header while adapting either script.
- **CSS `box-sizing`**: `templates.py`'s `BASE_CSS` sets
  `*{box-sizing:border-box;}`. Without it, any template combining
  `width:100%` with horizontal padding (`quiet_quote` in particular) renders
  a box wider than the 1920px stage and long text overflows off-frame
  instead of wrapping. Don't remove this rule.
- **Playwright/Chromium version mismatch**: see Requirements above — pin
  `--chrome` to whatever binary actually exists rather than trying to make
  `playwright install` succeed in a locked-down environment.
- **Crossfade shortens total duration**: see `assemble_section.py`'s
  docstring and step 6 above — this is the single most impactful thing to
  get right, and the most likely thing to silently regress if any beat list
  is regenerated without re-running assembly.
- **A rendered graphic clip shorter than the beat needs it to be triggers
  the "loop if short" fallback in `normalize()`**, which repeats the card's
  reveal animation from the start instead of holding its settled end state.
  Whenever you change a GEN beat's duration (including the sync fix in step
  3), re-render that graphic with `record_graphics.py` before reassembling
  — don't assume an old render is still long enough.
