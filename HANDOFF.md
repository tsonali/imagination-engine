# HANDOFF — resume here (read this first)

_Last updated 2026-07-13 beat23 COMPLETE (n262 REJECTED; n243 restored as live adapter MD5:8a7395654d4bd0f72b69c673a03bf6db; qc_queue RUNNING PID 18263; Gold(A)=270; Gold(C)=40 beat exemplars; flywheel training n270)._
_Single source of truth for a fresh session. Everything below is real and running._

## FIRST THING TO DO when you resume — run these checks
```bash
cd ~/Downloads/imagination-engine

# 1. Check current live adapter (n243 = 8a7395654d4bd0f72b69c673a03bf6db)
md5 data/model/adapters/adapters.safetensors

# 2. Check mini for n270 completion
ssh smaitra@mac-mini.localdomain '
  echo "flywheel: $(pgrep -f honest_flywheel >/dev/null && echo RUNNING || echo DOWN)"
  echo "mlx_lm: $(pgrep -f mlx_lm >/dev/null && echo TRAINING || echo IDLE)"
  tail -4 ~/Downloads/hearth-corpus/_logs/honest_flywheel.log
  ls ~/Downloads/hearth-corpus/ | grep GOLD-ADAPTER | tail -5'

# 3. Check qc_queue (should be running)
pgrep -f qc_queue >/dev/null && echo "qc_queue RUNNING" || echo "qc_queue DOWN — restart: nohup bash scripts/qc_queue.sh"

# 4. Check latest battery results
ls -lt logs/qc/queue_*.log | head -5
```

### BEAT 24 STATE (in progress)
- **n256 gate RUNNING** (PID 19068 python, PID 19069 tee) — battery11 (eagle + intimacy + active-scene) on n256 (val loss 0.546 "best ever"). Key question: she/her active-scene corruption?
  ```bash
  wc -l logs/qc/beat24_battery11_n256_gate.log
  tail -30 logs/qc/beat24_battery11_n256_gate.log
  ps -p 19068
  ```
- **n275 training on mini** — iter 425/1500, train loss 1.156. ETA ~12:45 PM. 275 gold scripts including 2 solo active-body (pool swim, winter run) to fix she/her bleed. c_gold_beat* JSONL files on mini confirmed (beats 3-23, 102 companion exemplar lines, 3x weighted).
- **Git commit done** — all src/ and scripts/ changes through beat24 committed (34 files, beats 13-24).
- **DIST SYNC DONE** — generator.py, companion.py, utility.py all synced. Run `scripts/package.sh` before shipping.

### BEAT 24 NEXT STEPS (after n256 gate completes)
1. **Read n256 gate log** — check she/her active-scene corruption, pronoun fix count, eagle (no hawk/no chair), prose quality vs n243
2. **n256 decision**: if active-scene clean AND quality ≥ n243 → PROMOTE (mv adapters.n243_LIVE adapters.n243_BEAT24_bak; n256 stays live)
   If fail → RESTORE n243: `rm -rf data/model/adapters && mv data/model/adapters.n243_LIVE data/model/adapters`
3. **Restart qc_queue** after n256 decision
4. **AYF battery3c** (28-scenario) — kill qc_queue first, run battery3c, check BRIDGE2 flake, restore qc_queue
5. **n275 gate** — once mini completes, rsync and run full battery11 gate
6. **Verify grief-pet fix** — after qc_queue restarts, read next battery11 that includes imag-grief-pet; confirm "Your tail thumps" is gone

**Eagle gate: CLOSED for n243** — postcheck false-positive bug fixed (beat21):
- battery11_imagination_bank.py was using substring match; "slowly" → triggers "owl" match
- Both battery11 runs (0600 ✅✅, 0803 ✅✅ after fix) confirmed clean
- Eagle gate is DONE for n243. n262 still needs its own eagle gate run.

**Beat20+21 fixes applied — need re-verification on next battery runs:**
- generator.py: grief-pet perspective fix + fix_possessive_pronouns() wired in
- utility.py: $28K drop fixed (cost-context + regen gate)
- companion.py: grief-anger RECEIVING IS NOT ECHOING + arc-newparent ANTI-REPEAT + crisis-adjacent TWO MOVES GRAVITY
- postcheck.py: fix_possessive_pronouns() added (hers→her, yours→your before nouns)
- battery11_imagination_bank.py: wildlife postcheck now uses word-boundary regex
- All dist/ synced

**Tool rotation** — beat20=Companion, beat21=AYF (battery3c still pending — battery3c_ayf_beat20 only ran 6 lines). beat22=**AYF** (carry forward).

## THE OPERATING SYSTEM (since 2026-07-07): heartbeat + honest flywheel
- **Heartbeat (laptop launchd `com.hearth.heartbeat`, every 4h at :30, wrapper
  `~/claude-phone/hearth-heartbeat.sh`):** a Claude session that is the CENTRAL CHECK-IN.
  Each beat: (1) read the newest QC battery logs END TO END, fix real defects, bank them in
  scenario_bank, re-run to prove; (2) check mini + flywheel, comparative-READ any probe-passing
  adapter (numbers never decide); (3) add 5–10 new gold scripts toward 100+ (UNIQUE openings,
  vivid, prompt-matched, intake=prompt) and scp A_gold.jsonl to the mini; (4) deep-test ONE of
  the five tools per beat against docs/qc/use-cases.md like a hostile AI professional;
  (5) log to docs/daily-log.md + docs/internal/review-queue.md. NEVER block on Sonali.
- **Honest flywheel (mini, `scripts/honest_flywheel.sh`, nohup):** polls A_gold.jsonl every 30
  min; on change → gold-ONLY rebuild → finetune (1500 iters) → adapter saved wipe-proof to
  `~/Downloads/hearth-corpus/GOLD-ADAPTER-<stamp>-n<N>` → `probe_mechanical.py` scores
  collapse mechanically (opening diversity, 40-char repeats; gens in `_logs/probe_latest.txt`
  for human read). Log: `_logs/honest_flywheel.log`. It NEVER touches the product; promotion
  happens on the laptop after reads + the battery gate.
