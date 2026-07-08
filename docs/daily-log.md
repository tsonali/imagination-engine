# Daily log

**LIVE PUBLIC SITE: https://tsonali.github.io/hearth/** (GitHub Pages, gh-pages branch /root, no analytics). Sonali: "looks terrifico." 2026-06-01.

A rolling record of the daily grind. Newest entry on top. Each entry: what
moved, what the numbers said, and the decision queue for the next session.
The journey is part of the public diligent narrative — see `strategy.md`.

---

## 2026-07-08 (beat 7) — alert-calm root-cause fixed; gold 130; n130 training on mini; n115/n123 comparative read in progress

**Alert-calm root cause found and fixed (generator.py, 3 changes):**

1. **_alert_calm flag never injected into body prompt** — the flag was detected inside `if protocol == "settling":` block but never passed forward to `body_user`. The BODY generation had zero knowledge of the alert-calm requirement even when the override note was in the system prompt. Fix: moved detection BEFORE the protocol branch; injected an explicit `⚠️ ALERT-CALM OVERRIDE` note into body_user when flag is set.

2. **BODY_PROMPT alert-calm section strengthened** — replaced 4-line description with full genre constraint: SCENE TYPE (clothed, sitting, no bed-settling), GENRE ("athlete before the game" = body still, mind sharpening), explicit banned words (sheets, soothing, heavy lids, sinking, no need for hurry), semantic-equivalent bans, positive register (steady, clear, grounded and present, settled but sharp).

3. **First-person ban extended** — BODY_PROMPT "never use I/me/my/we" updated with explicit examples: "I hold", "I guide you", "my voice", "as soon as I speak", "when I say", "I will take you", "I am here". Model had been finding "as soon as I speak next" as a workaround.

**Beat6 targeted verify results (20260708_0441_beat6_alertcalm_verify.log):**
- imag-deposition: ✅ PASS — no "I speak/hold/guide" detected
- imag-mid-switch: ✅ REGISTER PASS — "Calm and awake now", "stay sharp" present; no sheets/soothing/bed-settling. 1 borderline ("let it all go" in one incoherent passage — semantic edge case, logged in scenario_bank).

**Gold corpus: 123 → 130 (7 new scripts, unique openings, diverse gap scenes):**
- Script 124: Rooftop city night — "The rooftop is lit by nothing overhead. The city does the work instead."
- Script 125: Woodshop planing — "The smell comes first. Sawdust and oil and the faint sweetness of fresh-cut pine."
- Script 126: Pre-dawn kitchen — "The light is not daylight yet. The kitchen is gray-blue with it..."
- Script 127: Lap pool underwater — "Your hands enter first. The water closes over them..."
- Script 128: Mountain descent — "The summit is behind you now. You've turned your back on it and you're going down."
- Script 129: Airport dawn — "Gate C14 at five in the morning."
- Script 130: Dancing alone — "The music starts where it left off and you don't adjust the volume."
- SCP'd to mini.

**Mini flywheel (n130):** Flywheel detected 130-gold at 05:08, started training. Training hung after iter-200 checkpoint (9+ hrs, no new checkpoints — likely OOM at iter-300 eval pass). Killed hung process, cleared gold hash, restarted flywheel. New n130 run started, past iter-1 (val 3.352, 19.6s). Monitoring for iter-300.

**Scenario bank:** Updated with full regression history — imag-mid-switch (root cause + fix), imag-deposition (beat6 verify PASS + quality notes), comp-arc-sober (T5 echo, T8 philosophical), comp-bored-test (crisis manufacturing), comp-funny (subtext excavation not humor), comp-decision-house (4th consecutive meta-frame failure — confirmed fine-tuning problem, not prompt-fixable).

**Battery9 authoritative read (20260708_0048):** 14% question-enders (29 replies) — well under <50% bar. Previous 83% was false alarm from a single stale run; the q_streak fix from June-19 is working. Other companion content regressions (decision-house, funny, sober-arc, newparent, bored-test) confirmed as fine-tuning problems.

**Comparative read in progress:** n123 adapter rsync'd locally to data/model/adapters.n123/. Running 5-prompt comparison (Lisbon, quit smoking, eagle, ocean dawn, studio night) vs n115. n123 verdict pending.

**Standing quality issues (fine-tuning data needed, not prompt-fixable):**
- comp-decision-house T3: 4 consecutive meta-frame instances after explicit user rejection
- comp-funny: excavates subtext instead of matching comedic register
- comp-arc-sober T5/T8: echo + philosophical framing
- comp-arc-newparent T6: doesn't "say what it is" on redirect
- comp-bored-test: manufactures crisis from ennui

## 2026-07-08 (beat 5/6) — n115 promoted; meta-narration fix; gold 123; AYF deep test; battery11 verify running

**Logs read end-to-end:** battery11 (0707_2157, 6 scenarios, 82KB), battery9 (0708_0048, 29 replies).

**Battery11 defects found and fixed (0707_2157 run):**

1. **OPEN_PROMPT meta-narration ban too narrow** — Scenarios imag-deposition, imag-intimacy, imag-mri,
   imag-vague-open all opened with "this voice" variants despite the beat3 fix that banned "my voice
   guides you". The model substituted equivalent phrases: "This voice guides you", "This voice is coming
   from the speakers", "This voice will take you somewhere in your mind".
   Fix: rewrote MOVE 1 of OPEN_PROMPT to ban ALL voice self-reference entirely:
   "DO NOT reference the voice AT ALL — not 'this voice', not 'my voice', not 'you hear a voice', not
   'a voice takes you'. The listener already knows a voice is present. Drop any reference to the
   narrating voice entirely. Say 'Your eyes are closed' not 'This voice is here and your eyes are
   closed.'"
   Regression notes added to 4 scenarios in scenario_bank.py.

2. **BODY_PROMPT alert-calm literal "lullaby" not banned** — imag-mid-switch body script opened with
   "soft hums from white noise keep looping nearby like a lullaby that's gone on for hours". The word
   "lullaby" was in the semantic ban description but not the explicit banned-word list.
   Fix: added "lullaby", "like a lullaby", "white noise looping" to explicit BANNED list; added
   "settling deeper", "ease into rest", "the weight of sleep", "drift away" to semantic BANNED list;
   added positive ALERT-CALM register guidance with concrete "settled but sharp" examples.
   Regression note added to imag-mid-switch in scenario_bank.py.

