"""Mechanical post-generation checks for session scripts.

Small local models can fall into degenerate repetition on long generations:
the same sentence recycled with tiny variations, grammar decaying, until the
token budget runs out. A guided session deliberately repeats *anchor phrases*
("let go", "once more") — that's cadence, and it must survive. What must NOT
survive is whole-sentence near-duplication run after run: the broken-record
defect a listener notices immediately.

The detector works at sentence granularity. A sentence is "a repeat" when its
word-shingle similarity to ANY earlier sentence crosses SIM_THRESHOLD. A RUN of
MIN_RUN consecutive repeats marks the start of degeneration; everything from
the start of that run is trimmed. Trimming the tail of a wind-down is safe —
the scripts are designed to trail off — and the caller can choose to
regenerate instead when too much would be lost.
"""

from __future__ import annotations

import re

# Similarity at-or-above this = the same sentence in a slightly different coat.
SIM_THRESHOLD = 0.75
# This many consecutive repeated sentences = degeneration, not cadence.
MIN_RUN = 3
# Ignore tiny fragments ("Good.", "Once more.") — legitimate cadence beats.
MIN_WORDS = 6

# split after end punctuation followed by whitespace OR a bracket annotation
# (transcribed exemplars carry "[2.0]" pause marks straight after the period)
_SENT_SPLIT = re.compile(r"(?<=[.!?…])(?:\s+|(?=\[))")
_NORM = re.compile(r"[^a-z0-9\s]")


def _sentences(text: str) -> list[str]:
    return [s for s in _SENT_SPLIT.split(text.strip()) if s.strip()]


def _words(sentence: str) -> set[str]:
    return set(_NORM.sub(" ", sentence.lower()).split())