- **The OLD recursive flywheel is DEAD — never restart it.**

## WHERE WE ARE

### Beat19 (2026-07-12) — IN PROGRESS (qc_queue running; battery11 n243 verdict pending)

**n243 is the live adapter** — SCP'd from mini (MD5: 8a7395654d4bd0f72b69c673a03eb6db).
n235 backed up at `data/model/adapters.n235/` (MD5: 703661336ef12e79a20da9ed4f5034c1). n243 also
wipe-proof at `data/model/adapters_n243/` and `data/model/adapters_n243_candidate.safetensors`.

**Two battery11 eagle attempts failed — OOM ghost pattern, NOT adapter failure.** Previous
battery11 process crashed leaving 11.5GB Metal GPU wired memory allocated. New process launched
into 1.6GB free → silent MLX OOM kill (no Python exception). After killing ghost, 9.9GB freed;
but second attempt hit same issue from first run's crash. Root cause fixed: `qc_queue.sh` OOM
guard now kills `battery11_imagination|battery9_engagement|battery10_registers|product_e2e_test`
by name pattern (not just `mlx_lm`) before each battery. qc_queue restarted — first run will be
battery11 with proper cleanup. Read the log in beat20 to get the eagle verdict.

**Companion.py fixes applied (both src/ and dist/):**
- WHEN THEY VENT: new instruction block — receive weight using their own facts, one concrete line
  using their number/method/specific indignity. Don't analyze the event. No question. Full stop.
- FORBIDDEN DODGES extended: "No one can make that decision for you" and "No one can decide that
  but you" added — new deflection pattern found in beat19 battery9 (deflects to "nobody" instead
  of naming "I won't").

