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
    r"|\bfor\s+me\s+(?:just|here|now|there|too)\b"  # "for me just watching"
    r"|\bunder\s+me\b"                  # should be "under you"
    r"|\bthrough\s+me\b"               # should be "through you"
    r"|\bwith\s+me\b"                  # should be "with you"
    r"|\bwe\s+(?:started|are\s+now|were\s+both|had\s+been|come\s+back)\b"  # narrator "we" (specific forms)
    r"|\bwe\s+(?:reach|reached|walk|walked|came|come|arrive|arrived|ran|run|go|went|were\s+here|need|sat|sit|stand|stood|move|moved|used\s+to|begin|began|open|opened|return|returned|end|ended|close|closed|start|started|leave|left|lift|lifted|drift|drifted|wake|woke|fade|faded)\b"  # narrator "we" + motion/state verbs
    r"|\bmy\s+(?:hand|hands|breath|side|step|voice|foot)\b"   # narrator body-part possessives
    r"|\bboth\s+of\s+us\b"             # "both of us" narrator collective
    r"|\bfor\s+us\b"                   # "for us" narrator collective
    # Grief-pet dog-POV leak (beat70): model puts listener in animal's body and refers
    # to the human as "your handler" / "your owner" — immediate perspective failure.
    r"|\byour\s+(?:handler|owner|master)\b"
    r"|\bmy\s+(?:handler|owner|master)\b",
    re.IGNORECASE,
)


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
    r"looks|laces|passes|breaks|stops|tells|makes|lets|comes|moves|sits|meets|"
    r"holds|takes|runs|walks|says|goes|sees|knows|wants|needs|leaves|starts|"
    r"becomes|keeps|brings|gets|"
    # Present tense additions (beat86: found in deposition script — 'her asks', 'her has')
    r"asks|has|gives|seems|appears|does|follows|reads|checks|watches|faces|"
    r"sets|puts|uses|calls|feels|shows|opens|closes|pulls|pushes|holds|places|"
    # Past tense forms (most common)
    r"reached|found|stood|turned|met|held|told|said|came|saw|kept|went|"
    r"spoke|broke|ran|took|got|left|made|started|moved|sat|walked|"
    r"entered|searched|passed|stopped|caught|looked|laced|"
    # Past tense additions (beat86)
    r"asked|had|gave|seemed|appeared|did|followed|watched|faced|"
    r"used|called|felt|showed|opened|closed|pulled|pushed|placed)\b",
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


def fix_possessive_pronouns(text: str) -> tuple[str, int]:
    """Replace 'hers NOUN' → 'her NOUN' and 'yours NOUN' → 'your NOUN'.

    The fine-tuned model sometimes generates 'hers own side', 'hers eyes',
    'yours apartment' — using the standalone possessive pronoun as an attributive
    adjective. This is a training artifact caught on n242 and n243 intimate scenes.
    The fix is inline substitution (not sentence-drop) so no content is lost.
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

    text = re.sub(r"\bhers\s+(\w+)", _replace_hers, text, flags=re.IGNORECASE)
    text = re.sub(r"\byours\s+(\w+)", _replace_yours, text, flags=re.IGNORECASE)
    return text, fixed


# "your STATIVE" → "you're STATIVE": model confuses possessive with contraction.
# Only fires for words that cannot be possessed (cannot say "your alone space" etc.).
_YOUR_CONTRACTION_RE = re.compile(
    r"\byour\s+(alone|here|there|gone|done|lost|found|safe|free|ready|okay|ok|fine)\b"
    r"(?!\s+(?:time|space|room|day|moment|self|work|years|hours|life|world|journey|path))",
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


_BACK_LEAK_PATTERNS = [
    re.compile(r"\bTwo sentences max\b", re.IGNORECASE),
    re.compile(r"^Open (?:your eyes )?when ready\b", re.IGNORECASE),
    re.compile(r"\bSoften the image\b", re.IGNORECASE),
    re.compile(r"\bCarry-back\b", re.IGNORECASE),
    re.compile(r"\bRe-room\b", re.IGNORECASE),
    re.compile(r"^Eyes open\b", re.IGNORECASE),
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
    # BACK section meta-commentary: "an imaginary run that was very real" — breaks immersion (beat68 battery11 imag-active-scene)
    re.compile(r"\bimaginary (?:run|session|experience|practice)\b", re.IGNORECASE),
    # Model occasionally hallucinates technical environment details — strip these.
    re.compile(r"\bTTS output device\b", re.IGNORECASE),
    re.compile(r"\btext.to.speech\b", re.IGNORECASE),
]

# Instruction prefixes that leak as a label before real content — strip the prefix only,
# keep the content that follows it (don't drop the whole sentence).
_INSTRUCTION_PREFIX_PATTERNS = [
    re.compile(r"Hard Cut Into The Scene:\s*", re.IGNORECASE),
]


def strip_back_instruction_leaks(text: str) -> tuple[str, int]:
    """Remove sentences that contain literal BACK_PROMPT instruction fragments.

    The model occasionally echoes sub-instructions ('Two sentences max.',
    'Open your eyes when ready.') as prose instead of following them silently.
    This strips sentences containing known leak patterns.
    Returns (cleaned_text, n_sentences_removed).
    """
    # First strip instruction prefixes that precede real content (keep the content).
    for pat in _INSTRUCTION_PREFIX_PATTERNS:
        text = pat.sub("", text)

    sentences = re.split(r"(?<=[\.\!\?])\s+", text.strip())
    kept = []
    removed = 0
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


# She/her subject pronouns that signal a hallucinated 3rd-person female in a solo script.
# "her" alone is excluded — too risky to drop (appears as possessive adjective in
# fix_possessive_pronouns output: "her voice" after "hers voice" fix). Only "she" as
# a subject pronoun and "hers" as a standalone possessive are unambiguous 3rd-person.
_SHE_HER_PATTERN = re.compile(r'\b(she|hers)\b', re.IGNORECASE)


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
    r'|\bboth\s+birds\b',                # "both birds carrying their own particular meanings"
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
