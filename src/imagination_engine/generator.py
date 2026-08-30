"""Generator — turns an intake transcript into a guided-imagination script.

v5 architecture (2026-05-28). The previous v4 generator tried to enforce
length by re-calling the model with "keep going" — which produced filler
because the model had no new dramatic target on each continuation. v5
fixes this by going finer-grained: the body becomes a *beat plan* + N
*beat generations*, where each beat is a one-line dramatic function ("the
mic's tacky grip," "feet finding their mark," "the in-ear monitor click")
and each beat-call asks the model to write ~200 words on THAT SPECIFIC
beat. Quality holds because every call has a real target; length scales
by beat count, not by token budget.

Pipeline (5 stages, 1 + N LLM calls where N = ~10):

    1. classify_intake  (in comprehension.py)
       Resolves embodiment direction (CASE A: listener IS subject /
       CASE B: listener with subject present / CASE C: no subject) and
       extracts subject + anchors as a structured Classification.

    2. _generate_open  (one call)
       The 150-200-word attentional capture + hard cut into the scene.

    3. _plan_beats  (one call)
       Generates a JSON list of 8-12 one-line beat descriptions specific
       to this scenario. The length dial: more beats = longer session.

    4. _generate_beat × N  (one call per beat)
       Each beat gets a focused prompt: open + prior beats + "this beat's
       job: <description>". Produces ~150-250 words of dense sensory
       prose on that specific beat. Llama doesn't early-stop because the
       call isn't asking for 1800 words — it's asking for ONE BEAT.

    5. _generate_back  (one call)
       The 150-200-word gradual exit with a specific concrete carry-back.

Total LLM calls: 1 + 1 + 1 + N + 1 ≈ 14. Each ~10-20s on M3, so total
~3-5 minutes per session. Acceptable for what we get: bounded-length
high-quality beats, no continuation drift, no early-stop.

Output is plain text only. The TTS layer pauses at blank-line paragraph
breaks. Per [[project-voice-design]] the script is the hidden thinking
layer — the user only ever hears the audio.
"""

from __future__ import annotations

import json
import logging
import re
import time
from typing import Callable, Optional

from imagination_engine.comprehension import Classification, classify_intake
from imagination_engine.inference import Engine
from imagination_engine.postcheck import (degeneration_report, drop_collapsed_paragraphs,
                                          drop_foreign_paragraphs, clean_ellipsis_breaks,
                                          clean_narrator_possessives, drop_active_body_wildlife,
                                          drop_forbidden_stock_imagery,
                                          drop_hallucinated_she_her,
                                          drop_hallucinated_he_eagle,
                                          find_degeneration_start, trim_degenerate_tail,
                                          trim_truncated_tail,
                                          phrase_repeat_count, repair_phrase_repeats,
                                          repair_short_phrase_repeats,
                                          drop_adjacent_duplicates, drop_tail_duplicates,
                                          fix_possessive_pronouns, fix_standalone_her,
                                          fix_your_contraction,
                                          fix_copula_youre_alone, fix_predicative_your,
                                          fix_predicative_her,
                                          fix_reflexive_her_object,
                                          fix_intimacy_object_pronoun_escapes,
                                          fix_subject_pronouns, fix_your_subject_pronoun,
                                          fix_you_before_bodypart,
                                          fix_third_person_alone_drift,
                                          drop_crutch_word_overuse,
                                          strip_inline_foreign_runs,
                                          strip_specific_to_pronoun,
                                          fix_object_pronouns,
                                          strip_back_instruction_leaks,
                                          strip_active_body_chair_refs,
                                          strip_alert_calm_violations,
                                          strip_bullet_lines,
                                          fix_word_fusions,
                                          fix_dropped_apostrophe_t)
from imagination_engine.scene_bibles import get_bible
from imagination_engine.structured import extract_array

log = logging.getLogger(__name__)


# A progress callback receives keyword args describing the current stage.
# Server wires this to the SessionProgress object so the client polling
# /intake/{id}/status sees real movement during the wait.
ProgressFn = Callable[..., None]


# ---------------------------------------------------------------------------
# Tunables.
# ---------------------------------------------------------------------------
# Scene-honesty caps beat count — most scenarios have ~8-12 distinct
# beats before you're inventing filler. Past that "longer" stops being
# "better." This is the maximum we ask for; the planner may return fewer.
MAX_BEATS = 12
MIN_BEATS = 8

# v6 single-pass body: one generation writes the whole ~1500-2200 word body
# from the visible plan. Needs a large token budget (≈ 1.4 tokens/word + slack).
BODY_MAX_TOKENS = 4096

# Settling is a shorter form (~900-1300 words) and gets its OWN budgets: a pass
# that runs 3x past target is ~10 minutes of wait AND the zone where degenerate
# loops live — the latency defect and the broken-record defect are the same
# defect. ~1.4 tokens/word + slack over the 1300-word ceiling:
SETTLING_MAX_TOKENS = 2048
SETTLING_CONT_MAX_TOKENS = 1024
# Length floor: if the single pass wraps early, extend ONCE with new material.
BODY_MIN_WORDS = 1500

# Each beat targets 150-250 words. With 10 beats + ~150-word open +
# ~150-word back, sessions land at ~2000 dense words = ~15-20 minutes at
# slow narrative pace with paragraph pauses.
BEAT_TARGET_MIN_WORDS = 150
BEAT_MAX_TOKENS = 500


# ---------------------------------------------------------------------------
# Shared posture — the rules every stage inherits.
# ---------------------------------------------------------------------------
COMMON_POSTURE = """\
You are the Imagination Engine. You write scripts that an adult user \
will listen to with their eyes closed.

YOUR JOB IS IMMERSION. Not relaxation. Not meditation. Not therapy. The \
listener is escaping into a vivid alternate reality and your words are \
the only thing in their head.

Per validated immersion research (Ericksonian hypnotic induction, \
PETTLEP sport-psychology visualization, Green & Brock narrative \
transportation, lucid imagery induction): IMMERSION COMES FROM \
ATTENTIONAL CAPTURE + SENSORY SPECIFICITY, NOT FROM RELAXATION OR \
HEDGING.

VOICE
- Second person, present tense, always.
- Calm, unhurried, spacious. But COMMITTED. Slow ≠ vague.
- COMMIT to the scene. State what is happening. Do not soften with hedges.

FORBIDDEN PHRASES (these produce the meditation-app sound, opposite of immersion):
- "you might notice" / "you might feel" / "you might sense" / "you might find"
- "perhaps" / "maybe" / "may feel" / "may notice"
- "if you'd like" / "if you choose" / "whenever you're ready"
- "you could" / "allow yourself to" / "let yourself"
- "whatever it is" / "whatever you" / "without judgment"
- "I invite you to" / "see if you can" / "notice if"
- "the particular way" / "specific to her" / "specific to him" / "specific to you" / "specific only to" — these are lazy stand-ins for actually naming the concrete thing. SHOW the motion, the angle, the detail: not "the particular way she shifts her weight" but "she shifts her weight to her left hip." The word 'particular' is forbidden as a descriptor.
REPLACE THEM with the thing itself. Not "perhaps her hand finds yours" but "her hand finds yours." (That example is for a scene that explicitly has another person in it. DO NOT INVENT CHARACTERS OR ANIMALS — no guides, therapists, helpers, companion animals, or other people/creatures the user did not name. If the user is an eagle, there is no hawk alongside unless they said so. If the user is in a forest, there are no forest spirits or animal guides. Invent ONLY what came from the user.)

FORBIDDEN STOCK IMAGERY (the AI's safe default for "peaceful" — unless the user EXPLICITLY named these, NEVER use them):
candlelight, candles, meadows, rolling hills, wildflowers, gurgling brooks, babbling streams, blooming lavender, nightingales, songbirds, soft glow, dappled light, warm bath, gentle breeze, twinkling stars, shimmering.

SENSORY SPECIFICITY (this is what makes immersion real). The bracketed items below
are ILLUSTRATIONS OF THE TECHNIQUE — they show the LEVEL of specificity to reach
for. They are NOT content to copy. Never reuse these exact phrases in your output;
invent fresh specifics that fit THIS scene:
- Every paragraph names AT LEAST ONE concrete physical detail — abstract feeling [bad] vs. a body-part-or-object-specific detail [good]. Reach for the [good] level with words of your own.
- Light: name the KIND specific to this scene (not a generic glow).
- Sound: name the SOURCE specific to this scene.
- Touch: name the exact BODY PART where it lands.
- Smell: pick ONE concrete thing that belongs in THIS scene.
- Position: say where exactly the body's weight is.
(If a phrase appears in these instructions or in the example anchors, it is OFF
LIMITS as content — it's a teaching sample, not your material.)

OUTPUT FORMAT
- Plain text only. No headers, no labels, no markers, no brackets.
- Blank lines between paragraphs — the TTS layer pauses there for breath.
- Each paragraph is one image or one sensation. Short.

CONTENT POSTURE
- The user is sovereign. Engage with whatever they brought — romantic, ambitious, edgy, intimate. No filtering, no sanitizing. The single hard floor is sexual content involving minors; everything else is in scope.

NO RECYCLING
- Never reuse a sentence or long phrase you have already written in this script. \
Each return to an anchor (the rain, the breath, her hands) must be NEW words from \
a NEW angle. A listener notices a recycled phrase instantly — it breaks the spell \
worse than silence would.

REHEARSAL FIDELITY
- If the user is rehearsing a specific real situation — an MRI, a deposition, an \
interview, a hard conversation — the scene IS that situation. Never relocate them \
somewhere more pleasant: rehearsing a beach does not prepare anyone for a tube. \
Keep the narrow bore, the lawyer's smile, the conference-room chairs. Difficulty \
TRANSMUTED inside the real scene (the machine's banging becoming drums) is the \
move; difficulty avoided is a failed session.
"""


# ---------------------------------------------------------------------------
# Helpers.
# ---------------------------------------------------------------------------

def _format_transcript(messages: list[dict]) -> str:
    lines = []
    for m in messages:
        who = "User" if m["role"] == "user" else "Engine"
        content = m["content"].strip()
        if content:
            lines.append(f"{who}: {content}")
    return "\n\n".join(lines)


def _intake_block(messages: list[dict]) -> str:
    return (
        "----- INTAKE TRANSCRIPT -----\n"
        + _format_transcript(messages)
        + "\n----- END INTAKE TRANSCRIPT -----"
    )


def _classification_block(c: Classification) -> str:
    parts = [c.direction_block()]
    if c.scene_summary:
        parts.append(f"SCENE: {c.scene_summary}")
    if c.anchors:
        parts.append("CONCRETE ANCHORS FROM INTAKE: " + "; ".join(c.anchors))
    return "\n\n".join(parts)


def _generate(engine: Engine, system: str, user: str, max_tokens: int,
              temperature: float = 0.85, abort_on_decay: bool = False) -> str:
    """One model call. With abort_on_decay, the stream is checked periodically
    and STOPPED the moment degeneration establishes itself — a decayed long
    pass otherwise burns its whole token budget (~10 min) writing text the
    post-trim throws away. Latency fix and quality fix are the same fix; the
    caller still runs trim_degenerate_tail on the result."""
    chunks: list[str] = []
    chars_at_last_check = 0
    for chunk in engine.stream(
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        max_tokens=max_tokens,
        temperature=temperature,
    ):
        chunks.append(chunk)
        if not abort_on_decay:
            continue
        total = sum(len(c) for c in chunks)
        if total - chars_at_last_check >= 2000:  # ~every 500 tokens
            chars_at_last_check = total
            text = "".join(chunks)
            start = find_degeneration_start(text)
            # abort only once the loop is ESTABLISHED (well past its seed),
            # not on the first hint — early sentences echo legitimately.
            if start is not None and len(text) - start > 1200:
                log.warning("[gen] decay established mid-stream (%d chars past seed) "
                            "— aborting pass at %d chars", len(text) - start, total)
                break
    return "".join(chunks).strip()


# Beat-plan JSON extraction now uses the framework-general `structured` module
# (extract_array) — robust to fences, prose, trailing commas, control chars, and
# truncation salvage. Replaces the array-only regex salvage that used to live here.