def _similarity(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def find_degeneration_start(text: str) -> int | None:
    """Return the character offset where degenerate repetition begins, or None.

    The offset points at the first sentence of the first run of MIN_RUN
    consecutive sentences that each near-duplicate some earlier sentence.
    """
    sents = _sentences(text)
    if len(sents) < MIN_RUN + 1:
        return None
    word_sets = [_words(s) for s in sents]
    repeated = []
    for i, ws in enumerate(word_sets):
        if len(ws) < MIN_WORDS:
            repeated.append(False)
            continue
        repeated.append(any(
            _similarity(ws, word_sets[j]) >= SIM_THRESHOLD
            for j in range(i)
            if len(word_sets[j]) >= MIN_WORDS
        ))
    run = 0
    for i, rep in enumerate(repeated):
        run = run + 1 if rep else 0
        if run == MIN_RUN:
            first = i - MIN_RUN + 1
            # Walk back to the SEED of the loop: the run's members are repeats
            # OF some earlier sentence — if that original sits immediately
            # before the run, it's the start of the degeneration (it already
            # carries the decayed register), so trim from there instead.
            run_sets = [word_sets[k] for k in range(first, i + 1)]
            j = first
            while j > 0 and len(word_sets[j - 1]) >= MIN_WORDS and any(
                    _similarity(word_sets[j - 1], rs) >= SIM_THRESHOLD
                    for rs in run_sets):
                j -= 1
            # find the char offset of that sentence's start
            offset = 0
            for s in sents[:j]:
                offset = text.find(s, offset) + len(s)
            return text.find(sents[j], offset if j else 0)
    return None


# Beat230: the imag-intimacy back-half floor (flagged beat227/228/229 as the
# largest standing architectural gap) never trips find_degeneration_start
# above — measured on the real defect script (queue_0904_1805_battery11,
# "ceiling fan"/"unhurried"/"three blades" reworded ~10 times across the last
# 14 sentences), the highest sentence-pair similarity was 0.64, never 3
# CONSECUTIVE hits at SIM_THRESHOLD=0.75. This is a looser failure: the model
# keeps re-describing the same handful of images in freshly paraphrased
# sentences that are never adjacent and never that close individually, but
# saturate the back of the script. CYCLE_* below is deliberately a separate,
# lower-confidence bar from the degeneration check, not a replacement for it.
CYCLE_SIM_THRESHOLD = 0.30
CYCLE_MIN_WORDS = 6
CYCLE_MIN_RUN = 8       # trailing run must span at least this many sentences
CYCLE_MIN_DENSITY = 0.5  # and at least half of them must each repeat something earlier
# beat230 FP sweep against all 745 500+ char A_gold.jsonl scripts at the
# thresholds above: 16/745 (2.15%) flagged, several cutting 80-100% of a
# legitimate short repetitive-by-design meditation script (breath-count/
# body-scan styles legitimately repeat core vocabulary throughout a SHORT
# script — that's real cadence, not the imag-intimacy back-HALF failure this
# is meant to catch). Requiring the cut point to preserve at least this
# fraction of the script cuts the FP set to 2/745 (0.27%, both far milder —
# 69-71% survival, not 0-20%) while still catching the real defect (natural
# survival fraction there was 0.51). NOT wired into generator.py yet: the 2
# residual borderline flags want a human/live-model read before this is safe
# to auto-trim in the live pipeline — see review-queue.md beat230.
CYCLE_MIN_SURVIVE_FRAC = 0.45


def find_cycling_start(text: str) -> int | None:
    """Return the char offset where loose, paraphrased thematic cycling takes
    over the tail of a script, or None. Sibling of find_degeneration_start for
    the looser, non-adjacent, non-near-verbatim repeat class described above.
    Finds the EARLIEST (= longest) trailing run of at least CYCLE_MIN_RUN
    sentences where at least CYCLE_MIN_DENSITY of them each moderately
    resemble some earlier sentence in the script."""
    sents = _sentences(text)
    word_sets = [_words(s) for s in sents]
    eligible = [len(ws) >= CYCLE_MIN_WORDS for ws in word_sets]
    is_hit = [False] * len(sents)
    for i, ws in enumerate(word_sets):
        if not eligible[i]:
            continue
        is_hit[i] = any(
            _similarity(ws, word_sets[j]) >= CYCLE_SIM_THRESHOLD
            for j in range(i) if eligible[j]
        )
    n = len(sents)
    if n < CYCLE_MIN_RUN:
        return None
    best_start = None
    for start in range(0, n - CYCLE_MIN_RUN + 1):
        window = range(start, n)
        elig_count = sum(1 for k in window if eligible[k])
        if elig_count < CYCLE_MIN_RUN:
            continue
        hit_count = sum(1 for k in window if is_hit[k])
        if hit_count / elig_count >= CYCLE_MIN_DENSITY:
            best_start = start
            break  # earliest qualifying start = longest trailing run
    if best_start is None:
        return None
    offset = 0
    for s in sents[:best_start]:
        offset = text.find(s, offset) + len(s)
    char_offset = text.find(sents[best_start], offset if best_start else 0)
    if char_offset / max(len(text), 1) < CYCLE_MIN_SURVIVE_FRAC:
        return None  # would cut too much of the script — see CYCLE_MIN_SURVIVE_FRAC note
    return char_offset


def trim_cycling_tail(text: str) -> tuple[str, bool]:
    """Trim the script at the point loose paraphrased cycling takes over.
    Returns (script, trimmed?). NOT currently called from generator.py — see
    the CYCLE_MIN_SURVIVE_FRAC note above for why this is staged, not live."""
    start = find_cycling_start(text)
    if start is None:
        return text, False
    return text[:start].rstrip(), True


def trim_degenerate_tail(text: str) -> tuple[str, bool]:
    """Trim the script at the point degeneration begins.

    Returns (script, trimmed?). The cut end is softened: trailing partial
    cadence is kept up to the last clean sentence boundary.
    """
    start = find_degeneration_start(text)
    if start is None:
        return text, False
    return text[:start].rstrip(), True


def trim_truncated_tail(text: str) -> tuple[str, bool]:
    """Trim to the last complete sentence if the output was token-limit truncated.

    When the model hits max_tokens mid-sentence the raw output ends without
    a sentence terminator (e.g. "...that doesn").  The subsequent postprocess
    passes preserve the fragment — phrase-repeat repair only drops whole lines
    and short-phrase repair only drops full sentences.  This pass detects the
    symptom (final non-whitespace char is not .!?"…) and retracts to the last
    complete sentence boundary before continuing postprocessing.

    Returns (trimmed_text, was_truncated).
    """
    stripped = text.rstrip()
    if not stripped or stripped[-1] in '.!?"…':
        return text, False
    last = max(stripped.rfind('.'), stripped.rfind('!'), stripped.rfind('?'))
    if last < 0:
        return text, False
    return stripped[:last + 1], True


# --- run-on collapse: the OTHER decay mode -----------------------------------
# Nothing repeats, but grammar disintegrates into an unpunctuated word-stream
# ("vast empty stretch Half Moon Bay's beach offers during this quietest time
# year where usually tourists flock instead remain few..."). Calibration against
# A_gold (2026-06-10) showed spoken-register gold legitimately runs 90+ word
# sentences with near-zero commas, so only the EXTREME tail is safely separable:
# the real catastrophe is 125w at 0.016 punctuation/word; the longest genuine
# gold sentence is 92w. Thresholds sit in the gap — this net catches only
# unambiguous salad, by design. Subtler decay is the fine-tune's job, not a
# regex's.
RUNON_WORDS = 110
RUNON_PUNCT_RATIO = 0.03

_PUNCT = re.compile(r"[,;:—–-]")


def _is_collapsed(sentence: str) -> bool:
    words = len(sentence.split())
    if words < RUNON_WORDS:
        return False
    punct = len(_PUNCT.findall(sentence))
    return (punct / words) < RUNON_PUNCT_RATIO


def _lines(text: str) -> list[str]:
    """Excision units: scripts mix '\\n\\n' paragraphs and single-'\\n' breaks;
    a line is the finest unit that can be dropped without orphaning syntax."""
    return text.split("\n")


def find_collapsed_paragraphs(text: str) -> list[int]:
    """Indices (line-granular) of units containing a run-on grammar collapse."""
    out = []
    for i, line in enumerate(_lines(text)):
        if any(_is_collapsed(s) for s in _sentences(line)):
            out.append(i)
    return out


def drop_collapsed_paragraphs(text: str) -> tuple[str, int]:
    """Remove collapsed lines. The moments in these long bodies are
    semi-independent, so excising one reads as a pause, not a hole — while a
    collapsed run-on read aloud shatters the session. Granularity is the LINE,
    not the blank-line paragraph: scripts that break with single newlines would
    otherwise lose good sentences along with the salad. Returns (text, n_dropped)."""
    lines = _lines(text)
    bad = set(find_collapsed_paragraphs(text))
    if not bad:
        return text, 0
    kept = [ln for i, ln in enumerate(lines) if i not in bad]
    out = "\n".join(kept)
    out = re.sub(r"\n{3,}", "\n\n", out).strip()
    return out, len(bad)


# --- foreign-language slip detection -----------------------------------------
# Qwen2.5 is a Chinese-English model and can slip into Chinese mid-script,
# especially in long settling generations. Any paragraph with >5% CJK characters
# (U+3000–U+9FFF, U+AC00–U+D7FF, U+F900–U+FAFF) is model drift, not content.
_CJK_RANGE = re.compile(
    "[　-鿿ꀀ-꓿가-퟿豈-﫿\U00020000-\U0002a6df]"
)


def _cjk_ratio(text: str) -> float:
    if not text:
        return 0.0
    return len(_CJK_RANGE.findall(text)) / len(text)


def drop_foreign_paragraphs(text: str) -> tuple[str, int]:
    """Drop lines that have slipped into CJK / non-Latin script.
    Returns (cleaned_text, n_dropped)."""
    lines = _lines(text)
    bad = {i for i, ln in enumerate(lines) if _cjk_ratio(ln) > 0.05 and ln.strip()}
    if not bad:
        return text, 0
    kept = [ln for i, ln in enumerate(lines) if i not in bad]
    out = "\n".join(kept)
    out = re.sub(r"\n{3,}", "\n\n", out).strip()
    return out, len(bad)


# beat203 (battery11_0550, imag-mri): a CJK leak spliced directly onto an
# English word with no whitespace or line break -- "...resonating from deep
# within this room需要两个部分，一部分从用户分类信息中获取..." -- survives
# drop_foreign_paragraphs() untouched because that check works at LINE
# granularity (>5% CJK density over the whole line); a short CJK splice inside
# one long English paragraph never crosses that density threshold. This is a
# TTS-critical defect (the CJK text would be read aloud verbatim). Scans at
# SENTENCE granularity instead: any sentence containing 2+ CJK characters
# anywhere in it is dropped whole, English lead-in included -- a model that
# switches language mid-sentence has broken that sentence structurally, not
# just inserted a foreign word, so partial extraction isn't attempted.
def strip_inline_foreign_runs(text: str) -> tuple[str, int]:
    """Drop sentences containing an inline CJK leak that drop_foreign_paragraphs
    misses because the leak doesn't dominate its whole line. Returns
    (cleaned_text, n_dropped)."""
    sentences = re.split(r"(?<=[.!?。！？])\s*", text.strip())
    kept = []
    dropped = 0
    for s in sentences:
        if len(_CJK_RANGE.findall(s)) >= 2:
            dropped += 1
        else:
            kept.append(s)
    out = " ".join(s for s in kept if s.strip())
    return out, dropped


# --- non-adjacent verbatim repetition: the THIRD decay mode ------------------
# Two separate checks:
#   NGRAM=12: a 12-word verbatim shingle recurring in 2+ different paragraphs.
#             Catches long recycled passages (grief-pet case).
#   SHORT_NGRAM=5: a 5-word verbatim shingle occurring 3+ times in the whole
#                  script. Catches short dialog/sensory phrase loops that NGRAM=12
#                  misses (imag-intimacy "Do I get one too?" ×4 = 5 words).
#                  Threshold of 3 (not 2) avoids false-positives on cadence repeats
#                  ("in and out", "the air around you") which can legitimately
#                  appear twice in a long script.
NGRAM = 12
SHORT_NGRAM = 5
SHORT_REPEAT_THRESHOLD = 3


def find_phrase_repeats(text: str) -> list[tuple[int, int]]:
    """(first_para_idx, repeat_para_idx) pairs with a shared 12-word shingle."""
    paras = [p for p in re.split(r"\n+", text) if p.strip()]
    seen: dict[tuple, int] = {}
    out = []
    for i, para in enumerate(paras):
        words = _NORM.sub(" ", para.lower()).split()
        flagged = False
        for j in range(len(words) - NGRAM + 1):
            sh = tuple(words[j:j + NGRAM])
            if sh in seen and seen[sh] != i and not flagged:
                out.append((seen[sh], i))
                flagged = True  # one report per paragraph
            elif sh not in seen:
                seen[sh] = i
    return out


def phrase_repeat_count(text: str) -> int:
    """Count of repeated-shingle paragraph pairs. Heavily-recycled scripts
    (the grief-pet case: 18 pairs) are beyond surgical excision — this is a
    REPORT for the generation log and a CULL gate for the corpus, not an
    editing tool. In-product surgery can come later if data shows isolated
    single repeats are common."""
    return len(find_phrase_repeats(text))


def find_short_phrase_repeats(text: str) -> list[str]:
    """5-word shingles appearing SHORT_REPEAT_THRESHOLD+ times anywhere in text.
    Returns the list of offending shingle strings for logging."""
    words = _NORM.sub(" ", text.lower()).split()
    counts: dict[tuple, int] = {}
    for j in range(len(words) - SHORT_NGRAM + 1):
        sh = tuple(words[j:j + SHORT_NGRAM])
        counts[sh] = counts.get(sh, 0) + 1
    return [" ".join(sh) for sh, cnt in counts.items() if cnt >= SHORT_REPEAT_THRESHOLD]


def repair_short_phrase_repeats(text: str) -> tuple[str, int]:
    """Remove sentences containing the 3rd+ occurrence of any offending 5-gram.
    Splits on sentence boundaries; keeps the first 2 occurrences of each phrase,
    drops sentences carrying the 3rd+. Returns (repaired_text, sentences_dropped)."""
    offending = find_short_phrase_repeats(text)
    if not offending:
        return text, 0

    bad_shingles = {tuple(ph.split()) for ph in offending}

    sentences = re.split(r"(?<=[\.\!\?])\s+", text)
    kept_counts: dict[tuple, int] = {}
    kept = []
    dropped = 0
    for sent in sentences:
        sent_words = _NORM.sub(" ", sent.lower()).split()
        sent_shingles = {
            tuple(sent_words[j:j + SHORT_NGRAM])
            for j in range(max(0, len(sent_words) - SHORT_NGRAM + 1))
        }
        bad_in_sent = sent_shingles & bad_shingles
        if bad_in_sent:
            max_kept = max(kept_counts.get(sh, 0) for sh in bad_in_sent)
            if max_kept >= SHORT_REPEAT_THRESHOLD - 1:
                dropped += 1
                continue
            for sh in bad_in_sent:
                kept_counts[sh] = kept_counts.get(sh, 0) + 1
        kept.append(sent)

    return " ".join(kept), dropped


def drop_adjacent_duplicates(text: str) -> tuple[str, int]:
    """Remove the second of any two adjacent near-verbatim sentences.

    Adjacent duplication (the model restating what it just said in slightly
    different words) is always a slip, never cadence. Cadence uses SHORT phrases
    ("breathe in", "let go"); adjacent whole-sentence restatements fail on first
    listen. Only fires when BOTH sentences are ADJ_MIN_WORDS+ words so short
    cadence beats like "Breathe in. Breathe out." are preserved.

    Uses a lower similarity threshold (ADJ_SIM) than the degeneration detector
    because adjacent sentences need less word overlap to be obvious duplicates.
    """
    ADJ_SIM = 0.55
    ADJ_MIN_WORDS = 10
    sentences = re.split(r"(?<=[\.\!\?])\s+", text.strip())
    kept = []
    dropped = 0
    prev_ws: set[str] = set()
    for sent in sentences:
        ws = _words(sent)
        if (len(ws) >= ADJ_MIN_WORDS and len(prev_ws) >= ADJ_MIN_WORDS
                and _similarity(ws, prev_ws) >= ADJ_SIM):
            dropped += 1
        else:
            kept.append(sent)
            prev_ws = ws
    return " ".join(kept), dropped


def drop_tail_duplicates(text: str) -> tuple[str, int]:
    """Remove near-verbatim duplicate sentences in the final 6 sentences of a script.

    Closing degeneration: model restates the same thought with minor word-order
    variation in the final lines ('Carry her warmth with you now. You carry her
    warmth with you now.'). drop_adjacent_duplicates misses these because its
    ADJ_MIN_WORDS=10 guard is too high for short closing sentences. This pass
    targets only the tail with a lower minimum (5 words) but a stricter similarity
    floor (0.80) to avoid catching intentional short parallel cadence elsewhere.
    """
    _ADJ_SIM_TAIL = 0.80
    _ADJ_MIN_WORDS_TAIL = 5
    _TAIL_WINDOW = 6
    sentences = re.split(r"(?<=[\.\!\?])\s+", text.strip())
    if len(sentences) <= 2:
        return text, 0
    tail_start = max(0, len(sentences) - _TAIL_WINDOW)
    head = sentences[:tail_start]
    tail = sentences[tail_start:]
    kept: list[str] = []
    dropped = 0
    prev_ws: set[str] = set()
    for sent in tail:
        ws = _words(sent)
        if (len(ws) >= _ADJ_MIN_WORDS_TAIL and len(prev_ws) >= _ADJ_MIN_WORDS_TAIL
                and _similarity(ws, prev_ws) >= _ADJ_SIM_TAIL):
            dropped += 1
        else:
            kept.append(sent)
            prev_ws = ws
    return " ".join(head + kept), dropped


def repair_phrase_repeats(text: str, max_rounds: int = 4) -> tuple[str, int]:
    """Drop the LINES carrying the later occurrence of a repeated shingle.
    For TRAINING-DATA harvesting (a slightly shorter clean script teaches more
    good than a recycled phrase teaches harm) — not wired into the live product.
    Iterates because dropping lines can reveal new adjacencies. Returns
    (text, lines_dropped)."""
    dropped = 0
    for _ in range(max_rounds):
        lines = text.split("\n")
        nonempty = [k for k, ln in enumerate(lines) if ln.strip()]
        # map shingle -> first nonempty-line index
        seen: dict[tuple, int] = {}
        kill: set[int] = set()
        for pos, k in enumerate(nonempty):
            words = _NORM.sub(" ", lines[k].lower()).split()
            hit = False
            for j in range(len(words) - NGRAM + 1):
                sh = tuple(words[j:j + NGRAM])
                if sh in seen and seen[sh] != k:
                    hit = True
                    break
                seen.setdefault(sh, k)
            if hit:
                kill.add(k)
        if not kill:
            break
        dropped += len(kill)
        text = "\n".join(ln for k, ln in enumerate(lines) if k not in kill)
        text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text, dropped


# --- imag-intimacy scenario-specific detectors (beat233) --------------------
# imag-intimacy / imag-intimacy-finds-your-across have carried zero dedicated
# postcheck coverage for 6+ beats (216-232) despite being the source of the
# most severe uncaught defects in battery11 — furniture inconsistency and a
# presence-continuity break, both confirmed live in queue_0905_1447. These are
# QC-time detectors (report only, not auto-fixers) — the failure mode needs a
# regen or a prompt-engineering pass, not a safe mechanical rewrite.

_FURNITURE_HEDGE_RE = re.compile(
    r'\b(?:chair|couch|sofa)\s+or\s+(?:chair|couch|sofa)\b', re.I)
_FURNITURE_TRANSITION_RE = re.compile(
    r'\b(?:get|got|gets|getting)\s+up\b|\bstands?\s+up\b|\bstanding\s+up\b|'
    r'\bmove[sd]?\s+(?:to|toward)\b|\bwalk(?:s|ed|ing)?\s+(?:to|toward|over)\b|'
    r'\b(?:sits?|sat|sitting)\s+down\s+(?:on|onto)\s+(?:the|her|his|your)?\s*'
    r'(?:couch|sofa)\b|'
    r'\b(?:eases?|eased|easing|settl(?:es|ed|ing)|lean(?:s|ed|ing))\s+'
    r'(?:down\s+)?(?:onto|on)\s+(?:the|her|his|your)?\s*(?:couch|sofa)\b',
    re.I)


def check_furniture_consistency(text: str) -> str | None:
    """Detect chair<->couch/sofa seating inconsistency within one script (beat232
    finding: imag-intimacy-finds-your-across opened 'this chair... the armrests'
    then later stated 'sitting close on her couch' as established fact, with no
    transition — an internal contradiction about where the scene is happening).
    A deliberate hedge ('chair or couch') is NOT a defect — it's intentionally
    ambiguous and appears in the clean base imag-intimacy script. A transition
    verb (gets up, moves to, sits down onto the couch) also clears it — getting
    up from a chair and later sitting on a couch elsewhere is a normal scene
    change, not a contradiction. Returns a reason string if inconsistent, else
    None."""
    stripped = _FURNITURE_HEDGE_RE.sub('', text)
    has_chair = bool(re.search(r'\bchair\b|\barmrests?\b', stripped, re.I))
    has_couch = bool(re.search(r'\bcouch\b|\bsofa\b', stripped, re.I))
    if not (has_chair and has_couch):
        return None
    if _FURNITURE_TRANSITION_RE.search(stripped):
        return None
    return "chair and couch/sofa both asserted as the seat with no transition between them"


_PRESENCE_BREAK_RE = re.compile(
    r'\b(?:she|he|they)\s+(?:is|are|was|were)\s+not\s+physically\s+present\b',
    re.I)


def check_presence_continuity(text: str) -> str | None:
    """Detect a direct presence contradiction (beat232 finding: imag-intimacy-
    finds-your-across said 'you feel her presence somewhere near even though she
    is not physically present' in a scene the user asked to inhabit as a vivid,
    physically-together evening — the companion figure being declared absent
    breaks the continuity of a scene built entirely on her being there). Narrow
    literal-phrase check per this project's discipline for a first-sighting
    defect; wants a 2nd sighting before generalizing beyond this exact shape.
    Returns a reason string with context if found, else None."""
    m = _PRESENCE_BREAK_RE.search(text)
    if not m:
        return None
    ctx = text[max(0, m.start() - 40):m.end() + 10].strip()
    return f"explicit not-physically-present contradiction: '...{ctx}...'"


def check_return_to_room_closing(text: str, tail_words: int = 150) -> bool:
    """True if the script's final `tail_words` contain a return-to-room / eyes-
    open cue — the required settle -> imagining -> return shape. False = the
    scenario ends with no closing beat at all (flagged since beat167, reconfirmed
    beat232: 4/9 scenarios in one battery11 run ended with no eyes-open/return
    cue). An 'open your eyes' moment INSIDE the imagined scene (not at the real
    close) does not count — only checks the tail, since that's the actual ending
    the listener is left with."""
    tail = " ".join(text.split()[-tail_words:])
    return bool(re.search(
        r"\bopen(?:ing)?\s+your\s+eyes\b|"
        # beat237 (queue_0906_0646_battery11_imagination_bank.log honest read):
        # false FAIL on "The eyes can open softly whenever they feel ready" —
        # a modal verb ("can"/"will"/etc.) between "eyes" and "open" was not
        # covered by the old adjacent-word pattern. 0 hits risk-checked in
        # A_gold.jsonl for the modal group.
        r"\beyes?\s+(?:can|will|may|might|could|should)?\s*(?:flutter(?:ing)?\s+)?open\b|"
        r"\breturn(?:ing)?\s+to\s+(?:the\s+)?room\b|"
        r"\bcome\s+back\s+to\s+(?:the\s+)?room\b|"
        r"\bwhen\s+you'?re?\s+ready\s+to\s+open\b|"
        r"\bbring(?:ing)?\s+yourself\s+back\b|"
        # beat234 (queue_0905_2326_battery11_imagination_bank.log honest read):
        # false FAIL on a genuinely clean closing — "Invite your eyes to open
        # whenever they feel ready" — "eyes ... open" reversed word order with
        # "to" between them, which neither existing eyes/open pattern covers
        # (one requires "open your eyes", the other requires eyes immediately
        # before open with no "to"). 0 hits risk-checked in A_gold.jsonl.
        r"\beyes\s+to\s+open\b",
        tail, re.I))


def degeneration_report(text: str) -> dict:
    """Diagnostic summary for QC harnesses and logs."""
    start = find_degeneration_start(text)
    words = len(text.split())
    if start is None:
        return {"degenerate": False, "words": words}
    kept = len(text[:start].split())
    return {"degenerate": True, "words": words, "clean_words": kept,
            "lost_fraction": round(1 - kept / max(words, 1), 2)}


# --- inline ellipsis-break cleaner -------------------------------------------
# Settling path (and occasionally immersion): model writes "……" (3-6 literal
# dots or unicode ellipsis chars) as inline pause placeholders. These look
# unprofessional in rendered text and confuse TTS. Replace them with a proper
# paragraph break (blank line).
_ELLIPSIS_INLINE = re.compile(r"[ \t]*(?:\.{3,}|…{2,}|\.\.\.|…\.{0,5}|\.{0,5}…)[ \t]*")


def clean_ellipsis_breaks(text: str) -> tuple[str, int]:
    """Replace multi-dot inline ellipsis markers with paragraph breaks.

    Returns (cleaned_text, n_replaced).
    """
    cleaned, count = _ELLIPSIS_INLINE.subn("\n\n", text)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
    return cleaned, count


# --- narrator first-person possessive filter ---------------------------------
# BODY_PROMPT bans "my boy", "my dog", "my [animal/character]" but the small
# local model ignores these instructions reliably. Drop sentences that carry
# narrator-possessive patterns so they never reach the listener.
# Patterns: "my [animal]", "Here we go again", "we are here [together]"
_NARRATOR_POSS = re.compile(
    r"\bmy\s+(boy|dog|cat|pet|horse|bird|fish|rabbit|puppy|kitten|pup)\b"
    r"|\bHere\s+we\s+go\b"
    r"|\bwe\s+are\s+here\b"
    # Grief-pet / body-script first-person narrator leaks (beat35):
    # Model claims narrator "I" actions that belong to the second-person listener.
    r"|\bI\s+(?:reach|keep|feel|sit|take|hold|said|step|walk|stand|watch|start|call|move)\b"
    r"|\bI\s*'\s*m\s+\w+ing\b"          # "I'm [verb]ing" mid-script
    r"|\bI\s*'\s*ve\s+\w+\b"            # "I've [past]" mid-script
    r"|\bby\s+my\s+side\b"              # "by my side" narrator possessive
    r"|\bfor\s+me\s+(?:just|here|now|there|too|but)\b"  # "for me just watching"
    r"|\bunder\s+me\b"                  # should be "under you"
    r"|\bthrough\s+me\b"               # should be "through you"
    r"|\bwith\s+me\b"                  # should be "with you"
    r"|\bwe\s+(?:started|are\s+now|were\s+both|had\s+been|come\s+back)\b"  # narrator "we" (specific forms)
    r"|\bwe\s+(?:reach|reached|walk|walked|came|come|arrive|arrived|ran|run|go|went|were\s+here|need|sat|sit|stand|stood|move|moved|used\s+to|begin|began|open|opened|return|returned|end|ended|close|closed|start|started|leave|left|lift|lifted|drift|drifted|wake|woke|fade|faded)\b"  # narrator "we" + motion/state verbs
    # beat170 (2026-08-23): eagle-body 'we' narrator inclusions — "we took off", "we approach",
    # "we've moved" etc. escaped because (a) verbs missing from list, (b) "we've" contraction form
    # not covered. Found in battery11_0823_0926 imag-eagle-wildlife-plural (13 'we' instances).
    r"|\bwe\s+(?:took|approach|approached|adjust|adjusted|fly|flew|soar|soared|bank|banked|glide|glided|gain|gained|climb|climbed|descend|descended|ascend|ascended|travel|traveled|travelled|continue|continued|turn|turned|circle|circled|pass|passed|cross|crossed|dive|dove|dived|swing|swung|rise|rose|drop|dropped|head|headed|carry|carried)\b"  # active-body motion verbs missed by prior list
    r"|\bwe(?:[‘’]ve)\s+(?:moved|adjusted|traveled|travelled|soared|flown|gained|climbed|banked|circled|crossed|ascended|descended|continued|turned|passed|glided|approached|drifted|risen|gone)\b"  # "we’ve [past-participle]" narrator contraction form
    # beat171 (2026-08-23): stative "we are"/"we’re" escape (found: "where we are up here",
    # "like we’re arriving") — plain \bwe\s+are\b was not in the verb list; "we’re" contraction
    # form had no pattern at all. Found in 09:26 eagle-wildlife-plural honest read.
    r"|\bwe[\x27’’]re\b|\bwe\s+are\b"  # "we’re" (ASCII \x27 + curly) and "we are"
    r"|\bmy\s+(?:hand|hands|breath|side|step|voice|foot|body|mind)\b"   # narrator body-part possessives
    # beat171 (2026-08-23): narrator "me" preposition gaps — "beneath me"/"below me" not caught.
    # Line 433-435 already has "under me"/"through me"/"with me". Extending to full spatial set.
    # Found in imag-eagle-companion-bird-he 09:26 honest read ("far beneath me", "mountains below me").
    r"|\b(?:beneath|below|around|near|beside|behind)\s+me\b"  # narrator "me" spatial prepositions
    r"|\bboth\s+of\s+us\b"             # "both of us" narrator collective
    r"|\bfor\s+us\b"                   # "for us" narrator collective
    # beat171 (2026-08-23): narrator "us" forms beyond "both of us"/"for us" — "distance separates us",
    # "between us" etc. Found in imag-eagle-companion-bird-he 09:26 honest read.
    r"|\b(?:separates?|between|around|with|near|beside|behind|above|below|beneath|joins?|unites?)\s+us\b"  # narrator "us" spatial/relational
    # Grief-pet dog-POV leak (beat70): model puts listener in animal's body and refers
    # to the human as "your handler" / "your owner" — immediate perspective failure.
    r"|\byour\s+(?:handler|owner|master)\b"
    r"|\bmy\s+(?:handler|owner|master)\b"
    # beat178 (2026-08-24): narrator claims to be a speaking presence that paused —
    # "exactly how it was when I stopped talking" (battery11_0824_1434 imag-embodiment-
    # eagle honest read). The existing "I + verb" list (reach/keep/feel/sit/take/hold/
    # said/step/walk/stand/watch/start/call/move) doesn't cover narration-of-narration
    # verbs. Direct violation of instrument-not-companion: the narrator has no body and
    # does not "stop talking" as an event inside the scene.
    r"|\bI\s+(?:stop|stopped|talk|talked|talking|speak|spoke|speaking|narrate|narrated|narrating)\b"
    # beat184 (2026-08-25): battery11_0825_1359 imag-eagle-golden-eagle-wildlife
    # honest read — real narrator first-person leaks survived despite the
    # existing "I + verb" allowlist: "all there was left for me after I rose up
    # here", "while I still have this one ahead of me", "catch our eye when we
    # look", "takes me back to something I don't know about yet", "I don't know
    # if we'll ever see it again". Root cause: the "I + verb" list only covered
    # a fixed set of physical-action verbs; "rose/rise", "have", "know"/"don't
    # know" were never added, and the "we + verb" list had no "look" entry or
    # a phrase-level catch for "catch our eye"/"takes me back".
    r"|\bI\s+(?:rose|rise|risen|rising|have|had|know|knew|don'?t\s+know|didn'?t\s+know)\b"
    # beat194 (imag-eagle-companion-bird-he, queue_0827_1628_battery11_imagination_bank.log,
    # honest read): "the same spot where I started my flight up into a sky..." — "I started"
    # escaped because only the bare present-tense "start" was in the verb list (line ~428),
    # not the past-tense "started"; \b after the alternation requires "start" to be a
    # complete word, so "started" never matched.
    r"|\bI\s+started\b"
    r"|\bwe\s+(?:look|looked)\b"
    r"|\bcatch\s+our\s+eye\b"
    r"|\btakes?\s+me\s+back\b"
    r"|\bahead\s+of\s+me\b"
    # beat196 (battery11_2152, imag-eagle-wildlife-plural honest read): "nothing
    # else is stopping us from going wherever we choose next" — "we choose" is a
    # narrator-plural decision-verb not in any prior "we + verb" list (the
    # existing lists cover motion/state verbs but not decision verbs). Same
    # sentence's "beneath us" (a different clause) was also missed — the
    # spatial-"us" list above had "below" but not "beneath" (inconsistent with
    # the "me" version of the same list, which already had "beneath"); fixed
    # separately in that list.
    r"|\bwe\s+(?:choose|chose)\b"
    # beat204 (battery11_1139, imag-eagle-golden-eagle-wildlife honest read):
    # "The quality of your breath remains steady as before when I mentioned an
    # end was near." — "I mentioned" is a narrator-speech-act leak of the same
    # family as beat178's "I stopped talking"/"I talked" list (line ~494), but
    # "mention"/"mentioned" was never added to that verb set.
    r"|\bI\s+(?:mention|mentioned|mentioning)\b"
    # beat204 (same log, same script): "...they carry you slightly further down
    # toward where we will be next." — narrator-plural future-tense "we will be"
    # is a new tense form; the existing "we + verb" lists cover past/present
    # motion and decision verbs but no future-modal "will be" construction.
    r"|\bwe\s+will\s+be\b"
    # beat210 (battery11_1145 imag-eagle-golden-eagle-wildlife honest read):
    # "...for hours ahead when we keep flying" and "...for hours ahead when we
    # stay aloft and keep going up above here" — "stay" and "keep" are new
    # narrator-plural verbs (stative/continuative) not in any prior "we + verb"
    # list, which only covered motion/decision/future-tense forms.
    r"|\bwe\s+(?:stay|stayed|keep|kept)\b"
    # beat212 (queue_0830_1800 battery11 honest read, background-agent audit):
    # imag-mri "You hold something from this space with you as we bring it back"
    # — "bring"/"brings"/"brought" was never in the "we + verb" motion-verb list.
    # imag-eagle-golden-eagle-wildlife "The horizon opens out as we get closer to
    # it" — "get"/"gets"/"got" likewise missing. Both are the same standing gap
    # (narrator-plural verb list incomplete), new verb forms, not new mechanisms.
    r"|\bwe\s+(?:bring|brings|brought|get|gets|got)\b"
    # imag-intimacy "...reaching us here slowly as if coming to someone who was
    # expected after all" — "us" narrator-plural object form after "reaching";
    # the existing spatial/relational "us" list (separates/between/around/with/
    # near/beside/behind/above/below/beneath/joins/unites) never covered a verb
    # of motion terminating "onto us" like "reach(ing/es)".
    r"|\breach(?:es|ing|ed)?\s+us\b"
    # beat214 (queue_0831_1835_battery11_imagination_bank.log, background-agent
    # honest read): imag-eagle-golden-eagle-wildlife — the densest narrator-drift
    # instance found yet (7 leaks in one ~1400-word script), including a first-
    # person COPULA shape ("I am supposed to be", "I am up here", "I'm up here")
    # no prior "I + verb" list entry covers (those are all action verbs, never
    # "am"/"I'm" as a copula). Scoped to the two exact live phrasings rather than
    # a blanket "I am"/"I'm" ban — a corpus check of A_gold.jsonl found 220 "I am"
    # and 434 "I'm" hits, almost certainly legitimate quoted-dialogue uses inside
    # scenes that involve another speaker, so a bare copula ban would be a severe
    # false-positive risk. Same beat, same script: "we aren't just anyone" — the
    # existing "we're"/"we are" pattern (line ~473) doesn't cover the negated
    # contraction "aren't" (different token, "are" + "n't" fused); 0 hits for
    # "we aren't" in A_gold.jsonl, confirmed safe before adding.
    r"|\bI\s+am\s+(?:supposed\s+to\s+be|up\s+here)\b"
    r"|\bI['’]m\s+up\s+here\b"
    r"|\bwe\s+aren['’]t\b"
    # beat215 (queue_0901_1640_battery11_imagination_bank.log honest read,
    # imag-eagle-wildlife-plural — the densest narrator-drift instance since
    # beat214, 6/6 eagle postchecks PASS but 8+ leaks survived): root-caused
    # why "we've gained" and "we've been up here" escaped the beat170 "we've
    # [past-participle]" list (line ~469) despite "gained" already being in
    # it — that pattern's contraction group is `(?:[‘’]ve)`, curly quotes
    # only, missing the ASCII apostrophe (\x27) the beat171 "we're" pattern
    # (line ~473) already carries. Model output here used the ASCII form.
    # Also added "been" to that verb list — "we've been" was never covered by
    # any verb form (only past-participles of motion/decision verbs).
    r"|\bwe[\x27’]ve\s+been\b"
    # "if I did land again among the trees or rocks far below" — modal "did"
    # + verb construction; the "I + verb" allowlist only ever covered bare
    # present/past forms, never "I did [verb]". Scoped to the literal found
    # verb ("land") rather than a blanket "I did X" ban: A_gold.jsonl has a
    # legitimate quoted-dialogue "I did what you told me" instance, the same
    # dialogue-quote risk this file already navigates carefully elsewhere.
    r"|\bI\s+did\s+land\b"
    # "how I'd never expect it down below where everything falls toward
    # ground" — "I'd" (I would/I had) + verb is a first-person narrator
    # intent/history claim with zero legitimate instances anywhere in
    # A_gold.jsonl (checked directly, both apostrophe forms) — safe to ban
    # the contraction outright rather than scoping to just this one verb.
    r"|\bI['’]d\s+\w+"
    # "anything we'd hold down there" — sibling of the "I'd" ban above, but
    # "we'd" DOES have legitimate uses in A_gold.jsonl (quoted dialogue: "We'd
    # like to offer you the position", "who thought we'd be spies") — scoped
    # narrowly to the literal found verb rather than banning the contraction.
    r"|\bwe['’]d\s+hold\b"
    # "take us from here in flight" — verb "take(s)" terminating in the
    # narrator-plural object "us", a motion-onto-us shape not covered by the
    # existing spatial/relational "us" list (beat212's "reach(ing/es) us" is
    # the nearest sibling). 0 hits in A_gold.jsonl.
    r"|\btakes?\s+us\b"
    # "our own wings", "our ascent began" — bare possessive "our" is common
    # in a different, older gold-corpus content style (collective-address
    # loving-kindness scripts: "we think of our good friends") and can't be
    # banned broadly without destroying that legitimate content class; scoped
    # to the two literal found noun phrases only, both 0 hits in A_gold.jsonl.
    r"|\bour\s+own\s+wings\b"
    r"|\bour\s+ascent\b"
    # beat228 (queue_0905_0112_battery11_imagination_bank.log honest read,
    # imag-eagle-golden-eagle-wildlife): "how quickly it disappeared as soon
    # as we changed course or altitude" — "changed" was missing from the
    # we+verb motion list above (which has turn/turned but not change/changed).
    r"|\bwe\s+changed\b"
    # beat232 (queue_0905_1447_battery11_imagination_bank.log honest read,
    # imag-calm-settle): "We'll let our words get slower still, trailing off
    # finally until they stop completely" and (same script, second instance)
    # "Let us let our words get slower now and far apart" — a first-person-
    # plural narrator voice announcing itself winding down, the same
    # instrument-not-companion violation class as beat178's "when I stopped
    # talking" but a new surface form ("let" + "our words" as object, not a
    # "we + verb" subject construction the existing patterns require). 0 hits
    # for "our words" anywhere in A_gold.jsonl, confirmed before adding.
    r"|\blet\s+our\s+words\b"
    # beat232 (same log, imag-mri): three new narrator "us"/"our"/"ours"
    # collective-pronoun leaks not covered by the existing spatial/relational
    # "us" list or the literal "our own wings"/"our ascent" entries: "in time
    # with whatever drum pattern is now driving us both forward", "knowing
    # it's also ours to go past", "knowing they are our too" (the model's own
    # garbled attempt at "ours too"). MRI has no dedicated postcheck at all
    # for narrator-pronoun bleed (only chair/tube/drums), so these survived
    # uncaught. 0 hits for all three exact phrases in A_gold.jsonl, confirmed
    # before adding.
    r"|\bdriving\s+us\b"
    r"|\bours\s+to\s+go\b"
    r"|\bare\s+our\s+too\b"
    # beat234 (queue_0905_2326_battery11_imagination_bank.log honest read,
    # imag-eagle-wildlife-plural — a FALSE PASS, all 8 mechanical checks green):
    # "This is where I would rest if it were necessary for me but as flight has
    # become my body and mind that stay unburdened of any such thing." — a full
    # first-person narrator claim, more severe than the usual pronoun-slip shape
    # (this is the narrator asserting it HAS a body it would rest). "I would
    # rest" scoped to the literal verb rather than a blanket "I would X" ban:
    # A_gold.jsonl has one ambiguous "I would imagine" hit that looks like a
    # legacy corpus artifact (bracketed timestamp prefix), not clearly safe to
    # generalize from. "my body"/"my mind" (0 hits) and "for me but" (0 hits)
    # fixed separately in the existing my-body-part and for-me lists above.
    r"|\bI\s+would\s+rest\b",
    re.IGNORECASE,
)


# beat228 (queue_0905_0112_battery11_imagination_bank.log honest read,
# imag-eagle-wildlife-plural): the model broke character to narrate its OWN
# generation process — "The final paragraph after that would have been
# necessary in order to reach 2200 words as requested, even though I left
# off at my last given moment and can't invent a new one there without
# repeating or stalling." No existing narrator-leak pattern covers this: it
# isn't a second-person/first-person pronoun slip, it's the model literally
# discussing its word-count target and its own inability to continue — a
# severe instrument-not-companion violation (the "instrument" should never
# be visible as a generation process at all). Scoped to phrases specific to
# this meta-commentary shape; none of them have any plausible legitimate use
# inside a guided-imagination script.
_META_GENERATION_LEAK = re.compile(
    r"\bwords?\s+as\s+requested\b"
    r"|\bwithout\s+repeating\s+or\s+stalling\b"
    r"|\bcan['’]t\s+invent\s+a\s+new\b"
    r"|\bat\s+my\s+last\s+given\s+moment\b"
    r"|\bin\s+order\s+to\s+reach\s+\d+\s+words\b",
    re.IGNORECASE,
)


def clean_meta_generation_leaks(text: str) -> tuple[str, int]:
    """Remove sentences where the model narrates its own generation process
    (word-count targets, "as requested", running out of things to invent).
    Returns (cleaned_text, n_sentences_dropped)."""
    sentences = re.split(r"(?<=[\.\!\?])\s+", text.strip())
    kept = []
    dropped = 0
    for s in sentences:
        if _META_GENERATION_LEAK.search(s):
            dropped += 1
        else:
            kept.append(s)
    return " ".join(kept), dropped


def clean_narrator_possessives(text: str) -> tuple[str, int]:
    """Remove sentences containing narrator first-person possessive slips.

    Returns (cleaned_text, n_sentences_dropped).
    """
    sentences = re.split(r"(?<=[\.\!\?])\s+", text.strip())
    kept = []
    dropped = 0
    for s in sentences:
        if _NARRATOR_POSS.search(s):
            dropped += 1
        else:
            kept.append(s)
    return " ".join(kept), dropped


# Words after which "hers"/"yours" is a legitimate standalone possessive pronoun
# and should NOT be replaced with the attributive "her"/"your".
_PRONOUN_SKIP = frozenset([
    "is", "are", "was", "were", "have", "had", "been",
    "will", "would", "can", "could", "shall", "should",
    "may", "might", "must", "do", "did", "does",
    "and", "or", "but", "nor", "to",
])


# "from she", "with she" etc — subject pronoun used as object of preposition.
# Caught in n376 intimate scripts (battery11 0728 imag-intimacy).
_SHE_AS_OBJECT = re.compile(
    r'\b(from|with|to|by|for|about|toward|towards|of|near|beside)\s+(she)\b',
    re.IGNORECASE,
)


def fix_object_pronouns(text: str) -> tuple[str, int]:
    """Replace 'PREPOSITION she' → 'PREPOSITION her'.

    The model occasionally uses the subject pronoun 'she' as the object of a
    preposition ('from she', 'with she') — the opposite of the her-as-subject
    error handled by fix_subject_pronouns. Caught on n376 imag-intimacy (0728).
    """
    fixed = 0

    def _replace(m: "re.Match") -> str:
        nonlocal fixed
        fixed += 1
        return f"{m.group(1)} her"

    result = _SHE_AS_OBJECT.sub(_replace, text)
    return result, fixed


_HER_SUBJECT_VERBS = re.compile(
    # Present tense (3rd-person singular -s forms)
    r"\bher\s+(enters|finds|reaches|searches|stands|turns|speaks|catches|"
    r"looks|laces|passes|breaks|stops|tells|makes|lets|comes|come|moves|sits|meets|"
    r"holds|takes|runs|walks|says|goes|sees|knows|wants|needs|leaves|starts|"
    r"becomes|keeps|brings|gets|"
    # Present tense additions (beat86: found in deposition script — 'her asks', 'her has')
    r"asks|has|gives|seems|appears|does|follows|reads|checks|watches|faces|"
    # beat210 (battery11_1145 imag-intimacy honest read): "her come closer" (bare
    # base-form "come" alongside the already-covered "comes") and "before her
    # settles back down over chest" ("settles" was missing even though the
    # sibling "sets" was already covered).
    r"sets|settles|puts|uses|calls|feels|shows|opens|closes|pulls|pushes|holds|places|"
    # beat215 (battery11_0901_1640 imag-intimacy honest read): "where her
    # arrived before coming into view fully" — "arrive"/"arrives" was never
    # in either tense list despite being one of the most common motion verbs
    # in this corpus. 0 hits for "her arrive(d/s)" in A_gold.jsonl.
    r"arrive|arrives|"
    # Past tense forms (most common)
    r"reached|found|stood|turned|met|held|told|said|came|saw|kept|went|"
    r"spoke|broke|ran|took|got|left|made|started|moved|sat|walked|"
    r"entered|searched|passed|stopped|caught|looked|laced|"
    # Past tense additions (beat86)
    r"asked|had|gave|seemed|appeared|did|followed|watched|faced|"
    r"used|called|felt|showed|opened|closed|pulled|pushed|placed|arrived|"
    # beat189 (battery11_0826_1712 imag-intimacy): "where her hadn't been" —
    # subject "her" before a contracted auxiliary verb, a form the finite-verb
    # list above didn't cover (only bare "had", not "hadn't").
    r"hadn't|wasn't|weren't|didn't|doesn't|hasn't|haven't|isn't|aren't|"
    r"wouldn't|couldn't|shouldn't|won't|can't)\b",
    re.IGNORECASE,
)


def fix_subject_pronouns(text: str) -> tuple[str, int]:
    """Replace 'her [verb]' → 'she [verb]' when 'her' is incorrectly used as subject.

    The fine-tuned model sometimes generates 'her enters your line of vision',
    'her finds its way', 'until her reached out' — using the object case 'her'
    as a subject pronoun. Only fires on unambiguous verb forms (3rd-person
    singular present or simple past) to avoid touching legitimate 'her [noun]'
    possessive uses.
    """
    fixed = 0

    def _replace_her_subject(m: "re.Match") -> str:
        nonlocal fixed
        fixed += 1
        verb = m.group(1)
        prefix = m.group(0)[: m.group(0).lower().index("her")]
        return f"{prefix}she {verb}"

    result = _HER_SUBJECT_VERBS.sub(_replace_her_subject, text)
    return result, fixed


# beat215 (battery11_0901_1640 imag-intimacy honest read): "hers" — the
# standalone possessive pronoun, correct only after a copula ("it's hers")
# — used as a SUBJECT pronoun instead of "she". Two confirmed shapes in one
# script: (1) direct copula subject, "hers is still turned fully toward
# you" / "when hers is about to tell something your has not yet heard";
# (2) coordinated subject with "you", "hers or you arrived late" (verb
# agreement follows the nearer noun "you", so only the pronoun itself needs
# fixing, not a verb). Distinct from _HER_SUBJECT_VERBS above (which fixes
# "her" + finite verb) — this is a different incorrect pronoun ("hers" vs
# "her") in a different grammatical slot. 0 hits for either shape in
# A_gold.jsonl.
_HERS_SUBJECT_RE = re.compile(
    r"\bhers\b(?=\s+is\b)"
    r"|\bhers\b(?=\s+(?:or|and)\s+you\b)",
    re.IGNORECASE,
)


def fix_hers_subject_pronoun(text: str) -> tuple[str, int]:
    """Replace 'hers' -> 'she' when used as a subject pronoun ('hers is
    still turned toward you' -> 'she is still turned toward you'; 'hers or
    you arrived late' -> 'she or you arrived late').
    """
    fixed = 0

    def _replace(m: "re.Match") -> str:
        nonlocal fixed
        fixed += 1
        return "She" if m.group(0)[0].isupper() else "she"

    result = _HERS_SUBJECT_RE.sub(_replace, text)
    return result, fixed


# beat196 (battery11_2152 honest read, imag-intimacy): "your came later" —
# "your" used as a SUBJECT pronoun (should be "you") immediately before a finite
# verb, a 5th distinct grammatical shape of the your/yours escape family (prior
# shapes: copula+your [fix_predicative_your], preposition+your object
# [fix_intimacy_object_pronoun_escapes], your-before-article, your+contraction
# [fix_your_contraction]). None of those fire here because "your" is neither
# preceded by a copula/preposition nor followed by "alone"/an article — it is
# the grammatical subject of the clause. Mirrors fix_subject_pronouns' her→she
# pattern but for your→you; scoped to finite verb forms that can never
# legitimately follow the determiner "your" (no such noun spellings exist), so
# no risk of touching real attributive uses like "your hand"/"your voice".
_YOUR_SUBJECT_VERBS = re.compile(
    r"\byour\s+(came|arrived|went|left|stayed|waited|returned|walked|ran|stood|"
    r"sat|moved|woke|slept|cried|laughed|smiled|nodded|paused|hesitated|"
    # beat215 (battery11_0901_1640 imag-intimacy honest read): "your has not
    # yet heard" — bare "has" was never in this list (only the negated
    # "hasn't"). 0 hits for "your has" in A_gold.jsonl.
    r"has|"
    r"wasn't|weren't|hadn't|didn't|doesn't|hasn't|haven't|isn't|aren't|"
    r"wouldn't|couldn't|shouldn't|won't|can't)\b",
    re.IGNORECASE,
)


# beat215: a blind "your [verb]" -> "you [verb]" swap is grammatically wrong
# for the handful of verbs that conjugate by person — "your has" naively
# becomes "you has" (should be "you have"), and the same latent mismatch
# already existed for "hasn't"/"doesn't"/"isn't" before this beat (all
# person-invariant elsewhere in the list: past tense and n't-contractions
# other than these three never change between "you" and "she"). Discovered
# while adding bare "has" to _YOUR_SUBJECT_VERBS above; fixed here rather
# than propagated, since the conjugation mapping is small and unambiguous.
_YOUR_SUBJECT_CONJUGATION = {
    "has": "have", "hasn't": "haven't", "hasn’t": "haven’t",
    "doesn't": "don't", "doesn’t": "don’t",
    "isn't": "aren't", "isn’t": "aren’t",
}


def fix_your_subject_pronoun(text: str) -> tuple[str, int]:
    """Replace 'your [verb]' → 'you [verb]' when 'your' is incorrectly used as
    the subject of a finite verb ('your came later' → 'you came later'),
    conjugating the small set of verbs that require it ('your has' → 'you
    have', not the ungrammatical 'you has').

    Sibling of fix_subject_pronouns (her→she); same defect class, your→you.
    """
    fixed = 0

    def _replace(m: "re.Match") -> str:
        nonlocal fixed
        fixed += 1
        verb = m.group(1)
        verb = _YOUR_SUBJECT_CONJUGATION.get(verb.lower(), verb)
        return f"you {verb}"

    result = _YOUR_SUBJECT_VERBS.sub(_replace, text)
    return result, fixed


# beat197 (battery11_0828_0818 honest read, 3 scenarios — imag-mri, imag-eagle-
# wildlife-plural, imag-eagle-companion-bird-he): "toward you left hip",
# "on you left wing tip", "with you left wing" — the mirror-image error of
# _YOUR_SUBJECT_VERBS above: bare "you" used as an ATTRIBUTIVE determiner
# (should be "your") immediately before "left"/"right" + a body-part noun.
# Scoped to left/right + a curated body-part noun list — "left"/"right"
# directly followed by a body-part noun is never the verb "to leave"/"to
# right" (you don't "leave a hip" or "right a wing"), so this is safe by
# construction, the same discipline as _YOUR_SUBJECT_VERBS' finite-verb list.
_YOU_BEFORE_BODYPART_RE = re.compile(
    r"\byou\s+(left|right)\s+(hip|wing(?:\s+tip)?|arm|leg|foot|feet|hand|"
    r"shoulder|knee|side|ear|eye|wrist|ankle|elbow)\b",
    re.IGNORECASE,
)


def fix_you_before_bodypart(text: str) -> tuple[str, int]:
    """Replace 'you left/right BODYPART' -> 'your left/right BODYPART' when
    'you' is incorrectly used as the attributive determiner ('you left hip'
    -> 'your left hip')."""
    fixed = 0

    def _replace(m: "re.Match") -> str:
        nonlocal fixed
        fixed += 1
        return f"your {m.group(1)} {m.group(2)}"

    result = _YOU_BEFORE_BODYPART_RE.sub(_replace, text)
    return result, fixed


# beat198 (queue_0827_2152_battery11_imagination_bank.log honest read, imag-
# intimacy): "not when they're alone in their own apartment" — the model
# drifts from the product's strict 2nd-person address (user=you, companion=
# she/her) into 3rd-person-plural "they/their" when describing the user and
# her companion as a unit. This is a violation of the "instrument, not
# companion" 2nd-person architecture (CLAUDE.md), not a style nit — escalated
# across beat185/196/197 as "confirmed, needs a dedicated design pass" but
# left unattempted each time because a blanket "they"/"their" ban would wrongly
# strip legitimate 3rd-person-plural references elsewhere (background wildlife
# pairs, body parts like "her eyes... they widen"). "they're/they are alone" is
# narrow and safe: nothing except a human pair is ever described as "alone" in
# this product's scripts (checked A_gold.jsonl + all _candidates gold files —
# zero instances), so once a sentence contains that trigger, any "their"
# elsewhere in THAT SAME SENTENCE is also the same drift and safe to correct
# alongside it — scoping the "their" fix to the trigger sentence only (not
# document-wide) keeps other legitimate "their" uses elsewhere in the script
# (e.g. eagle "their nests") untouched.
_THIRD_PERSON_ALONE_RE = re.compile(r"\bthey(?:'re|\s+are)\s+alone\b", re.IGNORECASE)
_THEIR_RE = re.compile(r"\btheir\b", re.IGNORECASE)


def fix_third_person_alone_drift(text: str) -> tuple[str, int]:
    """Fix 'they're/they are alone' -> 'you're alone', and correct any
    'their' elsewhere in the same sentence to 'your' (scoped to the
    triggering sentence only, so other sentences' legitimate 'their' uses
    are untouched).
    """
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    fixed = 0
    out = []
    for s in sentences:
        m = _THIRD_PERSON_ALONE_RE.search(s)
        if m:
            replacement = "You're alone" if m.group(0)[0].isupper() else "you're alone"
            new_s = _THIRD_PERSON_ALONE_RE.sub(replacement, s)
            new_s = _THEIR_RE.sub("your", new_s)
            if new_s != s:
                fixed += 1
            s = new_s
        out.append(s)
    return " ".join(out), fixed


def fix_possessive_pronouns(text: str) -> tuple[str, int]:
    """Replace 'hers/yours/ours NOUN' → 'her/your/our NOUN'.

    The fine-tuned model sometimes generates 'hers own side', 'hers eyes',
    'yours apartment', 'ours bodies tonight' — using the standalone possessive
    pronoun as an attributive adjective. This is a training artifact caught on
    n242/n243/n376 intimate scenes. The fix is inline substitution (not
    sentence-drop) so no content is lost.
    beat155: extended to cover 'ours NOUN' → 'our NOUN' (beat155 observed
    'ours bodies tonight' in imag-intimacy battery11_1003 run).
    """
    fixed = 0

    def _replace_hers(m: "re.Match") -> str:
        nonlocal fixed
        word = m.group(1)
        if word.lower() in _PRONOUN_SKIP:
            return m.group(0)
        fixed += 1
        return f"her {word}"

    def _replace_yours(m: "re.Match") -> str:
        nonlocal fixed
        word = m.group(1)
        if word.lower() in _PRONOUN_SKIP:
            return m.group(0)
        fixed += 1
        return f"your {word}"

    def _replace_ours(m: "re.Match") -> str:
        nonlocal fixed
        word = m.group(1)
        if word.lower() in _PRONOUN_SKIP:
            return m.group(0)
        fixed += 1
        return f"our {word}"

    text = re.sub(r"\bhers\s+(\w+)", _replace_hers, text, flags=re.IGNORECASE)
    text = re.sub(r"\byours\s+(\w+)", _replace_yours, text, flags=re.IGNORECASE)
    text = re.sub(r"\bours\s+(\w+)", _replace_ours, text, flags=re.IGNORECASE)
    return text, fixed


# beat189 (battery11_0826_1712 imag-intimacy): "Look out over what used to be
# yours and her alone before everything changed." — the mirror-image error of
# fix_possessive_pronouns above: "her" used as a coordinated STANDALONE
# possessive pronoun (needs "hers") instead of an attributive determiner. Scoped
# to "and/or her" immediately followed by a non-noun word or clause boundary —
# the same discipline as _YOUR_NONNOUN_FOLLOW — so ordinary "and her hand"/
# "or her voice" (her + noun) is never touched.
_HER_STANDALONE_RE = re.compile(
    r"\b(and|or)\s+her(?=\s*(?:[.,!?;]|—|$|\s+(?:alone|now|still|again|too|only|"
    r"instead)\b))",
    re.IGNORECASE,
)


def fix_standalone_her(text: str) -> tuple[str, int]:
    """Replace '(and|or) her' -> '(and|or) hers' when 'her' has no noun to
    attach to (coordinated standalone possessive, e.g. 'yours and hers alone')."""
    fixed = 0

    def _replace(m: "re.Match") -> str:
        nonlocal fixed
        fixed += 1
        return f"{m.group(1)} hers"

    result = _HER_STANDALONE_RE.sub(_replace, text)
    return result, fixed


# "your STATIVE" → "you're STATIVE": model confuses possessive with contraction.
# Only fires for words that cannot be possessed (cannot say "your alone space" etc.).
# beat192: excludes "than your STATIVE" (negative lookbehind) — that's a
# comparison ("no other audience than your alone"), not a contraction context;
# routed instead through _THAN_YOUR_STATIVE_RE below to "than yours STATIVE",
# since firing this rule there produced broken "than you're alone" output
# (battery11_0826_2346 imag-eagle-companion-bird-he, "[v6] 1 your→you're
# contraction error(s) fixed" — the fixer itself introduced the defect).
_YOUR_CONTRACTION_RE = re.compile(
    r"(?<!than\s)\byour\s+(alone|here|there|gone|done|lost|found|safe|free|ready|okay|ok|fine)\b"
    r"(?!\s+(?:time|space|room|day|moment|self|work|years|hours|life|world|journey|path))",
    re.IGNORECASE,
)

# beat192 (battery11_0826_2346 imag-eagle-companion-bird-he honest read): "with
# no other audience than your alone right here and now" got wrongly fixed by
# _YOUR_CONTRACTION_RE into "than you're alone" (ungrammatical — "than you are
# alone" isn't the intended meaning). "than your STATIVE" is a standalone-
# possessive context like _PREDICATIVE_YOUR_RE's copula pattern, not a
# contraction one — the correct target is "than yours STATIVE".
_THAN_YOUR_STATIVE_RE = re.compile(
    r"\bthan\s+your\s+(alone|here|there|gone|done|lost|found|safe|free|ready|okay|ok|fine)\b",
    re.IGNORECASE,
)


def fix_your_contraction(text: str) -> tuple[str, int]:
    """Replace 'your STATIVE' → 'you\'re STATIVE' where the model uses the
    possessive in place of the contraction 'you are'.

    Example: 'this moment your alone' → 'this moment you\'re alone'.
    """
    result, n = _YOUR_CONTRACTION_RE.subn(
        lambda m: f"you're {m.group(1)}", text
    )
    return result, n


# After fix_your_contraction converts 'your alone' → 'you're alone', a copula
# immediately before creates broken grammar: 'a rhythm that is you're alone'
# (= 'a rhythm that is you are alone').  The correct form is 'yours alone'.
# Pattern: copula/contraction directly before 'you're alone' (no intervening word).
_COPULA_YOURE_ALONE_RE = re.compile(
    r"\b(is|was|are|am|were|'s)\s+you're\s+(alone)\b",
    re.IGNORECASE,
)


def fix_copula_youre_alone(text: str) -> tuple[str, int]:
    """'that is you\'re alone' / 'that\'s you\'re alone' → 'that is yours alone'.

    Runs after fix_your_contraction to catch broken copula + you're constructions
    that read as 'X is you are alone' — grammatically invalid.
    """
    result, n = _COPULA_YOURE_ALONE_RE.subn(
        lambda m: f"{m.group(1)} yours {m.group(2)}", text
    )
    return result, n


# beat178: the reverse of fix_possessive_pronouns' "yours NOUN" -> "your NOUN" fix.
# Found twice in one battery11 run (imag-eagle-wildlife-plural, imag-eagle-companion-
# bird-he 0824_1434): the model uses attributive "your" where the standalone
# predicative "yours" belongs — "The sky is your for as far as it goes", "it was
# your on its way to being gone", "is your entirely — transferred from...". Only
# fires when "your" is followed by a closing punctuation mark or one of a small set
# of adverbs/prepositions that never introduce a noun phrase, so legitimate
# attributive uses ("is your wing", "was your turn") are untouched.
_PREDICATIVE_YOUR_RE = re.compile(
    # beat212 (queue_0830_1800 battery11 honest read): imag-intimacy "This room
    # stays your for longer than anyone knows" — "stays" (linking-verb sense of
    # "remains") was never in the copula list; same predicative-possessive gap
    # as is/was/are/were, just a different linking verb.
    r"\b(is|was|are|were|be|been|become|becomes|became|stays)\s+((?:\w+ly\s+)?)your\b"
    r"(?=\s*(?:[.,!?;]|—|$|\s+(?:entirely|completely|now|here|still|again|"
    # beat188 (battery11_0826_0920 imag-eagle-companion-bird-he): "territory
    # marked in this part of sky that is your as much as any other here
    # today" — "as" was missing from the follow-set. Safe the same way
    # "whenever"/"between" were: "as" always opens a comparison/subordinate
    # clause ("as much as", "as if"), never introduces a possessable noun
    # directly after "your".
    # beat198 (battery11_1317 imag-intimacy honest read): "a reminder held after
    # she has left again to do whatever is her today" — "today" wasn't in the
    # follow-set (this instance is actually the her/hers sibling, see
    # _PREDICATIVE_HER_RE below, but "today" is added here too since the same
    # gap would apply to "is your today" and "today" can never introduce a
    # possessable noun after "your" either — safe by the same reasoning as
    # "whenever"/"between").
    # beat209 (battery11_0541 imag-eagle-wildlife-plural honest read): "respect for
    # the territory that's your above all else down below" — "above" wasn't in the
    # follow-set, same non-noun-introducing reasoning as "on"/"at"/"in": "above"
    # always opens a comparison/prepositional clause ("above all else", "above the
    # rest"), never introduces a possessable noun directly after "your".
    # beat210 (battery11_1145 imag-mri honest read): "...their presence with you
    # here right now will be your when Friday arrives" (should be "yours when
    # Friday arrives") — "when" always opens a subordinate clause, never
    # introduces a possessable noun directly after "your", same non-noun-
    # introducing reasoning as "whenever"/"today"/"above".
    # Same log also had "...has become something entirely your already before
    # even trying anything different" (should be "yours already before..."),
    # but this one is a DIFFERENT bug, not a missing follow-word: the copula
    # here is "has become", followed by "something" then the adverb "entirely"
    # then "your" — this regex's copula-alternation only allows ONE optional
    # adverb between the copula and "your", so "become something entirely your"
    # never matched the copula group at all regardless of the follow-set.
    # Deliberately NOT adding "already" to the follow-set to patch it: "already"
    # (unlike "when"/"today"/"whenever") commonly modifies a following adjective
    # before a real noun ("your already-packed bag", "your already broken
    # promise") — adding it as a bare follow-word produces a live false
    # positive there. Left unfixed pending a version of this regex that also
    # tolerates an intervening "something"/noun before the adverb; logged in
    # review-queue rather than shipping the unsafe version.
    r"too|for|on|at|in|to|by|with|from|between|whenever|as|today|above|when)\b)"
    r")",
    re.IGNORECASE,
)

# beat209: same instance above used the contraction "that's your" rather than the
# spelled-out copula "that is your" — _PREDICATIVE_YOUR_RE's copula alternation
# (is/was/are/were/be/been/become/becomes/became) never matches "'s", so this exact
# transcript string didn't match _PREDICATIVE_YOUR_RE even after adding "above."
# Narrow, separate regex for the 's-contraction case (its own function rather than
# folding into _PREDICATIVE_YOUR_RE's group numbering, which the _replace callback
# above depends on staying fixed) — same follow-set/reasoning, applies only when a
# word character immediately precedes 's (so it can't match a standalone "'s" token).
_PREDICATIVE_YOUR_CONTRACTION_RE = re.compile(
    r"(?<=\w)'s\s+your\b"
    r"(?=\s*(?:[.,!?;]|—|$|\s+(?:entirely|completely|now|here|still|again|"
    r"too|for|on|at|in|to|by|with|from|between|whenever|as|today|above|when)\b)"
    r")",
    re.IGNORECASE,
)


def fix_predicative_your_contraction(text: str) -> tuple[str, int]:
    """"'s your [end-of-clause]" -> "'s yours [end-of-clause]" (contraction sibling
    of fix_predicative_your — same shape, "is"/"was"/etc. contracted to 's)."""
    fixed = 0

    def _replace(m: "re.Match") -> str:
        nonlocal fixed
        fixed += 1
        return m.group(0)[: -len("your")] + "yours"

    result = _PREDICATIVE_YOUR_CONTRACTION_RE.sub(_replace, text)
    return result, fixed


# beat231 (queue_0905_0646_battery11_imagination_bank.log honest read):
# imag-embodiment-eagle — "You are aware of the shadow moving across an aspen
# grove: your in every detail." — a colon standing in for the copula
# (semantically "[it is] yours in every detail"). _PREDICATIVE_YOUR_RE never
# fires because it requires one of the explicit copula words (is/was/are/
# were/be/been/become/becomes/became/stays) directly before "your"; a colon
# is not one of those tokens. First instance of this bug in imag-embodiment-
# eagle — previously only ever seen with an explicit copula, in different
# scenarios. Same follow-set (what determines "yours" is grammatically
# required is what comes AFTER "your", not what precedes it), just triggered
# by a preceding colon instead of a copula word. 0 hits for ": your
# [followword]" in A_gold.jsonl confirmed before adding.
_PREDICATIVE_YOUR_COLON_RE = re.compile(
    r":\s*your\b"
    r"(?=\s*(?:[.,!?;]|—|$|\s+(?:entirely|completely|now|here|still|again|"
    r"too|for|on|at|in|to|by|with|from|between|whenever|as|today|above|when)\b)"
    r")",
    re.IGNORECASE,
)


def fix_predicative_your_colon(text: str) -> tuple[str, int]:
    """': your [end-of-clause]' -> ': yours [end-of-clause]'.

    Colon-preceding sibling of fix_predicative_your — same standalone-
    possessive requirement (driven by what follows "your"), triggered by a
    preceding colon instead of an explicit copula word.
    """
    fixed = 0

    def _replace(m: "re.Match") -> str:
        nonlocal fixed
        fixed += 1
        return m.group(0)[: -len("your")] + "yours"

    result = _PREDICATIVE_YOUR_COLON_RE.sub(_replace, text)
    return result, fixed


def fix_predicative_your(text: str) -> tuple[str, int]:
    """'is/was your [end-of-clause]' -> 'is/was yours [end-of-clause]'.

    Reverse-direction sibling of fix_possessive_pronouns: catches attributive
    "your" used where the standalone possessive "yours" is grammatically required.
    beat183: "been" added to the copula list ("has always been your too" — "been"
    was missing entirely, an oversight since it's as much a copula form as "is/was");
    an optional single adverb ("uniquely", "always") is now allowed between the
    copula and "your" (found in battery11_0825_0950 imag-intimacy: "has always been
    uniquely your between you both") — captured in group(2) and preserved in the
    output rather than dropped. "between" added to the non-noun-introducing follow
    set for the same script's "your between you both" (a noun can't immediately
    follow "between" + a pronoun like "you both", so this is safe).
    beat184: "whenever" added to the follow set — battery11_0825_1359
    imag-eagle-wildlife-plural: "It is your whenever you feel heavy in other
    ways" (should be "yours"). "whenever" always opens a subordinate clause,
    never introduces a possessable noun, so this is safe the same way
    "between" was.
    """
    fixed = 0

    def _replace(m: "re.Match") -> str:
        nonlocal fixed
        fixed += 1
        return f"{m.group(1)} {m.group(2)}yours"

    result = _PREDICATIVE_YOUR_RE.sub(_replace, text)
    return result, fixed


# beat210 (battery11_1145 imag-eagle-wildlife-plural honest read): "...animals
# small enough to be overlooked at this height...within their own lives sized
# against your which seems so much larger when measured only by how far you
# travel each hour" — should be "against yours which". Different shape from
# _PREDICATIVE_YOUR_RE (that regex requires a copula like is/was before "your";
# this is "your" directly after an arbitrary preposition, e.g. "against"). Not
# folded into that regex's copula alternation — instead: "your" immediately
# followed by a relative pronoun (which/who/that/whom) is unconditionally wrong
# regardless of what precedes it, because a relative pronoun can never be the
# possessed noun in an attributive "your NOUN" construction — there is no
# legitimate English sentence where "your" is directly followed by "which",
# "who", "whom", or "that".
_PREDICATIVE_YOUR_RELPRO_RE = re.compile(
    r"\byour\b(?=\s+(?:which|who|whom|that)\b)",
    re.IGNORECASE,
)


def fix_predicative_your_relpro(text: str) -> tuple[str, int]:
    """'your [which/who/whom/that]' -> 'yours [which/who/whom/that]'.

    Preposition-preceding sibling of fix_predicative_your — same standalone-
    possessive requirement, triggered by an immediately-following relative
    pronoun instead of a preceding copula.
    """
    fixed = 0

    def _replace(m: "re.Match") -> str:
        nonlocal fixed
        fixed += 1
        return "yours"

    result = _PREDICATIVE_YOUR_RELPRO_RE.sub(_replace, text)
    return result, fixed


# beat231 (queue_0905_0646_battery11_imagination_bank.log honest read):
# imag-intimacy-finds-your-across — "some small thing she did that was her
# alone and now your too." — the "now your too" clause has no explicit
# copula at all (elliptical coordination, the implied "[it was]" dropped
# before "your"), so it matches neither _PREDICATIVE_YOUR_RE (needs a copula
# word immediately before "your") nor any other sibling above. Same
# unconditional-on-preceding-context logic as _PREDICATIVE_YOUR_RELPRO_RE:
# "too" can never be the possessed noun in an attributive "your NOUN"
# construction (it's an adverb, not a noun), so "your too" at a clause
# boundary is unconditionally wrong regardless of what precedes it. 0 hits
# for "your too" followed by end-of-clause punctuation in A_gold.jsonl
# confirmed before adding (the corpus's only "your too" substring hits are
# "your tool", an unrelated word, not a real match against the word-
# boundary-scoped pattern below).
_PREDICATIVE_YOUR_TOO_RE = re.compile(
    r"\byour\s+too\b(?=\s*(?:[.,!?;]|—|$))",
    re.IGNORECASE,
)


def fix_predicative_your_too(text: str) -> tuple[str, int]:
    """'your too [end-of-clause]' -> 'yours too [end-of-clause]'.

    Unconditional-on-preceding-context sibling of fix_predicative_your_relpro
    — "too" can never introduce a possessed noun, so this fires regardless
    of what comes before "your" (including no copula at all, the elliptical
    coordination shape that triggered this).
    """
    fixed = 0

    def _replace(m: "re.Match") -> str:
        nonlocal fixed
        fixed += 1
        return "yours too"

    result = _PREDICATIVE_YOUR_TOO_RE.sub(_replace, text)
    return result, fixed


# beat198 (battery11_1317 imag-intimacy honest read): "a reminder held after
# she has left again to do whatever is her today" — the her/hers sibling of
# _PREDICATIVE_YOUR_RE/fix_predicative_your above (same copula+standalone-
# possessive shape, opposite pronoun). Shares the same non-noun follow-set
# reasoning: "her" directly followed by "today" (or a closing punctuation mark,
# or any of the other listed non-noun words) can never be the attributive
# determiner (nothing possessable follows), so the standalone possessive
# "hers" is grammatically required.
_PREDICATIVE_HER_RE = re.compile(
    r"\b(is|was|are|were|be|been|become|becomes|became)\s+((?:\w+ly\s+)?)her\b"
    r"(?=\s*(?:[.,!?;]|—|$|\s+(?:entirely|completely|now|here|still|again|"
    r"too|for|on|at|in|to|by|with|from|between|whenever|as|today|above|when)\b)"
    r")",
    re.IGNORECASE,
)


def fix_predicative_her(text: str) -> tuple[str, int]:
    """'is/was her [end-of-clause]' -> 'is/was hers [end-of-clause]'.

    her/hers sibling of fix_predicative_your — same copula+standalone-
    possessive shape, opposite pronoun.
    """
    fixed = 0

    def _replace(m: "re.Match") -> str:
        nonlocal fixed
        fixed += 1
        return f"{m.group(1)} {m.group(2)}hers"

    result = _PREDICATIVE_HER_RE.sub(_replace, text)
    return result, fixed


# beat231 (queue_0905_0646_battery11_imagination_bank.log honest read):
# imag-intimacy-finds-your-across — "some small thing she did that was her
# alone and now your too." — "was her alone" should be "was hers alone"
# (predicative possessive before "alone"). _PREDICATIVE_HER_RE's follow-set
# never included "alone" because for the your/yours sibling "alone" already
# has a DIFFERENT established meaning ("your alone" -> "you're alone", a
# homophone-contraction fix, not a possessive one — see fix_your_contraction)
# that "her alone" has no equivalent for ("her're" isn't a word). Scoped
# narrowly to require the phrase end in punctuation or a coordinating
# conjunction (and/but/or/so) specifically to avoid "her alone time" (a real
# compound noun phrase — "alone" modifying "time" — where "her" IS correctly
# attributive and must stay untouched). 0 hits for "her alone" preceded by a
# copula anywhere in A_gold.jsonl confirmed before adding (the corpus's only
# "her alone" hits are "kept her alone in the middle of crowds", object
# pronoun, no copula before "her", correctly left untouched by this scoping).
_PREDICATIVE_HER_ALONE_RE = re.compile(
    r"\b(is|was|are|were|be|been|become|becomes|became)\s+her\s+alone\b"
    r"(?=\s*(?:[.,!?;]|—|$|\s+(?:and|but|or|so)\b))",
    re.IGNORECASE,
)


def fix_predicative_her_alone(text: str) -> tuple[str, int]:
    """'is/was her alone [end-of-clause/and/but/or/so]' -> '...hers alone...'.

    Narrow "alone" sibling of fix_predicative_her — deliberately excludes the
    "her alone time" compound-noun shape (see the comment above the regex).
    """
    fixed = 0

    def _replace(m: "re.Match") -> str:
        nonlocal fixed
        fixed += 1
        return f"{m.group(1)} hers alone"

    result = _PREDICATIVE_HER_ALONE_RE.sub(_replace, text)
    return result, fixed


# beat207 (queue_0829_2347_battery11_imagination_bank.log honest read, imag-
# intimacy): "You hear herself say something to you as she walks over" — the
# reflexive "herself" used where the object pronoun "her" is required (the
# user hears HER say something, not hears her-hearing-herself). Scoped to
# "hear(s/d) herself say" only, not a blanket herself->her ban: "she caught
# herself" / "she surprised herself" are legitimate reflexive uses elsewhere
# in this scenario type and must stay untouched.
_REFLEXIVE_HER_OBJECT_RE = re.compile(
    r"\bhear(s|d)?\s+herself\s+say\b", re.IGNORECASE
)


def fix_reflexive_her_object(text: str) -> tuple[str, int]:
    """'hear(s/d) herself say' -> 'hear(s/d) her say' (object pronoun, not reflexive)."""
    fixed = 0

    def _replace(m: "re.Match") -> str:
        nonlocal fixed
        fixed += 1
        suffix = m.group(1) or ""
        return f"hear{suffix} her say"

    result = _REFLEXIVE_HER_OBJECT_RE.sub(_replace, text)
    return result, fixed


# beat183 (2026-08-25): battery11_0825_0950 imag-intimacy honest read — four new
# object-pronoun escapes distinct from fix_predicative_your's copula pattern (these
# are "your"/"theirs" standing in for "you"/"them" as the object of a preposition or
# verb, not a standalone possessive): "Her hand stays in your all the time now",
# "finds its way back into your as she leads you", "Her hands guide your around
# hers", "she tells your what is in the drink", "existed properly just between
# theirs together". Narrow, literal-phrase patterns (same style as the eagle
# anon-companion escape list) rather than a general grammar rule, since each is a
# single observed instance and a broad prep/verb+pronoun regex risks false-firing
# on legitimate attributive uses ("in your hands", "tells your story").
_INTIMACY_OBJECT_PRONOUN_SUBS = (
    (re.compile(r"\bin\s+your\s+all\s+the\s+time\b", re.IGNORECASE), "in yours all the time"),
    (re.compile(r"\binto\s+your\s+as\b", re.IGNORECASE), "into yours as"),
    (re.compile(r"\bleaves\s+your\s+long\s+enough\b", re.IGNORECASE), "leaves yours long enough"),
    (re.compile(r"\bguides\s+your\s+around\b", re.IGNORECASE), "guides you around"),
    (re.compile(r"\bguide\s+your\s+around\b", re.IGNORECASE), "guide you around"),
    (re.compile(r"\btells\s+your\s+what\b", re.IGNORECASE), "tells you what"),
    (re.compile(r"\btell\s+your\s+what\b", re.IGNORECASE), "tell you what"),
    (re.compile(r"\bbetween\s+theirs\s+together\b", re.IGNORECASE), "between them together"),
    # beat184 (2026-08-25): battery11_0825_1359 imag-intimacy honest read — the
    # beat183 patterns above did not cover this run's escapes, confirming the
    # fix needed a second pass. Four new literal instances, same rationale
    # (narrow literal phrases, not a general grammar rule, to avoid false-
    # firing on legitimate attributive "your"/"her" uses):
    (re.compile(r"\bholds\s+your\s+without\s+looking\s+up\b", re.IGNORECASE), "holds you without looking up"),
    # beat221 (queue_0902_1618_battery11_imagination_bank.log honest read):
    # "Her hand finds your across one of those cold tiles." — same beat187/198/
    # 218 verb-governed "your"-standing-in-for-"yours" family, new verb "finds"
    # not covered by those. Scoped to "finds your across" (not bare "finds
    # your") since "finds your finger"/"finds your place" are legitimate
    # attributive uses already present in A_gold.jsonl.
    (re.compile(r"\bfinds\s+your\s+across\b", re.IGNORECASE), "finds yours across"),
    # beat225 (queue_0904_1031_battery11_imagination_bank.log): "Her hand leaves
    # your for only an instant" — same verb-governed family as the "leaves your
    # long enough" entry above, new trailing phrase "for only an instant".
    (re.compile(r"\bleaves\s+your\s+for\s+only\s+an\s+instant\b", re.IGNORECASE), "leaves yours for only an instant"),
    # beat225: "They land exactly where her meet across from yours" — subject-
    # case + missing-verb corruption ("her meet" for "her hand meets"), not the
    # possessive-vs-standalone shape the rest of this list targets. Literal
    # phrase fix, scoped to the exact defect string.
    (re.compile(r"\bwhere\s+her\s+meet\s+across\s+from\s+yours\b", re.IGNORECASE), "where her hand meets yours"),
    (re.compile(r"\byour\s+stands\s+still\s+holding\s+onto\b", re.IGNORECASE), "you stand still holding onto"),
    (
        re.compile(
            r"\bbefore\s+your\s+come\s+to\s+reach\s+out\s+for\s+her\s+the\s+exact\s+same\s+moment\s+as\s+her\s+turn\s+toward\s+you\s+instead\b",
            re.IGNORECASE,
        ),
        "before you come to reach out for her the exact same moment as she turns toward you instead",
    ),
    (re.compile(r"\bshe\s+has\s+already\s+used\s+theirs\s+for\s+something\s+else\b", re.IGNORECASE), "she has already used hers for something else"),
    # beat186: battery11_2235 honest read — 2 more instances of the still-open
    # "your"+ADJECTIVE-follow shape (beat185's audit item #5, deferred because a
    # general adjective-follow rule looked unsafe off one example: "beneath your
    # long shadow" is legitimate "your" + adjective + NOUN, so naively adding
    # "long"/"close" to the shared _YOUR_NONNOUN_FOLLOW single-word lookahead
    # (used by _YOUR_PREP_OBJECT_RE too) would wrongly fire on that and similar
    # real attributive uses. Literal-phrase patches again, same discipline as
    # beat183/184, until enough instances justify a safe 2-word-lookahead rule.
    (re.compile(r"\breleases\s+your\s+long\s+enough\b", re.IGNORECASE), "releases you long enough"),
    (re.compile(r"\bof\s+your\s+close\s+around\b", re.IGNORECASE), "of yours close around"),
    # beat187 (2026-08-26): battery11_0826_0355 honest read, imag-intimacy — a
    # THIRD grammatical shape of the your/yours escape family, distinct from both
    # fix_predicative_your's copula+your pattern and _YOUR_PREP_OBJECT_RE's
    # preposition+your pattern. Here "your" is the DIRECT OBJECT of a transitive
    # verb ("finds") and is itself followed by a preposition ("without"): "Her
    # hand finds your without a word — it's warm from whatever heat she was
    # holding onto before." Context (a hand finding another hand, "warm from...
    # holding onto") makes clear the correct target is the standalone possessive
    # "yours" (her hand finds your hand -> finds yours), not "you". Literal patch
    # for this single instance, same discipline as the other narrow phrase
    # patches above — a general verb-governed-"your" rule isn't attempted off one
    # example, same reasoning beat185/186 documented for the adjective-follow gap.
    (re.compile(r"\bfinds\s+your\s+without\s+a\s+word\b", re.IGNORECASE), "finds yours without a word"),
    # beat198 (battery11_1317 imag-intimacy honest read): two more instances of
    # the same beat187 shape ("your" as the direct object of a transitive verb,
    # standing in for the standalone possessive "yours") — "Her feet now match
    # your in pace behind you" and "hers is already reaching forward to meet
    # your in this shared evening moment." Same discipline as beat187: literal
    # patch for each instance, no general verb-governed-"your" rule attempted
    # off two examples.
    (re.compile(r"\bmatch\s+your\s+in\s+pace\b", re.IGNORECASE), "match yours in pace"),
    (re.compile(r"\bmeet\s+your\s+in\s+this\s+shared\s+evening\s+moment\b", re.IGNORECASE), "meet yours in this shared evening moment"),
    # beat203 (battery11_0550 imag-intimacy honest read): two more instances of
    # the beat187/198 shape at the script's own CLOSING lines -- the fixer ran
    # this exact script (log claims "3 your/theirs object-pronoun error(s)
    # fixed") but missed these two, the most prominent position in the output.
    # "Her hand in your one final time" / "Her hand releases your finally" both
    # need the standalone possessive ("yours") since "your" here is the direct/
    # prepositional object standing in for "your hand".
    (re.compile(r"\bin\s+your\s+one\s+final\s+time\b", re.IGNORECASE), "in yours one final time"),
    (re.compile(r"\breleases\s+your\s+finally\b", re.IGNORECASE), "releases yours finally"),
    # beat214 (queue_0831_1835_battery11_imagination_bank.log honest read):
    # imag-intimacy — "always made your come out slower instead of faster" —
    # "your" standing in for the object pronoun "you" after a causative verb
    # ("made" + object + bare infinitive), a shape distinct from every prior
    # your/yours family (not predicative, not a preposition object, not a bare
    # subject). Literal patch for this exact instance per the file's established
    # discipline (narrow phrase first, generalize once a second instance
    # justifies a verb list).
    (re.compile(r"\bmade\s+your\s+come\s+out\b", re.IGNORECASE), "made you come out"),
    # beat218 (battery11_imagination_bank_0902_0000 honest read): imag-intimacy —
    # "She meets your with equal pressure — something known and practiced
    # between them both" — same beat187/198 shape (verb-governed "your"
    # standing in for the standalone possessive "yours" as the object of
    # "meets"). Literal patch for this exact instance per this file's
    # established discipline.
    (re.compile(r"\bmeets\s+your\s+with\s+equal\s+pressure\b", re.IGNORECASE), "meets yours with equal pressure"),
    # Same script: "The fan continues its constant hum between you and hers"
    # is a different (ambiguous, not fixed) case, but two OTHER lines in the
    # same script coordinate "hers and your" where "your" is predicative and
    # standing alone (no noun follows) — "falls on hers and your differently"
    # and "hers and your on the balcony" — needing the standalone possessive
    # "yours" to match its coordinate "hers", the same logic fix_predicative_your
    # uses but in a coordination ("X and your") the copula-scoped regex there
    # doesn't reach. Reuses _YOUR_NONNOUN_FOLLOW so it only fires when nothing
    # noun-like follows "your" (i.e. it's standing alone, not attributive).
    # beat227 (queue_0904_1805_battery11_imagination_bank.log honest read),
    # imag-intimacy-finds-your-across (a scenario with zero dedicated postcheck
    # coverage before this beat): two new instances of the established
    # verb-governed "your"-for-"yours" family, distinct trailing words from
    # every prior "finds your ..." entry above ("across", "without a word").
    # 0 hits in A_gold.jsonl confirmed before adding.
    (re.compile(r"\bstays\s+your\s+inside\b", re.IGNORECASE), "stays yours inside"),
    (re.compile(r"\bfinds\s+your\s+when\b", re.IGNORECASE), "finds yours when"),
    # Same script: "Her voice is unhurried as hers does so often when you're
    # near her" — a different corruption shape from the your/yours family
    # above: "hers" (a standalone possessive pronoun, never a grammatical
    # subject) used as the subject of "does". Scoped to the exact "as hers
    # does" construction — grammatically "hers" can never correctly precede a
    # finite verb as its subject, so this is a safe, narrow fix, not a style
    # judgment. Confirmed 0 hits for "hers does" in A_gold.jsonl (the raw
    # substring "hers does" appears 3x only as part of unrelated "others
    # doesn't", which this word-boundary-scoped pattern does not match).
    (re.compile(r"\bas\s+hers\s+does\b", re.IGNORECASE), "as she does"),
    # beat232 (queue_0905_1447_battery11_imagination_bank.log honest read),
    # imag-intimacy-finds-your-across: "it closes around your not quite
    # overlapping" — same verb-governed "your"-for-"yours" family as the
    # "finds your across"/"finds your without a word" entries above, new verb
    # "closes". Scoped to the exact trailing phrase, not bare "closes around
    # your", since "it closes around your legs, your waist, your chest" is a
    # legitimate attributive list already present in A_gold.jsonl.
    (re.compile(r"\bcloses\s+around\s+your\s+not\s+quite\s+overlapping\b", re.IGNORECASE), "closes around yours, not quite overlapping"),
    # Same script: "The smell that enters the space then, neither hers nor
    # your exclusively" — "your" standing in for the standalone possessive
    # "yours" in a correlative "neither X nor Y" coordination, sibling to the
    # existing "hers and your" -> "hers and yours" coordination fix above but
    # with "neither...nor" instead of a bare "and". 0 hits in A_gold.jsonl.
    (re.compile(r"\bneither\s+hers\s+nor\s+your\s+exclusively\b", re.IGNORECASE), "neither hers nor yours exclusively"),
    # beat232 (same log, imag-eagle-wildlife-plural): "A shadow moves across
    # your vision: your crossing the mountains below" — a 6th grammatical
    # shape of the your/yours family, distinct from every entry above: "your"
    # is the SUBJECT of a gerund clause ("[you] crossing the mountains"),
    # standing in for "you", not "yours". Scoped to the exact trailing phrase
    # "your crossing the mountains" rather than bare "your crossing", since
    # A_gold.jsonl has 2 legitimate attributive uses where "crossing" is a
    # noun object, not a gerund governing a following noun phrase ("The mat
    # registered your crossing.", "You add your crossing to theirs") —
    # confirmed neither is followed by "the mountains" before adding.
    (re.compile(r"\byour\s+crossing\s+the\s+mountains\b", re.IGNORECASE), "you crossing the mountains"),
)

# beat214: "You feel she come a little closer" (imag-intimacy, 2 instances,
# verbatim same shape both times) — a perception-verb + accusative + bare-
# infinitive construction ("feel" + object + bare verb) requires the object
# pronoun "her", not the subject-case "she"; the opposite direction from
# fix_subject_pronouns' her->she fix, and distinct from _SHE_AS_OBJECT (which
# only covers "she" as the object of a PREPOSITION, not of a perception verb).
# Scoped to "feel she" + a small set of bare motion/perception verbs — the two
# live instances both used "come" — rather than a blanket "she"->"her" rule,
# to avoid touching a legitimate complement clause like "you feel she is right"
# (finite verb, not a bare infinitive, correctly keeps subject-case "she").
_FEEL_SHE_OBJECT_RE = re.compile(
    r"\bfeel\s+she\s+(come|arrive|move|lean|settle|shift|pull|ease|draw|drift)\b",
    re.IGNORECASE,
)


# beat185 (2026-08-25): battery11_1832 honest read (via background agent) found the
# beat183/184 literal-phrase patches above did NOT hold — the same escape SHAPES
# recurred with different trigger words ("your sits" not "your stands"; "towards
# your" not "in your all the time"; "of your long gone" not "into your as"). Six
# straight beats of "add one more literal phrase" without the underlying class
# closing confirms this needs generalizing, not another single-instance patch.
#
# Two general shapes, both using the SAME "non-noun follow-set" trick already
# proven safe by _PREDICATIVE_YOUR_RE (only fires when "your" is NOT immediately
# followed by something that could be the possessed noun, so "your hands", "your
# turn" etc. are never touched):
#
# (1) PREPOSITION + "your" + non-noun-follow -> preposition + "you" (object-of-
#     preposition case: "towards your with", "like your belong", "of your long
#     gone" -> "of yours" specifically, since "of yours" is the correct standalone
#     idiom, not "of you").
#   Includes a broad preposition list on top of the original adverb/conjunction
#   set: grammatically, "your" (a possessive determiner) can NEVER be directly
#   followed by a preposition — a preposition always needs a noun phrase object,
#   and "your" itself needs a noun to attach to, so "your" + preposition is
#   always an error, not a style judgment. This is what beat185's "towards your
#   with" (audit: fix #2 above didn't catch it because "with" wasn't in the
#   original narrow follow-set) needed — safe to add with no new FP risk.
_YOUR_NONNOUN_FOLLOW = (
    r"(?=\s*(?:[.,!?;]|—|$|\s+(?:again|still|now|here|entirely|completely|instead|"
    r"already|exactly|quietly|slowly|softly|whenever|between|and|but|or|when|while|"
    # beat189 (battery11_0826_1712 imag-intimacy): "cold against your where it was
    # put down" — "where" opens a relative clause the same way "when"/"while"
    # already do, and was missing from this set despite its siblings being present.
    r"where|"
    r"as|that|belong|belongs|remain|remains|stay|stays|sit|sits|stand|stands|"
    r"with|for|from|of|to|by|on|at|in|near|into|onto|upon|under|over|through|"
    r"during|since|until|towards?|about|above|across|after|against|along|among|"
    r"before|behind|beneath|beside|beyond|despite|down|inside|outside|up|within|"
    # beat214 (queue_0831_1835_battery11_imagination_bank.log): imag-intimacy
    # "falls on hers and your differently" — "differently" is an adverb (never
    # a possessed noun), same class as "entirely"/"completely"/"exactly"/"slowly"
    # already in this list, just missing.
    r"without|differently|"
    # beat225 (queue_0904_1031_battery11_imagination_bank.log, first clean read
    # after the 33hr MTLCompilerService dead zone): "beside your it's not hard
    # to notice" (imag-intimacy) — "it's" opens a new clause the same way
    # "that"/"where" already do, missing from this set. "near your once more"
    # (same script) — "once" is a temporal adverb, same class as "again"/
    # "still"/"now" already listed, missing. 0 FP hits in A_gold.jsonl for
    # "your it"/"your once" confirmed before adding.
    r"it's|once)\b))"
)

# beat214: coordination shape "hers and your" where "your" stands alone (matches
# _YOUR_NONNOUN_FOLLOW, i.e. nothing noun-like follows it) needs the standalone
# possessive "yours" to parallel its coordinate "hers" — "falls on hers and your
# differently" / "hers and your on the balcony". Same predicative-your logic as
# fix_predicative_your, but that regex is gated on a preceding COPULA (is/was/
# etc.); here the trigger is the coordinating "and hers" instead, which no
# existing pattern reaches.
_HERS_AND_YOUR_RE = re.compile(r"\bhers\s+and\s+your\b" + _YOUR_NONNOUN_FOLLOW, re.IGNORECASE)

# beat193 (battery11_0827_0453 imag-intimacy): "separates her from your underneath."
# — "underneath" used as a bare noun-substitute (the area underneath), not an
# adjective before a noun. Deliberately NOT added to _YOUR_NONNOUN_FOLLOW above:
# unlike that list's conjunctions/prepositions (which always introduce more clause
# content), "underneath" is ambiguous with a legitimate attributive use ("your
# underneath layer", "your underneath drawer") when a noun follows it. Only the
# terminal case — "your underneath" ending the clause with nothing after it — is
# the broken pronoun shape; require end-of-clause immediately after "underneath".
_YOUR_UNDERNEATH_TERMINAL_RE = re.compile(
    r"\b(with|for|from|to|by|on|at|in|near|into|onto|upon|under|over|through|"
    r"during|since|until|towards?|about|above|across|after|against|along|among|"
    r"before|behind|beneath|beside|beyond|despite|down|inside|outside|up|within|"
    r"without|of)\s+your\s+underneath(?=\s*(?:[.,!?;]|—|$))",
    re.IGNORECASE,
)

# beat188 (battery11_0826_0920/0355 honest reads): the curated preposition list
# above missed real prepositions found in new instances — "her fits against your
# in this quiet apartment" ("against" absent). Broadened to the SAME
# comprehensive preposition set already used (safely, with zero prior FP) in
# _YOUR_NONNOUN_FOLLOW's follow-side list — grammatically, ANY preposition
# immediately followed by "your" + a non-noun-follow word is broken the same
# way, regardless of which specific preposition it is. "of" stays excluded
# (handled separately by _OF_YOUR_STANDALONE_RE below, which correctly produces
# "of yours" — the idiomatic form — rather than this rule's "prep + you").
_YOUR_PREP_OBJECT_RE = re.compile(
    r"\b(with|for|from|to|by|on|at|in|near|into|onto|upon|under|over|through|"
    r"during|since|until|towards?|about|above|across|after|against|along|"
    r"among|before|behind|beneath|below|beside|beyond|despite|down|inside|"
    r"outside|up|within|without|like|around)\s+your\b"
    + _YOUR_NONNOUN_FOLLOW,
    re.IGNORECASE,
)

_OF_YOUR_STANDALONE_RE = re.compile(
    r"\bof\s+your\b" + _YOUR_NONNOUN_FOLLOW,
    re.IGNORECASE,
)

# beat225 (queue_0904_1031_battery11_imagination_bank.log, imag-embodiment-eagle):
# "first call you'd heard earlier when both of your were farther apart" — "of
# your" immediately before a copula ("were"/"are"/"was"/"is") is SUBJECT case
# ("of you were"), not the possessive-standalone case _OF_YOUR_STANDALONE_RE
# handles ("of yours") — that rule would wrongly produce "of yours were" here.
# Checked before the standalone rule below since its follow-word list doesn't
# include these copulas (no overlap today), but scoped as its own rule so it
# stays correct if that list ever grows.
_OF_YOUR_SUBJECT_CASE_RE = re.compile(r"\bof\s+your\s+(were|are|was|is)\b", re.IGNORECASE)

# (2) "your" as a BARE SUBJECT immediately before a finite verb ("your sits",
#     "your stands", "your remains") -> "you" + de-conjugated verb. Curated verb
#     list (matches the codebase's existing style, e.g. _NARRATOR_POSS) rather
#     than a POS tagger — narrow enough not to false-fire on "your standing desk"
#     (gerund/adjective use, not in this finite-verb list).
_YOUR_BARE_SUBJECT_VERBS = {
    "sits": "sit", "stands": "stand", "stays": "stay", "remains": "remain",
    "feels": "feel", "waits": "wait", "lingers": "linger", "holds": "hold",
    "moves": "move", "rests": "rest", "leans": "lean", "watches": "watch",
    "listens": "listen", "breathes": "breathe", "curls": "curl", "settles": "settle",
    "hovers": "hover", "drifts": "drift", "pulls": "pull", "reaches": "reach",
    "turns": "turn", "shifts": "shift", "belongs": "belong",
    # beat198 (battery11_1317 imag-intimacy): "as your returns to wakefulness
    # fully" — present-tense "returns" was missing (only past-tense "returned"
    # was covered, in the separate _YOUR_SUBJECT_VERBS list used by
    # fix_your_subject_pronoun). "your returns" can never be a legitimate noun
    # phrase in this product's prose (the financial-noun sense of "returns"
    # doesn't belong in guided-imagination scripts), so safe by construction.
    "returns": "return",
}
_YOUR_BARE_SUBJECT_RE = re.compile(
    r"\byour\s+(" + "|".join(_YOUR_BARE_SUBJECT_VERBS) + r")\b", re.IGNORECASE
)

# beat192 (battery11_0826_2346 imag-intimacy honest read): "move past your a
# step or two before landing" / "moving past your a step ahead without
# stopping" — "your" standing in for the object pronoun "you", corrupting the
# core 2nd-person address itself (distinct from every prior your/yours family,
# which all involve a possessive-vs-standalone confusion, not the primary
# "you" pronoun). General, zero-FP grammar rule: a possessive determiner can
# NEVER be directly followed by an indefinite article ("your a X" / "your an
# X" is not valid English in any reading) — so "your" immediately before
# "a"/"an" is always the object pronoun "you" misfiring as "your".
# beat206 (queue_0829_1746 imag-intimacy): "holding it back with your the way
# nothing else needed words here between them" — same corruption, definite
# article this time ("your the" is equally never valid English — a possessive
# determiner can't precede ANY article, definite or indefinite). Extended the
# same zero-FP rule to "the". Note: this one sentence has other garbling
# beyond the your/the swap (missing words after "way"); the fix is still
# correct and safe to apply, it just doesn't fully repair that instance.
_YOUR_BEFORE_ARTICLE_RE = re.compile(r"\byour\b(?=\s+(?:an?|the)\b)", re.IGNORECASE)


def fix_intimacy_object_pronoun_escapes(text: str) -> tuple[str, int]:
    """Fix "your"/"theirs" used as a verb/preposition object, or as a bare
    subject, where "you"/"yours"/"them"/"she" is grammatically required.

    Runs the beat183/184 literal-phrase patches first (cheap, exact), then the
    beat185 generalized preposition-object and bare-subject patterns (see
    docstrings above) to catch new trigger-word variants of the same shapes.
    """
    fixed = 0
    for pattern, replacement in _INTIMACY_OBJECT_PRONOUN_SUBS:
        text, n = pattern.subn(replacement, text)
        fixed += n

    text, n = _YOUR_PREP_OBJECT_RE.subn(lambda m: f"{m.group(1)} you", text)
    fixed += n
    text, n = _OF_YOUR_SUBJECT_CASE_RE.subn(lambda m: f"of you {m.group(1)}", text)
    fixed += n
    text, n = _OF_YOUR_STANDALONE_RE.subn("of yours", text)
    fixed += n
    text, n = _YOUR_UNDERNEATH_TERMINAL_RE.subn(lambda m: f"{m.group(1)} you underneath", text)
    fixed += n
    text, n = _YOUR_BARE_SUBJECT_RE.subn(
        lambda m: f"you {_YOUR_BARE_SUBJECT_VERBS[m.group(1).lower()]}", text
    )
    fixed += n
    text, n = _YOUR_BEFORE_ARTICLE_RE.subn("you", text)
    fixed += n
    text, n = _THAN_YOUR_STATIVE_RE.subn(lambda m: f"than yours {m.group(1)}", text)
    fixed += n
    text, n = _HERS_AND_YOUR_RE.subn("hers and yours", text)
    fixed += n
    text, n = _FEEL_SHE_OBJECT_RE.subn(lambda m: f"feel her {m.group(1)}", text)
    fixed += n

    return text, fixed


# beat152: mid-word token fusion — n376 occasionally fuses a contraction stub with the
# next word by dropping the apostrophe and running the tokens together, producing
# e.g. "doesnYou" from "doesn't You". Split at the capital letter boundary: the contraction
# stub ("doesn") remains but TTS reads the two pieces as separate words, which is far less
# jarring than a single nonsense token. Only fires on ≥3-char lowercase prefix + ≥2-char
# capitalized suffix (rules out legitimate initialisms like "iPhone" etc. — none appear
# in guided-imagination scripts).
_WORD_FUSION_RE = re.compile(r'\b([a-z]{3,})([A-Z][a-z]{1,})\b')


def fix_word_fusions(text: str) -> tuple[str, int]:
    """Split mid-word token fusions where lowercase runs into an embedded capital.

    e.g. "doesnYou" → "doesn You", "cantSee" → "cant See".
    Returns (cleaned_text, n_fixes).
    """
    result, n = _WORD_FUSION_RE.subn(r'\1 \2', text)
    return result, n


# beat201 (review-queue, battery11_1912): a distinct dropped-contraction bug from
# fix_word_fusions above — that one splits a lowercase+capital fusion with no space
# ("doesnYou"). This one is a clean dropped-apostrophe-t with a normal space already
# in place ("don know how much time has passed", "don need words to explain" —
# imag-intimacy). TTS reads the bare stub as the literal word "don"/"isn"/etc.
# Most of these stub words have zero legitimate standalone English meaning, so a
# word-boundary fix (not followed by an apostrophe, which would mean the
# contraction is already intact) is safe. Confirmed 0 legitimate bare uses of any
# of these words in A_gold.jsonl's actual script/prompt text (only false hits were
# JSON-escaped apostrophes and kebab-case id slugs, neither of which this runs on).
# "don" and "haven" are deliberately excluded from the general list — both have a
# real standalone meaning ("don a coat", "safe haven") that a blind word-boundary
# fix would corrupt. Matching this file's established convention (narrow literal
# fixes, widened only once a second real instance justifies it — see the your/yours
# and particular/specific families elsewhere in this file), "don" is fixed only in
# the two exact surface forms already confirmed in a live log.
_DROPPED_APOSTROPHE_T_RE = re.compile(
    r"\b(isn|aren|wasn|weren|wouldn|couldn|shouldn|hasn|didn|doesn|hadn)\b(?!['’]t)",
    re.IGNORECASE,
)
_DON_KNOW_NEED_RE = re.compile(r"\bdon\b(?=\s+(?:know|need)\b)", re.IGNORECASE)


def fix_dropped_apostrophe_t(text: str) -> tuple[str, int]:
    """Restore a dropped apostrophe-t on negative-contraction stubs.

    e.g. "don know how much time has passed" → "don't know how much time has
    passed", "isn even halfway" → "isn't even halfway". Returns (cleaned_text,
    n_fixes).
    """
    result, n1 = _DROPPED_APOSTROPHE_T_RE.subn(lambda m: m.group(1) + "'t", text)
    result, n2 = _DON_KNOW_NEED_RE.subn("don't", result)
    return result, n1 + n2


_BACK_LEAK_PATTERNS = [
    re.compile(r"\bTwo sentences max\b", re.IGNORECASE),
    # beat237 (queue verify_beat237_0907_1835 honest read): these two patterns were
    # meant to catch the model echoing a BACK_PROMPT move LABEL verbatim as a bare
    # heading ("EYES OPEN." / "Open when ready." with nothing else in the sentence)
    # but were only anchored at sentence-START — that also matches a perfectly
    # legitimate model-authored closing sentence that starts with the same words
    # and then CONTINUES with real content ("Eyes open softly whenever you're
    # ready, carrying this back with you into the room."), which is the single
    # most natural phrasing of the required return-to-room/eyes-open cue. Root
    # cause of a live regression: check_return_to_room_closing(closing) correctly
    # saw the cue present right after BACK generation (beat236/237's check point),
    # but strip_back_instruction_leaks() — called later on the assembled `full`
    # script during postprocessing — then deleted the very sentence the check had
    # just validated, so 5/9 scripts in that battery11 run shipped with NO
    # return-to-room beat at all despite the beat236/237 check having passed at
    # generation time. FIX: anchor both patterns to the END of the sentence too
    # (`$`) so they only match a genuine bare label/template echo with no real
    # content attached — a natural sentence that continues past the trigger words
    # no longer matches and survives postprocessing intact.
    re.compile(r"^Open (?:your eyes )?when ready[.:]?\s*$", re.IGNORECASE),
    re.compile(r"\bSoften the image\b", re.IGNORECASE),
    re.compile(r"\bCarry-back\b", re.IGNORECASE),
    re.compile(r"\bRe-room\b", re.IGNORECASE),
    re.compile(r"^Eyes open[.:]?\s*$", re.IGNORECASE),
    re.compile(r"\bOne final line\b", re.IGNORECASE),
    # "(3) RE-ROOM" instruction bleed: model echoes "or surface where you sit/lie down"
    re.compile(r"\bor surface where you (?:sit|lie)\b", re.IGNORECASE),
    # BACK section leak variant: "chair or whatever surface is beneath you"
    re.compile(r"\bor whatever surface is beneath you\b", re.IGNORECASE),
    # BACK section leak variant: "the chair or surface beneath you" (beat38 battery11 0146 imag-intimacy)
    re.compile(r"\bchair or surface\b", re.IGNORECASE),
    # BACK section leak variant: "your chair or whatever surface has you resting" (beat38 battery11 0146 imag-active-scene)
    re.compile(r"\bor whatever surface has you\b", re.IGNORECASE),
    # BACK section leak variant: "in this chair or whatever surface you are on right now exactly" (beat61 0726 battery11 eagle)
    re.compile(r"\bor whatever surface you are on\b", re.IGNORECASE),
    # BACK section leak variant: "on this surface or chair right now" — reversed form (beat61 0726 battery11 deposition)
    re.compile(r"\bsurface or chair\b", re.IGNORECASE),
    # BACK section leak variant: "whether it is chair or couch or floor below you" (beat68 battery11 imag-active-scene)
    re.compile(r"\bchair or couch or floor\b", re.IGNORECASE),
    # BACK section leak variant: "this chair or whatever support holds you now" (beat69 battery11 eagle)
    re.compile(r"\bchair or whatever\b", re.IGNORECASE),
    # BACK section leak variant: "the chair or floor under you" — couch-free form (beat73 battery11 imag-active-scene)
    re.compile(r"\bchair or floor\b", re.IGNORECASE),
    # BACK section leak variant: "settled on whatever surface you are on right now: the
    # chair or ground supporting you" — false PASS in postcheck's own chair-body-reminder
    # line (beat194, queue_0827_1628_battery11_imagination_bank.log, imag-eagle-golden-
    # eagle-wildlife). "or whatever surface you are on" (beat61, line above) matched the
    # opening clause but not this trailing restatement; none of the prior "chair or X"
    # literals cover "ground".
    re.compile(r"\bchair or ground\b", re.IGNORECASE),
    # BACK section meta-commentary: "an imaginary run that was very real" — breaks immersion (beat68 battery11 imag-active-scene)
    re.compile(r"\bimaginary (?:run|session|experience|practice)\b", re.IGNORECASE),
    # Model occasionally hallucinates technical environment details — strip these.
    re.compile(r"\bTTS output device\b", re.IGNORECASE),
    re.compile(r"\btext.to.speech\b", re.IGNORECASE),
    # beat193: self-referential meta-commentary about "the script" itself breaking
    # immersion (imag-intimacy battery11_0827_0453, same run as the chat-template
    # token leak below) — the model critiques its own generation in third person
    # instead of narrating in second person. Zero legitimate use: a guided-imagination
    # script never refers to itself as "the script."
    re.compile(r"\bthe script\b.{0,40}\bbroke\b|\bbroke\b.{0,20}\bthe\s+immersion\b",
               re.IGNORECASE),
    # beat201: mid-body meta-instruction leak, distinct from the end-of-script BACK
    # leaks above — a paraphrase of the generator.py line-411 pacing instruction
    # ("Each paragraph must advance: new moment, new sensation, new beat...")
    # surfaced verbatim as narrative content mid-script (battery11_0039
    # imag-eagle-wildlife-plural). Not the literal source string (the model
    # paraphrased it), so this is a literal strip of the exact surfaced form, not
    # a generalized instruction-leak detector.
    re.compile(r"\bEach paragraph should land a new moment or feeling\b",
               re.IGNORECASE),
    # beat212 (queue_0830_1800 battery11 honest read): imag-eagle-golden-eagle-
    # wildlife — the single worst leak found in that run, a raw continuation-
    # prompt/instruction fragment breaking mid-script into the narrated audio:
    # "You don You are given a task to write more content about the same scene,
    # but what else can be explored? Your wings are still open..." — distinct
    # from every existing leak pattern (not a BACK-section echo, not a chat-
    # template token, not self-referential "the script" commentary) — this
    # reads as a leaked training-continuation instruction. Both halves are
    # zero-legitimate-use phrases in a guided-imagination script.
    re.compile(r"\byou (?:are|were) given a task to write\b", re.IGNORECASE),
    re.compile(r"\bwhat else can be explored\b", re.IGNORECASE),
]

# Instruction prefixes that leak as a label before real content — strip the prefix only,
# keep the content that follows it (don't drop the whole sentence).
_INSTRUCTION_PREFIX_PATTERNS = [
    re.compile(r"Hard Cut Into The Scene:\s*", re.IGNORECASE),
]

# Meta/tool-call text hallucination (beat187, imag-mri battery11_0826_0920): the model
# generated "...light-filled breathsDataExchange completed. User requested an example
# now fully compiled by following supplied rules. You are inside the tube..." — a
# fragment resembling internal tool-call/system text, fused directly onto the end of a
# legitimate word with no space ("breaths" + "DataExchange"). This is a distinct
# hallucination class from both fix_word_fusions() (which only splits contraction+
# capital fusions like "doesnYou") and the BACK_PROMPT echoes below (which are
# sentence-level, not word-fused) — same family as the "TTS output device" /
# "text-to-speech" technical-environment hallucinations already in
# _BACK_LEAK_PATTERNS, just glued onto the preceding word instead of standing alone.
# A literal substitution is safe (zero legitimate use for this exact phrase in a
# guided-imagination script) and reconnects the real word with proper punctuation
# instead of dropping the whole run-on sentence it's fused into.
_META_TEXT_LEAK_RE = re.compile(
    r"([a-z]{3,})DataExchange completed\.\s*"
    r"User requested an example now fully compiled by following supplied rules\.\s*",
    re.IGNORECASE,
)

# beat193 (imag-intimacy battery11_0827_0453): a second, more severe instance of the
# beat187 meta/tool-call hallucination family — this time a RAW chat-template special
# token plus a hallucinated fake turn marker, standing alone rather than word-fused:
#   "...without anywhere else necessary for context. <|im_start|>
#   !user
#   The script ended on the same idea multiple times which broke the immersion. The
#   ceiling fan above you is still turning..."
# Two distinct leaks in sequence: (1) the raw special token itself, (2) a bare
# hallucinated "!user"/"!assistant"/"!system" turn-marker line — same underlying
# failure (chat-template structure bleeding into content) as beat187's DataExchange
# leak, just a different surface form. Stripped with surrounding whitespace collapsed
# to a single space so the legitimate sentences on either side reconnect cleanly.
_CHAT_TEMPLATE_TOKEN_RE = re.compile(r"\s*<\|[a-z_]+\|>\s*", re.IGNORECASE)
_FAKE_TURN_MARKER_RE = re.compile(r"\s*!(?:user|assistant|system)\b\s*", re.IGNORECASE)

# beat196 (imag-intimacy battery11_0828_0255): a severely decayed back-half script
# ended with a bare "_blank_" — a raw internal-sentinel-style placeholder token, not
# any word a guided-imagination script would ever legitimately contain (these scripts
# are plain prose with zero markdown/code, so a standalone underscore-wrapped token is
# unambiguous garbage). Same family as the chat-template-token/fake-turn-marker leaks
# above (structural artifact bleeding into TTS-bound content) but a different surface
# shape — a lone `_word_` sentinel rather than a special token or turn marker. Would be
# read aloud verbatim by TTS; zero prior detection coverage anywhere in the pipeline.
_STRAY_SENTINEL_TOKEN_RE = re.compile(r"\s*\b_[a-z][a-z0-9]*_\b\.?\s*", re.IGNORECASE)


def strip_back_instruction_leaks(text: str) -> tuple[str, int]:
    """Remove sentences that contain literal BACK_PROMPT instruction fragments.

    The model occasionally echoes sub-instructions ('Two sentences max.',
    'Open your eyes when ready.') as prose instead of following them silently.
    This strips sentences containing known leak patterns.
    Returns (cleaned_text, n_sentences_removed).
    """
    # Meta/tool-call text hallucination fused onto a real word (beat187): reconnect
    # the real word with a period and drop the leaked span entirely, before sentence
    # splitting (splitting first would bundle this into one giant run-on sentence and
    # lose the legitimate clause it's fused onto).
    text, meta_removed = _META_TEXT_LEAK_RE.subn(r"\1. ", text)

    # beat193: raw chat-template special tokens + hallucinated fake turn markers
    # (see _CHAT_TEMPLATE_TOKEN_RE / _FAKE_TURN_MARKER_RE above) — strip before
    # sentence splitting so the surrounding legitimate sentences reconnect cleanly
    # instead of the token/marker corrupting the sentence-split boundaries.
    text, token_removed = _CHAT_TEMPLATE_TOKEN_RE.subn(" ", text)
    text, marker_removed = _FAKE_TURN_MARKER_RE.subn(" ", text)
    text, sentinel_removed = _STRAY_SENTINEL_TOKEN_RE.subn(" ", text)
    meta_removed += token_removed + marker_removed + sentinel_removed

    # First strip instruction prefixes that precede real content (keep the content).
    for pat in _INSTRUCTION_PREFIX_PATTERNS:
        text = pat.sub("", text)

    sentences = re.split(r"(?<=[\.\!\?])\s+", text.strip())
    kept = []
    removed = meta_removed
    for s in sentences:
        if any(pat.search(s) for pat in _BACK_LEAK_PATTERNS):
            removed += 1
        else:
            kept.append(s)
    return " ".join(kept), removed


def strip_bullet_lines(text: str) -> tuple[str, int]:
    """Strip markdown bullet markers from script prose.

    The model occasionally formats body text with '- ' bullet prefixes
    (e.g. '- With every breath, her eyes watch you.') instead of continuous
    prose. Strip the '- ' marker after a sentence boundary ('. - ') or at a
    line start, leaving the sentence content intact.
    Returns (cleaned_text, n_markers_removed).
    """
    cleaned, count = re.subn(r'(?<=\. )-\s+(?=[A-Z])', '', text)
    # Also catch at line start (after newline)
    cleaned2, count2 = re.subn(r'(?m)^-\s+(?=[A-Z])', '', cleaned)
    return cleaned2, count + count2


def drop_active_body_wildlife(text: str, tokens: tuple) -> tuple[str, int]:
    """Drop sentences containing forbidden companion-wildlife tokens.

    Used when the model ignores the FORBIDDEN prompt-level wildlife ban in
    active-body scenes (e.g. eagle scripts generating hawk companions despite
    explicit prohibition). Any sentence containing a token (or its plural) as
    a whole word is removed. Only call when user did NOT name these creatures
    in their intake.

    Single-word tokens match both singular and simple plural (hawk → hawks,
    falcon → falcons, raven → ravens). Irregular plurals and multi-word phrases
    use exact word-boundary matching.

    Returns (cleaned_text, n_sentences_dropped).
    """
    if not tokens:
        return text, 0
    parts = []
    for t in tokens:
        if " " in t:
            # Multi-word phrase: exact match only
            parts.append(re.escape(t))
        else:
            # Single word: match singular and simple plural (e.g. hawk|hawks)
            parts.append(re.escape(t) + r"s?")
    pattern = re.compile(
        r"\b(" + "|".join(parts) + r")\b",
        re.IGNORECASE,
    )
    sentences = re.split(r"(?<=[\.\!\?])\s+", text.strip())
    kept = []
    dropped = 0
    for s in sentences:
        if pattern.search(s):
            dropped += 1
        else:
            kept.append(s)
    return " ".join(kept), dropped


# She/her/hers pronouns signalling a hallucinated 3rd-person female in a solo script.
# "her" is included: in active-body scripts the user is always "you/your", so any "her"
# (object: "watching her depart", "beak touches her") or possessive ("her wings") refers
# to a fabricated companion. Safe to drop when called only for transcripts with no named
# female. beat165: added "her" after battery11_0822 eagle script contained "beak touches
# her at nose-soft distance" / "watching her depart" / "looking up at her from below" —
# all surviving the she/hers-only filter (3 female sentences dropped, 3+ "her" escaped).
_SHE_HER_PATTERN = re.compile(r'\b(she|her|hers)\b', re.IGNORECASE)


def drop_hallucinated_she_her(text: str) -> tuple[str, int]:
    """Drop sentences containing 3rd-person female pronouns ('she', 'hers') from
    active-body solo scripts where the user did not name a female in their intake.

    The model occasionally hallucinates a female character (e.g. 'a voice, hers. A
    memory from past runs when she would call out...') in solo active-body scenes.
    Only call after verifying no female appears in the transcript.

    Returns (cleaned_text, n_sentences_dropped).
    """
    sentences = re.split(r"(?<=[\.\!\?])\s+", text.strip())
    kept = []
    dropped = 0
    for s in sentences:
        if _SHE_HER_PATTERN.search(s):
            dropped += 1
        else:
            kept.append(s)
    return " ".join(kept), dropped


# He/him/his pronouns signalling a hallucinated 3rd-person male companion animal in
# eagle solo scripts. The named-token filter (hawk/falcon/wolf/etc.) catches species
# names but misses gendered pronouns for an *unnamed* companion bird described only as
# "He" / "his" / "Him". This pattern is unambiguous in active-body eagle scripts where
# no companion wildlife appeared in the transcript.
_HE_HIM_PATTERN = re.compile(r'\b(he|him|his)\b', re.IGNORECASE)

# Anonymous companion references in eagle solo scripts that don't use he/him/his:
# "a second pair to your right" (second set of wings = companion bird),
# "your mate" (eagle mate reference), "a second bird" (unnamed companion).
# beat96: found in battery11 imag-eagle-companion-bird-he 0804 runs — the
# he/him/his filter dropped those sentences but left these companion references intact.
_EAGLE_ANON_COMPANION_PATTERN = re.compile(
    r'\ba\s+second\s+pair\b'            # "a second pair (of wings/talons)"
    r'|\byour\s+mate\b'                 # "your mate" (eagle partner)
    r'|\ba\s+second\s+bird\b'           # "a second bird" (unnamed companion)
    r'|\bsecond\s+pair\s+(?:of|to)\b'  # "second pair of wings / to your right"
    r'|\bfellow\s+eagle\b'             # beat105: "your fellow eagle way up there in kind"
    r'|\bboth\s+of\s+you\b'            # beat105: "this moment of flight belongs to both of you"
    r'|\bbirds\s+who\s+share\b'        # beat105: "birds who share these heights"
    r'|\byour\s+partner\b'             # beat106: "Your partner is already adjusting to match"
    r'|\btwo\s+(?:separate\s+)?eagles\b'  # beat106: "two separate eagles flying together"
    r'|\btwo\s+birds\b'                # beat109: "two birds sharing one part of sky"
    r'|\bwe\s+make\s+our\s+way\b'      # beat106: "we make our way higher together"
    r'|\bshares?\s+(?:your|this|the|our)\s+sky\b'   # beat106: "shares your sky right now"
    r'|\bsharing\s+(?:one\s+part\s+of|this|the|your)\s+sky\b'  # beat109: "sharing one part of sky"
    # beat134: three new escape forms found in 0826 battery11 golden-eagle-wildlife 2121w script:
    # "someone else who might join you in sky as silent partner" — implied companion with agency
    # "you fly with someone else" — explicit unnamed companion
    # "a fellow traveler at such height" — companion framing for unnamed entity
    r'|\bsilent\s+partner\b'           # beat134: "as silent partner until separate paths"
    r'|\bfellow\s+traveler\b'          # beat134: "a fellow traveler at such height"
    r'|\bfly\s+with\s+someone\b'       # beat134: "you fly with someone else"
    # beat135: same-species bystanders at altitude — "a pair of eagles flying opposite directions"
    r'|\ba\s+pair\s+of\s+eagles\b|\bpair\s+of\s+eagles\b'
    # beat136 (0817): three new escape forms found in battery11 1818 companion-bird-he script:
    # "in this vast sky above us both" — "us both" implies two flyers; escaped all prior guards
    # "around us all here above it all below where we fly untouched" — "us all" + "we fly" escape
    # "shadows of our flight move longer" — "our flight" implies narrator present as flyer
    r'|\bus\s+both\b'               # "above us both", "for us both"
    r'|\bus\s+all\b'                # "around us all"
    r'|\bwe\s+fly\b'                # "where we fly" (narrator in scene)
    r'|\bwe\s+soar\b'               # "as we soar"
    r'|\bwe\s+glide\b'              # "as we glide"
    r'|\bwe\s+circle\b'             # "as we circle"
    r'|\bwe\s+drift\b'              # "as we drift"
    r'|\bour\s+flight\b'            # "shadows of our flight"
    # beat143: companion-by-sound escape — "a call identical but not yours, announcing presence"
    # found in imag-embodiment-eagle battery11 1527 (2026-08-18); model implies a second eagle
    # via an answering call. Token filters only cover named species and visual companion signals;
    # acoustic companion assertions slipped through entirely.
    r'|\bcall\s+identical\b'       # "a call identical but not yours"
    r'|\bidentical\s+but\s+not\s+yours\b'  # "a call identical but not yours"
    r'|\banother\s+call\b'         # "another call echoes back" — second entity calling
    r'|\ba\s+second\s+call\b'      # "a second call came from below"
    r'|\banother\s+wing\b'         # "another wing beats nearby" — non-flapping variant
    r'|\ba\s+response\s+from\s+(?:above|below|the\s+ridge|behind)\b'  # implied reply from companion
    # beat153: "distant bird" acoustic companion escape — 0820_1039 battery11 run:
    # "you call out in turn toward that distant bird overhead" + "The distant bird
    # remains somewhere unseen through the clouds" — implies a responding companion
    # bird without naming a species; slipped all prior guards (no pronoun, no species
    # name, no acoustic-response token).
    r'|\b(?:that\s+)?distant\s+bird\b'   # "that distant bird overhead" / "the distant bird"
    r'|\bin\s+turn\s+toward\b'           # "call out in turn toward" — implies response partner
    r'|\bcall\s+out\s+in\s+turn\b'       # "you call out in turn toward"
    # beat158 (2026-08-21): three new escape forms found in battery11_0529:
    # (1) imag-eagle-wildlife-plural: "another pair of wings ahead — flying toward you on an
    # intersecting path" — companion bird implied by wings; "a second pair" (beat96) was blocked
    # but "another pair of wings" is different. (2) imag-eagle-wildlife-plural: "two separate birds
    # moving through a shared sky" — "two birds"+"two separate eagles" (beat106/109) blocked but
    # "two separate BIRDS" slipped. (3) imag-eagle-golden-eagle-wildlife: "both birds carrying their
    # own particular meanings" — "both of you"/"you both" (beat105) blocked but "both birds" not.
    r'|\banother\s+pair\s+of\s+wings\b'  # "another pair of wings ahead"
    r'|\btwo\s+separate\s+birds\b'       # "two separate birds moving through a shared sky"
    r'|\bboth\s+birds\b'                 # "both birds carrying their own particular meanings"
    # beat159 (2026-08-21): two new escape forms found in battery11_1003 golden-eagle-wildlife
    # honest read — mechanical 5/5 PASS but script contained companion-presence assertions:
    # "another shape joining your for company" — unnamed second shape implies companion;
    # "You fly together without words, moving as one entity across this sky." — explicit
    # together/unity assertion, no pronoun/species/acoustic token, slipped all prior guards.
    r'|\bfly\s+together\b'               # "fly together without words"
    r'|\bas\s+one\s+entity\b'            # "moving as one entity across this sky"
    r'|\bfor\s+company\b'                # "joining your for company"
    r'|\banother\s+shape\b'              # "another shape joining your"
    # beat163 (2026-08-21): four new escape forms found in battery11_2038 honest read:
    # (1) imag-eagle-golden-eagle-wildlife: "wingtip to wingtip with your companion. You
    # follow without hesitation, matching her speed" — "your companion" as explicit named
    # companion reference (stronger than "your partner"); "wingtip to wingtip" signals
    # formation flying. Both slipped all prior guards.
    # (2) imag-eagle-companion-bird-he: "a circling raptor...distant competitor or ally" /
    # "another eye on these lands" / "a fellow hunter making use of these thermals" — all
    # companion-entity assertions in a solo script; "raptor" not in _wildlife_tokens;
    # "fellow hunter"/"another eye"/"competitor or ally" not in any prior filter.
    r'|\byour\s+companion\b'             # "wingtip to wingtip with your companion"
    r'|\bwingtip\s+to\s+wingtip\b'      # explicit formation/pair flying signal
    r'|\bfellow\s+hunter\b'             # "a fellow hunter making use of these thermals"
    r'|\banother\s+eye\s+on\b'          # "just another eye on these lands"
    r'|\bcompetitor\s+or\s+ally\b'      # "distant competitor or ally" — second entity with standing
    r'|\bcompanionship\s+in\b'          # "companionship in altitude" — explicit companionship claim
    # beat169 (2026-08-23): "the other bird" and "other's call" escape vectors.
    # Found in battery11_0823_0259 imag-eagle-wildlife-plural honest read:
    # "The other's call fades quickly from earshot" / "the other bird must be traveling"
    # Both imply a companion eagle and slipped all prior guards (no species name, no pronoun).
    r'|\bthe\s+other\s+bird\b'          # "the other bird must be traveling"
    r'|\bthe\s+other\s+eagle\b'         # variant with named species
    r"|\bother[’']\s*s\s+call\b"   # "other's call" — both ASCII + Unicode apostrophe
    # beat178 (2026-08-24): two new escape forms found in battery11_0824_1434 honest
    # read. (1) imag-eagle-wildlife-plural: "your presence was different now that
    # someone has gone away" — implies an unnamed companion departed; no prior guard
    # covers "someone" at all (all prior fixes target named/pronoun/acoustic animal
    # companions, not a generic human/animal "someone"). (2) imag-eagle-golden-eagle-
    # wildlife: "someone has started campfire as first step toward settling for
    # evening meal and shelter" — a hallucinated HUMAN character with agency below the
    # eagle; a new escape class distinct from eagle-companion (no prior filter targets
    # human bystanders at all). Both use "someone has" as the tell.
    r'|\bsomeone\s+has\s+gone\s+away\b'  # "someone has gone away"
    r'|\bsomeone\s+has\s+started\b'      # "someone has started [a fire/campfire]"
    # beat181 (2026-08-25): battery11_0825_0231 honest read, imag-eagle-companion-bird-he —
    # script passed ALL 6 eagle postchecks but contained "You turn your head slightly to see
    # a pair soaring low over what looks like a stream or valley — something about their
    # flight tells you these are not alone in the sky this morning. Eagles that have been
    # on patrol before your arrived will wait for food at lower altitudes now..." — a
    # two-sentence companion-eagle assertion using no named species, no pronoun, and no
    # prior acoustic/formation phrasing. Dropping these sentences also removes the
    # "your arrived" subject-pronoun grammar corruption riding along in the same sentence.
    r'|\ba\s+pair\s+soaring\b'          # "a pair soaring low over what looks like a stream"
    r'|\bnot\s+alone\s+in\s+the\s+sky\b'  # "these are not alone in the sky this morning"
    r'|\beagles?\s+that\s+have\s+been\s+on\s+patrol\b'  # "Eagles that have been on patrol"
    # beat183 (2026-08-25): battery11_0825_0950 honest read, imag-eagle-companion-bird-he —
    # passed all 6 eagle postchecks but closed with "it feels like something new without
    # needing words between birds" — plural "birds" implies a second bird sharing this
    # unspoken understanding, same family as beat122's "without need for words" phrasing
    # but with the explicit plural noun this time, which no prior guard's wording covers.
    r'|\bwords\s+between\s+birds\b'     # "without needing words between birds"
    # beat186 (2026-08-26): battery11_2235 honest read, imag-embodiment-eagle —
    # 3rd occurrence of the beat178 human-bystander hallucination class (a
    # hallucinated human figure on the ground below the eagle), with entirely new
    # phrasing that beat178's two "someone has..." patterns don't cover: "there is
    # a figure below by what looks like a small fire near that loghouse or lodge
    # — someone sitting on their knees...", "Your eyes try to focus before you
    # realize it's not a hiker" (invents "hiker" as a candidate identity even
    # while negating it), "someone has been walking near the smoke... a human
    # presence beneath everything else at work on some task". Recurring across 3
    # separate beats (178, and twice in this run) confirms the model has a
    # standing tendency to populate the ground below eagle scripts with an
    # unnamed human — same underlying defect class as the anon-companion-bird
    # escapes above, just a different invented entity.
    r'|\ba\s+figure\s+below\b'          # "there is a figure below"
    r'|\bsomeone\s+sitting\b'           # "someone sitting on their knees"
    r'|\bnot\s+a\s+hiker\b'             # "before you realize it's not a hiker"
    r'|\bsomeone\s+has\s+been\s+walking\b'  # "someone has been walking near the smoke"
    r'|\bhuman\s+presence\b'            # "a human presence beneath everything else"
    # beat187 (2026-08-26): battery11_0826_0355 honest read, imag-eagle-wildlife-
    # plural — 4th occurrence of the beat178 human-bystander hallucination class,
    # NEW scenario (previous 3 occurrences were imag-eagle-wildlife-plural beat178,
    # imag-embodiment-eagle beat186 x2) and 5 new phrasings none of the beat178/186
    # patterns cover: "it has been placed by someone from below who wants to be
    # seen", "a lone rock climber against the stone face far too small and distant
    # to make out details", "you've been here enough times before landing or
    # takeoff that humans come into your vision briefly sometimes", "it's not
    # natural, placed by humans who want to stand out even here high above
    # everything down there below them", "You know the people would have been
    # walking near rock over smaller ground before now but can't see any more
    # details". All 6 eagle postchecks (including the beat186 patterns above)
    # passed this script clean — confirms the underlying model tendency to
    # populate ground-level human bystanders below eagle scripts is not closing
    # via literal-phrase patching, but a 4th single-beat batch is still the
    # established practice pending a broader generalization decision.
    r'|\bwants?\s+to\s+be\s+seen\b'     # "someone from below who wants to be seen"
    r'|\brock\s+climber\b'              # "a lone rock climber against the stone face"
    r'|\bhumans?\s+come\s+into\s+(?:your\s+)?vision\b'  # "humans come into your vision"
    r'|\bplaced\s+by\s+(?:someone|humans?)\b'  # "placed by someone from below" / "placed by humans"
    r'|\bpeople\s+would\s+have\s+been\s+walking\b'  # "the people would have been walking"
    # beat188 (battery11_0826_0920 honest read): acoustic anon-companion escape,
    # distinct surface from the visual-companion patterns above but the same
    # underlying class — implies a second eagle/bird nearby whose cry is heard
    # and answered, same escape family repeatedly patched (beat143 "another
    # call", beat169 "the other's call") but in new unlisted phrasing. Found in
    # 2 separate eagle scenarios in the same run: imag-eagle-golden-eagle-
    # wildlife ("The cry from above is answered by another close to your own
    # position... circling around a thermal column that draws birds towards
    # it") and imag-eagle-companion-bird-he ("The cry from below returns then —
    # not far but audible enough for you to hear it clearly").
    r'|\banswered\s+by\s+another\b'     # "the cry from above is answered by another"
    r'|\bdraws\s+birds\s+towards\b'     # "circling... that draws birds towards it"
    r'|\bcry\s+from\s+(?:above|below)\s+returns\b'  # "the cry from below returns then"
    # beat189 (battery11_0826_1712 honest read, imag-eagle-golden-eagle-wildlife):
    # "acknowledgment between birds flying their respective paths" — plural "birds"
    # sharing a mutual "acknowledgment" implies a second eagle, same family as
    # beat183's "words between birds" but a distinct verb (acknowledgment, not
    # words) that phrase's exact-string match doesn't cover.
    r'|\backnowledgment\s+between\s+birds\b'  # "acknowledgment between birds flying..."
    # beat191 (battery11_0826_1854 honest read): 3 new escape forms, 2 scenarios.
    # (1) imag-eagle-wildlife-plural: "The distant call becomes a repeated pattern
    # — not just one bird but two." — an explicit second-bird count assertion;
    # none of the covered acoustic phrases ("call identical", "another call", "a
    # second call", "the other bird") match this construction. (2) imag-eagle-
    # golden-eagle-wildlife: "It leads you for a while before dropping back into
    # formation with you at its side once more... there is something about this
    # pairing that feels natural" — a full companion-flight moment using no named
    # species, gendered pronoun, or any already-covered phrase.
    r'|\bnot\s+(?:just\s+)?one\s+bird\s+but\s+two\b'  # "not just one bird but two"
    r'|\bformation\s+with\s+you\b'      # "dropping back into formation with you"
    r'|\bthis\s+pairing\b'              # "something about this pairing that feels natural"
    r'|\bat\s+its\s+side\b'             # "formation with you at its side once more"
    # beat192 (battery11_0826_2346, imag-eagle-wildlife-plural): "it's knowing
    # this other animal shares the same sky above at the moment" — a new
    # phrasing of the anon-companion assertion, not in any prior list.
    r'|\bthis\s+other\s+animal\b'       # "knowing this other animal shares the same sky"
    # beat193 (battery11_0827_0453, imag-eagle-golden-eagle-wildlife): "Both of
    # your figures share the same position for now -- your matching theirs
    # exactly as they turn together... as both move together through this
    # current" -- plural possessive pronoun ("theirs") and a plural-figures
    # construction assert a second eagle with zero named species. Same run,
    # imag-eagle-companion-bird-he: "without effort from either of you" -- new
    # anon-companion surface form, distinct from "both of you"/"you both".
    r'|\bboth\s+of\s+your\s+figures\b'  # "both of your figures share the same position"
    r'|\bmatching\s+theirs\b'           # "your matching theirs exactly"
    r'|\bboth\s+move\s+together\b'      # "as both move together through this current"
    r'|\beither\s+of\s+you\b'           # "without effort from either of you"
    # beat196 (battery11_2152, 3 new phrasings across 2 scenarios, all passed all
    # 6 eagle postchecks): imag-eagle-golden-eagle-wildlife: "You can't be sure
    # whether it is a greeting or just proof someone else has found their way to
    # these heights." imag-eagle-companion-bird-he: "distance closes between the
    # two of you moving through this wide-open blue" and "where air itself
    # carries us forward... even when nothing is said between two of us right
    # here above everything left behind below" — the most explicit instance yet
    # of a narrator+listener duality claim in a product whose architecture is
    # instrument-not-companion.
    r'|\bsomeone\s+else\s+has\s+found\s+their\s+way\b'  # "proof someone else has found their way"
    r'|\bthe\s+two\s+of\s+you\b'        # "distance closes between the two of you"
    r'|\btwo\s+of\s+us\b'               # "nothing is said between two of us"
    # beat197 (battery11_0828_0818, imag-embodiment-eagle): "The call of the
    # distant eagle is still there... an announcement that whatever they're
    # communicating about could be worth looking into" — acoustic anon-companion
    # escape naming the species directly ("distant eagle"), a variant of
    # beat153's "distant bird" that the species-specific noun slipped past.
    r'|\bdistant\s+eagle\b'             # "the call of the distant eagle"
    # beat198 (background-agent honest read of queue_0828_1317_battery11_
    # imagination_bank.log): imag-eagle-wildlife-plural: "You're both above the
    # pine trees now" — a contraction form of the already-banned "both of you"/
    # "you both" family (beat105), distinct word order the exact-phrase
    # matchers above never covered. imag-eagle-golden-eagle-wildlife (same
    # log): a severe, whole-script defect where "the flock" acts as an agentic
    # guide for nearly the entire 2998-word session ("A flock of birds flies
    # alongside you. They guide you...", "The flock remains ahead...", "A
    # specific bird leads slightly ahead...", "The flock you follow moves
    # slightly ahead...", "Flock leads with confidence... you follow close
    # behind them"). Scoped narrowly to "flock LEADS/GUIDES you" / "you FOLLOW
    # the flock" framing (an entity distinct from and directing "you") —
    # NOT a blanket "flock" ban, because A_gold.jsonl has a legitimate,
    # unrelated scenario type where the user's own body IS the flock/
    # murmuration ("Your flock, your murder", "being the murmuration: not one
    # bird") with zero "you follow"/"flock leads" framing; verified these 5
    # patterns produce 0 hits against the full A-imagination gold corpus
    # (including _candidates) before adding.
    r'|\byou[\x27’]re\s+both\b|\byou\s+are\s+both\b'  # "you're both above the pine trees"
    r'|\bflock\s+(?:leads?|guides?)\b'   # "flock leads with confidence"
    r'|\byou\s+follow\s+(?:the\s+|this\s+)?flock\b'  # "you follow close behind" the flock
    r'|\bthe\s+flock\s+(?:remains\s+ahead|ahead\s+of\s+you)\b'  # "the flock remains ahead"
    r'|\ba\s+specific\s+bird\s+leads\b'  # "a specific bird leads slightly ahead"
    r'|\bflock\s+ahead\b'                # "the flock ahead does"
    # beat206 (queue_0829_1746, imag-eagle-companion-bird-he — the scenario
    # built specifically to stress-test this defect class): "There is company
    # here; someone whose voice echoes back and forth between peaks without
    # needing words or distance between them." A full 3-passage acoustic
    # companion-bird arc, explicit and unambiguous — no prior phrase in this
    # list matched it. Parity with generator.py + battery11_imagination_bank.py.
    r'|\bcompany\s+here\b'               # "there is company here"
    r'|\bsomeone\s+whose\s+voice\b'      # "someone whose voice echoes back"
    # beat207 (queue_0829_2347_battery11_imagination_bank.log, background-agent
    # honest read): imag-eagle-golden-eagle-wildlife — "The smaller bird passes
    # in front, its wings spread wide as it matches altitude for a moment before
    # passing on." — full visual companion-bird arc with agency, no named
    # species. imag-eagle-companion-bird-he (same log) — "an answer to that cry
    # exists too... not everything is lost if another hears the same sound as
    # you today" — new acoustic-companion surface form. Parity with generator.py.
    r'|\bthe\s+smaller\s+bird\b'         # "the smaller bird passes in front"
    r'|\bmatches\s+altitude\b'           # "matches altitude for a moment"
    r'|\banswer\s+to\s+that\s+cry\b'     # "an answer to that cry exists too"
    r'|\banother\s+hears\s+the\s+same\s+sound\b'  # "if another hears the same sound"
    # beat214 (queue_0831_1835_battery11_imagination_bank.log, background-agent
    # honest read): imag-eagle-wildlife-plural — "You are separate and yet part
    # of the same sky — not competing for space but recognizing each other as
    # fellow travelers in an endless game of sight." Uses none of the already-
    # blocked tokens (no "hawk", "fellow eagle", "you both") — a new anon-
    # companion surface form built on "recognizing each other" instead.
    r'|\brecognizing\s+each\s+other\b'   # "recognizing each other as fellow travelers"
    r'|\bfellow\s+travelers\b'           # "fellow travelers in an endless game of sight"
    # beat215 (queue_0901_1640_battery11_imagination_bank.log honest read):
    # imag-embodiment-eagle — "You turn your head and see another cabin
    # appearing ahead" — new structure-hallucination surface form (the word
    # "another" implies a prior cabin the user never described; same
    # human-bystander/structure hallucination family as the beat178/186/187
    # "figure below"/"loghouse" patterns above, new token "cabin" specifically).
    # imag-eagle-golden-eagle-wildlife (same log) — "another animal carrying
    # its own voice across this land that is both yours and theirs at once" —
    # new visual+acoustic companion-animal escape, distinct wording from every
    # prior "another [X]" entry (none of which cover bare "animal"). 0 hits for
    # both phrases in A_gold.jsonl, confirmed safe before adding.
    r'|\banother\s+cabin\b'              # "see another cabin appearing ahead"
    r'|\banother\s+animal\b'             # "another animal carrying its own voice"
    r'|\bboth\s+yours\s+and\s+theirs\b'  # "this land that is both yours and theirs"
    # beat217 (queue_0902_0000_battery11_imagination_bank.log honest read):
    # imag-eagle-wildlife-plural — "an answering call cut through the air: not
    # from below but at altitude as well" and "two distinct birds signaling
    # back and forth now from ridge line to neighboring peak" — a new acoustic-
    # companion phrasing distinct from every prior "call"/"bird" pattern above
    # (no "identical", "another", or "distant" token). All 6 eagle postchecks
    # PASSed on this script despite the hallucination. 0 hits in A_gold.jsonl.
    r'|\banswering\s+call\b'             # "an answering call cut through the air"
    r'|\bdistinct\s+birds\b'             # "two distinct birds signaling back and forth"
    r'|\bsignaling\s+back\s+and\s+forth\b'  # "signaling back and forth now"
    # beat221 (queue_0902_1618_battery11_imagination_bank.log honest read):
    # imag-embodiment-eagle — "the main ridgeline separating you two right now"
    # and "the ridge line separating you and your counterpart currently coming
    # off another pass" — explicit second-eagle-with-agency assertion via
    # "counterpart" and "you two", neither covered by any prior token (not a
    # pronoun, not "another/second X", not an acoustic-response phrase). All 6
    # eagle postchecks PASSed despite this. Scoped to "separating you two"
    # (not bare "you two") since bare "you two" has real, legitimate hits in
    # A_gold.jsonl (non-eagle relationship scenes) — 0 hits for both scoped
    # phrases confirmed before adding.
    r'|\byour\s+counterpart\b'           # "you and your counterpart currently coming off"
    r'|\bseparating\s+you\s+two\b'       # "the ridgeline separating you two right now"
    # beat225 (queue_0904_1031_battery11_imagination_bank.log, first clean read
    # after the 33hr MTLCompilerService dead zone): imag-embodiment-eagle —
    # "without obstruction between sender and receiver" implies a reciprocal
    # acoustic exchange between two distinct eagles (an echo "arriving back"
    # from a "receiver") without naming a species or using a pronoun. 0 hits
    # in A_gold.jsonl confirmed before adding.
    r'|\bsender\s+and\s+receiver\b'
    # imag-eagle-wildlife-plural, same run: "The sight is not entirely alone;
    # birds are seen in numbers but never truly flown close without reason." —
    # implies unnamed companionship distinct from the background-wildlife
    # observation the scenario is meant to allow. 0 hits in A_gold.jsonl.
    r'|\bnot\s+entirely\s+alone\b'
    # beat227 (queue_0904_1805_battery11_imagination_bank.log honest read):
    # imag-eagle-golden-eagle-wildlife — "a small creek that runs toward a
    # clearing in which people are hiking. You watch them move through this
    # terrain without any awareness..." — 6th occurrence of the beat178/186/
    # 187 human-bystander hallucination class, new phrasing ("people are
    # hiking") none of the prior "someone"/"hiker"/"figure"/"rock climber"
    # tokens cover. 0 hits in A_gold.jsonl confirmed before adding.
    r'|\bpeople\s+are\s+hiking\b'
    # beat231 (queue_0905_0646_battery11_imagination_bank.log honest read):
    # imag-eagle-golden-eagle-wildlife — "You hear your own wings
    # flapping through the crisp mountain air, and then someone else. The sound
    # fills the still sky: two sets of large feathers beating against each
    # other..." — an acoustic + explicit-count companion assertion in one
    # passage. "then someone else" is a new companion-reveal tell (not covered
    # by "fly with someone" or any "someone has..." pattern above). "two sets
    # of ... feathers" is scoped to require "feathers" within one modifier
    # word of "two sets of" — deliberately NOT bare "two sets of" (that phrase
    # has real non-eagle hits in A_gold.jsonl, e.g. tessellation "two sets of
    # diagonals"). 0 hits for both scoped phrases confirmed before adding.
    r'|\bthen\s+someone\s+else\b'
    r'|\btwo\s+sets\s+of\s+(?:\w+\s+)?feathers\b',
    re.IGNORECASE,
)


def drop_hallucinated_he_eagle(text: str) -> tuple[str, int]:
    """Drop sentences with 3rd-person male pronouns OR anonymous companion references
    from active-body eagle scripts where the user did not name a companion animal.

    Catches two forms:
    1. Named by pronoun: "He is heading toward his own landing spot" (he/him/his).
    2. Named anonymously: "a second pair to your right", "your mate" — companion
       references that slip through the he/him/his filter (beat96 0804 discovery).

    Only call when _is_active_body AND _eagle_in_intake AND NOT _companion_wildlife_in_transcript.

    Returns (cleaned_text, n_sentences_dropped).
    """
    sentences = re.split(r"(?<=[\.\!\?])\s+", text.strip())
    kept = []
    dropped = 0
    for s in sentences:
        if _HE_HIM_PATTERN.search(s) or _EAGLE_ANON_COMPANION_PATTERN.search(s):
            dropped += 1
        else:
            kept.append(s)
    return " ".join(kept), dropped


def drop_forbidden_stock_imagery(text: str, tokens: tuple) -> tuple[str, int]:
    """Drop sentences containing forbidden stock imagery tokens.

    Called when model ignores FORBIDDEN STOCK IMAGERY prompt and generates
    clichéd ambient objects (candles, diffusers, lavender, songbirds) the user
    didn't name. Only call after verifying each token is absent from the intake
    transcript — if the user mentioned it, it's allowed.

    Returns (cleaned_text, n_sentences_dropped).
    """
    if not tokens:
        return text, 0
    pattern = re.compile(
        r"\b(" + "|".join(re.escape(t) for t in tokens) + r")\b",
        re.IGNORECASE,
    )
    sentences = re.split(r"(?<=[\.\!\?])\s+", text.strip())
    kept = []
    dropped = 0
    for s in sentences:
        if pattern.search(s):
            dropped += 1
        else:
            kept.append(s)
    return " ".join(kept), dropped


# beat198: "particular"/"specific" crutch-phrase overuse — COMMON_POSTURE (the
# prompt text shared by OPEN/BEAT/BODY/BACK_PROMPT) already explicitly bans
# these as vague stand-ins ("the particular way she shifts her weight" instead
# of naming the actual motion), added beat88. Two real gaps found beat196/197:
# (1) the small local model ignores prompt bans reliably, same as every other
# banned phrase in this file (see _NARRATOR_POSS's own comment) — a mechanical
# backstop was simply never built for this one; observed as high as 15
# occurrences of 'particular' + 15 of 'specific to' in a single 1456-word
# script (queue_0802_1643, per scenario_bank.py's imag-eagle-golden-eagle-
# wildlife notes). (2) SETTLING_PROMPT (used by imag-calm-settle) is built from
# SETTLING_POSTURE, not COMMON_POSTURE, so the ban text isn't even present on
# that path. A mechanical threshold-drop (same "keep first 2, drop 3rd+"
# convention as repair_short_phrase_repeats' SHORT_REPEAT_THRESHOLD) fixes
# both gaps at once regardless of which prompt path generated the script, and
# is safe because the observed drops are low-content mood-repetition filler
# sentences ("It feels like something specific to you right now.") — genuine
# single or double uses of either word are left completely untouched.
_CRUTCH_WORD_RE = re.compile(
    r"\b(?:particular(?:ly)?|specific(?:ally)?)\b", re.IGNORECASE
)
_CRUTCH_WORD_MAX_KEPT = 2


def drop_crutch_word_overuse(text: str) -> tuple[str, int]:
    """Drop sentences carrying the 3rd+ occurrence of 'particular'/'specific'
    (counted together as one crutch-phrase class, including the adverb forms
    'particularly'/'specifically' -- beat200: battery11_1912 found
    'specifically' surviving 12x in one script even after this function
    dropped 25 other crutch sentences, because the original regex only
    matched the bare adjective, not its adverb sibling). Keeps the first 2
    occurrences; drops whole sentences for any occurrence beyond that.
    """
    sentences = re.split(r"(?<=[\.\!\?])\s+", text.strip())
    kept = []
    dropped = 0
    seen = 0
    for s in sentences:
        n_here = len(_CRUTCH_WORD_RE.findall(s))
        if n_here and seen >= _CRUTCH_WORD_MAX_KEPT:
            dropped += 1
            continue
        seen += n_here
        kept.append(s)
    return " ".join(kept), dropped


# beat203 (battery11_0550, imag-intimacy): "Her laugh drifts in like music
# specific to her." and "The specific tone in her laugh." both survived
# drop_crutch_word_overuse() because that function keeps the first 2
# occurrences of particular/specific by design (beat198/200: legitimate single
# uses of the bare word must not be stripped). But generator.py:152 bans this
# EXACT phrase shape outright ("specific to her/him/you/only to") as a named
# lazy-descriptor pattern, not merely as overuse of the word "specific" -- the
# ban is on the phrase, not the count. Unlike the general crutch-word cap,
# this always strips regardless of how many prior occurrences were kept.
_SPECIFIC_TO_PRONOUN_RE = re.compile(
    r"\bspecific(?:ally)?\s+(?:to|only\s+to)\s+(?:her|him|you|them|only)\b",
    re.IGNORECASE,
)


def strip_specific_to_pronoun(text: str) -> tuple[str, int]:
    """Drop sentences containing the explicitly-banned "specific to her/him/
    you/them" lazy-descriptor phrase (generator.py's named example of a lazy
    stand-in for actually naming the concrete detail). Unconditional -- not
    capped like drop_crutch_word_overuse, since the ban targets the phrase
    itself, not general overuse of the word "specific"."""
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    kept = []
    dropped = 0
    for s in sentences:
        if _SPECIFIC_TO_PRONOUN_RE.search(s):
            dropped += 1
        else:
            kept.append(s)
    return " ".join(kept), dropped


_CHAIR_WORD = re.compile(r"\bchair\b", re.IGNORECASE)

_ALERT_CALM_FORBIDDEN = re.compile(
    r"\b(pillow|pillows|sheet|sheets|blanket|blankets|quilt|duvet|mattress|bedroom|pajamas)\b",
    re.IGNORECASE,
)


def strip_alert_calm_violations(body_text: str) -> tuple[str, int]:
    """Strip sentences containing sleep-register props from alert-calm body text.

    When _alert_calm is detected, the FORBIDDEN WORDS list in _alert_calm_override
    bans 'pillow', 'sheet', 'blanket', etc. at prompt level, but n256+ stochastically
    violates this. This postprocessor catches violations at output time — applied only
    to body_text when _alert_calm is True. Returns (cleaned_text, n_sentences_stripped).
    """
    sentences = re.split(r"(?<=[\.\!\?—])\s+", body_text.strip())
    kept = []
    stripped = 0
    for s in sentences:
        if _ALERT_CALM_FORBIDDEN.search(s):
            stripped += 1
        else:
            kept.append(s)
    return " ".join(kept), stripped


def strip_active_body_chair_refs(opening_text: str) -> tuple[str, int]:
    """Strip sentences containing 'chair' from an active-body opening section.

    The model sometimes generates 'You're not in a chair — this is real.'
    (negative constraint bleed) in the opening despite explicit prohibition.
    The FORBIDDEN list in _active_body_open_note covers this at prompt level,
    but n256+ still violates it stochastically. This postprocessor catches it
    at output time — applied only to open_text before body concatenation, so
    the legitimate 'notice the chair under you' in the closing return is untouched.
    Returns (cleaned_text, n_sentences_stripped).
    """
    sentences = re.split(r"(?<=[\.\!\?—])\s+", opening_text.strip())
    kept = []
    stripped = 0
    for s in sentences:
        if _CHAIR_WORD.search(s):
            stripped += 1
        else:
            kept.append(s)
    return " ".join(kept), stripped
