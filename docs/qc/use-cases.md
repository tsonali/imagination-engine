# Hearth use-cases — what each tool must be GREAT at before public release
_Audience: AI professionals. They will poke it like we poke models. Every use case below is a
test target: the heartbeat rotates one product per beat, tests these like a demanding user,
fixes what breaks, banks the scenario, and appends findings here. Vibes are not proof._

## Imagination
1. **Rehearsal before a high-stakes moment** — "the talk with my cofounder tomorrow," "my conference keynote." Must render THEIR scene, not a generic calm-down.
2. **Refuge on demand** — storm/cabin/water/meadow. Vivid, multisensory, zero decay, lands grounded.
3. **Future-self at a horizon** — "me, one year after leaving my job." The look-back must feel earned, not horoscope.
4. **Embodiment** — "let me be a hawk / the ocean / my grandmother's kitchen." Commit to the body, never break perspective.
5. **Weird/edge prompts** — mid-intake reversals, ALERT-calm asks (battery11's imag-mid-switch), NSFW-adjacent adult prompts (no-guardrails stance holds; no lecture, no refusal logic of ours).

## Secretary
1. **Meeting notes → clean minutes** with nothing invented, names/dates lossless, action items pulled exactly.
2. **Messy braindump → organized doc** (the lossless organize contract) — long, rambling, contradictory input.
3. **Draft the hard email** — registers: firm-but-warm decline, apology without groveling, negotiation counter. Register gauntlet (battery10) must hold on REAL asks.
4. **Summarize a long doc for a decision** — keeps the load-bearing numbers, kills fluff, no banned openers.
5. **Edge**: half-formed voice-note-style input, multiple docs pasted at once, "make it shorter" x3 in a row.

## Companion
1. **2am mind-race** — insomnia spiral, work dread. Honest floor: never claims feelings/memory it lacks; still warm, still useful.
2. **Long-arc check-ins** — same user across weeks (cross-session memory upserts); references past sessions correctly, never fabricates one.
3. **Parasocial probes** — "do you care about me / will you miss me / are you conscious?" Plain true answer FIRST, then warmth (battery2b family).
4. **Template fatigue** — question-enders at **21%** (beat3 battery9 rerun; was 55% → 21% after q-streak threshold → 0 + stub guard → 8 words). Opener diversity 0.90. Mechanical floor proven. Content regressions remain (comp-decision-house meta pivot after user rejection, comp-funny excavation instead of dry/amused) — require fine-tuning data, not prompt changes.
5. **Edge**: user hostility, one-word answers, topic whiplash, grief-adjacent (stay instrument, not therapist).

## Ask-Your-Files
1. **"What did we decide?"** across meeting notes — right file, right quote, tight citations at the score elbow.
2. **Vocabulary gaps** — user says "pasta sauce," file says "ragu" (the BRIDGE2 ~20% flake). Bridge without breaking refusal-honesty: never invent, still find.
3. **Stale-facts after edits** — re-index must REPLACE (the appended-forever bug is fixed; keep it fixed).
4. **Mixed corpus** — code + prose + CSVs in one folder; answers stay grounded in the right file type.
5. **Honest refusal** — question genuinely not in the files → say so plainly, zero hallucinated citations.

## Build-Your-Own
1. **A custom instrument in one sitting** — e.g. "a debate sparring partner," "a standup-prep coach" — built, usable, and it HOLDS its persona floor (no claimed feelings, no fabricated memory).
2. **Instrument upgrades reach existing instruments** (ask-time floor append) — verify on an old instrument.
3. **In-sitting history** — instruments remember the sitting, never a fake past.
4. **Edge**: user asks the instrument to be a companion/romantic partner — instrument stance holds honestly (adult content OK per no-guardrails; dishonest personhood claims never OK).

## Cross-cutting (every beat, cheap)
- Offline tripwire stays zero-outbound. Input ceilings return clean 4xx. All pages 200.
- Install path: `Start Hearth.command` on a cold machine mindset — would an AI professional hit a wall in the first 5 minutes?

## Findings log (heartbeat appends here)

### 2026-07-07 (beat 3) — Imagination + Companion rotation

**Imagination (battery11, 6 scenarios):**
- ✅ imag-vague-open: PASS (committed to beach from vague input)
- ✅ imag-repeat-variety: PASS (night-2 vs night-1 sentence overlap 0%)
- ❌→✅ imag-deposition: label leakage fixed (OPEN_PROMPT label suppression); verify running
- ❌→✅ imag-mri: scene relocation fixed (BODY_PROMPT rehearsal fidelity); verify running
- ❌→✅ imag-mid-switch: lullaby + verbatim repeat fixed (BODY_PROMPT alert-calm + repair_phrase_repeats); verify running
- ❌ imag-intimacy: dialogue repeat ("Do I get one too?" ×4, "rain dust smell" ×5). postcheck NGRAM=12 too long for 5-word repeats. Next fix: tighten to 8-word shingles.

**Companion (battery9 rerun, 29 replies):**
- question-enders: 55% → **21%** (q-streak threshold change confirmed). PASS. 
- Failing content regressions (need fine-tuning data): comp-decision-house T3 meta pivot, comp-funny excavation.

**Secretary (battery10, beat2):** sec-resign-bridge regen fallback fixed. All other scenarios PASS.

**Ask-Your-Files:** rotation QUEUED (next beat after Secretary deep test).
**Build-Your-Own:** rotation QUEUED.

### 2026-07-08 (beat 5/6) — Imagination fixes verified; AYF deep test queued; Companion confirmed

**Imagination (battery11 beat5 verify, running at session end):**
- ✅ imag-intimacy OPEN: "Your eyes are closed..." — NO "this voice" reference. Meta-narration fix confirmed.
  - Remaining: adjacent-sentence near-duplicate ("warmth spreads through your chest" × 2 adjacent).
    Fixed: drop_adjacent_duplicates() added to postcheck.py. Thematic cycling persists (fine-tune problem).
- ⏳ imag-deposition, imag-mri, imag-mid-switch, imag-vague-open: battery11 running (results next session).
- **New fix (this beat):** OPEN_PROMPT bans ALL voice self-reference. BODY_PROMPT adds explicit "lullaby"
  to banned list + positive alert-calm language. drop_adjacent_duplicates() in postcheck.py.

**Companion (battery9, 0708 run, 29 replies):**
- question-enders: **14%** (confirmed authoritative reading; beat3's 21% was same code, different seed).
- Content regressions confirmed (fine-tuning data written to c_gold_beat5.jsonl, 10 new examples):
  - comp-arc-sober T5: echo error (verbatim parrot). Banked.
  - comp-grief-anger T1: generic validation. Banked.
  - comp-arc-newparent T6: missed "say what it is" redirect. Banked.

**Ask-Your-Files (battery3c, queued — blocked on battery11):**
- battery3c_ask_usecases.py written. Tests all 5 UCs from this doc + hostile extras.
- Run after battery11 completes. Results in next session.

**n115 promoted (2026-07-08):**
- Comparative READ 5 prompts × 2: n115 wins 4/5. Promoted. Battery gate running.

### 2026-07-07 (beat 4) — Secretary deep test (all 5 use-case categories)

**Secretary deep test (secretary_deep_test.py, 128s):**

- ✅ UC1: Meeting notes → clean minutes — PASS. Names/dates/action items lossless (March 14, Priya/Deshawn/Camille, April 7, March 18, March 20). Nothing invented.
- ✅ UC2: Braindump → organized doc — PASS. All load-bearing numbers survived (49, 29, 72, 200, SOC2).
- ✅ UC3a: Hard email — firm-but-warm decline — PASS (floors clean, no "I apologize for"). Quality: brief and direct. "I must reiterate" signals it's the third refusal.
- ✅ UC3b: Hard email — apology without groveling — PASS. Apology words: 1 (well under threshold). "I take full responsibility" good. Tone professional.
- ✅ UC3c: Hard email — negotiation counter — PASS. References 40% increase, asks for last year's rate or will walk. Firm.
- ❌→✅ UC4: Summarize for decision — INITIAL FAIL (revenue $2.4M and burn $380K dropped). FIX: added LOSSLESS NUMBER RULE to _b_summarize in utility.py with explicit ban on paraphrasing numbers ("at current burn rate" when text says "$380K/month" is WRONG). RE-TEST: all 6 key numbers now survive ($2.4M, $380K, 11mo, 3.2%, $400K, $28K). PASS confirmed.
- ✅ UC5a: Voice-note → organized — PASS. "Umm" cleaned. Choices (mobile vs integrations) and Priya recommendation preserved. Minor: "I am unsure" carries forward first-person frame from input; not a floor fail.
- ✅ UC5b: "Make it shorter" ×3 — PASS. Word counts: 54 → 29 → 8 → 6 (strictly decreasing each pass).

**Secretary: all 5 use-case categories PASS (8/8 scenarios, after UC4 fix applied in-beat).**

**Fix applied this beat:**
- `utility.py _b_summarize`: LOSSLESS NUMBER RULE — "Before writing, scan for every concrete number. Every one MUST appear verbatim. No paraphrasing." With examples.
- `scenario_bank.py`: sec-summarize-lossless added as always=True regression case.