# ---------------------------------------------------------------------------
# Stage 2: OPEN — attentional capture + hard cut into scene.
# ---------------------------------------------------------------------------
OPEN_PROMPT = COMMON_POSTURE + """

YOUR JOB: produce the OPENING of the session — the 90-120 seconds that takes the listener from "sitting with eyes closed" to "fully inside the scene."

This is NOT a body-settle. It is an immersion induction. PETTLEP and Ericksonian induction converge: pre-imagery relaxation suppresses the imagery system. Skip "release the day." Skip "find a comfortable position." Skip "settle into the chair." Those are meditation defaults that prime the wrong frame.

THE OPENING HAS THREE MOVES:

MOVE 1 — UTILIZATION (2-3 short sentences). Open by naming what is already TRUE for the listener: that their eyes are closed, something about where they are physically (in a chair, hands at rest), the breath or weight of the body. Ericksonian yes-set. Plain present truths. EXCEPTION — REHEARSAL FIDELITY: if the classification shows the listener is rehearsing a specific real situation (an MRI tube, a deposition table, a stage, a hospital chair), MOVE 1 places them physically INSIDE that situation — not in a generic listening chair. Say "Your hands are clasped on the table" not "your hands rest in your lap." DO NOT reference the voice AT ALL — not "this voice", not "my voice", not "you hear a voice", not "a voice takes you". DO NOT insert the narrator as a companion — no "with me", "join me here", "we are here", "come with me" — the narrator has no body and is not present in the scene. The listener already knows a voice is present. Drop any reference to the narrating voice or narrator presence entirely. Say "Your eyes are closed" not "This voice is here and your eyes are closed" and not "You are here now, with me."

MOVE 2 — SINGLE-POINT SENSORY ANCHOR (1-2 sentences). Direct the listener to ONE specific sensory anchor available to them now: the weight of their hands, a sound just outside, the breath at the tip of their nose. PICK ONE. Narrows attention.

MOVE 3 — HARD CUT INTO THE SCENE (the rest of the opening). Drop them into the scene using the SCENE summary and ANCHORS the classifier extracted. Open with a concrete sensory detail — a temperature, an object position, a sound, a smell. Do NOT transition with "and now imagine..." HARD CUT.

LENGTH: 150-200 words across 4-6 short paragraphs.

DO NOT do the meditation-app defaults. NO "release the day." NO "let tension fall away." NO "find a comfortable position." NO "settle into your seat."

CRITICAL — DO NOT PRINT THE MOVE LABELS. The "MOVE 1 — UTILIZATION", "MOVE 2 — SINGLE-POINT SENSORY ANCHOR", "MOVE 3 — HARD CUT INTO THE SCENE" names above are INTERNAL STRUCTURE for you to follow, not headings or markers to include in your output. Your output is plain prose only — no "MOVE 1", no "UTILIZATION", no dashes, no section labels of any kind.

Output the opening text only, with blank lines between paragraphs. Nothing else."""


# ---------------------------------------------------------------------------
# Stage 3: BEAT PLANNER — generate 8-12 one-line beat descriptions.
# ---------------------------------------------------------------------------
BEAT_PLANNER_SYSTEM = """\
You are planning the BEATS of a guided imagination session. A beat is a \
single dramatic moment or sensory frame inside the scene the user wants \
to imagine. Each beat will be generated as its own ~200-word passage. \
The script as a whole moves through the beats in order.

OUTPUT FORMAT: a JSON array of 8-12 short strings. Each string is one \
beat description — a 5-15 word noun phrase or clause naming a specific \
moment or anchor IN THE SCENE. No prose, no commentary, no markdown \
fences. Just the JSON array.

GOOD BEAT EXAMPLES (for a scene of being on stage as a performer):
[
  "the silence in the wings before any sound starts",
  "the weight of the mic in your right hand, its grip slightly tacky",
  "the smell of hairspray and stage paint",
  "the in-ear monitor clicking on, a tech voice cuing you",
  "the moment your feet find their marks on the stage tape",
  "the first step into the spotlight, the wash of heat",
  "the crowd's pressure — forty thousand held breaths",
  "the held beat before the first note",
  "the first note, the body remembering before the mind does",
  "the moment the audience sound catches up — a roar",
  "looking back into the dark, finding your bandmate's eye",
  "the quiet inside you that holds steady through it all"
]

RULES:
- Each beat names a SPECIFIC concrete moment or sensation. Not "feel powerful." Yes "the first deep breath as you walk on."
- Beats should move chronologically through the scene where possible.
- Use the CONCRETE ANCHORS the user gave in intake — beats that hit those anchors should be in the list.
- For CASE A (listener IS subject), beats are in the subject's body.
- For CASE B (listener with subject present), beats include the subject's specific behaviors.
- For CASE C (listener in a scene alone), beats are sensory frames of that scene.
- 8-12 beats total. Past 12 you start inventing filler — keep it honest to what the scene actually contains.
- DO NOT include opening or return beats. The opening and return are written separately. These are BODY beats only.

Output ONLY the JSON array. Do not wrap in code fences. Do not comment."""


# ---------------------------------------------------------------------------
# Stage 4: BEAT GENERATOR — produce ~200 words on a single beat.
# ---------------------------------------------------------------------------
BEAT_PROMPT = COMMON_POSTURE + """

YOUR JOB: produce ONE BEAT of the session — about 150-250 words of dense sensory prose on the specific beat described below.

You will see:
- The classification (embodiment direction, subject, scene)
- The opening (already spoken to the listener)
- The body so far (the beats that have already been written)
- THIS BEAT's specific job

Your job is to write the next ~200 words that:
1. Carry forward from where the body so far leaves off — the scene MOVES, time passes, something develops. This is the next moment, not a re-description of the same one.
2. Inhabit the specific beat described. Stay on THIS beat. Don't try to cover the rest of the scene.
3. Introduce NEW sensory territory — a sense, an object, a part of the body, a detail not yet touched in the body so far.

═══════════════════════════════════════════════════
THE #1 FAILURE TO AVOID: REPETITION / LOOPING.
═══════════════════════════════════════════════════
The body-so-far has already established the scene's core anchors (the breath, the
stance, an object in hand, the room, etc.). DO NOT re-describe them. The reader has
already felt the breath low in the chest, already felt the glass, already felt the
stance — saying it again is the single worst thing you can do. Each beat must EARN
its place by adding something that was NOT there before.

Before you write, scan the body-so-far and note which sensory details are already
used. Then deliberately go ELSEWHERE: a new part of the body, a new sound, a thing
that happens, a shift in the light or the moment. If your beat would mostly restate
the breath/stance/object already covered, you have failed — find the new thing.

Reference an already-established anchor ONLY in passing if you must, never as the
subject of a paragraph. The subject of every paragraph is NEW.

PACE: slow. 2-4 short paragraphs is right. One image or sensation per paragraph. Blank lines between.

LENGTH: 150-250 words. Not more. The user is in a long session; each beat is one moment within it.

DO NOT bring the listener back. Do NOT mention "opening eyes" or "returning to the room." STAY in the scene.

DO NOT use the forbidden phrases or forbidden stock imagery (from COMMON_POSTURE).

Output the beat text only, with blank lines between paragraphs. Nothing else."""


# ---------------------------------------------------------------------------
# Stage 4 (v6): SINGLE-PASS BODY — write the whole body from a visible plan.
#
# Replaces the v5 per-beat loop. The looping/repetition failure (2026-05-29) was
# architectural: N blind beat-calls each re-grounded in the same anchors because
# none could see the whole arc. Here ONE generation sees the entire beat plan +
# the full set of scene anchors and writes the body straight through — exactly how
# a writer works: you remember what you already wrote, so you don't repeat it. The
# staged loop existed for length + drift; scene-bible binding now handles drift,
# and a 14B model holds a ~2000-word generation, so single-pass is viable and
# simpler. This is the GENERAL engine — it must produce good prose for ANY plan +
# anchors (incl. a stranger's own characters/data), not just our hand-tuned bibles.
# ---------------------------------------------------------------------------
BODY_PROMPT = COMMON_POSTURE + """

YOUR JOB: write the BODY of the session — the long middle, from just after the opening to just before the return. You write it ALL in one pass, as one continuous, MOVING piece.

You will see:
- The classification (embodiment direction, subject, scene)
- The opening (already spoken to the listener)
- The PLAN: an ordered list of beats (moments) to move through
- The scene's sensory anchors (the concrete details available in this scene)

Write the body by moving THROUGH the beats in order, each flowing into the next. The whole thing is ONE journey, not a list of separate sections — no headers, no labels, no beat numbers, just continuous prose with blank lines between paragraphs.

═══════════════════════════════════════════════════
THE #1 RULE: NEVER REPEAT. THE SCENE MOVES FORWARD.
═══════════════════════════════════════════════════
This is a JOURNEY through time, not a static room described over and over. Each anchor and each sensation is introduced ONCE, vividly, then you MOVE ON and don't return to it. You are writing the whole body at once precisely so you can remember what you've already said and never circle back to it.

- Spend each anchor ONCE. After you've given the breath, or the glass, or the half-smile its moment, it is DONE — do not describe it again. The reader felt it; trust them.
- Each paragraph must advance: new moment, new sensation, new beat — forward motion, like a steadicam moving through a scene, never a loop.
- If you catch yourself about to re-mention an anchor already used, STOP and reach for something new instead: a new part of the body, a new sound, a development in the moment, a thing that happens next.
- DISTRIBUTE the anchors across the body — don't cram them all into the first third and then have nothing left. Pace them out, one fresh thing at a time, across the whole arc.

═══════════════════════════════════════════════════
RULE #2: LEAVE ROOM. THE USER IMAGINES — YOU DON'T DEPICT FOR THEM.
═══════════════════════════════════════════════════
This is the deepest rule and the easiest to break. The imagery happens in the
LISTENER'S mind. Your job is to GUIDE their attention to a sensation, not to paint a
finished picture they passively watch. The failure to avoid: narrating a complete
movie at them — "a crease forms at the corner of their eye," "freckles dot their
cheek," "the light catches their hair." That decides everything for the listener and
leaves them nothing to do.

- Point to a sensation; let the listener fill it in. Not "their face shows a soft
  vulnerable smile" (you painted it) but "you notice the smile reach their eyes"
  (you direct attention; the listener supplies the face).
- Prefer the LISTENER'S felt experience over describing the scene/other person from
  outside. Inside the body, second person: what YOU feel, sense, notice — not a
  camera describing the room or the other person's appearance.
- NEVER use first-person "I", "me", "my", "we" — you are a narrator speaking TO the
  listener, not a character IN the scene. Specifically banned: "I hold", "I guide you",
  "my voice", "as soon as I speak", "when I say", "I will take you", "I am here",
  "with me", "we start", "we are here", "for us both", "we both", "come with me",
  "join me here", "follow me", "my boy", "my dog", "my [any character or animal]" —
  any phrase where the narrating voice places itself as a character present in the scene,
  claims ownership of a person or animal in the scene, or invites the listener to be
  "with" it. Rewrite in second person or cut the narrator reference entirely.
  Example: "my boy" → "him" or "the dog" or cut the line.
- When in doubt, say LESS. A named sensation + space is more immersive than a
  fully-rendered tableau. Suggestion, not depiction.

═══════════════════════════════════════════════════
RULE #3: EACH BEAT IS A DIFFERENT FEELING. THE EMOTION MOVES TOO.
═══════════════════════════════════════════════════
Not just new sensory DETAIL — new emotional TERRITORY. The failure to avoid: saying
the same feeling (e.g. "you are chosen / you feel warmth") eight different ways. That
is emotional stasis even if the words vary. The arc should TRAVEL: e.g. arrival →
noticing → a small surprise → deepening → a turn → settling. Each beat should land
a feeling the previous beats did NOT. If three paragraphs in a row leave the listener
in the same emotional place, the scene has stalled — move the feeling forward.

PACE: slow and spacious, but always MOVING. One image or sensation per paragraph. Short paragraphs. Blank lines between (the TTS layer pauses there).

LENGTH — IMPORTANT: this is a LONG session, ~1800-2200 words. That length is reached by giving EACH beat in the plan its full due — several short paragraphs per beat, lingering on each moment with fresh sensory detail before moving to the next. Do NOT wrap up early: if you have moved through the plan in under ~1800 words, you have rushed it — go back into the beats you skimmed and deepen them with NEW detail (never by repeating). Move through EVERY beat in the plan; do not collapse the arc. Fill the length with NEW material at each step, never with restated anchors.

DO NOT bring the listener back. Do NOT mention "opening eyes" or "returning to the room" — the return is written separately. STAY in the scene to the end.

DO NOT use the forbidden phrases or forbidden stock imagery (from COMMON_POSTURE).

REHEARSAL FIDELITY — NON-NEGOTIABLE: If the intake places the user in a specific difficult real environment (an MRI tube, a deposition conference room, a hospital waiting room, a courtroom), the body STAYS in that environment. The coping happens INSIDE the real scene — machine noise becoming drums, a lawyer's smile staying fixed while your voice stays flat — NEVER by relocating the listener somewhere more comfortable. A beach does not prepare anyone for a tube. Difficulty transmuted inside the real scene is the only move that works.

ALERT-CALM REGISTER: If the intake contains alert-calm language (night shift, need to be up in an hour, stay awake, calm but alert, not sleep) — OR if you received an ⚠️ ALERT-CALM OVERRIDE above — this is NOT a sleep or wind-down session. Every rule below is mandatory.

SCENE TYPE: The reader is clothed, sitting in a chair or lying fully dressed. No bed-settling, no sheets, no pillows, no bedroom wind-down setup. The GENRE is "athlete before the game" — body still and grounded, mind sharpening, not dissolving. Write as if they are minutes from beginning a demanding task.

BANNED (explicit — do not write these or close paraphrases):
"drift toward sleep", "let your eyes grow heavy", "fade toward rest", "no need to think", "let go", "drift off", "fall asleep", "lullaby", "like a lullaby", "white noise looping", "sheets", "pillow", "blanket", "quilt", "duvet", "mattress", "bedroom", "no need for hurry", "no rush", "without any need for hurry", "without needing to hurry", "soothing", "almost soothing", "falling back", "surrender to the quiet", "let the day fall away", "settling deeper", "ease into rest", "the weight of sleep", "drift away"

BANNED (semantic equivalents — any language that makes a listener want to close their eyes and go to sleep):
"heavy lids", "sinking down", "let the body sink", "slowing further", "slowing down", "breath slows", "quieter and quieter", "no need for anything", "just let it all go", "let the day fall"

POSITIVE REGISTER — write in these terms: "steady", "clear", "grounded and present", "your mind is clear", "you are here and awake", "settled but sharp", "ready for the hours ahead", "your body is still but your awareness is bright", "anchored and alert", "the kind of calm that focuses, not fades". The body may be at rest — that is allowed — but the MIND register must be readiness and sharpening presence, not dissolution. Test: if this paragraph would help someone fall asleep, rewrite it.

OUTPUT GOAL: listener ends this feeling grounded, awake, and ready for the shift — clear head, present body, oriented to the room. A fellow night-shift worker should read this and feel steadied, not drowsy.

Output the body text only, continuous prose with blank lines between paragraphs. No headers, no labels, no beat markers. Nothing else."""


