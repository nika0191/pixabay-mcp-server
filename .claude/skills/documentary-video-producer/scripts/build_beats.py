"""Helpers for turning a sentence's aligned span into a list of on-screen
beats — real-footage sub-cuts and/or a branded-graphic hold.

Import this from your own per-section build script (see SKILL.md); it is a
small library, not a CLI, because the actual content decisions (which stock
clip or which graphic goes with which sentence) require human/model judgment
about the footage available and what the sentence means — that part cannot
be automated away.

Two ways to place a beat within a sentence's span, and when to use each:

1. `split_evenly(span, items)` — divide the sentence into N equal real-footage
   sub-cuts. Use for sentences that are pure narration/description with no
   single graphic-worthy idea: change the shot every ~2-3s to keep pace.

2. `whole_span(span)` — a SINGLE beat covering the entire sentence. Use this
   for the sentence containing a GEN (graphic) beat whenever the graphic's
   content states/restates that sentence's core idea — a stat, a comparison,
   a quoted clause, a defined term. If the graphic only occupies one of
   several equal sub-cuts, the narration keeps talking about that exact
   number for a few more seconds after the frame has already cut away to
   unrelated b-roll — a jarring, easy-to-notice desync. Extending the
   graphic to the sentence's full span (which can be 5-12+ seconds for a
   dense compound sentence) fixes it, at the cost of that beat no longer
   being a quick cut. That's an acceptable, deliberate trade: sync accuracy
   over pacing for that one beat.

   If only PART of a sentence is the graphic's subject (e.g. a scene-setting
   clause before the actual fact), use `partial_span(span, boundary_word,
   sentence_words)` — see below — to find where the relevant clause starts
   and split there instead of at the sentence midpoint.

Rule of thumb when deciding per sentence: does the graphic's on-screen text
directly quote or restate something spoken IN this exact sentence? If yes
and that content is the sentence's main point, use whole_span. If the
graphic is a broader recap/callback spanning ideas from multiple sentences,
DON'T stretch it across all of them (it goes stale, and long unbroken holds
looked criticized as "static" in review) — keep it at a natural, brief
placement instead and let real footage carry the elaboration.

Watch the real/graphics time ratio per section after applying whole_span:
data-dense sections (a run of sentences that are each one stat) can push
graphics well past the usual ~15% target. That's fine and expected — flag
it to the user rather than silently forcing cards to stay short and
desynced just to protect the ratio.
"""


def split_evenly(span, items):
    """span: (start, end). items: list of (kind, payload) pairs, e.g.
    [("PIX", ("clip_id", 0.0)), ("PIX", ("clip_id", 3.0))] or
    [("GEN", "template_key")].
    Returns list of (kind, payload, start, end)."""
    start, end = span
    n = len(items)
    sub = (end - start) / n
    return [(kind, payload, start + i * sub, start + (i + 1) * sub) for i, (kind, payload) in enumerate(items)]


def whole_span(span, kind, payload):
    """One beat covering the entire span — see module docstring for when."""
    start, end = span
    return [(kind, payload, start, end)]


def partial_span(span, split_fraction, before, after):
    """Split a sentence's span at a given fraction (0-1) rather than evenly
    across N items — use when you know roughly where the relevant clause
    starts (e.g. from reading the sentence) but don't have exact word-level
    timestamps for that inner boundary. `before`/`after` are each either a
    single (kind, payload) tuple or a list of them (which will themselves be
    split evenly within their portion)."""
    start, end = span
    mid = start + (end - start) * split_fraction

    def expand(part, a, b):
        if isinstance(part, tuple):
            part = [part]
        return split_evenly((a, b), part)

    return expand(before, start, mid) + expand(after, mid, end)


def word_boundary_time(whisper_words, sentence_word_start_idx, target_word_offset):
    """If you have per-word whisper timestamps (from whisper_align.py's cached
    word list) and know the transcript-word index where a sentence starts,
    this returns the timestamp of the word at
    sentence_word_start_idx + target_word_offset — use it to split a sentence
    at an EXACT clause boundary instead of guessing a fraction. Requires you
    to have already built the transcript_words -> whisper index alignment
    (see whisper_align.align's t2w construction) and pass whisper_words
    indexed the same way partial_span's caller does; this is intentionally
    left as a thin lookup rather than baked into partial_span, since most
    beats in practice were fine with a fraction guess plus a quick sanity
    check against the rendered video."""
    return whisper_words[sentence_word_start_idx + target_word_offset]["start"]


def flatten_to_order(beats, clip_path_fn, html_write_fn, gfx_path_fn):
    """Turn a flat list of (kind, payload, start, end) beats — the
    concatenation of split_evenly/whole_span/partial_span calls across all
    sentences in a section, IN NARRATION ORDER — into the `order` list
    assemble_section.py expects, plus the list of GEN html/duration jobs to
    render with record_graphics.py.

    clip_path_fn(clip_id) -> absolute path to the downloaded clip file.
    html_write_fn(beat_index, payload) -> writes the template HTML for this
      GEN beat to disk and returns that path (payload is whatever key/args
      you used to identify which template+content to render).
    gfx_path_fn(beat_index) -> the path the rendered graphic clip will live
      at once record_graphics.py has run (order.json references this path
      before it exists, same as a normal pre-assembly manifest).

    Returns (order, gen_jobs). order is a list of [path, duration, offset]
    triples (offset is 0.0 for GEN beats, the requested seek offset for PIX).
    gen_jobs is a list of (beat_index, html_path, duration) for
    record_graphics.py.
    """
    order = []
    gen_jobs = []
    for idx, (kind, payload, start, end) in enumerate(beats):
        dur = round(end - start, 3)
        if kind == "PIX":
            clip_id, offset = payload
            order.append([clip_path_fn(clip_id), dur, offset])
        else:
            html_path = html_write_fn(idx, payload)
            gfx_path = gfx_path_fn(idx)
            gen_jobs.append((idx, html_path, dur))
            order.append([gfx_path, dur, 0.0])
    return order, gen_jobs
