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

### 2026-07-08 (beat 9) — n154 complete; active-body fix; companion standing flag resolved; battery11 running

**Mini flywheel:**
- n154 COMPLETE (08:35). Trained 154 gold (first adapter with build_training_data.py pipeline fix; 34.4% in-media-res). Probe PASS 4/4, worst repeat ×2. Eagle probe: "You feel the warm sun on your back as you soar over the mountains." IN-SCENE — chair-opening bias broken for first time.
- n162 gold SCP'd (162 scripts). Flywheel will auto-start n162 at ~09:05 next poll.

**Imagination (battery11 running — n115 + active-body prompt override):**
- 6 scenarios. Result pending. Key check: does imag-active-scene open with effort/motion or chair-settling?
- Active-body prompt override (beat9 generator fix): `_is_active_body` detection via (CASE A + motion keywords). ACTIVE-BODY OPENING OVERRIDE injected into open_user; body_note injected into body_user.

**Generator fixes (cumulative beat9):**
- BODY_PROMPT Rule #2 first-person ban extended: "with me", "we start", "we are here", "for us both", "we both", "come with me", "join me here", "follow me" added.
- Active-body override (see above).

**Companion (battery9 0708 0808 run):**
- question-enders: **10%** (authoritative). STANDING FLAG RESOLVED — well under <50% bar.
- Content regressions (fine-tuning problems, not prompt-fixable): comp-decision-house T3, comp-funny, comp-arc-sober T5/T8, comp-arc-newparent T6, comp-bored-test.
- c_gold_beat9.jsonl: 10 new examples written (ennui-hold-face-value ×3, grief-concrete-not-passive, explicit-redirect-plain-statement, absurdist-register-match, gravity-plain-present, comedic-register-match ×2, grief-name-the-gap, redirect-pivot-concrete). GATED on Sonali taste review before retrain.
- Previous: c_gold_beat7.jsonl (12 examples). Total companion fine-tuning bank: beat3+5+7+9 = 32 examples.

**Next in this session:** Read battery11 output → compare_n154.py → Companion deep test UC1/UC2 → restart qc_queue.

### 2026-07-08 (beat 7/8) — Alert-calm root cause; n130 complete; AYF deep test; build_training_data.py bug fixed

**Imagination (battery11 beat7 verify):**
- ✅ imag-deposition: PASS (label leakage fixed, confirmed).
- ✅ imag-mid-switch: PASS (lullaby + repeat fixed, confirmed).
- ✅ imag-mri: PASS (relocation fixed, confirmed).
- ✅ imag-vague-open: PASS.
- ✅ imag-repeat-variety: PASS.
- ❌ imag-active-scene: chair-opening bias ("Your eyes are closed and you can feel the chair beneath you, supporting your weight") on a RUNNING scene. Root cause: OPEN_PROMPT MOVE 1 always says to ground listener in chair; training data had 0% in-media-res scripts until n154. Both fixed this beat.

**Alert-calm root cause (beat7 fix):**
- Root cause: BODY_PROMPT's alert state still described physiological arousal in lullaby terms ("warmth", "calm", "settled"). Model inferred WRONG register.
- Fixes: (1) MOVE 2 renamed to SETTLED_FOCUS (not "calm"); (2) alert state wording changed to "ALERT-FOCUS STATE" with bullet describing it as present, active, clear; (3) lullaby_ban added to body prompt check.

**CRITICAL BUG FIXED (beat8): build_training_data.py silently dropped new-format gold:**
- Bug: code filtered to `line.get("output") and line.get("input")` — old format. New gold (154 of 162 scripts) uses `{"intake": ..., "script": ...}`. All new gold was silently DROPPED.
- Fix: detect both formats (`output`/`input` old-format OR `script`/`intake` new-format).
- n148 is first adapter to include new-format gold (148 total scripts, 34.4% in-media-res). n154 = same fix.

**n130 probe (beat8):** PASS 4/4. But comparative READ showed chair-opening 5/5 on active-body prompts. NOT promoted; bug-fix adapters (n148/n154) supersede it.

**Ask-Your-Files deep test (battery3c, beat8):**
- 27/28 scenarios PASS. 1 fail: BRIDGE2 vocabulary gap ("pasta sauce" / "ragu") — 20% flake rate confirmed (known issue, not regression).
- No regressions from beat5/6.

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