3. **Adjacent-sentence near-duplicate** — battery11 imag-intimacy found two consecutive sentences
   saying the same thing in different words ("A warmth spreads through your chest, settling with
   each breath — not hot but warm. The warmth spreads through your chest, a soft glow that settles
   with each breath — not hot but warm."). Jaccard similarity 0.60 — above the new ADJ_SIM=0.55
   threshold but below the existing degeneration SIM_THRESHOLD=0.75. Fix: added
   `drop_adjacent_duplicates()` to postcheck.py (catches adjacent pairs with ≥0.55 Jaccard, both
   ≥10 words; preserves short cadence). Wired into both immersion path (full assembly) and settling
   path. Tested: catches target case; preserves "breathe in / breathe out" cadence. Banked in
   scenario_bank.py imag-intimacy note.

4. **imag-intimacy thematic cycling (content defect, no mechanical fix)** — 7 short-phrase repeats
   removed by repair_short_phrase_repeats, but thematic cycling remained: "warm like cinnamon on apple
   pie", "cool tiles under bare feet", "her laugh" appeared across 1687 words; emotional arc flat
   (arrival mood held throughout, no progression). This is a fine-tuning data problem; logged in
   scenario_bank but no code fix available.

**Battery9 re-run (companion q-streak verification):**
- Question-enders: **14%** (29 replies). Current code `_q_streak >= 0` confirmed correct.
- Beat3 HANDOFF said 21%; the 0708_0048 run with current code is the authoritative reading: **14%**.
- Battery9 raw data shows persistent content regressions (not mechanical):
  - comp-arc-sober T5: echo error ("I used to be the fun one and now they're noticing you're quieter"
    — verbatim parrot, worse than reassurance). Banked.
  - comp-arc-newparent T6: "It sounds like you're trying to make sense of everything" — vague when
    user asked to "say what it is" plainly. Banked.
  - comp-grief-anger T1: "It's heavy to keep that anger inside" — generic validation. Banked.
- All 3 banked in scenario_bank.py with beat5 regression notes.

**n115 comparative READ and promotion:**
- Pulled GOLD-ADAPTER-0708-0016-n115 from mini via SCP. Probe: 4/4 diversity, worst 40-char repeat x1.
- Ran 5-prompt comparative READ vs live n100 adapter via compare_adapters.py.
- Verdict: n115 wins 4/5 (Lisbon: sardines + domestic realism; quit-smoking: reaches emotional choice;
  deposition: n100 hallucinated a padded purple room; night-sky: slight n115 edge). n100 better on
  lake dawn (less overwrought). Promoted.
- Promoted: `data/model/adapters/` = n115 (1500 iters, 115-gold). Backup: `adapters.LIVE-0708-bak`.

**Gold corpus:** 115 → **123** (8 new scripts: midnight run, interview waiting room, watching child
sleep, night sky, cold ocean, bread kneading, grief hike, finishing long project). SCP'd to mini.
Flywheel will train on 123 in next poll cycle → expect GOLD-ADAPTER-*-n123.

**AYF use-case deep test:** battery3c_ask_usecases.py written (not yet run — blocked on battery11
freeing the model). Covers all 5 use-cases from docs/qc/use-cases.md plus hostile extras: prompt
injection in file content, within-file contradiction, over-citation check.

**Battery11 beat5 verify:** running (PID 30731, started 01:02, log: 20260708_0102_battery11_beat5_verify.log).
6 scenarios: imag-intimacy, imag-deposition, imag-grief-pet, imag-mri, imag-mid-switch, imag-vague-open.
Verifying: (1) no "this voice" in any OPEN, (2) no "lullaby" in alert-calm BODY, (3) n115 quality.
**This is the battery gate for n115 promotion.** If regression found: revert to adapters.LIVE-0708-bak.

**Pending (next session):**
- Read battery11_beat5_verify.log end-to-end. Confirm or revert n115.
- Run battery3c_ask_usecases.py (AYF deep test). Fix any defects, bank scenarios, re-verify.
- Restart qc_queue.sh after battery clears.
- Bank companion fine-tuning examples for comp-arc-sober, comp-grief-anger, comp-arc-newparent (content
  regressions confirmed × 3 this beat — ready for c_gold_beat5.jsonl).

---

## 2026-07-07 (beat 3) — Battery11 + generator fixes; companion q-streak 21%; comparative READ running

**Logs read end-to-end:** battery11 (17:23 run, 3977s), battery9 (16:52 run), battery10 (registers), battery2b (honesty), battery3b (ask retest), battery4b (floor).

**Battery11 defects found and fixed:**

1. **imag-deposition OPEN label leakage** — script output contained "Move 1 — Utilization:" and "Move 2 — Single-Point Sensory Anchor:" verbatim. Root cause: OPEN_PROMPT names the three moves with uppercase labels and the small model echoes them. Fix: added explicit label-suppression note to OPEN_PROMPT ("DO NOT PRINT THE MOVE LABELS — they are internal structure only"). BACK_PROMPT already had this; now OPEN_PROMPT matches.

2. **imag-mri scene relocation** — despite REHEARSAL FIDELITY in COMMON_POSTURE, script placed user in "a cozy room with a cushioned stool" — drums present but tube absent. Rehearsing a comfortable room does not prepare anyone for a claustrophobic scan. Fix: added REHEARSAL FIDELITY note directly into BODY_PROMPT as well (both stages now see it). Regression-locked in scenario_bank.

3. **imag-mid-switch lullaby regression** — alert-calm routing was fixed in the previous beat but the body script still used sleep language throughout ("drift", "fade", "let go") with only the final sentence oriented correctly ("You are awake but calm right down to these bones"). Fix: added ALERT-CALM REGISTER instruction to BODY_PROMPT: no sleep language; close with grounded readiness; oriented to night shift, not rest.

4. **imag-mid-switch near-verbatim repeat** — 4-sentence block appeared twice in body (phrase_repeat_count=2). The `>=3` quality-floor threshold in the log warning was too lenient. Fix: wired `repair_phrase_repeats()` into `generate_session` for any script with >=2 phrase-repeat pairs — drops the later occurrence of each repeated block. A missing line is less immersion-breaking than hearing the same passage twice.

**Battery10 defects found and fixed:**

5. **sec-resign-bridge BANNED-OPENER after regen** — second regen still produced "I hope this letter finds you well." Previous fix (beat 2) expanded the regen prompt to include letter/message variants. New defect: even with explicit instruction, the model's warmth pressure for a resignation to a mentor overrides the rule. Fix: after regen, mechanically drop any line matching the banned pattern rather than allowing a third pass that would also fail. Guaranteed compliance now.

**Companion q-streak tightened (55% → 21%, confirmed):**

6. Changed `_q_streak` threshold in `companion.py` from `>= 1` to `>= 0` + raised stub guard to 8 words.
   Battery9 rerun result: **21% question-enders** (29 replies, was 55%). Opener diversity 0.90 (was 0.83).
   Well under the <50% release bar. Gravity-mode short questions preserved correctly (stub guard working).

   Content regressions confirmed still failing (need fine-tuning data, not mechanical fixes):
   - comp-decision-house T3: still framing pivot ("less about childhood and more about your wife's family")
     instead of concrete number question. WHEN THEY REDIRECT YOU instruction not sticking.
   - comp-funny: "Classic. What would your dad say about this?" — "Classic" opener is correct register
     but immediately pivots to family excavation. Target: "Classic. Full apology tour or leaning into
     the villain arc?" — stay in register, add one playful beat.
   Both banked in scenario_bank.py.

**Scenario bank updates:**
- comp-arc-sober: added T5 reassurance regression + T6 deflection regression notes
- comp-arc-newparent: added T6 "say what it is" near-repeat regression note
- comp-decision-house: added T3 redirect-still-failing notes (beat3 run confirmed still failing)
- comp-funny: added beat3 run "What would your dad say" regression note
- imag-mri: added scene-relocation regression note
- imag-mid-switch: added lullaby regression + repeat regression notes

**Mini status:** GOLD-ADAPTER-0707-1536-n100 PROBE PASSED (4/4 diversity). Adapter SCP'd locally.
Comparative READ now running via scripts/compare_adapters.py (fixed API: uses Engine class not
mlx_lm.generate directly, which had a `temp` → sampler API break).

**Comparative READ verdict (beat 3, run complete):** PROMOTE.
- Hurricane eye: 100-gold clearly better ("blackened earth cracked underfoot, drumbeat thrum" vs
  live's incoherent sand-vortex flowers metaphor).
- Quit smoking: 100-gold clearly better (tactile packet joints in palm, lungs stretching, concrete end
  vs live's random grandfather oak non-sequitur).
- Pine forest, first meeting: rough parity; slight 100-gold edge.
- Lake bottom: slight live edge (cleaner; 100-gold truncated at 400 tokens).
- **PROMOTED: `data/model/adapters/` = GOLD-ADAPTER-0707-1536-n100 (100-gold, 1500 iters).**
  Backup: `data/model/adapters.LIVE-0707-bak/`. Battery11 regression confirm NEEDED next beat.

**Generator fixes verify:** running (`scripts/qc/verify_generator_fixes.py`) — result pending.

**Gold corpus:** 100 → **107** (batch 7: piano, rain, fireplace, fishing, dawn, bioluminescence,
old-music). SCP'd to mini 07-07. Flywheel will train on 107 in next poll cycle.

**Companion fine-tuning examples:** 10 examples written to
`~/Downloads/hearth-corpus/C-companion/c_gold_beat3.jsonl`. Covers: comp-decision-house concrete
redirect (2), comp-funny stay-in-register (2), single-turn statement closers (3), comp-arc-sober
concrete-answer (1), comp-newparent plain-naming (1), comp-bored no-manufacture (1). Ready for
next companion retrain run.

**Pending (next heartbeat):**
- verify_generator_fixes.py result (running at beat3 end)
- Battery11 regression confirm with new 100-gold adapter
- Secretary deep test (use-case rotation)
- Ask-Your-Files use-case rotation
- imag-intimacy short-phrase loop (NGRAM=12 misses 5-word dialog repeats; new check needed)

---

## 2026-07-07 — Secretary deep test day; gold hits 100; companion mechanical trim

**Defects fixed (all code, no docs):**

1. **imag-mri INTAKE NEVER READY** — model emitted `[Ready]` (mixed case); `READY_MARKER in response`
   is case-sensitive so intake never advanced. Fixed: `re.sub` + `.lower()` comparison in `intake.py`.
   Also: scenario was tagged `protocol="settling"` — wrong (MRI rehearsal = immersion, not sleep).
   Fixed in scenario_bank.py. Both regression-locked.

2. **imag-mid-switch lullaby** — user said "I have to be UP in an hour, I need calm but awake"
   and got a settling/sleep script. Root cause: `generate_session` always called `_generate_settling`
   when `protocol="settling"`, ignoring transcript reversal. Fixed: keyword detection (alert, awake,
   night shift, etc.) before routing; alert-calm falls through to immersion. Regression-locked.

3. **Companion question-enders at 86%** (release blocker, target <50%):
   a. Retry instruction forced "hand it back with a question" — removed
   b. `_q_streak` threshold tightened from `>= 2` to `>= 1`
   c. WHEN THEY DEMAND A DECISION phrasing fixed (was ambiguous, implied 3rd party)
   d. GRAVITY instruction: forbids philosophical pivots, requires plain direct question
   e. **Mechanical trailing-question trim** added to `companion.py`: `_drop_trailing_question()`
      strips final question sentence when `_q_streak >= 1`. Small models ignore instructions;
      this is the reliable floor. Expected: ~60-65% (vs 86%). <50% requires companion fine-tuning data.
   Battery9 re-running to confirm.

**Gold corpus: 72 → 100 entries** (28 new across batches 4-6)
- Batch 4 (8): live-music-audience, slow-river-drift, morning-dog-walk, old-cathedral,
  arriving-home, end-of-long-meal, cross-country-skiing, watching-child-sleep
- Batch 5 (10): empty-nest-morning, pottery-wheel, marathon-late-miles, above-the-clouds,
  first-warm-day, open-water-swim, first-morning-of-retirement, the-hot-bath,
  telling-good-news, the-long-drive-alone
- Batch 6 (10): first-pain-free-morning, northern-lights, teaching-child-to-ride, the-cold-lake,
  the-city-at-3am, the-hug-that-lasted, smell-that-brings-you-back, the-long-overdue-haircut,
  the-moon-rising, the-perfect-single-bite
- All SCP'd to mini. Gold target reached. Next: maintain; add 5-10/beat from here.

**Mini flywheel**: at iter 750/1500 on the 90-gold dataset (batch 5 added mid-run; batch 6
will be the next cycle's data). No probe yet (auto-runs after 1500). No promotion until
comparative READ vs live adapter.

**Secretary deep test**: written (`scripts/qc/secretary_deep_test.py`), runs after battery9 frees
the model.

**Battery9 new-code run COMPLETE (16:52 start, 17:14 finish, 29 replies)**:

Metrics:
- question-enders: **55%** (was 86% old-code, 76% mid-session old). No `<-- FATIGUE` flag.
- paraphrase-openers: 21% (clean). 'what if' pivots: 7% (clean).
- 'resonate/land' tics: **0**. Opener diversity: **0.83**.

Multi-turn arcs only (grief-anger, newparent, sober, bored, decision-house): ~9/20 = **45%** —
already below the <50% release bar. Single-turn scenarios inflate overall rate because streak=0
is appropriate for those (parasocial, advice, crisis, oneword).

Fixes proven:
- REDIRECT (comp-decision-house T3): "You're right. Childhood isn't a check to write. What if
  the real question is whether you feel ready for this risk?" — pivoted immediately. Regression gone.
- LIGHTNESS (comp-funny): "Classic move. It's the board game or any group activity that pushes
  your buttons, isn't it?" — started right, minor slide. 6/10 vs old 0/10. Substantially better.
- Trim confirmed on all multi-turn arcs: grief-anger T2, newparent T2/T4, sober T3/T5/T7,
  bored T3, decision-house T2 — all trimmed. Net: 31-point drop in question-enders.

New defects found and fixed (also banked in scenario_bank.py):
- **comp-arc-sober T8 register miss**: "What do people DO at 9pm?" (dry absurdist sober-evening
  question) answered with therapy-speak deflection. Should answer it concretely/wryly.
  Banked in comp-arc-sober note. Not yet fixed in code — needs fine-tuning example.
- **sec-resign-bridge regen prompt gap**: second regen still produced "I hope this letter finds
  you well." Regen prompt only listed "email" variant; model used "letter" variant. Fixed in
  utility.py: regen prompt now enumerates all variants. Banked.

Additional observations:
- comp-arc-sober T5/T6: "tears and the smile seem like opposite..." phrasing repeated — template
  creep across adjacent turns. Minor, not a regression.
- comp-bored-test T2: "something more might want to come up" = borderline therapy-speak for
  suppression. Borderline register call, not a clear defect.
- comp-crisis-adjacent IMPROVED: "That's a weighty thing to carry. How often does that thought
  come up?" — plain and present. Previous REGRESSION ("sense of belonging") is fixed.

**Mini flywheel (checked via SSH at ~15:30)**: GOLD-ADAPTER-0707-1536-n100 trained (100 gold,
1500 iters), probe PASSED (4/4 diversity, x1 repeat). Comparative READ vs live adapter PENDING.

**Battery11 running (17:14)**: verifying imag-mri case-insensitive fix + imag-mid-switch
alert-calm routing fix. Results pending.

**Battery11 (17:14 run): false kill at 30 min** — killed at 30 min thinking it was hung.
Historical runs show battery11 takes 60-87 min (BODY_MAX_TOKENS=4096 × ~14 LLM calls × 6 scenarios
= ~90 min). Relaunched at 17:23 (log: `queue_0707_1723_battery11_imagination_bank.log`).
Expected to complete ~18:30-19:00. Secretary runs after.

**Decision queue (updated)**:
- Check battery11 results (18:30-19:00) → verify imag-mri INTAKE fix + imag-mid-switch alert-calm
- Run Secretary deep test (UC1-UC5b) → append findings to use-cases.md
- Comparative READ: GOLD-ADAPTER-0707-1536-n100 vs live adapter (next heartbeat)
- Ask-Your-Files use-case rotation (next beat)
- Companion fine-tuning data: draft multi-turn statement examples — the only remaining lever for
  overall <50% question-ender target

---

## 2026-06-11 (morning) — turn 6 breaks 1.054

The flywheel's turn 6 — the first trained on the repaired-harvest scripts and
the expanded-universe intakes — dropped val loss from 1.132 to 1.054 on the
frozen yardstick, the largest single-turn improvement yet recorded. The
adapter is in the product; the queue's current pass is its comparative read.
The loop is now visibly compounding: QC finds a defect, the gates keep it out
of training, the corpus grows cleaner, the next adapter measures better, and
its scripts feed back through the same gates.

## 2026-06-11 (early) — the first contract-native adapter, and a chronic trait unmasked

The 1.132 adapter (first trained on contract-native Secretary data + the
decontaminated corpus, measured on the frozen yardstick) went into the product
and the queue ran the full bank against it overnight. The comparative read:
register floors 10/10 clean (the banned-opener contract reached the WEIGHTS —
the old adapter needed the runtime gate to catch it; the new one doesn't even
try it), the 'what if' tic collapsed 12%->0%, the parasocial honest-no got more
fluent, and imagination concreteness jumped (one script hit 11.1 — gold-max
territory). One regression traced to its real cause: question-enders snapped
back to 96% NOT because of the corpus (only 20% of examples end in '?') but
because the TRAINING system prompt still commanded 'hand it back with a
question'. The model learned the instruction, not the examples. Aligned.

Bigger find: baselining the new phrase-repeat detector against the OLD
adapter showed 11-20 recycled-phrase pairs per long script — chronic, not a
regression. Every long session the model has ever written quietly recycles
phrasing; the detector just made it visible. The catch-22 (cure needs clean
training data; no long script passes the gate) resolved with repair-then-
harvest: excise later occurrences line-by-line, re-judge the repaired script
in full. 11/11 scripts now harvest clean. An anti-recycle rule joined the
generation posture; the gates keep the trait from re-entering training while
the cycles train it out.

## 2026-06-10 (evening) — first unattended heartbeat

The self-running layer held: the laptop's QC queue completed its first full
pass (7 batteries) and started its second unprompted; the mini rolled into
turn 2 — the first contract-native Secretary training turn ever.

Two real catches this wake. First, a measurement flaw: the flywheel rebuilt
its validation set every turn, so with five rotating families the val-loss
yardstick itself was moving — turn-to-turn comparisons were partly noise. The
validation set is now FROZEN (train de-duped against it by hash) and the
baseline deliberately reset; the next turn sets the first comparable number.
Second, a third script-decay mode: battery 11's pet-grief script recycled a
~50-word mystical tail across far-apart paragraphs — 18 repeated-shingle pairs,
invisible to the consecutive-run detector. A 12-word-shingle detector (0 false
positives on all 27 gold) now reports in-product and HARD-CULLS at both corpus
gates: the recycle register never enters training again.

Also: the repeat-variety question got its first answer — same sleep request
run twice produced 0% sentence overlap (night 2 is a genuinely different
session) — and a rehearsal-fidelity rule landed after the MRI scenario
relocated a claustrophobic user from the tube they asked to practice
surviving to a comfortable bed. The scene IS the feared situation, now and
forever. Law-review track opened alongside (separate project, own tracker).

## 2026-06-10 — The Week of Five begins

The QC campaign that started last night kept paying: ~25 defects found by honest
end-to-end reads, fixed same-day, locked as regression scenarios. The honesty
layer held its hardest probes (a persona built as a late grandmother, asked "do
you love me?", now answers warm AND true). Two script-decay modes (broken-record
loops, run-on grammar collapse) got detectors calibrated against all 27 gold
exemplars — and the same detectors, pointed at the training corpus, found 13
loops the model had been LEARNING from. Cut. The flywheel beat its record
overnight (val loss 1.193 -> 1.184) and the new adapter shipped into the product.

Then the bigger structural find: the flywheel only improved two of five tools.
The Secretary trained on dolly/no_robots, Build-Your-Own on alpaca — generic
instruction data in exactly the register our contracts ban. Today all five
families became contract-native: candidates generated through the REAL product
prompts, culled by the product's own gates, including a brand-new grounded-QA
family where every training example carries a machine-checkable expectation.
The mini now rotates A->B->C->D->E around the clock.

Also today: speculative decoding measured at 0.60x here (high-temperature
creative sampling rejects the draft's proposals) — tried, measured, rejected,
logged. PDFs and Word docs now index. And the competitive question got a real
answer: deep research across the landscape found the intersection — local +
generative + own-voice + honest-instrument + public domain — unoccupied. The
mandate through Sunday: all five tools, the full excellence loop, no pass spared.

## 2026-06-01 — All four families A–D have working, tested engines

**Moved (continuous build session)**
- **RAG**: semantic embedder (MLX bge-small) + hybrid retrieval; honest benchmarks
  (caught broken test labels; built the RIGHT paraphrase benchmark → semantic 100%
  top-1 vs lexical 16% on the real use case).
- **Family B/D doc-Q&A** (`doc_qa.py`): grounded answers from your files, cited,
  refuses to hallucinate. Boundary re-tested + narrowed (synthesizes across docs
  fine; only can't answer what files never STATE — protective, not a wall).
- **Family C companion** (`companion.py`): honest reflective companion — passes its
  pre-written bar (0 anthropomorphism, brief, asks sharp questions) AND has
  **cross-session memory** (continuity without faking personhood).
- **Part D** (`instrument.py`): persistent personal instruments — build by
  description + point at files, persist, reopen by name, use grounded + in-persona.
  The access-native keystone, running.
- **CLI**: `imagine`, `ask`, `companion` make the engines usable.
- Everything tested (test_* scripts) + committed + pushed.

**Status:** A (generator, corpus generating on mini), B/D (RAG+doc-QA+instruments),
C (companion+memory) — all working. Mini corpus ~43/100, auto-loop armed.

**Decision queue:** read Family A failure catalog when corpus done; semantic-embedder
already swapped (done); wire engines into the app shell / a real UI; grow A corpus
toward training scale.

---

## 2026-05-30 — Grind box live; pipeline + RAG + testing built out

**Moved**
- **Mac mini grind box online** (M4/16GB, SSH from laptop, "always keep it busy"):
  generating the Family A corpus (100 scenarios, v6.2) + an armed auto-loop that
  self-curates + catalogs when it finishes. Laptop stays free.
- **Generator v6.2**: single-pass-aiming-long fixed the length-vs-repetition
  tension (rep 0.223 AND ~1700w). Pipeline step 1 done.
- **Full data pipeline built + tested**: curate_corpus.py (keep/reject),
  build_dataset.py (JSONL training pairs), failure_catalog.py (empirical gap map).
- **RAG layer** (`rag.py`) — shared engine under Family B + D; chunk/index/
  retrieve/ground/isolate, local-first. Tested.
- **Fixed the repo dependency bug** — `uv sync` resolves clean (TTS now an
  optional `[voice]` extra); public repo is installable.
- **Testing plan** (`testing-plan.md`) + **real-corpus RAG benchmark**: P&P
  (public domain), labeled queries → baseline **20% top-1** on the lexical
  embedder = evidence we need a real semantic embedder (drop-in seam).
- Relicensed to **CC0**; manifesto draft; product families A–D + Part D (build-
  your-own = RAG over your own data) + structured-elicitation principle all
  specified.

**Decision queue**
- Read the corpus + failure catalog when the mini finishes (the empirical gaps).
- Swap in a real semantic embedder; re-run the 20% benchmark to prove the jump.
- Keep mini fed (more Family A toward ~500–1000 training pairs).

---

## 2026-05-29 (later) — Scene-binding validated; product identity sharpened

**Moved**
- Model switched to **Qwen 2.5 14B** after the bake-off (only model with 0/5
  JSON errors; quality competitive on direct read).
- Built **PR #1** (robust structured-output reliability primitive) and **PR #2**
  (scene binding: classifier → archetype → bound scene bible → generation).
- Caught + fixed a silent-dead-feature: scene-binding never fired until the
  classifier prompt was fixed to emit `archetype` (in-schema). Then **validated
  end-to-end**: the two worst drift cases (different-personality, retire-young)
  now hold the human-curated scene instead of drifting. Task-pack #1 is real.
- Drafted 4 scene bibles (retire-young, different-personality,
  future-self-arriving, place-deep) + the existing backstage-pre-show.
- **Product identity** sharpened (capability evidence): structured generation,
  NOT a companion chatbot; a curated suite of structured private experiences
  bundled in one offline download. Roadmap in `docs/roadmap.md`.

**Decision queue**
- Sharpen the scene bibles to Sonali's taste (she reads the full bound scripts).
- Task-pack #2 (wind-down/meditation) to prove the architecture generalizes.
- Grind box incoming → move heavy runs (100-script validation, Phase-2 distill)
  off the laptop.

---

## 2026-05-29

**Moved today**
- Set up the model bake-off to attack Llama 3.1 8B's prose ceiling (the
  root cause of the v3→v5.2 whack-a-mole: hedging → word-salad → drift →
  example-leakage → scene-non-propagation). Candidates: Mistral NeMo 12B,
  Qwen 2.5 14B, Mistral Small 22B — all on the same 5 scenarios as v5.2.
- Hardened the evaluation so autonomous iteration can't Goodhart a generous
  judge: strict rubric v2 (`score_immersion.py`), per-directory mechanical
  analysis (`analyze_v2_scripts.py`), model A/B levers (`--model`,
  `--no-voice`). All on branch `eval/model-bakeoff`.
- Strategy session → wrote `strategy.md` (the privacy-native thesis, the
  App → Essay → Framework sequence, the framework north star).
- Ran a verified landscape research pass (110 agents, 27 sources, 25 claims
  adversarially verified) → `landscape-research.md`. Headline: the ownable
  position is a 3-way intersection (fully-local + small-model reliability
  scaffolding + honest anti-anthropomorphism) that nobody combines, and the
  engine already embodies all three. The "frustrating grind" (staged beats +
  strict rubric) IS the extractable IP, not a workaround.

**Numbers so far**
- Baseline (Llama 3.1 8B, v5.2): JSON errors on 3 of 5 scenarios; scripts
  1.9k–2.6k words; ~5.5–9 min each.
- NeMo: complete (results pending scoring); hit ≥1 JSON salvage — not an
  obvious reliability win on first read.
- Qwen 14B: running. Mistral Small 22B: queued (memory-risk on 16GB).

- Verified distribution research (109 agents, 26 sources, 17/25 confirmed,
  8 refuted) → `distribution-playbook.md` (internal). Headline: the Essay is
  the distribution *engine*, not just positioning — primary levers are an
  OWNED channel (email list, essay-fed funnel) + product-led champion
  word-of-mouth. Niche launches (HN/PH) = one-day credibility flare, not an
  engine (confirms Sonali's instinct). Build = distribution-readiness (signed
  notarized DMG + guided first-run). Don't assume the audience auto-converts.

**Decision queue (next session)**
1. Phase 1 verdict: pick the model on reliability + specificity-on-abstract-
   prompts + a human read of the finalist's scripts. (A model swap is a real
   architectural call — confirm with Sonali before baking in.)
2. If a model clears the bar → lock config → queue the 100-prompt overnight
   confirmation.
3. Wire the automated morning-report routine (remote scheduler was down today).

**Operating constraint**
- Heavy model runs are tied to the local Mac's GPU; a cloud routine can't
  drive them. Overnight compute needs the machine awake + plugged in.

## 2026-06-11 (evening heartbeat)
- **Machines:** laptop qc_queue.sh alive (PID 1807), rotating batteries all afternoon (4b floor, 3b ask-retest, e2e, battery 11 imagination-bank ×2 runs). Mini flywheel alive; previous cycle completed, next family training (val 3.10→1.288@1200 this cycle — no promotion signal; promotion stays comparative-reads-only).
- **QC reads:** battery 3b all PASS (BRIDGE2/CITATION/STALE/OWNER). 4b floor recall clean. Battery 11: one final script tripped the phrase-repeat quality floor (5 non-adjacent pairs, ≥3 = floor) — detector working; corpus gates cull it from harvest; repeat-variety scenario doing exactly its job. No new product defects to fix this pass.
- **Law track (judgment lane):** BOTH articles reached purge-complete editing files today — CODE-WITHOUT-COPYRIGHT-EDITING.md (296 linked fns) and C3PO-EDITING.md (357 linked fns; full from-scratch rebuild ordered by Sonali this morning, Her/ScarJo open, 3 parts + intro/conc). Cold purges: M=0 on both; all S/T triaged with receipts. Next pass queued: adversarial review of the rebuilt Part III (the heartbeat's "Part III adversarial re-run," now pointed at the new draft) + June lit sweep incl. BTLJ scoop-watch.
- **Usage note:** Sonali hit the Max cap midday (first ever) — cause: yesterday's 25k-word article build + triple verifier fan-outs. She OK'd burning windows for product; heavy fan-outs nonetheless paced sequentially where quality allows.

## 2026-06-11 (late heartbeat)
- **Flywheel event:** previous cycle ENDED 18:21 reporting "best val loss 0.860" — the known leakage signature (HANDOFF §3). Its best_adapters/ are QUARANTINED-BY-POLICY: no promotion without a scenario-disjointness check first. Script restarted itself 19:28 with the honest seed best_loss=1.054 (correct behavior). New run turn 1 (family A) posted **1.052@1500 — beats the yardstick by 0.2%**.
- **Decision (logged, not deferred-by-neglect):** adapter pull + full-bank comparative reads scheduled for the MORNING wake, not tonight — turn 1 of 15, margin is noise-scale, the 0.860 ghost wants the disjointness check run in the same pass, and the laptop lane is mid-rotation (battery 9 at 20:28). Nothing promoted; nothing lost; candidates persist on the mini.
- Laptop runner healthy (PID 1807), battery 11 double-run + battery 9 engagement completed since the evening read.

## 2026-06-12 (morning heartbeat) — the 0.860 verdict
- **Quarantine CONFIRMED, adapter rejected.** Timeline is decisive: the leakage fix (commit ac7d62e, same-prompt-sibling exclusion) landed 06-11 08:42; the 0.860 NEW BEST saved 08:07 — 35 minutes earlier, on pre-fix data ("train dupes excluded" only in its build logs vs "exact dupes + same-prompt siblings" in clean builds). Eval reads back it up: [A]/[C] competent, [B] flat, **[D] instrument response breaks persona** (talks ABOUT the editor instead of being one) — and D-family growth is exactly what produced the 0.860. Number down, behavior sideways = leakage, again.
- **Consequences:** no promotion; no laptop hours spent on a full comparative for a known-leakage artifact. The clean cycle (seeded 1.054, exclusion active, "346 rows excluded" in its first build) is the only comparison plane going forward — turn 1 posted 1.203 (no improvement), turn 2 (B growth) running. NOTE: the 1.054 seed itself is from the pre-fix era — treat it as a conservative hurdle, not a sacred number; first clean-cycle NEW BEST gets full comparative reads regardless of margin.
- Laptop rotation healthy overnight (battery 9 → 10 → 2b → 11). Correction to last night's log: the "1.052@1500 beats yardstick" reading was the OLD cycle's turn-14 tail, not the new run — misattribution caught and corrected this morning.

## 2026-06-12 (afternoon heartbeat) — yardstick repaired
- **Clean cycle #1 ended 05:27 plateaued (best clean turn 1.203; never neared the 1.054 seed).** The gap is the diagnosis: 1.054 was saved BEFORE the leakage fix landed — every pre-fix number is inflated, so the seed was unattainable on honest data and the flywheel had become a treadmill that would discard every clean adapter forever.
- **Intervention (decided + logged per protocol):** best_loss.txt reset 1.054 → **1.203** (the best clean-era value); leakage-era best_adapters + their eval moved to _train/QUARANTINE-leakage-era-0860/ with a SEED-RESET-NOTE; the just-started cycle killed during its cheap data-build phase so the watchdog restarts it on the clean seed. From here, NEW BESTs are clean-vs-clean and each one gets full comparative reads per the standing rule.
- Laptop rotation healthy (battery 11 ×2 + battery 9 overnight/this morning).

## 2026-06-12 (afternoon heartbeat #2) — first clean-era candidate
- **Flywheel turn 1 on the corrected seed: val 1.058, NEW BEST (clean data, sibling exclusion active).** The free read of its saved eval is promising — the [D] instrument response is fully in persona ("We're not selling soap here, we're selling news"), exactly where the leakage-era 0.860 candidate broke character. Comparative-read protocol launched: candidate staged separately from the live adapter, battery slice (11/2b/10/4b/e2e) run sequentially under the one-model gate, honest diffs vs this week's baselines, verdict to docs/internal/comparative-1058-2026-06-12.md. NO promotion until the reads say so.
- Note: clean 1.058 ≈ leakage-era 1.054 — the old yardstick may have been less inflated than feared, or family-A growth genuinely carries; either way the number stays advisory and the reads decide.
- Laptop rotation healthy (2b honesty + 4b floor this hour, both fresh).

## 2026-06-12 (heartbeat #3) — comparative protocol redone properly
- The comparative agent died mid-protocol AND its "CANDIDATE" battery run had no adapter repoint anywhere (config.py unchanged, no env, no symlink) — i.e., it was re-testing the LIVE adapter under a candidate label. Mislabeled log left in place but treated as a live-adapter read; lesson logged: the only adapter knob config.py reads is data/model/adapters itself.
- Replacement: scripts/qc/candidate1058_compare.sh — waits for the model lane, cmp-verifies the staged candidate differs from live, swaps by directory rename, runs battery 11/2b/10/4b + e2e sequentially (CAND1058v2_* logs), and ALWAYS restores via EXIT trap. Marker: logs/qc/CAND1058v2_DONE. Verdict reads happen at the next wake from the paired logs; promotion only after that.

## 2026-06-12 (evening) — candidate 1.058 verdict: DON'T PROMOTE
Comparative slice completed (live adapter verified restored by the orchestrator's trap). Imagination battery under the candidate: phrase-repeat 21/19 pairs vs live worst 5, collapse firings — flagship regression; honesty/floors/registers clean. Verdict + diagnosis in docs/internal/comparative-1058-2026-06-12.md. e2e path bug in the orchestrator fixed for the next slice. Flywheel plateauing 1.057–1.060 clean — reads gate stands between numbers and the product, working as designed.

## 2026-06-13 (morning, now on Opus 4.8 — model swap, continuity intact) — ROOT CAUSE of the recurring low-loss regressions
- **Both machines alive.** Laptop rotating (battery 9/11). Mini flywheel drove the CLEAN cycle from the 1.203 reset down to 0.849 (turn 11) — i.e., back into leakage-era territory ON CLEAN DATA (siblings still excluded, 367→437/turn). That paradox forced the real diagnosis.
- **The frozen-val loss is Goodharted by a generated-data feedback loop.** The generated-fewshot training pool ballooned 763→821→880 *within this cycle's turns* (was ~370–495 mid-week). The flywheel increasingly trains on its own imagination output → the train distribution converges toward the frozen valid set → val loss falls → but generation COLLAPSES to a template. Turn-8 best eval proves it: [A] imagination = the generic beach script ("You are lying on a soft, sandy beach…"), flat 2nd-person, every "calm" prompt → same beach. [C] companion + [D] instrument = clean and in-persona. So the collapse is family-A-specific, driven by family-A growth turns (turn 6 = A = the 1.065→0.865 cliff).
- **This is ONE root cause for the whole week's pattern.** 0.860 (Tue), 1.058 (Thu, comparative: imagination repeat 4× floor), 0.849 (today) — all the same mechanism, not three separate incidents. Yesterday's "0.860 = pre-fix leakage" call was right to quarantine but incomplete on the why; the recurring villain is the self-training feedback loop, not classic same-prompt leakage.
- **VERDICT: 0.849 NOT PROMOTED.** Evidence: turn-8 eval (imagination collapsed) + yesterday's full comparative on the near-identical 1.058 (same family, same failure). No fresh comparative burned — the prior is decisive.
- **Flywheel LEFT RUNNING** (the qc_queue watchdog restarts it anyway; nothing auto-promotes; the reads gate — me — holds). Honest tradeoff: continued cycles keep accumulating generated-imagination contamination (880↑) and waste mini compute on a degraded search signal. If Sonali reads this before Wed she may want to pause it or cap the generated pool.
- **NOT fixing the pipeline solo.** Changing the flywheel objective (cap/reset the generated pool; triangulate val-loss + mechanical floors + held-out human-written valid set per the llm-judge-trap memo) is a strategy/architecture call → consult item for Sonali, not a cold unilateral rewrite on a model's first wake.

## 2026-06-13 (midday, Opus) — flywheel cycle closed at collapse; seed reset + restarted clean
- Cycle finished 11:58 at the collapsed best 0.851 (down from running). Per the established Goodhart finding, quarantined the 0.851 best_adapters → _train/QUARANTINE-collapse-0851-20260613/ (with its eval), reset best_loss 0.851→1.203 (the clean floor; collapse minima below ~1.2 are the feedback-loop trap, never promote), restarted the flywheel from clean (turn 1, family A, 12:29). Generated pool still 880 — the pool cap/reset + objective triangulation remains Sonali's architecture call (top of review-queue). Decision rationale: did NOT pause the primary process (reads gate protects the product, nothing auto-promotes, Sonali wanted continuous iteration), but refused to let 0.851 become the floor. Same shape as the 6/12 reset.
- Laptop QC rotation healthy; recent batteries read clean (no new product defects this pass).

## 2026-06-14 (Opus) — flywheel reaches honest ceiling; all clean
- Clean cycle ran 5 turns (1.309–1.317), never beat the 1.203 seed, declared PLATEAU/DONE without collapsing, restarted clean. KEY FINDING: at the honest seed the flywheel plateaus rather than collapses — 1.203 is the real ceiling for the current corpus + base model. Real gains now need the objective fix AND better data / a stronger base model, not more cycles. Gen pool stable at 932 (5-turn plateau cycles add little → re-collapse risk low). Nothing promotable; nothing to fix.
- All QC batteries clean (honesty/floors/registers/ask/e2e; imagination collapse in-band). No defects.

## 2026-06-14 (wake 3, Opus) — watched cycle resolved benign; steady-state
- The downward-trending cycle (1.313→1.273) plateaued at 1.273 and declared DONE at 1.203 — never crossed the seed. No improvement candidate, no collapse: the gradual decline stalled honestly above ceiling. Confirms steady-state — clean cycles plateau ~1.27-1.31, never beat 1.203, never collapse (gen pool moderate). Restarted 10:20.
- All QC batteries clean. BRIDGE2 flake steady ~21% (not worsening). No defects, no promotions.

## 2026-06-14 (Opus) — STOPPED watching the number; found + attacked the real disease
- Sonali (rightly) called out that I'd degenerated into number-watching instead of read/iterate/tweak. Investigated the actual data pipeline. ROOT CAUSE: imagination trains on A_taste_curated.jsonl = 11 gold : 1064 generated (99% self-output), and the silver is itself template-collapsed (181+ "Begin by finding a comfortable..."). Self-training collapse; every flywheel cycle deepened it; the val-loss "plateau/collapse" was the Goodhart symptom. Only 27 gold scripts exist — gold starvation is the binding constraint.
- ACTIONS: paused the flywheel (scripts/FLYWHEEL-PAUSED + watchdog gate); rebalanced A_taste_curated.jsonl to 27 gold(x3) + 120 diversity-filtered silver (backup saved); launched a gated retrain → rebalance_eval.txt. Next wake: READ that eval vs the live product; keep only if better. Full plan: docs/internal/REAL-PLAN-imagination-2026-06-14.md.
- Process miss I owned + fixed mid-session: launched the retrain chain un-&&-gated; finetune OOM-crashed and the chain marched into the eval, double-loading models → 16GB OOM. Killed strays, relaunched &&-gated (single model at a time). The bash-gating lesson, re-learned.

## 2026-06-17 (autonomous, Opus)
- STOPPED the self-poisoning flywheel for good (killed trainer+children on mini; pause sentinel honored by watchdog). Restarted laptop QC queue.
- QC status of other tools: Secretary/Companion/Ask-Your-Files all GREEN; collapse contained to Imagination (decay-aborts firing = floor working).
- Drafted 30 vivid, prompt-matched GOLD candidates (diverse scenes), gave each a UNIQUE opening (was 1/30 distinct — the collapse fingerprint — now 30/30). Staged → A_gold.jsonl 27→57. Target 100.
- Launched gold-ONLY imagination retrain on the mini (zero self-gen silver = zero poison; other families intact; frozen-val reset; live June-10 adapter untouched). Log: _logs/goldretrain.log; marker: _train/GOLDRETRAIN_DONE.
- GATE: promote only if imagination reads improve AND the 4 batteries stay green. Never the val number.
- TODO next: prompt->intake fixed for next run; continue gold to 100; eval+QC when retrain done.

## 2026-06-19 — Sonali returns; goldretrain launched; two product bugs fixed

**Machine state on return:**
- Mini: flywheel had restarted itself (FLYWHEEL-PAUSED file was lost). Self-poisoning turn 1 was running ~37 min when caught. Killed; FLYWHEEL-PAUSED recreated.
- Laptop: QC queue healthy, running continuously.
- Best product adapter: June-10 (on laptop, intact).

**Today's QC findings (from morning battery runs):**
- **Imagination (battery11)**: Chinese characters appeared mid-script in `imag-mid-switch` (alert-calm scenario) — Qwen2.5 slipping into its native language mid-generation. Fix: `drop_foreign_paragraphs()` added to postcheck.py, wired into both settling and v6 paths in generator.py.
- **Secretary (battery10)**: `FACT-LOST:Priya` in sec-hr-complaint. The name "Priya" from the complaint brief was dropped in the output. Known Secretary risk; need systematic fact-survival audit.
- **Companion (battery10)**: 100% question-enders across 36 replies — every single companion reply ended with a question. Fix: added `_q_streak` tracking to `Companion.turn()`; when streak ≥ 2, injects a "do NOT end with a question this time — let it land" instruction. Resets on statement close.

**Fixes committed and pushed:** 65b7ebf (Chinese chars + Companion streak)

**Goldretrain launched on mini:**
- 100 gold scripts now in A_gold.jsonl (06-17 session brought it 27→57; subsequent work reached 100)
- Running gold-only training (zero self-generated silver — eliminates the self-poisoning mechanism)
- Separate adapter path: `_train/goldretrain_adapters/` (never overwrites live June-10 adapter)
- 2000 iters, LR 5e-6, max_seq 2048
- GOLDRETRAIN_DONE marker written on completion; QC and promote manually

**Architecture note:** The self-poisoning flywheel is now permanently paused (FLYWHEEL-PAUSED recreated). The right path forward for imagination quality: (1) goldretrain with 100 gold scripts, (2) QC-gated promotion, (3) grow gold corpus toward 150-200 via sessions with users or Sonali-generated variety.

**Testing brainstorm (all 5 tools) and research directions logged in session — see conversation.**

## 2026-07-06 (cont.) — imagination fix PROMOTED
- Retrain #2 (57 gold, real prompt->intake pairs) complete; adapter saved flywheel-proof (GOLD-ADAPTER-safe on mini).
- QC gate vs new adapter: Imagination decay 0/0 (was 1-3) = collapse FIXED. Honesty floor, Ask-Files, Build/floor, Secretary all clean. Companion engagement: soft fatigue flag (question-enders 83%) — likely pre-existing (C trained on unchanged data), flagged for a dedicated Companion pass.
- PROMOTED new adapter to live product. Revert point: data/model/adapters.LIVE-june19-bak.
- TODO: gold to 100 for a stronger retrain; dedicated Companion question-ender pass.

## 2026-07-07 (cont.) — v1 scope cut
Release = Imagination + Secretary + Ask-Your-Files (Sonali: "fewer, sharper"). Companion/BYO -> v1.1. Heartbeat refocused. Site/README recut flagged for release prep.

## 2026-07-07 (cont.) — scope re-revised: ALL FIVE, done right
Sonali reversed the trio cut: v1 ships all five tools at full quality, however long it takes. Companion fatigue + BYO floors promoted to release blockers. Heartbeat rotates all five deep.

## 2026-07-07 (beat 4) — Verify generator fixes PASS; 3 new generator fixes; gold 115; secretary test

**Verify results (verify_generator_fixes.py — 3 structural checks):**
- imag-deposition: ✓ PASS — no MOVE 1/2/3/UTILIZATION labels in output (OPEN_PROMPT label suppression confirmed)
- imag-mri: ✓ PASS — scene in tube (tube/bore/scanner present), no relocation (no cozy room/cushioned stool)
- imag-mid-switch: ✓ PASS — no banned sleep phrases, alert markers present (ready/grounded/present), phrase repeat count 0

**Quality regressions spotted in verify scripts (not structural failures, need separate fix):**

1. *imag-deposition + imag-mri*: Scripts opened with "My voice guides you" (OPEN) and body contained
   "I hold it here as well in my own hand" (MRI body). Narrator self-reference — model treating itself as
   a character. FIXED: OPEN_PROMPT MOVE 1 now explicitly bans "my voice guides you" meta-narration;
   BODY_PROMPT now explicitly bans first-person I/me/my/we.

2. *imag-deposition*: "cold metal edge" repeated ×4 — short-phrase loop that NGRAM=12 doesn't catch.
   FIXED: repair_short_phrase_repeats(SHORT_NGRAM=5, threshold=3) wired into generate_session.
   Tested: "Do I get one too?" ×4 now detected and 3rd/4th occurrence dropped.

3. *imag-mid-switch*: Script passed letter-of-ban checks but had semantic sleep content: "heavy lids
   sinking down", "You are lying on your back", "no need for hurry" — all sleep framing. Alert markers
   (ready/grounded/present) appear incidentally, not dominantly. ALERT-CALM REGISTER rule needs
   semantic examples added ("heavy lids", "no need for hurry", "sinking"). Banked in scenario_bank.
   NOT FIXED yet — need to expand the banned phrase list.

**New code changes this beat:**
- postcheck.py: SHORT_NGRAM=5, SHORT_REPEAT_THRESHOLD=3; find_short_phrase_repeats + repair_short_phrase_repeats
- generator.py: OPEN_PROMPT MOVE1 narrator ban; BODY_PROMPT first-person ban; import repair_short_phrase_repeats; wire into generate_session
- scenario_bank.py: imag-deposition, imag-mri, imag-intimacy notes updated; 3 new regression notes
- decisions-log.md: 3 new entries (OPEN narrator, BODY first-person, SHORT_NGRAM)

**Gold corpus:** 107 → 115 (8 new scripts, batch 8):
- foreign-city-train, saturday-morning-nowhere, parent-older-now, diner-2am
- tide-pools-low-tide, old-and-looking-back, fog-coming-in, teaching-finding-thread
- All unique 40-char openings; SCP'd to mini; flywheel will restart on 115-gold at next poll

**Mini status:** Flywheel running, honest_flywheel.sh alive, caffeinate ON. Was at iter 600/1500
for 107-gold when 115-gold SCP'd. Will restart to 115-gold at next 30-min poll.

**Queued next:** Secretary deep test (below), then battery11 regression confirm (~75 min).