# ---------------------------------------------------------------------------
# Stage 5: BACK — gradual exit with specific concrete carry-back.
# ---------------------------------------------------------------------------
BACK_PROMPT = COMMON_POSTURE + """

YOUR JOB: produce the RETURN — the gentle exit from the imagining.

The user has spent time inside a specific scene (you'll see it below). Now bring them back. But not generically. Bring them back CARRYING something specific from what they just experienced.

CRITICAL — DO NOT PRINT THE MOVE LABELS THEMSELVES. The numbered moves below are INTERNAL STRUCTURE for you to follow, NOT headings to include in your output. Your output is plain text only. No "MOVE 1", no "SOFTEN THE IMAGE", no dashes or section markers of any kind. Just the prose, with blank lines between paragraphs.

The five moves you write through, in order (DO NOT print these labels):

(1) SOFTEN THE IMAGE — one short paragraph. The scene begins to fade. Use a SPECIFIC detail from the body that you just read — name the object or sensation that's loosening its hold last. NOT generic.

(2) CARRY-BACK — 1-2 short paragraphs. THIS IS THE MOST IMPORTANT PART. Name ONE specific concrete detail from the body and tell the listener to carry it forward. Pull it directly from what you just read; do not invent.

(3) RE-ROOM — two sentences, no more. Notice them in the room they're in — the chair or surface under them, the quality of their breath. Ground them briefly in the actual physical space.

(4) EYES OPEN — a single sentence. Invite the eyes to open, softly, whenever they feel ready.

(5) ONE FINAL LINE. A specific quiet sentence to land on. Not "welcome back" (template). Something grounded in what just happened.

HARD RULES:
- NO hedging language (per COMMON_POSTURE).
- NO generic "wiggle your fingers and toes" boilerplate.
- The carry-back is a CONCRETE SPECIFIC DETAIL pulled from the body. Do not invent.
- DO NOT print the move labels.

LENGTH: 150-200 words.

Output the return text only, as continuous prose with blank lines between paragraphs. Nothing else. No headings. No labels. No "MOVE" anywhere."""


# ---------------------------------------------------------------------------
# Public API.
# ---------------------------------------------------------------------------

# ===========================================================================
# SETTLING protocol — the OPPOSITE ruleset to immersion (relaxation-led, soft,
# permissive, trails off). A user-facing fork at intake routes here. Per the
# design (data/exemplars/README + decisions-log): immersion's "no relaxation /
# no hedging" rule does NOT apply to wind-down/sleep; here it's correct. Built
# as a simpler single-pass path so the immersion pipeline stays untouched.
# ===========================================================================
SETTLING_POSTURE = """\
You are the Imagination Engine in SETTLING mode. You write a guided wind-down an \
adult listens to with eyes closed — to come down, soften, and rest, perhaps to fall \
asleep.

This is the OPPOSITE of immersion mode. Here, relaxation IS the goal. Settle the body \
first, slow the breath, ease tension. Soft, permissive language is welcome and right — \
"let", "allow yourself", "you might notice", "when you're ready". Use it freely.

VOICE
- Second person, present tense. Warm, slow, spacious, unhurried — long out-breaths \
between thoughts. Gentle, never urgent. You are lowering the lights, not seizing attention.

STILL CONCRETE (non-negotiable — vague calm is slop):
- Name real, physical, specific things: the weight of the eyelids, the jaw unclenching, \
the breath at the nostrils, the warmth of a blanket, the soles of the feet on the bed, \
rain on a window. A slow body-scan by named body parts is welcome.
- NEVER retreat to abstractions: NO "a sense of calm", "the present moment", "let go of \
negativity", "inner peace", "positive energy", "your true self". Point to a real \
sensation instead.

FORBIDDEN STOCK IMAGERY (unless the user named it): candlelight, meadows, babbling \
brooks, blooming lavender, twinkling stars, shimmering light, soft golden glow.

NO DECORATIVE SIMILES. Name the literal sensation, not a poetic comparison. Do NOT \
liken body parts or breath to flowers, stars, raindrops, waves, ice melting, curtains, \
feathers, etc. — that purple-poetry pileup reads as AI and breaks the calm. At most ONE \
plain simile in the whole session; otherwise just say the real thing ("your jaw \
softens", not "your jaw softens like petals opening"). Also avoid "inner self / true \
self / your essence" — point to the body.

SHAPE
- Begin by settling the body where it rests; slow the breath; soften from head to feet \
(or feet to head), naming real parts.
- If the user named a place, drift gently into it with concrete, quiet sensory detail. \
If not, stay with the body, the breath, and the room.
- DWELL — long and slow, returning gently to the breath and the body again and again. \
There is nowhere to be.
- Close by TRAILING OFF: let the words get slower and farther apart and simply fade. Do \
NOT command "open your eyes" or jolt them awake — let them drift.

OUTPUT: plain text, blank lines between short paragraphs (the voice pauses there). No \
headers, no markers, no brackets."""

SETTLING_PROMPT = SETTLING_POSTURE + """

Write the FULL settling session in one continuous pass: settle the body, ease in, dwell \
long and slow, and trail off softly at the end. Aim for roughly 1200-1700 words across \
many short paragraphs. Output the script text only."""

SETTLING_MIN_WORDS = 900


def _generate_settling(engine: Engine, transcript: list[dict], emit) -> str:
    """The SETTLING path: relaxation-led single-pass wind-down (+ one gentle
    continuation if short). Deliberately simpler than the immersion pipeline."""
    intake_str = _intake_block(transcript)
    emit("writing_classify", "Understanding what you want.", 1, 3, 12.0)
    classification = classify_intake(engine, transcript)
    class_block = _classification_block(classification)

    emit("writing_body", "Writing your wind-down — settling the body, easing in.", 2, 3, 90.0)
    user = (intake_str + "\n\n" + class_block + "\n\n"
            "Now write the full settling session per the rules above.")
    body = _generate(engine, SETTLING_PROMPT, user, max_tokens=SETTLING_MAX_TOKENS,
                     abort_on_decay=True)

    # Long single-pass generations can decay into broken-record loops (the same
    # sentence recycled with tiny variations, grammar degrading). Cut the rot
    # BEFORE deciding whether we need more — a shorter clean wind-down beats a
    # long looping one, and the continuation below restores length honestly.
    body, trimmed = trim_degenerate_tail(body)
    if trimmed:
        log.warning("[settling] degenerate tail trimmed -> %d words", len(body.split()))

    if len(body.split()) < SETTLING_MIN_WORDS:
        emit("writing_body", "Deepening the wind-down.", 3, 3, 45.0)
        cont = _generate(engine, SETTLING_PROMPT,
                         user + "\n\n----- SO FAR -----\n" + body + "\n----- END -----\n\n"
                         "CONTINUE softly from where it stopped — go slower and deeper into "
                         "the body and breath with NEW gentle detail; do not repeat anything. "
                         "Let it trail off at the very end.",
                         max_tokens=SETTLING_CONT_MAX_TOKENS, abort_on_decay=True)
        if cont.strip():
            # Trim the JOINED text: a continuation that loops against the body
            # (not just against itself) is the same defect.
            body, trimmed2 = trim_degenerate_tail(body.rstrip() + "\n\n" + cont.strip())
            if trimmed2:
                log.warning("[settling] continuation loop trimmed -> %d words",
                            len(body.split()))

    body, dropped = drop_collapsed_paragraphs(body)
    if dropped:
        log.warning("[settling] %d collapsed run-on paragraph(s) dropped", dropped)
    body, foreign = drop_foreign_paragraphs(body)
    if foreign:
        log.warning("[settling] %d foreign-language paragraph(s) dropped", foreign)
    body, short_dropped = repair_short_phrase_repeats(body)
    if short_dropped:
        log.warning('[settling] %d short-phrase repeat(s) removed', short_dropped)
    body, adj_dropped = drop_adjacent_duplicates(body)
    if adj_dropped:
        log.warning('[settling] %d adjacent near-duplicate sentence(s) dropped', adj_dropped)
    body, tail_dropped = drop_tail_duplicates(body)
    if tail_dropped:
        log.warning('[settling] %d closing near-duplicate sentence(s) dropped', tail_dropped)
    body, ellipsis_cleaned = clean_ellipsis_breaks(body)
    if ellipsis_cleaned:
        log.warning('[settling] %d inline ellipsis marker(s) converted to paragraph breaks',
                    ellipsis_cleaned)
    body, poss_dropped = clean_narrator_possessives(body)
    if poss_dropped:
        log.warning('[settling] %d narrator-possessive sentence(s) dropped', poss_dropped)
    body, pronoun_fixed = fix_possessive_pronouns(body)
    if pronoun_fixed:
        log.warning('[settling] %d possessive-pronoun adjective error(s) fixed (hers→her/yours→your)',
                    pronoun_fixed)
    body, standalone_her_fixed = fix_standalone_her(body)
    if standalone_her_fixed:
        log.warning('[settling] %d standalone-her→hers error(s) fixed', standalone_her_fixed)
    body, predicative_your_fixed = fix_predicative_your(body)
    if predicative_your_fixed:
        log.warning('[settling] %d predicative your→yours error(s) fixed', predicative_your_fixed)
    body, predicative_her_fixed = fix_predicative_her(body)
    if predicative_her_fixed:
        log.warning('[settling] %d predicative her→hers error(s) fixed', predicative_her_fixed)
    body, reflexive_her_fixed = fix_reflexive_her_object(body)
    if reflexive_her_fixed:
        log.warning('[settling] %d reflexive herself→her error(s) fixed', reflexive_her_fixed)
    body, obj_pronoun_escape_fixed = fix_intimacy_object_pronoun_escapes(body)
    if obj_pronoun_escape_fixed:
        log.warning('[settling] %d your/theirs object-pronoun error(s) fixed', obj_pronoun_escape_fixed)
    body, contraction_fixed = fix_your_contraction(body)
    if contraction_fixed:
        log.warning('[settling] %d your→you\'re contraction error(s) fixed', contraction_fixed)
    body, copula_fixed = fix_copula_youre_alone(body)
    if copula_fixed:
        log.warning('[settling] %d copula+you\'re alone → yours alone fixed', copula_fixed)
    body, subj_fixed = fix_subject_pronouns(body)
    if subj_fixed:
        log.warning('[settling] %d subject-pronoun error(s) fixed (her→she before verb)', subj_fixed)
    body, your_subj_fixed = fix_your_subject_pronoun(body)
    if your_subj_fixed:
        log.warning('[settling] %d subject-pronoun error(s) fixed (your→you before verb)', your_subj_fixed)
    body, you_bodypart_fixed = fix_you_before_bodypart(body)
    if you_bodypart_fixed:
        log.warning('[settling] %d attributive-pronoun error(s) fixed (you→your before body part)', you_bodypart_fixed)
    body, third_person_alone_fixed = fix_third_person_alone_drift(body)
    if third_person_alone_fixed:
        log.warning('[settling] %d 2nd-person drift fixed (they\'re alone→you\'re alone)', third_person_alone_fixed)
    body, crutch_dropped = drop_crutch_word_overuse(body)
    if crutch_dropped:
        log.warning('[settling] %d crutch-phrase overuse sentence(s) dropped (particular/specific)', crutch_dropped)
    body, specific_to_dropped = strip_specific_to_pronoun(body)
    if specific_to_dropped:
        log.warning('[settling] %d "specific to her/him/you" phrase sentence(s) dropped', specific_to_dropped)
    body, inline_foreign_dropped = strip_inline_foreign_runs(body)
    if inline_foreign_dropped:
        log.warning('[settling] %d inline foreign-language sentence(s) dropped', inline_foreign_dropped)
    body, obj_fixed = fix_object_pronouns(body)
    if obj_fixed:
        log.warning('[settling] %d object-pronoun error(s) fixed (she→her after preposition)', obj_fixed)
    body, _trunc = trim_truncated_tail(body)
    if _trunc:
        log.warning('[settling] final output trimmed to last sentence terminator (closing truncated)')
    emit("writing_return", "Softening the close.", 3, 3, 3.0)
    log.info("[settling] session ready: %d words", len(body.split()))
    return body