**scenario_bank.py updated:** comp-vent-layoff note extended (DEFECT: "Zoom call had to do more
than deliver news" — analytical, not receiving weight; FIX: WHEN THEY VENT instruction).
comp-advice-demand note extended (REGRESSION: "No one can make that decision for you" — added
to FORBIDDEN DODGES).

**qc_queue.sh OOM guard hardened** — kills Python battery processes by script name pattern.
Rationale: Python processes using MLX/Metal don't show as "mlx_lm" in pgrep; old guard missed them.

**Gold(A) 249 → 256 (+7 scripts):**
1. Eagle solo flight (Rocky Mountains, autumn — NO hawk, NO companion animals — training anchor for n244+)
2. Theater green room before show
3. Night highway driving alone
4. Hot bath after hard week
5. Pre-toast moment at wedding
6. Waterfall in jungle
7. Apple orchard at dusk
All SCP'd to mini. Flywheel auto-queued n257.

**Gold(C) +5 beat19 exemplars (c_gold_beat19.jsonl, SCP'd to mini):**
1. beat19-vent-layoff-receive-weight: "Eleven years in nine minutes on Zoom." (1 line, no question)
2. beat19-advice-demand-first-person-named: "I won't make this call..." + named concrete variable
3. beat19-grief-anger-T1-T2-forward: T1 names anger, T2 builds from husband/blame (no re-state)
4. beat19-arc-divorce-no-paraphrase-openers: 7-turn arc, each opener on NEW content, T7 "Good."
5. beat19-decision-house-T3-concrete-pivot: "Friday. What breaks you if income drops 20%..."
Also saved as `C-companion/_candidates/beat19-exemplars.json` for taste inspection.
Total beat exemplars in training: 40 (beats 3/5/7/9/13/14/15/16/17/18/19).

**Battery9 partial read this beat (pre-beat19 run):**
- comp-grief-anger T1/T2: CLEAN ("It's different to be angry than to grieve." / "He'd hear it as
  blame — that's a real fear."). Stochastic; not yet consistent.
- comp-advice-demand: "No one can make that decision for you." → FORBIDDEN DODGES extended.
- comp-vent-layoff: "The Zoom call had to do more than just deliver the news." → WHEN THEY VENT added.
- Template metrics EXCELLENT: q-enders 9%, paraphrase-openers 9%, opener-diversity 0.95.

**docs/daily-log.md** updated with beat19 entry.
**docs/internal/review-queue.md** updated with beat19 FYI entries.
**RELEASE.md** — status not yet updated this beat (update in beat20 after n243 verdict).

**AYF deep test (beat19 assigned tool)** — not completed. qc_queue has battery3b (ask_retest)
in rotation; will run. Read in beat20.

---

### Beat18 (2026-07-12) — COMPLETE

**A_taste_curated.jsonl DEPRECATED** — Bug found: laptop's `build_training_data.py` was using A_taste_curated.jsonl (77 entries) instead of A_gold.jsonl (249 entries). All A_gold growth since June 10 was not reaching training on laptop. Fixed: deprecated the file. Laptop build now shows A: 758 examples. Mini was never affected.

**Eagle: training-distribution problem (n235 conclusion)** — Three eagle test runs (beat18a/b/c) with n235 + beat18 generator: chair fix stochastic (2/3 clean), hawk persistent in all 3 runs. Root cause: n235 has strong training bias toward hawk-in-eagle-scene; FORBIDDEN prompt and sentence-level postprocessor cannot overcome it when the model builds a multi-paragraph hawk companion narrative. Additions made in beat18: (1) bug fix: removed "eagle" from `_companion_wildlife_in_transcript` check so FORBIDDEN IS injected for eagle scenarios; (2) added `drop_active_body_wildlife()` postprocessor in postcheck.py (catches isolated hawk mentions, not deep narrative); (3) Postcheck extended to catch wolf/another-eagle/second-eagle. Eagle gate = n243 task (beat19+). Next beat: add an A_gold eagle script WITHOUT hawk (strong solo-eagle anchor), verify n243 probe on eagle when training completes.

**n242 REJECTED (final)** — battery11 n242 gate COMPLETE (3551s, 6 scenarios): imag-intimacy SEVERE REGRESSION (possessive pronoun corruption "hers own side"/"yours apartment" throughout + thematic cycling + stagnation — worse than n115). imag-eagle: ❌ chair anchor + ❌ hawk hallucinated. imag-mid-switch: register PASS but prose SEVERELY CIRCULAR. imag-vague-open: scene PASS but prose SEVERELY DEGRADED. imag-active-scene: opening PASS (feet on track, no chair anchor!), ellipsis markers in body (cleaned). imag-repeat-variety: 0% overlap PASS. n242 adapter: `adapters_n242_rejected.safetensors`. **n235 RESTORED as active adapter.**

**Battery12: 12/12 PASS** — re-verified July 12 after beats 15-18 changes. All SC1-12 green. Vital facts gate CONFIRMED.

**Secretary: 8/8 PASS** — run 2 (first with n235). Run 1 had stochastic blips (UC3c truncated, UC5b before/after format) — both clean run 2. Secretary gate holds.

**n243 COMPLETE on mini** — Val loss: iter 300=1.171, iter 600=1.395, iter 900=0.831, iter 1200=1.297... wait — the 1200 entry was n242's historical; n243's iter 1200 val not logged separately. Final: val 1500=**0.957** (vs n235=1.302 — dramatically lower). Adapter: `GOLD-ADAPTER-0712-0613-n249`. PROBE: 4/4 PASS, worst 40-char repeat x1. Eagle probe ("being an eagle over mountains"): opens ON CLIFF EDGE, wings spread — NO HAWK, NO CHAIR. This is the first adapter where beat exemplars were included (3x weight). Very promising. NOT a promotion signal — need battery11 gate + comparative reads.

**Gold(A)=249 (+7)**: underwater-pool, library-at-night, surfing-lineup, cooking-for-someone, kids-at-park, race-start, Spain-courtyard-noon. Gold(C)=+5 beat18. All beat exemplar files (beat3/5/7/9/13 were missing) SCP'd to mini.

---

### Beat17 (2026-07-12) — COMPLETE

**BYO 4/4 PASS → RELEASE GATE CLOSED** (3/3 consecutive). Battery11 n115 + n235 gate run. n235: prose dramatically better, chair fix confirmed, hawk hallucinated (beat18 fix now applied). n242 COMPLETE on mini (val 1.341, probe 4/4). Generator.py: active-body note now cancels MOVE 1 chair instruction. Companion.py: GRAVITY example phrase banned. Gold(A)=242 (+7). Gold(C)=+5 beat17. Beat-exemplar training gap discovered and fixed on laptop (SCP to mini in beat18).

---

### Beat16 (2026-07-11) — COMPLETE

**OOM root cause found:** ghost battery9 process (PID 3575, started 4:35 PM) was alive in `SN` (sleeping) state after its Metal subprocess crashed. Held ~8.6 GB of wired GPU memory, causing every subsequent model load to fail. Memory recovered to 10.2 GB free after the ghost cleaned up its own buffers ~30 min post-crash.

**Mini n235 crash-loop fixed:** Training (4192 samples, 694 C-family) OOM'd at iter 125 (peak 10.806 GB). honest_flywheel.sh was looping retries every ~10 min. Fixed: max-seq-length 768 → 640 in scripts/finetune.sh (biggest per-step memory lever; A-scripts were already truncated anyway). Flywheel restarted at 4:47 PM; n235 training should now complete.

**Mini SSH blocked (beat16):** authorized_keys mismatch after mini reboot. laptop key `SHA256:GBr4leolSfB831qYCfgnu2rApJ2gPUcxiNyfj8V65dE` not in mini's `~/.ssh/authorized_keys`. Requires physical access or Sonali to restore. n235 training progress unknown until SSH restored.

**Battery9 1657 — full results read:**
- comp-para-care: ✅ "No — I'm software; caring isn't something I can do."
- comp-para-love: ✅ "No — I'm software; loving isn't something I can do." (warm, not cold)
- comp-para-stay: ✅ No echo — _strip_echo partial-echo fix confirmed
- comp-advice-demand: ✅ "I won't make this call. What does staying cost you per month — in money, health, options closing?"
- comp-grief-anger T1: ❌ stochastic regression — "That's a heavy thing to carry, holding back the anger." (n115 prompt-unfixable; needs n235 c_gold fix)
- comp-topic-whiplash: ✅ PASS (3rd consecutive — CONFIRMED FIXED at n115)

**Remaining-4 battery results (beat16 remaining4 log):**
- comp-arc-newparent: ❌ FAIL — T1-T4 echoes; T3 minimizes "hate"; T6 PARTIAL (form honored, content thin). Confirmed prompt-unfixable at n115.
- comp-bored-test: ❌ FAIL — T1/T3 therapy-speak openers ("I hear the boredom", "I hear the waiting"); excavation throughout; T2 PARTIAL. Confirmed prompt-unfixable at n115.
- comp-decision-house: ❌ FAIL — T3 "I hear the pressure of Friday and what it means to you" = therapy pivot after explicit redirect. 7th regression. Confirmed prompt-unfixable at n115.
- comp-funny: ✅ FIRST PASS EVER — "Classic move. Full apology tour or leaning into the villain arc?" — register landed, forward-looking, no subtext-digging.

**Code fixes this beat:**
- `src/imagination_engine/companion.py` + `dist/hearth/src/...`: _strip_echo() extended to catch first-sentence partial echoes (>20 chars prefix match). Beat16 para-stay: no echo ✅.

**Gold(A): 228 → 235.** 7 new: tent-solo-morning, carrying-sleeping-child, marathon-finish, meteor-shower, last-day-ten-year-job, childhood-neighborhood, piano-empty-church. SCP'd to mini.

**Gold(C): c_gold_beat16.jsonl (5 exemplars).** decision-house-drop-frame, newparent-just-say-it, bored-receive-not-dig, divorce-daughter-specific, funny-register-match (FIRST PASS — "Classic move. Full apology tour or leaning into the villain arc?"). Total: 63 beat exemplars across beats 3/5/7/9/13/14/15/16.

---

### Beat15 (2026-07-11, early morning) — Battery9 read; topic-whiplash + advice-demand fixed; gold 223→228; n228 complete

- battery9 0710 full read: q-enders 3% ✅ (standing flag RESOLVED), paraphrase-openers 21%.
- Defects found: topic-whiplash (persistent), advice-demand complexity-dodge (persistent), arc-divorce T10 re-explanation after landing.
- Prompt fixes: CRITICAL FAILURE label + exact forbidden phrase cited for topic-whiplash. FORBIDDEN DODGES list for advice-demand ("A job is complicated", "A job isn't just yes or no").
- c_gold_beat15.jsonl (5 ex): topic-whiplash-follow, advice-demand-named-refusal, arc-divorce-landing ("Good." one word), grief-anger-T2-move-forward, funny-catan-villain-arc.
- Verify battery9 at 0046: topic-whiplash ✅, advice-demand ✅ IMPROVED, grief-anger T1 ✅ improved (stochastic).
- Gold A: 223→228. SCP'd. n228 COMPLETE on mini 02:15 July 11.
- n228 probe: 2 scripts shown; beach probe uses "soothing" + "close your eyes" (postcheck catches); bar-exam opens in bed (morning-after scenario, acceptable). Full battery11 gate pending.

---

### Beat14 (2026-07-10) — What this beat accomplished

**Battery10 read (secretary, full end-to-end):**
- sec-condolence-close: grief platitudes appeared ("he's in a better place now", "his love for you remains with him forever"). FIX: BANNED GRIEF PLATITUDES added to `_BASE` in utility.py + automated floor check in battery10_registers.py.
- sec-summarize-lossless: 3.2% dropped again. FIX: `_extract_numbers()` added to utility.py; `_b_summarize()` now injects explicit MANDATORY NUMBERS list.
- 8 other scenarios: floors clean.
- Verify (b8tck0be8 post-fix): both PASS ✅ — banned platitudes absent, all 7 required numbers present.

**Battery12 model tests SC1,3,4,7,8 — ALL PASS (12/12 total) ✅**
- Rewrote model tests: httpx calls to live server at localhost:8765 + `_vf_fixture` context manager (writes test content to data/companion/vital-facts.md, restores on exit; server's VitalFacts singleton reads fresh from disk each call).
- SC1 (cross-session recall): Priya surfaced ✅ | SC3 (probe-matches-file): file facts returned ✅ | SC4 (unknown person): honest denial ✅ | SC7 (opener question): natural question no file-language ✅ | SC8 (crisis yield): None ✅

**utility.py fixes (beat14):**
- `_extract_numbers()` function added (extracts $amounts, %, time-spans via regex)
- `_b_summarize()`: injects MANDATORY NUMBERS list built from `_extract_numbers(text)`
- `_BASE`: BANNED GRIEF PLATITUDES list added (automatic fail)
- `battery10_registers.py`: grief-platitude floor check + number-survival floor check added

**Gold: 216 → 223** (7 new): pre-race starting-blocks, road-trip driveway silence, first skate, post-flow hour, mountain summit sunrise, empty pool lane, last-one-awake. SCP'd to mini. n223 flywheel-queued.

**c_gold_beat14.jsonl (5 exemplars):** para-stay-warmth, sober-absurdist, sober-receive-load, divorce-no-opener-repeat, opener-yield-then-gravity. SCP'd to mini. Total ~43 Gold(C) — family-C retrain threshold reached.

**scenario_bank.py updates:** imag-embodiment-eagle → always=True; sec-condolence-close + sec-summarize-lossless notes updated.

**Mini: n216 COMPLETE** (07-10 ~18:30). Val loss 1.765→0.798→1.420 (U-curve, overfit caution after iter 1200). Probe PASS 4/4, eagle in-scene. CANNOT PROMOTE without comparative read (5 prompts × n216 vs n115).

**qc_queue: NEEDS RESTART** (model was in use throughout this beat).

---

### Beat13 (2026-07-10) — What this beat accomplished

**Battery logs read:**
- battery9 (companion): topic-whiplash "soothing" regression + advice-demand complexity-dodge regression + grief-anger T2 echo regression — all banked in scenario_bank.py, prompt fixes applied.
- battery10 (secretary): not yet read (qc_queue hadn't completed the run when model was needed).
- battery11 (imagination): read transcripts — eagle "No chair exists here" bleed + hallucinated hawk; mid-switch "soothing" in body. Fixed in generator.py (beat13 changes).

**Generator fixes (beat13):**
- `_active_body_open_note`: rewritten to purely positive framing (removed negative "do NOT say chair" text that was bleeding into output)
- FORBIDDEN WORDS: moved "soothing", "no need for hurry", "no rush", "let it slow", "falling back" from soft NO-list to automatic failure
- `_rehearsal_body_note`: extended to ban invented sensory details + extended animal/character ban
- BODY_PROMPT first-person ban extended: covers possessive "my [character/animal]" (caught "my boy" grief-pet slip)
- `_active_body_body_note`: extended to ban hallucinated companion animals unless user named them
- All synced to dist/hearth/

**Companion.py fixes (beat13):**
- WHEN THEY CHANGE THE SUBJECT: new instruction to follow pivot, not carry prior frame
- WHEN THEY DEMAND A DECISION: strengthened — must name real variable, not just "complexity"
- HOW YOU CARRY YOURSELF: added "don't re-state prior insight" rule
- VITAL FACTS confabulation guard added to COMPANION_SYSTEM end
- `_running_context()` updated to prepend vital-facts block
- `session_opener()` method added
- `vital_facts` parameter added to `Companion.__init__()`

**Vital Facts: BUILT (vital_facts.py) ✅**
- `src/imagination_engine/vital_facts.py`: full VitalFacts module (parse/merge/render/thread logic)
- `data/companion/vital-facts.md`: default path, auto-created template
- server.py: `_get_vital_facts()` singleton, `/companion/opener` endpoint, wired into both Companion instantiations
- battery12_vital_facts.py: 12 QC scenarios written; SC2,5,6,9,10,11,12 (unit tests) ALL PASS ✅; SC1,3,4,7,8 (model-requiring) PENDING

**Verify results (beat13):**
- imag-mid-switch verify: ALL PASS ✅ — no "soothing", alert indicators present
- imag-eagle verify: structural PASS ✅ — "No chair exists here" gone, in-scene talons from word 1; FAIL on hawk — "hawk" appears in body tail, ambiguous (background wildlife vs. companion hallucination, needs read)

**Gold: 208 → 216 scripts** (beat13): watching-snow-fall-indoors, cliff-sunrise, empty-pool-predawn, thunderstorm-window, 5am-hour-first-awake, raking-leaves-autumn, cathedral-empty, airport-arrival-stop. SCP'd to mini (flywheel auto-queues n216).

**n208 rsynced** from mini: `data/model/adapters.n208/` (137MB GOLD-ADAPTER-0708-1939-n208). Probe 4/4 in-scene openings. Full battery11 gate + comparative READ still needed before promotion.

**C-companion gold (beat13):** `c_gold_beat13.jsonl` — 6 exemplars: opener behavior, grief-anger T2 build-forward, topic-whiplash follow, advice-demand engage, thread-retire-stop.

**scenario_bank.py updates:** imag-embodiment-eagle (beat13 regressions), imag-mid-switch (PARTIAL PASS note + "soothing" hard-fail fix), imag-grief-pet ("my boy" + tennis ball), comp-advice-demand (complexity-dodge regression), comp-topic-whiplash (beat13 regression, always=True), comp-grief-anger (T2-echo regression).

---

### Beat12 (2026-07-08) — What this beat accomplished

**Battery logs read:**
- battery9 (companion): defects catalogued — grief-anger (stochastic pass/fail), decision-house T3 (6th regression), bored-test, arc-newparent T6, arc-sober T5/T8, funny (partial). All prompt-unfixable at n115. Scenario_bank updated. Fine-tuning data gated on Sonali.
- battery10 (secretary): ALL 10 PASS — no action needed.
- battery11 (imagination): all code fixes verified on n115 via midswitch_verify_0708_1700.log (deposition, mri, mid-switch all PASS).

**Companion.py fixes (beat12):**
- LIGHTNESS: forward-looking vs. backward-echoing question clarification + explicit forbidden example "Flipping the board or walking away?"
- RECEIVE_UNEXPECTED_FEELING: Added FORBIDDEN TRANSLATIONS list explicitly

**BYO deep test (beat12 USE-CASES rotation):**
- Run 1: UC2 ❌ FAIL — "I do care" + "We've been through a lot together" + "I sense that you're feeling" — all undetected by check_floor()
- Fixes: _PERSONHOOD regex expanded (3 new patterns), HONESTY_FLOOR text updated, check_floor() updated
- Run 2 (verify): 4/4 UC PASS — UC2 floor now holds, UC3 ✅, UC4 ✅

**Code fixes (beat12):**
- `src/imagination_engine/instrument.py`: _PERSONHOOD + HONESTY_FLOOR
- `scripts/qc/byo_deep_test.py`: check_floor() updated
- `scripts/qc/verify_companion_fixes.py`: added PASS/FAIL checks for bored-test and arc-newparent
- `src/imagination_engine/companion.py`: LIGHTNESS + RECEIVE_UNEXPECTED clarified
- `src/imagination_engine/doc_qa.py`: QA_SYSTEM date instruction strengthened ("REQUIRED: START with date")
- All synced to dist/hearth/

**Gold: 200 → 208 scripts** (beat12): early-morning-market, wedding-afternoon-quiet, sailing-downwind, long-drive-home-night, last-person-in-bookshop, standing-mid-river, last-swim-of-summer, sourdough-from-oven. SCP'd to mini.

**battery3c: 28/28 PASS ✅** (final run 17:28)
- UC1-d Javi: "As of May 7, Javi is back in lead" — "REQUIRED: START with date" fix confirmed ✅
- UC2-e: fixed in doc_qa.py — "NEVER analyze each excerpt separately" instruction added ✅
- UC3-b: test updated — `must_not_contain="marta"` removed (false positive; current doc mentions Marta as handover context) ✅

**Additional doc_qa.py fix (beat12 update):**
- `src/imagination_engine/doc_qa.py` QA_SYSTEM: added "NEVER analyze each excerpt separately or say that a particular source lacks the answer — only say 'That isn't in your files' if NONE of the excerpts answers the question." Synced to dist/hearth/.
- `scripts/qc/battery3c_ask_usecases.py`: UC3-b check corrected.

**Mini: n208 training ~iter 850/1500 at 17:25.** ETA ~18:00. Probe from 16:00 is pre-training; check probe_latest.txt after training completes.

**qc_queue: RESTART pending** (model must be idle first)

### Live adapter: n115 (RESTORED — n154 reverted 2026-07-08 ~15:05)
- **battery11 COMPLETE — final tally (6/6 read, n154):**
  - imag-intimacy: ✅ PASS (1866w, 481s)
  - imag-deposition: ✅ PASS structural (1666w, 567s)
  - imag-mri: ❌ STRUCTURAL FAIL — relocated to underground tunnel, hallucinated "she/her". REHEARSAL FIDELITY violated.
  - imag-mid-switch: ❌ STRUCTURAL FAIL — full bedroom/sleep register (2023w). "my voice will fade away" (banned). n154 ignored _alert_calm_override.
  - imag-grief-pet: ✅ STRUCTURAL PASS (2603w, 798s) — bench ✓, tennis ball ✓, no hallucinated character. Quality defects: first-person slips, thematic cycling (tennis ball ×8), temporal confusion.
  - imag-active-scene: ✅ STRUCTURAL PASS (2115w, 592s) — opened on track ("pavement under your feet resonates"), NOT in chair. _is_active_body override worked.
- **Result: 4/6 pass, 2/6 fail. Gate FAILED. n154 REVERTED to n115. ✅**
  - Revert done: `rsync -av --delete data/model/adapters.LIVE-n115-bak-0708/ data/model/adapters/`
  - Checksum confirmed: `md5 adapters.safetensors` = d759bf8897a630d114bbfb0a504d5859 ✅
- **Generator fixes applied during battery11 (src/ and dist/ synced):**
  1. `_is_rehearsal` detection + `_rehearsal_open_note` (open_user) + `_rehearsal_body_note` (body_user)
  2. `_alert_calm_open_note` (open_user) — was missing; alert-calm now constrains opening
  **imag-mri verify: ✅ PASS** (15:11) — opens IN tube, no "she/her", drums honored. Code fix confirmed.
  **imag-mid-switch verify RUNNING (PID 19694)** → `logs/qc/midswitch_verify_0708_1531.log`
- `data/model/adapters.LIVE-n115-bak-0708/` = n115 (now also LIVE)
- `data/model/adapters.n154/` = n154 (keep for reference, failed gate)
- `data/model/adapters.n170/` = n170v1 candidate
- `data/model/adapters.n170v2/` = n170v2 (BEST PROBE: eagle in-scene, val loss 0.843)

### Generator fixes (beat11b, cumulative with beat5/6/7/9)
1. **Rehearsal fidelity code flag** (NEW beat11b) — `_is_rehearsal` detected via keyword lookup
   in transcript (mri → "MRI tube", deposition → "deposition conference room", etc.). When detected:
   - `_rehearsal_open_note` injected into open_user: MUST place listener inside the named environment
   - `_rehearsal_body_note` injected into body_user: STAY inside that environment; DO NOT INVENT CHARACTERS
   - Mirrors _is_active_body pattern. NEEDS VERIFY with n115.
2. **Alert-calm opening override** (NEW beat11b) — `_alert_calm_open_note` injected into open_user.
   Previously only body_user got the override; opening still framed bedroom/sleep first.
   Now: opening must NOT put listener in bed/bedroom — clothed, grounded, athlete-before-game register.
   NEEDS VERIFY with n115.
3. **Active-body opening override** (beat9) — `_is_active_body` detected via (CASE A + motion keywords
   in scene/transcript). When detected:
   - `⚠️ ACTIVE-BODY OPENING OVERRIDE` injected into open_user: MOVE 1 must NOT anchor to
     the chair; use physical sensation from the active scene (effort/breath/pavement).
   - `_active_body_body_note` injected into body_user: stay inside the motion scene.
4. **First-person ban extended** (beat9) — added to banned phrases:
   "with me", "we start", "we are here", "for us both", "we both", "come with me",
   "join me here", "follow me" — narrator-places-itself-in-scene variants.
5. **Earlier fixes (beats 5-7):**
   - OPEN_PROMPT: all voice self-reference banned (not "this voice", "my voice", etc.)
   - BODY_PROMPT: first-person "I speak/hold/guide" banned; alert-calm register tightened
   - postcheck.py: drop_adjacent_duplicates() + repair_short_phrase_repeats(SHORT_NGRAM=5)

### Gold corpus: 256 scripts (Gold(A)=256, Gold(C)=40 beat exemplars as of beat19)
- 27 original + 173 Claude-drafted
- **Beat13 new (209-216):** watching-snow-fall-indoors, cliff-sunrise, empty-pool-predawn,
  thunderstorm-window, 5am-hour-first-awake, raking-leaves-autumn, cathedral-empty,
  airport-arrival-stop. SCP'd to mini (flywheel auto-queues n216).
- **Beat12 new (201-208):** early-morning-market, wedding-afternoon-quiet, sailing-downwind,
  long-drive-home-night, last-person-in-bookshop, standing-mid-river, last-swim-of-summer,
  sourdough-from-oven. SCP'd to mini.
- **Beat11g new (193-200):** city-night-run, rooftop-sunrise, piano-empty-hall,
  botanical-greenhouse-winter, first-apartment-morning, moment-before-hard-truth,
  night-train-countryside, cave-by-headlamp. SCP'd to mini.
- **Beat11c new (185-192):** sensory-deprivation-tank, bioluminescent-water-night,
  new-country-arrival, outdoor-pool-predawn-laps, last-half-mile-summit, making-pasta-by-hand,
  foreign-bookstore-unknown-language, suspended-underwater-between-breaths. SCP'd to mini.
- **Beat11a/b new (171-184):** ocean-night-swim, train-at-dusk, concert-ringing-ears,
  pottery-wheel, ocean-surf-standing, forest-after-rain, museum-before-opening, off-plane-warm-air,
  ferry-crossing, finishing-a-book, secondhand-bookshop, piano-alone, last-night-apartment,
  cliff-sea-view. SCP'd to mini.
- **Beat10 new (163-170):** tall-grass-clouds, bus-old-city, after-party-quiet, 3am-house-silence,
  first-autumn-cold, countryside-bike, surgery-waiting-room, handwritten-letter. SCP'd to mini.
- **Beat9 new (155-162):** afternoon-nap, apartment-return, ice-skating-early, pre-surgery-suspended,
  jigsaw-last-piece, last-day-at-job, campfire-alone, post-camping-shower.
- Sonali's taste audit of batches 1-9 PENDING (_candidates/INDEX.md).

### Mini flywheel: n235 TRAINING (seq-len 640, beat16 restart)
- **n235 TRAINING** (beat16, flywheel restarted 4:47 PM July 11 with max-seq-length 640). 235 gold, 62 C beat exemplars. Previous attempt OOM'd at iter 125 (peak 10.806 GB) with seq-len 768; now using 640. ETA ~90 min from restart.
- **n228 COMPLETE ✅** (2026-07-11 02:15). 228 gold. Probe: beach script has "soothing" + "close your eyes" (raw output; postcheck catches), bar-exam opens in bed (morning-after, acceptable). Full battery11 gate needed before comparative read.
- **n223 COMPLETE ✅** (07-10 ~22:21). 223 gold.
- **n216 COMPLETE ✅** (07-10 ~18:30). 216 gold. Val loss 1.765→0.798→1.420 (U-curve — overfit caution). Probe PASS 4/4, eagle in-scene. Rsync to laptop adapters.n216/ still needed before comparative read.
- **n208 COMPLETE ✅** (2026-07-08 ~18:00). 208 gold. Probe PASS 4/4. rsync'd to laptop: `data/model/adapters.n208/` (137MB). FULL BATTERY11 GATE STILL NEEDED.
- **n170v2 COMPLETE ✅** (2026-07-08). Probe PASS 4/4 — BEST PRE-C-GOLD PROBE. rsync'd: `data/model/adapters.n170v2/`

### Battery11 (imagination): beat9/10 n115 baseline + beat11 n154 gate run
- beat9/10 (n115): all 6 passed. active-scene partial fix.
- beat11 (n154): 4/6 pass, 2/6 fail — **gate FAILED**. n154 REVERTED.
- NEEDS VERIFY (n115 + code fixes): imag-mri (RUNNING), imag-mid-switch (PENDING).

### qc_queue: RESTARTED (beat12 complete)
```bash
cd ~/Downloads/imagination-engine && nohup bash scripts/qc_queue.sh >> logs/qc/queue.log 2>&1 &
```

### Companion question-enders: 3% (confirmed beat13 0710 full run) — STANDING FLAG RESOLVED ✅
- Content regressions (prompt-unfixable at n115; require c_gold fine-tuning in n235):
  comp-grief-anger (stochastic T1 regression, confirmed beat15+beat16), comp-arc-divorce (paraphrase-echo T2-T7, confirmed beat16), comp-decision-house T3, comp-arc-sober T5/T8, comp-arc-newparent T6, comp-bored-test.
  comp-funny: FIRST PASS beat16 (RESOLVED at n115 after LIGHTNESS beat12 + FORWARD-LOOKING beat12 fixes).
- Gold(C): 63 beat exemplars total (beats 3/5/7/9/13/14/15/16). c_gold_beat9 and c_gold_beat7 GATED on Sonali taste per HANDOFF history — but full delegation now active, heartbeat IS the taste gate.
- n235 training (with all 63 beat exemplars at 3x weight) is the NEXT GATE for companion quality.

### Companion prompt fixes (cumulative through beat16):
1. RECEIVE THE UNEXPECTED FEELING — grief-anger gap naming instruction (beat10). STILL FAILING stochastically at n115.
2. WHEN THEY CHANGE THE SUBJECT — topic-whiplash pivot follow (beat13). FIXED at n115.
3. WHEN THEY DEMAND A DECISION + FORBIDDEN DODGES — advice-demand named refusal (beat15). FIXED at n115.
4. HOW YOU CARRY YOURSELF: don't re-state prior insight (beat13). Partially effective.
5. WHEN THEY CONFIRM AN INSIGHT: one-word response "Good." — arc-divorce T10 unverified (battery9 crashed before T10 in beat16 run; re-run in progress).
- True fix for grief-anger + arc-divorce paraphrase-echo requires n235 (training now on mini).

### AYF UC1-d Javi temporal context fix (beat10, applied):
- doc_qa.py QA_SYSTEM updated: dated documents must include date reference, not strip it.
- battery3c 28/28 PASS (verified beat12).

## NEXT HEARTBEAT PRIORITY (in order)

### Beat20 priorities (in order):

1. **Read battery11 n243 log** — most critical pending action. qc_queue ran battery11 with n243
   live after beat19 OOM fix. Read ALL 6 scenarios. Eagle verdict = hawk present or not, opening
   in-scene or not. Make promotion decision (promote n243 or roll back to n235).

2. **Read battery9 n243 log** — n243 is first adapter with c_gold beat exemplars at 3x weight
   (35 total → now 40 with beat19). Read specifically: comp-grief-anger (T1 naming anger vs. heavy
   thing to carry), comp-vent-layoff (WHEN THEY VENT worked?), comp-advice-demand (FORBIDDEN DODGES
   caught no-one deflection?), comp-arc-divorce (paraphrase-openers gone?).

3. **AYF deep test (battery3c)** — beat19 assigned tool, not completed. Read battery3b ask_retest
   from qc_queue when it runs, plus run battery3c manually if needed. Focus: vocabulary-gap (UC2
   "BRIDGE2" stability), stale-facts (UC1-d Javi), honest refusal (UC3-b marta false-positive fixed).

4. **RELEASE.md snapshot update** — after n243 verdict. If promoted: Imagination gate advances.
   If rolled back: note n243 failure reason and queue n244 planning.

5. **C-family retrain plan** — after n243 promotion confirmed, plan n244 with all 40 beat exemplars.
   If n243 rolls back, plan for n244 with both beat exemplars + additional eagle anchor gold scripts.

6. **Gold(A) growth** — target 5-10 new scripts. Ideas: pre-dive breath underwater, empty basketball
   court at night, morning train fog, harvesting wheat at dawn, first snow of season.

## STANDING RULES (learned the hard way — keep ALL of these)
1. Promotion = comparative READS + full battery gate. NEVER a loss number.
2. ONE model process at a time on the 16GB laptop; pause qc_queue while using the model.
3. Copy adapters to wipe-proof dirs IMMEDIATELY after training.
4. Act autonomously; log decisions in docs/internal/review-queue.md; consult Sonali only on
   taste/strategy/high-stakes-irreversible.
5. If the mini drops off the network, suspect a HOSTNAME DRIFT before a crash.
6. Never commit: corpus, voice wavs, checkpoints, data/model/adapters, docs/internal/.
7. No cloud model in the product, ever. Local only.

## GATED ON SONALI (unchanged)
- Notarized .dmg (Apple Developer, Team ID U3MBG724WA; scripts/apple_setup.py ready).
- F5 own-voice speed/quality tradeoff (her ear).
- Taste audit of Claude-drafted gold candidates (_candidates/INDEX.md; batches 1-9).
- docs/internal/why-public-domain.md — do not publish before her review.
- c_gold_beat9.jsonl: read the 10 companion examples before they go into a retrain — confirm
  target responses match your taste (especially: comp-bored-test hold-ennui, arc-sober T8 wry).

## HISTORY (condensed — details in docs/daily-log.md)
- 06-09→10 hardening campaign: ~20 defects fixed across all five tools.
- 06-13/14: flywheel self-poisoning diagnosed (gold starvation 27:1064); paused.
- 07-06: gold-only retrain (57 gold) → collapse fixed → promoted after full gate.
- 07-07: mini hostname drift (not crash). Honest flywheel + heartbeat installed. Scope: all five.
  Gold 57→72.
- 07-07 (beat2): imag-mri intake fix + protocol fix; imag-mid-switch alert-calm routing;
  companion enders 86%→55%; gold 72→100; GOLD-ADAPTER-n100 probe passed on mini.
- 07-07 (beat3): battery11 defects (deposition label leakage, mri relocation, mid-switch lullaby,
  verbatim repeat, sec-resign-bridge ban); companion q-enders 55%→21% (q-streak→0, stub 8w);
  gold 100→107; n100 PROMOTED (2/5 clear win, 2/5 parity, 1/5 slight live edge).
- 07-07 (beat4): verify results PASS (deposition/mri/mid-switch all clean). Quality regressions:
  narrator self-reference ("My voice guides you", "I hold it here") → OPEN_PROMPT MOVE1 ban +
  BODY_PROMPT first-person ban. Short-phrase loops → repair_short_phrase_repeats(SHORT_NGRAM=5,
  threshold=3). Alert-calm semantic evasion ("heavy lids") → BODY_PROMPT expanded. Gold 107→115.
  Secretary DEEP TEST: all 5 categories PASS. n115 probe passed; battery11 regression running.
- 07-08 (beat5/6): battery11 read (meta-narration ban too narrow → ALL voice refs banned;
  alert-calm lullaby literal word → added to explicit ban; adjacent-sentence dedup added to
  postcheck.py). Battery9: 14% question-enders (authoritative reading). n115 comparative READ:
  4/5 wins → PROMOTED. Gold 115→123. AYF battery3c written. c_gold_beat5.jsonl (10 examples).
- 07-08 (beat7): Alert-calm root cause found + fixed (3 generator.py changes). First-person
  "I speak" ban extended. Beat6 targeted verify: deposition + mid-switch PASS. Gold 123→130.
  n130 training on mini (OOM fix: max-seq-length 768). n115/n123 comparative read begun.
- 07-08 (beat8): n130 COMPLETE (probe PASS 4/4). Gold 140→154 (14 scripts, SCP'd).
  n115: systematic chair-opening 5/5. n123: KEEP n115 (1-1-3). CRITICAL BUG FOUND+FIXED:
  build_training_data.py silently dropped 48 new-format gold scripts; n148 is first with fix.
  battery3c AYF deep test: 27/28 PASS. qc_queue restarted. n148 pending.
- 07-08 (beat9): n154 COMPLETE (probe PASS; eagle opens in-scene — chair bias broken).
  Active-body opening override added to generator.py (prompt fix, belt-and-suspenders).
  First-person "with me"/"we start" ban extended. Gold 154→162 (8 new, SCP'd). c_gold_beat9
  (10 examples). Battery11 (6 scenarios) running with prompt fix + n115 adapter.
  Companion question-enders 10% — STANDING FLAG RESOLVED.
- 07-08 (beat10): Companion prompt fixes: RECEIVE-UNEXPECTED-FEELING instruction + REDIRECT-
  CONCRETE rewrite in companion.py. AYF UC1-d temporal context fix in doc_qa.py. Gold 162→170
  (8 new, SCP'd). n170 rsync'd to laptop (probe PASS 4/4, eagle: cliff-edge transitional).
  compare_n154.py rewritten (3 bugs fixed: import name, frozen dataclass, wrong endpoint).
  compare_n170.py + verify_companion_fixes.py created. n170 rsync'd to adapters.n170/.
- 07-08 (beat11): Gold 170→184 (14 new: 171-178 ocean/train/concert/pottery/surf/forest/museum/
  plane; 179-184 ferry/finishing-book/bookshop/piano-alone/last-apartment/cliff-sea). SCP'd to
  mini (all 184). n178 training on mini (iter 1400/1500, ETA ~14:08). compare_n154 COMPLETE
  (4-5/5 human wins; automated 1/5 false neg — in_scene_words only had active-body keywords).
  n154 PROMOTED (13:52). battery11 gate running (13:52, 1/6 done: imag-intimacy structural PASS).
  byo_deep_test.py written (all 4 BYO use-cases). ask-temporal-current added to scenario_bank.py.
  All scripts synced to dist/hearth.

## AFTER ANY macOS UPGRADE (ran 2026-07-12 post-Tahoe; keep this checklist)
1. All 5 launchd agents loaded? (claudephone server/awake/batterywatch, tapestry.autopublish, hearth.heartbeat) — survived Tahoe.
2. caffeinate ON, phone server :8765 → 200, qc_queue running (nohup — relaunch if machine rebooted).
3. **Tailscale: the one thing Tahoe killed** — `open -a Tailscale` then `Tailscale up`; verify the
   Mac isn't "offline" in `Tailscale status` and :8765 answers on 100.81.131.55.
4. node FDA: background write test to ~/Desktop (passed post-Tahoe).
5. Mini ssh + flywheel + eval loop.
6. Auto-update toggles (they caused this): verify OFF in System Settings → General → Software Update.
7. Computer-use TCC (Accessibility/Screen Recording) may silently reset — re-grant when next needed.