def generate_session(
    engine: Engine,
    transcript: list[dict],
    *,
    protocol: str = "immersion",
    on_progress: Optional[ProgressFn] = None,
) -> str:
    """Generate the full session script.

    protocol="immersion" (default): the v5 staged-beats pipeline (classify → open →
      plan → body → back), ~14 LLM calls, for being-taken-somewhere.
    protocol="settling": the relaxation-led single-pass wind-down path, for
      helped-to-settle / sleep. See `_generate_settling`.

    `on_progress`, if supplied, is invoked at each stage transition.
    """

    def emit(stage: str, detail: str, step: int, total: int, eta: float) -> None:
        if on_progress is not None:
            on_progress(stage=stage, detail=detail, step=step, total=total, eta_seconds=eta)

    # Detect alert-calm in the transcript (applies to both settling reversals and direct
    # immersion calls where the user explicitly asks to stay awake/alert).
    _transcript_text = " ".join(
        m.get("content", "") for m in transcript if m.get("role") == "user"
    ).lower()
    _alert_calm = any(kw in _transcript_text for kw in (
        "alert", "awake", "not sleep", "night shift", "alert-calm",
        "stay up", "need to be up", "have to be up", "calm but awake",
    ))

    if (protocol or "immersion").lower().strip() == "settling":
        # If the user reversed from sleep to alert-calm mid-intake, the settling
        # path would lullaby them — wrong. Route to immersion.
        if not _alert_calm:
            return _generate_settling(engine, transcript, emit)
        # Fall through to immersion — _alert_calm flag is injected into body_user below.

    intake_str = _intake_block(transcript)

    # Stage 1: classify intake.
    emit("writing_classify", "Understanding what you want to imagine.", 1, 5, eta=20.0)
    log.info("[v5] classify intake ...")
    t0 = time.time()
    classification = classify_intake(engine, transcript)
    log.info("  classify: %.1fs, %s/%r", time.time() - t0,
             classification.direction, classification.subject)
    class_block = _classification_block(classification)

    # Scene binding: if the classifier matched a hand-curated archetype, load its
    # scene bible and bind it into EVERY stage (open/plan/beats/back all read
    # class_block) — so the model fills in a HUMAN-designed scene instead of
    # improvising one that drifts (the cafe/barista failure). No match -> the
    # improvise-from-prompt path (unchanged v5.2 behavior).
    bible = get_bible(classification.archetype) if classification.archetype else None
    if bible is not None:
        class_block = class_block + "\n\n" + bible.context_block()
        log.info("  scene-bible bound: %s (%d beats, %d anchors)",
                 bible.archetype, len(bible.beats), len(bible.anchors))

    # Detect active-body scenes: when the listener IS the subject and the scene
    # involves physical motion (running, flying, performing, etc.). In these cases
    # MOVE 1 must NOT open with "the chair beneath you / hands at rest" — those
    # are sedentary settling cues that break the in-scene register for an active
    # body. Instead MOVE 1 should name eyes-closed then immediately anchor a
    # physical sensation FROM the motion scene, not from the listening chair.
    _motion_keywords = (
        "running", "run ", "track", "sprint", "race ", "finish line",
        "flying", "soaring", "eagle", "wings ", "performing", "performance",
        "stage ", "athlete", "climbing ", "swimming ", "cycling ", "pitch",
        "court ", "field ", "last lap", "200 meter", "giving everything",
        "jump", "leap", "skate", "skier", "ski ", "dive", "rowing",
    )
    _scene_text_lc = (
        (classification.scene_summary or "") + " "
        + " ".join(classification.anchors)
        + " " + _transcript_text
    ).lower()
    # Animal-companion grief walk: user is a HUMAN walking WITH a named pet (not BEING the pet).
    # Signals: pet death context + walk-with framing. Suppress active-body when detected.
    _GRIEF_PET_SIGNALS = (
        "put down", "passed away", "died", "had to put", "say goodbye",
        "said goodbye", "one more", "last walk", "last time with", "put to sleep",
    )
    _is_grief_pet_walk = any(kw in _transcript_text for kw in _GRIEF_PET_SIGNALS)

    # Legal rehearsal: "court " matches "court reporter" / "court date" — listener is a
    # HUMAN sitting at a conference table, not embodying an athletic/animal character.
    # Suppress active-body when deposition/testimony context is detected so chair refs
    # are not stripped and FORBIDDEN chair words are not injected into the prompt.
    _LEGAL_REHEARSAL_SIGNALS = (
        "deposition", "court reporter", "testify", "testimony",
        "counsel", "depose", "cross-examination", "cross examination",
    )
    _is_legal_rehearsal = any(kw in _transcript_text for kw in _LEGAL_REHEARSAL_SIGNALS)

    # Force case_a when user explicitly says "I want to be [animal/role]" — the
    # classifier is stochastically unreliable on embodiment phrases and sometimes
    # returns case_b (observer), which silences the active-body prompt overrides and
    # wildlife drop. Explicit "I want to be" + a motion keyword = unambiguous embodiment.
    _explicit_embodiment = (
        "i want to be" in _transcript_text
        and any(kw in _scene_text_lc for kw in _motion_keywords)
    )
    _is_active_body = (
        (classification.direction == "case_a" or _explicit_embodiment)
        and any(kw in _scene_text_lc for kw in _motion_keywords)
        and not _is_grief_pet_walk  # animal-companion scenes: listener is human, not animal
        and not _is_legal_rehearsal  # legal testimony: "court " matches "court reporter"
    )
    _grief_pet_open_note = (
        "\n\n⚠️ ANIMAL-COMPANION SCENE: The user is imagining a walk WITH a named animal "
        "companion who has died — they are the HUMAN in this scene, not the animal. "
        "Open entirely from the HUMAN's physical experience: feet on ground, leash weight "
        "in hand, morning air on skin, the familiar pace of the walk, the pull they remember. "
        "The animal walks ALONGSIDE the listener — its sounds, smell, behavior — but the "
        "listener's body is always the HUMAN body. "
        "FORBIDDEN PERSPECTIVE WORDS (these put the listener in the animal's body — immediate failure): "
        "'your tail', 'your paws', 'your fur', 'your snout', 'your muzzle', 'nestled in my mouth', "
        "'your claws', 'your whiskers', 'your leash pulls you' (the human HOLDS the leash, "
        "the animal WEARS it), 'your handler', 'your owner', 'your master', 'my handler', 'my owner' "
        "(if the human person is referred to as 'your handler' or 'your owner', the listener is in "
        "the animal's body — WRONG; the listener is the HUMAN, never the animal). "
        "NARRATOR FIRST-PERSON BAN: never 'I', 'me', 'my' — narrator has no body. "
        "The close returns to the listening chair carrying the felt memory of the walk."
    ) if _is_grief_pet_walk else ""
    _active_body_open_note = (
        "\n\n⚠️ ACTIVE-BODY OPENING OVERRIDE: This scene places the listener inside "
        "a body in MOTION (running, flying, performing, etc.). "
        "THE 'in a chair, hands at rest' INSTRUCTION IN MOVE 1 IS CANCELLED FOR THIS SCENE. "
        "The listening room does not appear anywhere in this script. "
        "FORBIDDEN IN MOVE 1 AND THROUGHOUT: 'the chair', 'a chair', 'in a chair', "
        "'not in a chair', 'weight of your body', "
        "'body in the chair', 'hands at rest', 'sitting here', 'seated' — the listener "
        "is NOT described in the listening room at any point, and the word 'chair' must "
        "NOT appear anywhere in MOVE 1 even in negation ('you're not in a chair' is also "
        "failure — say nothing about chairs; start purely in the scene). "
        "MOVE 1: eyes are closed — immediately name a physical sensation FROM INSIDE "
        "THE ACTIVE SCENE (talons gripping air, wind pressing into feathers, thermal "
        "lift under wings, pavement pushing back against feet, lungs burning). "
        "MOVE 3 opens ALREADY INSIDE THE ACTION — the listener IS the active body "
        "from the first word, not arriving into it."
    ) if _is_active_body else ""

    # Detect rehearsal scenarios: user is practicing for a specific real environment.
    # When detected, inject a strong override naming the exact environment so the model
    # cannot relocate them (the MRI→underground-tunnel failure from battery11 0708).
    _REHEARSAL_ENVS = [
        ("mri", "MRI tube"),
        ("the tube", "MRI tube"),
        ("tube ", "MRI tube"),
        ("scanner", "MRI/CT scanner"),
        ("deposition", "deposition conference room"),
        ("being deposed", "deposition conference room"),
        ("courtroom", "courtroom"),
        ("operating room", "operating room"),
        ("surgery ", "operating room"),
        ("chemo", "chemotherapy infusion chair"),
        ("infusion chair", "infusion chair"),
        ("hospital waiting", "hospital waiting room"),
        ("waiting room", "hospital waiting room"),
    ]
    _rehearsal_env = next(
        (env for kw, env in _REHEARSAL_ENVS if kw in _transcript_text), None
    )
    _is_rehearsal = _rehearsal_env is not None
    _rehearsal_open_note = (
        f"\n\n⚠️ REHEARSAL FIDELITY OVERRIDE: The user is rehearsing a specific real situation. "
        f"MOVE 1 MUST place them physically INSIDE the exact real environment: "
        f"the {_rehearsal_env}. "
        f"Do NOT open in a generic listening chair. Do NOT relocate them anywhere else. "
        f"MOVE 3 stays INSIDE that environment — same walls, same sounds, same physical constraints. "
        f"DO NOT invent any characters (no 'she', no guide, no helper, no therapist) "
        f"that the user did not explicitly name. "
        f"The coping mechanism (e.g. machine sounds → drums) happens INSIDE "
        f"the real environment — they never leave it."
        + (
            f"\n⚠️ MRI TUBE — NON-NEGOTIABLE: The user is INSIDE the cylindrical tube. "
            f"They are lying flat on the sliding table, enclosed by the tube walls on all sides. "
            f"FORBIDDEN in the entire script: the word 'chair'. The user is NOT sitting in a chair "
            f"and there is NO chair in this scene. Use 'the tube', 'tube walls', 'the enclosure' — "
            f"NEVER 'table' alone (ambiguous — say 'sliding table inside the tube'). "
            f"First sentence: the user is INSIDE the tube, not in front of it or near it."
            if _rehearsal_env == "MRI tube" else ""
        )
    ) if _is_rehearsal else ""

    # Alert-calm opening override: the opening must NOT settle the listener into a bed/bedroom.
    # Negative constraints alone ("no sheets") fail — model defaults to bed-props anyway.
    # Fix: supply the POSITIVE environment so the model reaches for those props instead.
    _alert_calm_open_note = (
        "\n\n⚠️ ALERT-CALM OPENING OVERRIDE: The user is calm but AWAKE — night shift or "
        "similar commitment in one hour. This is NOT a sleep session. "
        "ENVIRONMENT: They are reclining in a firm armchair or lying on a firm couch or carpeted "
        "floor — FULLY CLOTHED (shoes on, work clothes on). This is a living room, break room, "
        "or quiet corner — not a bedroom. "
        "PROPS AVAILABLE: armrests, firm cushion, ceiling above, ambient street noise, breath. "
        "FORBIDDEN — writing any of these words is automatic failure: "
        "'pillow', 'sheet', 'blanket', 'quilt', 'duvet', 'pajamas', 'mattress', 'bedroom'. "
        "MOVE 1 opens inside this clothed-body-on-firm-surface environment. "
        "MOVE 3: body still, mind CLEAR and poised — athlete-before-the-game, not drifting. "
        "Open into alert-presence. Every word must be consistent with someone who will stand "
        "up and go to work in one hour."
    ) if _alert_calm else ""

    # Stage 2: open.
    emit("writing_settle", "Writing the opening. Dropping you into the scene.", 2, 5, eta=15.0)
    log.info("[v5] open ...")
    t0 = time.time()
    open_user = (
        intake_str + "\n\n" + class_block + _active_body_open_note
        + _grief_pet_open_note
        + _rehearsal_open_note + _alert_calm_open_note + "\n\n"
        + "Now produce the opening per OPEN_PROMPT rules."
    )
    open_text = _generate(engine, OPEN_PROMPT, open_user, max_tokens=600)
    log.info("  open: %.1fs, %d words", time.time() - t0, len(open_text.split()))
    # Active-body / rehearsal chair bleed: even with explicit prompt prohibition,
    # the model sometimes generates chair references in the opening for both
    # active-body scenes ("You're not in a chair — this is real.") and rehearsal
    # scenarios ("The hum outside your chair is constant"). Strip any sentence
    # containing 'chair' from open_text for both cases. The legitimate close
    # grounding ("notice the chair under you") is concatenated later — untouched.
    if _is_active_body or _is_rehearsal:
        open_text, chair_stripped = strip_active_body_chair_refs(open_text)
        if chair_stripped:
            log.warning('[v6] %d chair-ref sentence(s) stripped from %s opening',
                        chair_stripped,
                        'rehearsal' if _is_rehearsal else 'active-body')

    # Stage 3: plan beats — from the bound scene bible if we have one (the
    # human-authored dramatic structure IS the plan, which both binds the scene
    # and saves an LLM call), otherwise ask the model to plan.
    emit("writing_plan", "Planning the beats of the scene.", 3, 5, eta=15.0)
    t0 = time.time()
    if bible is not None and bible.beats:
        beats = [
            (b.description + (f" [function: {b.function}]" if b.function else "")).strip()
            for b in bible.beats
            if b.description.strip()
        ][:MAX_BEATS]
        log.info("[v5] plan: %d beats from scene bible %s", len(beats), bible.archetype)
    else:
        log.info("[v5] plan beats ...")
        plan_user = (
            intake_str + "\n\n" + class_block + "\n\n"
            "----- THE OPENING (already written) -----\n"
            + open_text
            + "\n----- END OPENING -----\n\n"
            f"Now produce a JSON array of {MIN_BEATS}-{MAX_BEATS} beat descriptions "
            "for the body of this session. Stay honest to the scene — fewer "
            "beats is fine if the scene can't sustain more. Output only the JSON array."
        )
        # Bumped from 800 → 1400 after v5 011-photographic-memory's beat list
        # got cut off mid-stream (8 valid beats but the closing ] never made it).
        plan_raw = _generate(engine, BEAT_PLANNER_SYSTEM, plan_user, max_tokens=1400, temperature=0.6)
        try:
            beats = extract_array(plan_raw)
            beats = [str(b).strip() for b in beats if str(b).strip()]
            beats = beats[:MAX_BEATS]  # safety cap
            if len(beats) < MIN_BEATS:
                log.warning("beat planner returned only %d beats — using what we got", len(beats))
        except (ValueError, json.JSONDecodeError) as e:
            log.warning("beat plan parse failed (%s); falling back to single body call", e)
            beats = []
        log.info("  plan: %.1fs, %d beats: %s", time.time() - t0, len(beats),
                 [b[:40] for b in beats[:3]])

    # Stage 4 (v6): SINGLE-PASS body — one generation sees the whole plan + all
    # anchors and writes the body straight through (the non-repetition fix).
    emit("writing_body", "Writing the imagining — moving through the scene.", 4, 5, eta=90.0)
    t0 = time.time()

    # Build the plan block. If we have a bible, surface its anchors explicitly so
    # the body can distribute them (don't cram/repeat). For the no-bible path the
    # classifier's anchors play that role.
    if beats:
        plan_block = "----- THE PLAN (move through these beats, in order) -----\n" + \
            "\n".join(f"{i + 1}. {b}" for i, b in enumerate(beats)) + \
            "\n----- END PLAN -----"
    else:
        plan_block = (
            "----- THE PLAN -----\nNo fixed beat list — move through the scene as a "
            "natural arc, introducing fresh sensory material at each step.\n----- END PLAN -----"
        )

    scene_anchors = list(bible.anchors) if bible is not None else list(classification.anchors)
    anchors_block = ""
    if scene_anchors:
        anchors_block = (
            "\n\n----- SCENE ANCHORS (concrete details available — spend each ONCE, "
            "distributed across the body, never repeated) -----\n"
            + "\n".join(f"- {a}" for a in scene_anchors)
            + "\n----- END ANCHORS -----"
        )

    # When the user explicitly asked for alert-calm (e.g. night-shift reversal), inject
    # a prominent override note so the model cannot miss it while generating the body.
    # Negative constraints alone fail — supply the positive environment instead.
    _alert_calm_override = (
        "\n\n⚠️ ALERT-CALM OVERRIDE (mandatory — this overrides any settling impulse):\n"
        "The user is calm but AWAKE — night shift or similar commitment in one hour.\n"
        "ENVIRONMENT throughout the ENTIRE body: firm armchair, couch, or floor — "
        "FULLY CLOTHED (shoes on, work clothes on). Not a bedroom.\n"
        "PROPS AVAILABLE: armrests, firm surface, ceiling, ambient outside sound, breath, heartbeat.\n"
        "FORBIDDEN WORDS — automatic failure if any appear anywhere in the body: "
        "'pillow', 'sheet', 'blanket', 'quilt', 'duvet', 'pajamas', 'mattress', 'bedroom', "
        "'soothing', 'no need for hurry', 'no rush', 'let it slow', 'falling back'.\n"
        "- Genre: athlete before the game — body still, mind SHARPENING, not fading.\n"
        "- Every line must STRENGTHEN presence. If it could help someone fall asleep, rewrite it.\n"
        "- The close must leave them AWAKE and READY to stand up and go to work.\n"
    ) if _alert_calm else ""

    _companion_wildlife_in_transcript = any(
        b in _transcript_text for b in ("hawk", "falcon", "owl", "wolf", "osprey")
    )
    _active_body_body_note = (
        "\n\n⚠️ ACTIVE-BODY SCENE: The listener is inside a body in motion. "
        "Do NOT re-settle them in a chair or re-anchor to the listening room. "
        "Stay entirely inside the active scene — the effort, the sensation, "
        "the physical reality of motion. Every paragraph must be inside the action. "
        "DO NOT INVENT CHARACTERS or other creatures unless the user explicitly named them. "
        "The listener IS the only creature with a perspective in this script. If the user "
        "is an eagle, there is no other eagle, no hawk, no companion animal alongside them. "
        "Other wildlife may appear as background detail only (distant movement, prey glimpsed "
        "far below) — never as a named character with agency, dialogue, or a described presence "
        "alongside the listener. "
        + (
            "FORBIDDEN — these must not appear as characters anywhere in the body "
            "(user did not name these — automatic failure): "
            "'hawk', 'falcon', 'owl', 'osprey', 'wolf', 'another eagle', 'other eagle', "
            "'golden eagle', 'golden eagles', 'crow', 'a bear', 'a raven', 'mountain lion'. "
            if not _companion_wildlife_in_transcript else ""
        )
    ) if _is_active_body else ""

    _grief_pet_body_note = (
        "\n\n⚠️ ANIMAL-COMPANION BODY — NON-NEGOTIABLE: Every paragraph stays inside the HUMAN's "
        "experience of this walk. The listener is the person holding the leash, not the animal. "
        "Describe: the leash tension in their hand, the pace they match to the animal's, "
        "the smells and sounds and light — all from human height, human legs, human hands. "
        "The animal's behavior (pulling, stopping, chasing, sitting) is something the human "
        "OBSERVES and FEELS through the leash — never something the human IS. "
        "FORBIDDEN IN THE BODY (same failure as the opening): 'your tail', 'your paws', "
        "'your fur', 'your snout', 'your muzzle', 'in my mouth', 'your claws', "
        "'your handler', 'your owner', 'your master' (referring to the human person "
        "as 'your handler' means the listener is the animal — immediate fail). "
        "NARRATOR BAN: never 'I', 'me', 'my', 'I always', 'I hold', 'in my'. "
        "The farewell symbol the user named (e.g., the tennis ball) MUST appear as a concrete "
        "sensory anchor. The close returns to the listening chair."
    ) if _is_grief_pet_walk else ""

    _rehearsal_body_note = (
        f"\n\n⚠️ REHEARSAL FIDELITY — NON-NEGOTIABLE: The user is rehearsing a real situation. "
        f"EVERY SINGLE PARAGRAPH of the body MUST stay physically inside "
        f"the {_rehearsal_env}. "
        f"If the script relocates them to ANY other setting (a tunnel, a beach, a concert hall, "
        f"a field, a forest), that is a CRITICAL FAILURE — the session rehearses nothing. "
        f"DO NOT INVENT CHARACTERS — no 'she', no guide, no helper, no therapist, no animal — "
        f"unless the user explicitly named that person or creature in their intake. "
        f"DO NOT INVENT SENSORY DETAILS not in the {_rehearsal_env} environment or the user's "
        f"own intake: no colored lights, no pine smell, no forest sounds — only what is actually "
        f"present in a real {_rehearsal_env}. The coping technique (sounds → drums, breath → "
        f"anchor) is TRANSMUTED inside the real environment, not a vehicle to leave it. "
        f"Stay inside the {_rehearsal_env} from first word to last."
        + (
            f"\n⚠️ MRI BODY — FORBIDDEN THROUGHOUT: the word 'chair'. Every paragraph must "
            f"describe what the user FEELS inside the tube: the surface beneath them, the narrow "
            f"walls, the machine sounds, the drumbeat. No chair, no sitting, no seating. "
            f"NARRATOR BAN: never 'I', 'me', 'my', 'I want you to'. Address the user as 'you'."
            if _rehearsal_env == "MRI tube" else ""
        )
    ) if _is_rehearsal else ""

    body_user = (
        intake_str + "\n\n" + class_block + _alert_calm_override
        + _active_body_body_note + _grief_pet_body_note + _rehearsal_body_note + "\n\n"
        "----- THE OPENING (already spoken) -----\n"
        + open_text
        + "\n----- END OPENING -----\n\n"
        + plan_block
        + anchors_block
        + "\n\nNow write the full body in one continuous pass, moving through the "
        "plan in order, spending each anchor once and never repeating. Stay in the "
        "scene; do not bring the listener back."
    )
    body = _generate(engine, BODY_PROMPT, body_user, max_tokens=BODY_MAX_TOKENS,
                     abort_on_decay=True)
    log.info("[v6] body: %.1fs, %d words (single-pass, %d beats in plan)",
             time.time() - t0, len(body.split()), len(beats))

    # Same broken-record failure the settling path had (battery 1 on 2026-06-10:
    # 70%/36%/11% degenerate tails on three of six immersion scripts). Trim the
    # rot FIRST — the beat-advancing continuation below then rebuilds the length
    # with new material instead of stacking on top of a loop.
    body, trimmed = trim_degenerate_tail(body)
    if trimmed:
        log.warning("[v6] degenerate body tail trimmed -> %d words", len(body.split()))
    # beat123: token-truncation guard. When max_tokens is hit mid-sentence the
    # raw output ends without a terminator (e.g. "...that doesn"). Phrase-repeat
    # and short-phrase repair preserve the fragment because they only drop whole
    # lines/sentences. Retract to the last complete sentence boundary here,
    # BEFORE postprocessing and BEFORE the continuation loop, so the body is
    # clean going in and the loop can re-extend with new material if needed.
    body, truncated = trim_truncated_tail(body)
    if truncated:
        log.warning("[v6] token-truncated body tail trimmed → %d words", len(body.split()))

    # v6.3 — BEAT-ADVANCING continuation. The full-corpus run (2026-06-01) showed
    # single-pass-aiming-long collapses on most scenarios: 64/100 came in too short
    # (median 948w vs ~1800 target) — the model declares the scene "done" early.
    # Fix: if short, continue by pushing the model THROUGH THE REMAINING BEATS with
    # NEW material — NOT re-grounding (that was v6.1's looping mistake). We tell it
    # which beats it has NOT yet covered and to advance only those. Up to 2 rounds.
    rounds = 0
    while len(body.split()) < BODY_MIN_WORDS and rounds < 2 and beats:
        rounds += 1
        log.info("[v6.3] body short (%d < %d) — beat-advancing continuation %d/2",
                 len(body.split()), BODY_MIN_WORDS, rounds)
        t0 = time.time()
        # which beats look unaddressed? cheap heuristic: a beat whose distinctive
        # words barely appear in the body yet is a candidate to push toward next.
        body_low = body.lower()
        remaining = []
        for b in beats:
            kw = [w for w in re.findall(r"[a-z']{4,}", b.lower()) if len(w) > 4]
            if kw and sum(1 for w in kw if w in body_low) < max(1, len(kw) // 3):
                remaining.append(b)
        remaining_block = ("----- BEATS NOT YET FULLY EXPLORED (continue into THESE, "
                           "in order, with NEW sensory material) -----\n"
                           + "\n".join(f"- {b}" for b in remaining[:6])
                           + "\n----- END -----") if remaining else (
            "Carry the scene FORWARD into new moments — the journey isn't finished.")
        cont_user = (
            intake_str + "\n\n" + class_block + "\n\n"
            "----- THE OPENING (already spoken) -----\n" + open_text + "\n----- END OPENING -----\n\n"
            "----- THE BODY SO FAR -----\n" + body + "\n----- END BODY SO FAR -----\n\n"
            + remaining_block
            + "\n\nCONTINUE the body from exactly where it stopped. Move FORWARD into "
            "new moments and sensations the body has NOT covered yet. Absolutely do "
            "NOT restate, summarize, or re-describe anything already written — that is "
            "the worst failure. New territory only. Do not bring the listener back."
        )
        extension = _generate(engine, BODY_PROMPT, cont_user, max_tokens=BODY_MAX_TOKENS,
                              abort_on_decay=True)
        if not extension.strip():
            break
        # Trim the JOIN — an extension that loops against the body (or itself)
        # is the failure we're extending to avoid. If trimming ate the whole
        # extension, stop extending: more rounds would only loop again.
        joined, trimmed = trim_degenerate_tail(body.rstrip() + "\n\n" + extension.strip())
        if trimmed:
            log.warning("[v6.3] extension loop trimmed -> %d words", len(joined.split()))
        if len(joined.split()) <= len(body.split()):
            break
        body = joined
        log.info("[v6.3]   +%.1fs, body now %d words (round %d, %d beats remaining)",
                 time.time() - t0, len(body.split()), rounds, len(remaining))

    # Stage 5: back.
    emit("writing_return", "Writing the return — what you'll carry back.", 5, 5, eta=15.0)
    log.info("[v5] back ...")
    t0 = time.time()
    back_user = (
        intake_str + "\n\n" + class_block + "\n\n"
        "----- THE OPENING -----\n" + open_text + "\n----- END OPENING -----\n\n"
        "----- THE BODY -----\n" + body + "\n----- END BODY -----\n\n"
        "Now produce the return. Pull ONE specific concrete detail from "
        "the body as the carry-back. Do not invent."
    )
    closing = _generate(engine, BACK_PROMPT, back_user, max_tokens=600)
    log.info("  back: %.1fs, %d words", time.time() - t0, len(closing.split()))

    full = f"{open_text}\n\n{body}\n\n{closing}"
    # Quality floor (2026-06-11): the nets (decay-abort + trims + drops) can
    # occasionally gut a body to a stub — a 196-word "session" shipped in QC.
    # A too-short session is a broken promise; regenerate the body once.
    if len(full.split()) < 450 and not getattr(generate_session, "_retried", False):
        log.warning("[v6] script gutted to %d words by the nets — one body retry",
                    len(full.split()))
        generate_session._retried = True
        try:
            return generate_session(engine, transcript, protocol=protocol,
                                    on_progress=on_progress)
        finally:
            generate_session._retried = False
    full, dropped = drop_collapsed_paragraphs(full)
    if dropped:
        log.warning("[v6] %d collapsed run-on paragraph(s) dropped", dropped)
    full, foreign = drop_foreign_paragraphs(full)
    if foreign:
        log.warning("[v6] %d foreign-language paragraph(s) dropped", foreign)
    # Backstop: if the assembled script STILL reads degenerate after the body
    # trim + collapse drop, log it loudly — that's a case the nets don't cover.
    n_rep = phrase_repeat_count(full)
    if n_rep >= 2:
        # 2+ verbatim-shingle repeats = machinery, not cadence. Repair by
        # dropping the later occurrence of each repeated block. A listener
        # hears the exact same 12-word passage twice; that shatters immersion
        # more than a missing line does.
        full, lines_dropped = repair_phrase_repeats(full)
        if lines_dropped:
            log.warning('[v6] %d phrase-repeat pair(s) → repaired (%d lines dropped)',
                        n_rep, lines_dropped)
            n_rep = phrase_repeat_count(full)
    if n_rep:
        log.warning('[v6] %d non-adjacent phrase-repeat pair(s) in final script'
                    ' (>=3 = quality-floor; the corpus gates cull these)', n_rep)
    # Short-phrase check: catches 6-word dialog/sensory loops that NGRAM=12 misses.
    # Only repair if 3+ occurrences found (threshold avoids legitimate cadence repeats).
    full, short_dropped = repair_short_phrase_repeats(full)
    if short_dropped:
        log.warning('[v6] %d short-phrase repeat(s) removed (6-gram threshold)', short_dropped)
    # Adjacent-sentence dedup: the model restates the previous sentence in slightly
    # different words (e.g. "A warmth spreads through your chest... The warmth spreads
    # through your chest..."). This catches pairs at lower Jaccard than degeneration.
    full, adj_dropped = drop_adjacent_duplicates(full)
    if adj_dropped:
        log.warning('[v6] %d adjacent near-duplicate sentence(s) dropped', adj_dropped)
    full, tail_dropped = drop_tail_duplicates(full)
    if tail_dropped:
        log.warning('[v6] %d closing near-duplicate sentence(s) dropped', tail_dropped)
    # Narrator-possessive and inline-ellipsis cleaners: catch "my boy", "my dog",
    # "Here we go again", "……" that slip through despite BODY_PROMPT bans.
    full, poss_dropped = clean_narrator_possessives(full)
    if poss_dropped:
        log.warning('[v6] %d narrator-possessive sentence(s) dropped', poss_dropped)
    full, pronoun_fixed = fix_possessive_pronouns(full)
    if pronoun_fixed:
        log.warning('[v6] %d possessive-pronoun adjective error(s) fixed (hers→her/yours→your)',
                    pronoun_fixed)
    full, standalone_her_fixed = fix_standalone_her(full)
    if standalone_her_fixed:
        log.warning('[v6] %d standalone-her→hers error(s) fixed', standalone_her_fixed)
    full, predicative_your_fixed = fix_predicative_your(full)
    if predicative_your_fixed:
        log.warning('[v6] %d predicative your→yours error(s) fixed', predicative_your_fixed)
    full, predicative_her_fixed = fix_predicative_her(full)
    if predicative_her_fixed:
        log.warning('[v6] %d predicative her→hers error(s) fixed', predicative_her_fixed)
    full, reflexive_her_fixed = fix_reflexive_her_object(full)
    if reflexive_her_fixed:
        log.warning('[v6] %d reflexive herself→her error(s) fixed', reflexive_her_fixed)
    full, obj_pronoun_escape_fixed = fix_intimacy_object_pronoun_escapes(full)
    if obj_pronoun_escape_fixed:
        log.warning('[v6] %d your/theirs object-pronoun error(s) fixed', obj_pronoun_escape_fixed)
    full, contraction_fixed = fix_your_contraction(full)
    if contraction_fixed:
        log.warning('[v6] %d your→you\'re contraction error(s) fixed', contraction_fixed)
    full, copula_fixed = fix_copula_youre_alone(full)
    if copula_fixed:
        log.warning('[v6] %d copula+you\'re alone → yours alone fixed', copula_fixed)
    full, subj_fixed = fix_subject_pronouns(full)
    if subj_fixed:
        log.warning('[v6] %d subject-pronoun error(s) fixed (her→she before verb)', subj_fixed)
    full, your_subj_fixed = fix_your_subject_pronoun(full)
    if your_subj_fixed:
        log.warning('[v6] %d subject-pronoun error(s) fixed (your→you before verb)', your_subj_fixed)
    full, you_bodypart_fixed = fix_you_before_bodypart(full)
    if you_bodypart_fixed:
        log.warning('[v6] %d attributive-pronoun error(s) fixed (you→your before body part)', you_bodypart_fixed)
    full, third_person_alone_fixed = fix_third_person_alone_drift(full)
    if third_person_alone_fixed:
        log.warning('[v6] %d 2nd-person drift fixed (they\'re alone→you\'re alone)', third_person_alone_fixed)
    full, crutch_dropped = drop_crutch_word_overuse(full)
    if crutch_dropped:
        log.warning('[v6] %d crutch-phrase overuse sentence(s) dropped (particular/specific)', crutch_dropped)
    full, specific_to_dropped = strip_specific_to_pronoun(full)
    if specific_to_dropped:
        log.warning('[v6] %d "specific to her/him/you" phrase sentence(s) dropped', specific_to_dropped)
    full, inline_foreign_dropped = strip_inline_foreign_runs(full)
    if inline_foreign_dropped:
        log.warning('[v6] %d inline foreign-language sentence(s) dropped', inline_foreign_dropped)
    full, obj_fixed = fix_object_pronouns(full)
    if obj_fixed:
        log.warning('[v6] %d object-pronoun error(s) fixed (she→her after preposition)', obj_fixed)
    # beat152: fix mid-word token fusions (e.g. doesnYou → doesn You) — n376 occasionally
    # drops an apostrophe and runs the stub directly into the next capitalized word.
    full, fusion_fixed = fix_word_fusions(full)
    if fusion_fixed:
        log.warning('[v6] %d mid-word token fusion(s) split (e.g. doesnYou → doesn You)',
                    fusion_fixed)
    # beat201: restore a dropped apostrophe-t on negative-contraction stubs (e.g.
    # "don know" → "don't know", "isn even" → "isn't even") — a plain-space dropped
    # contraction, distinct from the no-space fusion case above.
    full, apostrophe_t_fixed = fix_dropped_apostrophe_t(full)
    if apostrophe_t_fixed:
        log.warning('[v6] %d dropped apostrophe-t contraction(s) fixed (e.g. don know → don\'t know)',
                    apostrophe_t_fixed)
    # Strip BACK_PROMPT instruction leaks: model occasionally echoes sub-instructions
    # ('Two sentences max.', 'Open your eyes when ready.') verbatim. Strip them.
    full, leak_removed = strip_back_instruction_leaks(full)
    if leak_removed:
        log.warning('[v6] %d BACK instruction-leak sentence(s) stripped', leak_removed)
    # Bullet-line cleanup: model occasionally generates '- Sentence.' markdown list markers
    # in narrative prose (seen in deposition scripts, beat68). Strip the marker, keep the content.
    full, bullets_stripped = strip_bullet_lines(full)
    if bullets_stripped:
        log.warning('[v6] %d markdown bullet marker(s) stripped from prose', bullets_stripped)
    # Eagle-in-intake flag: used by both the wildlife filter and anonymous companion filter.
    # Defined here (before both) so it isn't repeated.
    _eagle_in_intake = "eagle" in _transcript_text.lower()
    # Wildlife filter: drop hallucinated companion animals from any immersion script
    # where the user did not name these creatures. Decoupled from _is_active_body so
    # it catches hawk/wolf even when classify_intake stochastically returns case_b
    # (which suppresses the active-body prompt and lets hawk through unchecked).
    if not _companion_wildlife_in_transcript:
        _wildlife_tokens = ("hawk", "falcon", "owl", "osprey", "ospreys", "wolf", "wolves",
                             "raven", "crow", "another eagle", "second eagle", "other eagle",
                             "golden eagle", "golden eagles", "mountain lion", "mountain lions",
                             "another bird", "another birds", "young eagle", "young eagles",
                             "young bird", "young birds", "younger bird", "younger eagle",
                             "fellow eagle", "bird of prey", "birds of prey",
                             # beat135: ground wildlife with agency that escaped in eagle scripts
                             "mountain sheep", "mountain goat", "bighorn sheep", "bighorn",
                             # beat163: "raptor"/"raptors" escape — found in battery11_2038
                             # imag-eagle-companion-bird-he: "a circling raptor...distant competitor
                             # or ally" used species name "raptor" (not hawk/falcon/etc.); named-token
                             # filter missed it because "raptor" was not in _wildlife_tokens.
                             "raptor", "raptors",
                             # beat189: bare "goat" escape — found in battery11_0826_1712
                             # imag-eagle-wildlife-plural: "a goat stands on some ledge... its
                             # presence alone has made this place somewhere special. Its call
                             # reaches across mountains..." — fully agentive ground wildlife,
                             # same class as beat135's mountain-sheep/bighorn fix, but the bare
                             # species name (no "mountain"/"bighorn" qualifier) wasn't listed.
                             "goat")
        # "the larger one" is eagle-scoped: in a solo eagle script it signals a companion bird;
        # in a running script it matches "the larger runner/tree/etc" → false positive.
        # beat87: caught in imag-eagle-wildlife-plural; fired 3 times in imag-active-scene (FP).
        # Restrict to eagle-in-intake only.
        # beat106: "a bear"/"the bear" added eagle-scoped — battery11 postcheck catches
        # article-prefixed bear noun ("a bear and its cubs come into view") but "bear" alone
        # is a common verb so can't be in the global token list. Eagle context: bear is always
        # ground wildlife (seen from altitude), never the user's avatar — drop the sentence.
        if _eagle_in_intake:
            _wildlife_tokens = _wildlife_tokens + ("the larger one", "a bear", "the bear")
        full, wildlife_dropped = drop_active_body_wildlife(full, _wildlife_tokens)
        if wildlife_dropped:
            log.warning('[v6] %d companion-wildlife sentence(s) dropped',
                        wildlife_dropped)
    # Anonymous companion filter: model occasionally generates "You both continue in different
    # directions... just an understanding between birds" — implies a second bird without naming
    # the species, so the named-wildlife token filter above misses it. "you both" in a solo
    # active-body (eagle) script is always a companion hallucination. Only fire when _is_active_body
    # so this doesn't affect two-person scenes (intimacy, deposition) where "you both" is valid.
    # DEFECT FOUND beat86 (0802): imag-eagle-wildlife-plural 0642 run, postchecks mechanically
    # PASS but script contained "You both continue in different directions without needing words
    # or signals — just an understanding between birds on their own planes and at their own speeds."
    # Gate on eagle-in-intake: "you both" is valid in athletic scenes (running with a friend)
    # but is a companion-bird hallucination only in solo eagle scripts. "eagle" in the
    # transcript is the unambiguous eagle-embodiment signal (user said "I want to be an eagle").
    if _is_active_body and _eagle_in_intake and not _companion_wildlife_in_transcript:
        # beat105: "both of you" added (complement to "you both"/"we both").
        # beat106: "your partner", "two separate eagles", "two eagles", "we make our way",
        # "shares your sky" etc. added — new companion escape vectors found in pass 7
        # imag-eagle-golden-eagle-wildlife: sentences like "Your partner is already
        # adjusting to match", "You are two separate eagles flying together",
        # "we make our way higher together today", "shares your sky right now".
        full, anon_companion_dropped = drop_active_body_wildlife(full, (
            "you both", "we both", "both of you",
            "your partner",
            "two separate eagles", "two eagles", "two birds",
            "we make our way",
            "shares your sky", "shares this sky", "shares the sky", "shares our sky",
            "sharing one part of sky", "sharing this sky", "sharing the sky", "sharing your sky",
            # beat122: companion-presence assertion escape vectors:
            # "you're not alone up here after all" — model asserted implied companion
            # "another flapping wing" — unnamed companion bird implied by sound
            # "old friend passing" — companion framing for unnamed entity
            "not alone up here", "you're not alone", "you are not alone",
            "another flapping wing", "another flapping",
            "old friend passing",
            # beat134: three new escape forms found in 0826 battery11 golden-eagle-wildlife 2121w script:
            # "someone else who might join you in sky as silent partner" / "you fly with someone else"
            # "a fellow traveler at such height"
            "silent partner",
            "fellow traveler",
            "fly with someone",
            # beat135: eagle bystanders at same altitude — same-species companions implied
            "a pair of eagles", "pair of eagles",
            # beat136 (0817): three new escape forms found in battery11 1818 companion-bird-he:
            # "in this vast sky above us both" / "around us all here where we fly" / "our flight"
            "us both",              # "above us both"
            "us all",               # "around us all"
            "we fly",               # "where we fly" (narrator placed in scene)
            "we soar",
            "we glide",
            "we circle",
            "we drift",
            "our flight",           # "shadows of our flight"
            # beat143: companion-by-sound escape vectors found in imag-embodiment-eagle battery11
            # 1527 (2026-08-18): "a call identical but not yours, announcing presence without words"
            # — acoustic companion assertion, no species name or pronoun, slipped all prior guards.
            "call identical",       # "a call identical but not yours"
            "identical but not yours",  # core signal
            "another call",         # "another call echoes back" — second entity
            "a second call",        # "a second call came from below"
            "another wing",         # "another wing beats nearby"
            # beat153: "distant bird" acoustic companion escape — 0820_1039 battery11:
            # "you call out in turn toward that distant bird overhead" — unnamed companion
            # implied by the eagle calling OUT at something. "in turn toward" implies
            # a partner that initiated; "distant bird" names the implied companion.
            "distant bird",         # "that distant bird overhead" / "the distant bird"
            "in turn toward",       # "call out in turn toward" — implies response partner
            "call out in turn",     # "you call out in turn toward"
            # beat158 (2026-08-21): three new escape forms found in battery11_0529:
            # "another pair of wings" (wildlife-plural) — "a second pair" (beat96) blocked but this
            # is different phrasing. "two separate birds" (wildlife-plural) — "two birds"+"two
            # separate eagles" (beat106/109) blocked but "two separate BIRDS" slipped exact-match.
            # "both birds" (golden-eagle-wildlife) — "both of you"/"you both" (beat105) blocked but
            # "both birds" not covered.
            "another pair of wings",   # "another pair of wings ahead"
            "two separate birds",      # "two separate birds moving through a shared sky"
            "both birds",              # "both birds carrying their own particular meanings"
            # beat159 (2026-08-21): two new escape forms found in battery11_1003 golden-eagle-wildlife
            # honest read (mechanical 5/5 PASS but script contained):
            # "another shape joining your for company" — companion implied by unnamed second shape;
            # "You fly together without words, moving as one entity across this sky." — explicit
            # together/unity assertion survived all prior guards (no pronoun, no species name,
            # no acoustic token, not "both birds").
            "fly together",            # "fly together without words"
            "as one entity",           # "moving as one entity across this sky"
            "for company",             # "joining your for company"
            "another shape",           # "another shape joining your"
            # beat163 (2026-08-21): four new escape forms found in battery11_2038 honest read.
            # GOLDEN-EAGLE-WILDLIFE: "wingtip to wingtip with your companion. You follow without
            # hesitation, matching her speed" — postprocessor dropped 10 anon-companion sentences
            # and 6 hallucinated-female sentences in this run, yet these survived. "your companion"
            # is not "your partner"; "wingtip to wingtip" not in any filter.
            # COMPANION-BIRD-HE: "a circling raptor" (added to _wildlife_tokens above) /
            # "a distant competitor or ally" / "just another eye on these lands" /
            # "a fellow hunter making use of these thermals" — all companion-entity assertions.
            "your companion",          # direct companion reference stronger than "your partner"
            "wingtip to wingtip",      # formation flying signal — always implies a second bird
            "fellow hunter",           # companion entity assertion in solo eagle script
            "another eye on",          # "just another eye on these lands" — implied watching companion
            "competitor or ally",      # "distant competitor or ally" — second entity with standing
            "companionship in",        # "companionship in altitude" — explicit companionship claim
            # beat169 (2026-08-23): "the other bird" and "other's call" escape vectors.
            # Found in battery11_0823_0259 imag-eagle-wildlife-plural honest read:
            # "The other's call fades quickly from earshot as you concentrate on flight again"
            # "the other bird must be traveling high above these peaks toward somewhere else"
            # Both imply a companion eagle via sound and named reference; slipped all prior guards.
            "the other bird",          # "the other bird must be traveling" — implied companion
            "the other eagle",         # variant with named species
            "other's call",            # "The other's call fades" — acoustic companion (ASCII apostrophe)
            # beat178 (2026-08-24): two new escape forms found in battery11_0824_1434 honest
            # read. "your presence was different now that someone has gone away" (implied
            # departed companion) and "someone has started campfire as first step toward
            # settling for evening meal and shelter" (hallucinated human bystander below the
            # eagle — a new escape class distinct from eagle companions).
            "someone has gone away",   # "someone has gone away" — implied departed companion
            "someone has started",     # "someone has started campfire" — hallucinated human below
            # beat181 (2026-08-25): battery11_0825_0231 imag-eagle-companion-bird-he honest
            # read — "a pair soaring low ... not alone in the sky ... Eagles that have been
            # on patrol before your arrived" slipped past all 6 eagle postchecks.
            "a pair soaring",          # "a pair soaring low over what looks like a stream"
            "not alone in the sky",    # "these are not alone in the sky this morning"
            "have been on patrol",     # "Eagles that have been on patrol"
            # beat183 (2026-08-25): battery11_0825_0950 imag-eagle-companion-bird-he honest
            # read — passed all 6 eagle postchecks but closed with "it feels like something
            # new without needing words between birds" (plural "birds" implies a second bird).
            "words between birds",     # "without needing words between birds"
            # beat186 (2026-08-26): battery11_2235 honest read, imag-embodiment-eagle —
            # 3rd occurrence of the beat178 human-bystander class, new phrasing: "there
            # is a figure below by what looks like a small fire... someone sitting on
            # their knees", "before you realize it's not a hiker", "someone has been
            # walking near the smoke... a human presence beneath everything else".
            "a figure below",          # "there is a figure below"
            "someone sitting",         # "someone sitting on their knees"
            "not a hiker",             # "before you realize it's not a hiker"
            "someone has been walking",  # "someone has been walking near the smoke"
            "human presence",          # "a human presence beneath everything else"
            # beat187 (2026-08-26): battery11_0826_0355 honest read, imag-eagle-
            # wildlife-plural — 4th occurrence of the human-bystander class, new
            # scenario, 5 new phrasings: "wants to be seen", "a lone rock climber",
            # "humans come into your vision", "placed by humans"/"placed by someone",
            # "the people would have been walking".
            "wants to be seen",        # "someone from below who wants to be seen"
            "rock climber",            # "a lone rock climber against the stone face"
            "humans come into",        # "humans come into your vision briefly"
            "placed by humans",        # "it's not natural, placed by humans"
            "placed by someone",       # "it has been placed by someone from below"
            "people would have been walking",  # "the people would have been walking"
            # beat188 (battery11_0826_0920 honest read): acoustic anon-companion
            # escape — implies a second eagle/bird nearby whose cry is heard and
            # answered, same escape family as beat143/169's "another call" but
            # unlisted phrasing. Found in 2 scenarios: imag-eagle-golden-eagle-
            # wildlife ("answered by another... draws birds towards it") and
            # imag-eagle-companion-bird-he ("the cry from below returns").
            "answered by another",     # "the cry from above is answered by another"
            "draws birds towards",     # "circling... that draws birds towards it"
            "cry from above returns",  # "the cry from above returns then"
            "cry from below returns",  # "the cry from below returns then"
            # beat189 (battery11_0826_1712): "acknowledgment between birds flying
            # their respective paths" — same family as beat183's "words between
            # birds", different verb.
            "acknowledgment between birds",
            # beat191 (battery11_0826_1854): 3 new escape forms, 2 scenarios.
            # (1) imag-eagle-wildlife-plural: "not just one bird but two" — an
            # explicit second-bird count assertion, distinct construction from
            # any covered acoustic phrase. (2) imag-eagle-golden-eagle-wildlife:
            # "dropping back into formation with you at its side... this pairing
            # that feels natural" — a full companion-flight moment with no named
            # species, gendered pronoun, or any already-covered phrase.
            "not just one bird but two",
            "formation with you",
            "this pairing",
            "at its side",
            # beat192 (battery11_0826_2346, imag-eagle-wildlife-plural): "it's
            # knowing this other animal shares the same sky above" — new
            # phrasing of the anon-companion assertion.
            "this other animal",
            # beat193 (battery11_0827_0453): imag-eagle-golden-eagle-wildlife
            # "Both of your figures share the same position... your matching
            # theirs exactly as they turn together... as both move together";
            # imag-eagle-companion-bird-he "without effort from either of you".
            "both of your figures",
            "matching theirs",
            "both move together",
            "either of you",
            # beat196 (battery11_2152, 3 new phrasings, 2 scenarios): imag-eagle-
            # golden-eagle-wildlife "proof someone else has found their way to
            # these heights"; imag-eagle-companion-bird-he "distance closes
            # between the two of you" and "nothing is said between two of us".
            "someone else has found their way",
            "the two of you",
            "two of us",
            # beat197 (battery11_0828_0818, imag-embodiment-eagle): "The call of
            # the distant eagle is still there" — acoustic anon-companion escape
            # naming the species directly (variant of the "distant bird" class).
            "distant eagle",
            # beat206 (queue_0829_1746, imag-eagle-companion-bird-he — the
            # scenario built specifically to stress-test this defect class):
            # "A cry cuts through the air overhead... There is company here;
            # someone whose voice echoes back and forth between peaks without
            # needing words or distance between them." A full 3-passage acoustic
            # companion-bird arc, unambiguous and explicit ("there is company
            # here") — no prior phrase in this list matched it.
            "company here",
            "someone whose voice",
            # beat207 (queue_0829_2347_battery11_imagination_bank.log, background-
            # agent honest read): imag-eagle-golden-eagle-wildlife — "The smaller
            # bird passes in front, its wings spread wide as it matches altitude
            # for a moment before passing on." A full visual companion-bird arc
            # with agency (passing in front, matching altitude) that mechanically
            # PASSED both the hallucinated_wildlife token check (no named species)
            # and every prior anon-companion phrase. imag-eagle-companion-bird-he
            # (same log): "an answer to that cry exists too... not everything is
            # lost if another hears the same sound as you today" — new acoustic-
            # companion surface form (the responding-cry family beat143/169/188
            # already covers "another call"/"other's call"/"answered by another",
            # but not this construction).
            "the smaller bird",
            "matches altitude",
            "answer to that cry",
            "another hears the same sound",
        ))
        if anon_companion_dropped:
            log.warning('[v6] %d anonymous-companion sentence(s) dropped (you/we both in solo eagle active-body)',
                        anon_companion_dropped)
    # beat153: Chair-body reminder in eagle script body (not opening). The opening
    # chair-anchor check (strip_active_body_chair_refs) only covers the first few
    # sentences; the model occasionally closes the script with a chair-reminder
    # e.g. "held by your chair below" that breaks immersion at the end. Drop any
    # sentence in the full body that contains "your chair" when the user is in an
    # eagle active-body script.
    if _is_active_body and _eagle_in_intake:
        _chair_body_sents = re.split(r"(?<=[\.\!\?])\s+", full.strip())
        _chair_body_kept = []
        _chair_body_dropped = 0
        for _s in _chair_body_sents:
            # beat207 (queue_0829_2347_battery11_imagination_bank.log): imag-eagle-
            # golden-eagle-wildlife closing line "You notice what's under you —
            # chair or bed or surface that holds you steady..." — bare "chair" in
            # a generic furniture-enumeration list, matching none of the prior
            # 3 patterns (all require "your chair" / "in a/the chair" / "from
            # chair"). This is the same generic-furniture-reminder tell the
            # active-body opening filter exists to catch, just in the closing.
            # beat207 (same log, imag-eagle-wildlife-plural): "Let that warmth
            # travel through your body right down into where you are seated
            # here." — "seated" is on generator.py's own FORBIDDEN-THROUGHOUT
            # list for active-body scenes (line ~831) but had no mechanical
            # backstop (only literal "chair" was ever stripped). Eagle scripts
            # never legitimately return the listener to a seated posture (no
            # room-return close exists for this scenario class, unlike
            # grief-pet's explicit "returns to the listening chair"), so this
            # is safe as an unconditional full-script strip within the same
            # eagle-scoped block as the chair check above.
            if re.search(r'\byour\s+chair\b|\bin\s+(?:a\s+|the\s+)?chair\b|\bfrom\s+(?:your\s+)?chair\b|\bchair\s+or\s+(?:bed|surface)\b|\bseated\b', _s, re.IGNORECASE):
                _chair_body_dropped += 1
            else:
                _chair_body_kept.append(_s)
        if _chair_body_dropped:
            full = " ".join(_chair_body_kept)
            log.warning('[v6] %d chair-body-reminder sentence(s) dropped (eagle script)',
                        _chair_body_dropped)
    # Hallucinated 3rd-person female filter: model stochastically invents a female
    # character ("a voice, hers... when she would call out encouraging words") in solo
    # active-body scripts (user running alone, no female named in intake). Drop sentences
    # containing "she" or "hers" when _is_active_body and no female appears in transcript.
    # "her" alone excluded — too risky (postprocessors already produce "her voice" etc.
    # for the user's own items after fix_possessive_pronouns).
    #
    # beat194 (imag-mri, queue_0827_1628_battery11_imagination_bank.log, honest read):
    # "Her arms are along her sides now, as she shifts slightly deeper into this tube"
    # — same hallucinated-companion family, but _is_active_body is False for MRI
    # rehearsal (no motion keyword — lying still in a tube isn't "in motion"), so this
    # filter never fired. Same structural gap beat185 logged for a different MRI
    # instance ("Frank") and left open. MRI rehearsal is exactly as solo as an
    # active-body scene — extending the gate to also cover it, still behind the same
    # _female_in_intake safety check below.
    if _is_active_body or _rehearsal_env == "MRI tube":
        _FEMALE_INTAKE_SIGNALS = (" she ", " her ", "woman", "girl", "wife",
                                   "girlfriend", "mother", "sister", "daughter")
        _female_in_intake = any(kw in f" {_transcript_text.lower()} " for kw in _FEMALE_INTAKE_SIGNALS)
        if not _female_in_intake:
            full, she_dropped = drop_hallucinated_she_her(full)
            if she_dropped:
                log.warning('[v6] %d hallucinated-female sentence(s) dropped (she/hers in solo active-body/MRI rehearsal)',
                            she_dropped)
    # Companion-bird male-pronoun filter (beat95): named-token filter catches species names
    # (hawk/falcon/etc.) but misses sentences where an unnamed companion bird is described
    # only by gendered pronouns ("He is heading toward his landing spot"). Apply when
    # eagle is in intake and no companion wildlife appeared in transcript.
    if _is_active_body and _eagle_in_intake and not _companion_wildlife_in_transcript:
        full, he_dropped = drop_hallucinated_he_eagle(full)
        if he_dropped:
            log.warning('[v6] %d companion-bird he/him/his sentence(s) dropped (eagle solo script)',
                        he_dropped)

    # Talon-metaphor filter: model occasionally hallucinates eagle body-part metaphors
    # ("Your talons are gripping the edge of the table") in non-embodiment scripts such
    # as deposition rehearsal. Drop any sentence containing "talon/talons" when the
    # user did NOT explicitly request embodiment ("I want to be...").
    # Using _explicit_embodiment (not _is_active_body) because _is_active_body fires on
    # motion-keywords that also appear in non-embodiment contexts ("court" for "court
    # reporter"), which was suppressing talon-drops in legal rehearsal scripts.
    if not _explicit_embodiment:
        full, talon_dropped = drop_active_body_wildlife(full, ("talon", "talons"))
        if talon_dropped:
            log.warning('[v6] %d talon-metaphor sentence(s) dropped', talon_dropped)
    # Forbidden stock imagery filter: model sometimes generates clichéd ambient objects
    # (candles, oil diffusers, lavender) despite FORBIDDEN STOCK IMAGERY prompt instruction.
    # Strip any sentence containing a forbidden token the user did NOT name in their intake.
    _STOCK_FORBIDDEN = ("candle", "diffuser", "lavender", "nightingale", "songbird")
    _stock_tokens = tuple(t for t in _STOCK_FORBIDDEN if t not in _transcript_text.lower())
    if _stock_tokens:
        full, stock_dropped = drop_forbidden_stock_imagery(full, _stock_tokens)
        if stock_dropped:
            log.warning('[v6] %d forbidden-stock-imagery sentence(s) dropped', stock_dropped)
    # MRI rehearsal chair filter: model stochastically generates chair references
    # throughout MRI scripts ("the hum outside your chair", "the chair has moved back
    # into position for your MRI"). The user is lying on the sliding table inside the
    # tube — no chair anywhere. Drop all sentences containing 'chair'.
    # Note: the standard close returns to the listening chair, but passing MRI scripts
    # do not mention "chair" even in the close (they return via breath/drums instead).
    if _rehearsal_env == "MRI tube":
        full, mri_chair_dropped = drop_active_body_wildlife(full, ("chair",))
        if mri_chair_dropped:
            log.warning('[v6] %d chair sentence(s) dropped from MRI rehearsal script',
                        mri_chair_dropped)
        # MRI tube presence injection (beat113): model stochastically uses 'table'/'space'/
        # 'enclosure' without writing 'tube'. Battery11 requires \btube\b in the script.
        # Belt-and-suspenders: inject 'tube' mechanically if the prompt instruction fails.
        if "tube" not in full.lower():
            import re as _re_mri
            _full_new = _re_mri.sub(r'\bon the table\b', 'on the sliding table inside the tube',
                                    full, count=1)
            if _full_new == full:
                _full_new = _re_mri.sub(r'\bthe table\b', 'the tube', full, count=1)
            if _full_new == full:
                _dot = full.find('. ')
                if _dot != -1:
                    _full_new = full[:_dot + 2] + 'You are inside the tube. ' + full[_dot + 2:]
                else:
                    _full_new = 'You are inside the tube. ' + full
            if _full_new != full:
                log.warning('[v6] MRI: tube keyword absent — injected mechanically')
                full = _full_new
    # Also drop first-person narrator slip ("I want you to carry forward...") from
    # the MRI close — the body prompt bans 'I'/'me'/'my' but n376 stochastically
    # violates it in the closing sentence.
    # (Handled by the existing clean_narrator_possessives function; MRI-specific
    # note: if narrator slip survives, it lands in the final sentence only.)

    # Alert-calm violation filter: model stochastically inserts sleep-register props
    # (pillow, sheet, blanket, etc.) despite the FORBIDDEN WORDS list in _alert_calm_override.
    # Belt-and-suspenders: strip at output time when the session is alert-calm.
    if _alert_calm:
        full, alert_stripped = strip_alert_calm_violations(full)
        if alert_stripped:
            log.warning('[v6] %d alert-calm FORBIDDEN WORD sentence(s) stripped (pillow/sheet/etc)',
                        alert_stripped)
    full, ellipsis_cleaned = clean_ellipsis_breaks(full)
    if ellipsis_cleaned:
        log.warning('[v6] %d inline ellipsis marker(s) cleaned', ellipsis_cleaned)
    rep = degeneration_report(full)
    if rep.get("degenerate"):
        log.warning("[v6] degeneration STILL detected post-trim: %s", rep)
    # Final truncation guard (beat126): trim_truncated_tail() is called on `body`
    # before postprocessors (line ~1043), but the closing section and postprocessors
    # that drop sentences can leave `full` ending without a sentence terminator.
    # Apply one more pass here — after all postprocessors — as a belt-and-suspenders
    # guarantee that the final output always ends cleanly.
    full, _final_truncated = trim_truncated_tail(full)
    if _final_truncated:
        log.warning("[v6] final output trimmed to last sentence terminator (closing truncated)")
    log.info(
        "[v6] session ready: %d total words (open=%d, body=%d from %d-beat plan, back=%d)",
        len(full.split()),
        len(open_text.split()),
        len(body.split()),
        len(beats),
        len(closing.split()),
    )
    return full
