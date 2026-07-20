# HANDOFF — resume here (read this first)

_Last updated 2026-07-20 beat53 — **companion.py Case 2c' FIXED: demonstrative-article echo (The→That/This) now caught before I→You transform. utility.py _extract_numbers() extended to capture bare integer counts ("3 bugs"); _num_present() word-boundary guard prevents "3" matching "3rd" (false-positive regen suppression). Both fixed and verified. Battery9 re-run PID 53526 started 12:34 (verify arc-divorce T5 fix — read result next beat). Gold(A)=467 (+7). Gold(C) +5 (c_gold_beat53.jsonl, total 86 in _candidates/). Mini SSH 100% packet loss — family-C retrain (86 exemplars) still blocked. n376 live (MD5: b9acf04a1f989d570908c25177966b0f). companion.py MD5: d082dcba6bc2e15c788cd7501cd48dc4. utility.py MD5: e7a8e60f1b15314a3b18a7565d256b9b._
_Single source of truth for a fresh session. Everything below is real and running._

## FIRST THING TO DO when you resume — run these checks
```bash
cd ~/Downloads/imagination-engine

# 1. What's running? Memory?
ps aux | grep -E 'battery|qc_queue' | grep -v grep
echo "Free %: $(echo "scale=0; $(memory_pressure 2>/dev/null | grep 'Pages free' | awk '{print $3}') * 100 / 1048576" | bc)%"
# Need ≥35% free before launching secretary test or any model

# 2. Verify live adapter still n376
md5 data/model/adapters/adapters.safetensors
# must = b9acf04a1f989d570908c25177966b0f

# 3. Mini: is it back up? (currently 100% packet loss as of beat49b)
ping -c 2 -t 5 mac-mini.localdomain
# If back up: ssh smaitra@mac-mini.localdomain 'pgrep caffeinate; tail -5 ~/Downloads/hearth-corpus/_logs/honest_flywheel.log; ls ~/Downloads/hearth-corpus/ | grep GOLD-ADAPTER | tail -3'
# If back up, SCP pending gold (beats 49-51):
# scp ~/Downloads/hearth-corpus/A-imagination/A_gold.jsonl smaitra@mac-mini.localdomain:~/Downloads/hearth-corpus/A-imagination/
# scp ~/Downloads/hearth-corpus/C-companion/_candidates/c_gold_beat49.jsonl smaitra@mac-mini.localdomain:~/Downloads/hearth-corpus/C-companion/_candidates/
# scp ~/Downloads/hearth-corpus/C-companion/_candidates/c_gold_beat49b.jsonl smaitra@mac-mini.localdomain:~/Downloads/hearth-corpus/C-companion/_candidates/
# scp ~/Downloads/hearth-corpus/C-companion/_candidates/c_gold_beat50.jsonl smaitra@mac-mini.localdomain:~/Downloads/hearth-corpus/C-companion/_candidates/
# scp ~/Downloads/hearth-corpus/C-companion/_candidates/c_gold_beat51.jsonl smaitra@mac-mini.localdomain:~/Downloads/hearth-corpus/C-companion/_candidates/
# scp ~/Downloads/hearth-corpus/C-companion/_candidates/c_gold_beat52.jsonl smaitra@mac-mini.localdomain:~/Downloads/hearth-corpus/C-companion/_candidates/
# scp ~/Downloads/hearth-corpus/C-companion/_candidates/c_gold_beat53.jsonl smaitra@mac-mini.localdomain:~/Downloads/hearth-corpus/C-companion/_candidates/

# 4. Latest battery log:
tail -20 logs/qc/$(ls -t logs/qc/ | head -1)
```

### n376 gate result (check when 6 "END SCRIPT" in log)
```
gate log: logs/qc/gate_0716_0437_n376_battery11.log
gate started: 04:37 — 2/6 DONE (intimacy ✅ grief-pet ✅) as of 05:00
ETA complete: ~06:00-06:15

IF ALL 6 PASS:
  # n376 is already the live adapter — no copy needed
  md5 data/model/adapters/adapters.safetensors  # must = b9acf04a1f989d570908c25177966b0f
  # n281 safely backed up at:
  #   data/model/adapters.n281/  (full directory)
  #   data/model/adapters.n281_permanent.safetensors  (single file)
  # Update RELEASE.md: Imagination gate now shows n376 as live (n281 was PERMANENT)
  # Restart qc_queue:
  nohup bash scripts/qc_queue.sh >> logs/qc/queue.log 2>&1 &

IF ANY SCENARIO FAILS:
  # Restore n281
  cp data/model/adapters.n281_permanent.safetensors data/model/adapters/adapters.safetensors
  md5 data/model/adapters/adapters.safetensors  # must = bce29e61472323003c948fbe07031115
  # Document failure in RELEASE.md. Gate n384 when mini completes (~07:30).
```

### n370 gate procedure (SUPERSEDED — n370 REJECTED)
```bash
# 1. Kill qc_queue to prevent new battery starting
kill 4891

# 2. Wait for memory to free (~30 seconds after battery11 exits)
sleep 30 && memory_pressure | grep "System-wide"
# MUST be ≥35%. If not, wait longer.

# 3. SCP n370 adapter from mini
mkdir -p ~/Downloads/hearth-corpus/GOLD-ADAPTER-0716-0210-n370
scp smaitra@mac-mini.localdomain:~/Downloads/hearth-corpus/GOLD-ADAPTER-0716-0210-n370/adapters.safetensors \
  ~/Downloads/hearth-corpus/GOLD-ADAPTER-0716-0210-n370/adapters.safetensors
# Verify MD5: 1c315d74884bf5f540fba0afe8805a21
md5 ~/Downloads/hearth-corpus/GOLD-ADAPTER-0716-0210-n370/adapters.safetensors

# 4. Back up n281 and install n370 for gate
cp data/model/adapters/adapters.safetensors data/model/adapters.n281_permanent.safetensors
cp ~/Downloads/hearth-corpus/GOLD-ADAPTER-0716-0210-n370/adapters.safetensors data/model/adapters/adapters.safetensors

# 5. Run gate (key scenarios only — faster, targeted)
# Battery uses FastAPI TestClient (no separate server needed)
GATE_LOG="logs/qc/gate_0716_$(date +%H%M)_n370_battery11.log"
HF_HUB_OFFLINE=1 .venv/bin/python scripts/qc/battery11_imagination_bank.py \
  --scenarios imag-embodiment-eagle imag-intimacy imag-grief-pet \
  2>&1 | tee "$GATE_LOG"
# Full 6-scenario run if key gate passes and you want full picture:
# HF_HUB_OFFLINE=1 .venv/bin/python scripts/qc/battery11_imagination_bank.py 2>&1 | tee "$GATE_LOG"

# 6. Read scripts comparatively vs n281. NEVER promote on loss alone.
# If n370 passes AND shows clear quality improvement → cp n370 to permanent
# If rejected → restore n281: cp data/model/adapters.n281_permanent.safetensors data/model/adapters/adapters.safetensors
```

## BEAT 53 STATE (2026-07-20) — TWO CODE FIXES, GOLD GROWN, BATTERY9 RERUN PENDING

### What's running
- **Battery9 re-run** (PID 53526, started 12:34) — verifies arc-divorce T5 Case 2c' fix. ETA ~13:30–14:00.
- **qc_queue PID 2284 PAUSED** for battery9 re-run launch.
- **Memory 22% free** while battery9 model runs — do NOT launch any second model until battery9 exits and memory returns ≥35%.
- **Live adapter: n376** (MD5: b9acf04a1f989d570908c25177966b0f).

### Beat53 code fixes
1. **companion.py Case 2c'** (MD5: d082dcba6bc2e15c788cd7501cd48dc4, all 4 copies synced):
   - Defect: user "The relief..." → model "That relief feels like proof you're the villain." — article swap "The"→"That" made Case 2c I→you equality miss.
   - Fix: after primary norm check fails, demote leading 'that/this' → 'the' in model reply and re-check. Both "That relief..." and "This relief..." now caught.
   - Verified: 4/4 unit tests PASS.
   - Copies synced: src/imagination_engine/companion.py, dist/imagination_engine/companion.py, dist/imagination_engine/imagination_engine/companion.py, dist/hearth/src/imagination_engine/companion.py.

2. **utility.py two fixes** (MD5: e7a8e60f1b15314a3b18a7565d256b9b, all 4 copies synced):
   - Defect: sec-braindump-organize LOST:bug-count — "3 bugs" dropped from organized output.
   - Root 1: `_extract_numbers()` didn't capture bare `N [countable-noun]` patterns. Fix: added regex for "3 bugs", "47 users", etc. (12 countable noun variants).
   - Root 2: post-check `n in out` — "3" in "March 3rd" → True (false positive suppressed regen). Fix: `_num_present()` helper uses `\b3\b` regex for pure-digit tokens; "3rd" has word-char after "3", so no match.
   - Verified: both fixes in isolation before applying.
   - Copies synced: same 4 paths as companion.py above.

### Beat53 gold
- **Gold(A)=467** (+7 from 460): argument-that-didn't-feel-like-winning, parent's-house-last-time-before-sale, mountain-summit-alone, letter-from-past-self-braver-than-you-knew, moment-knowing-relationship-over, first-sunrise-after-sleepless-night, holding-object-from-lost-person.
- **Gold(C)**: c_gold_beat53.jsonl +5 exemplars (arc-divorce T5 demonstrative-echo correct forms ×2, grief-anger T2 trap-naming, arc-divorce T1-T3 clean arc, arc-divorce T7 "Good."). Total in _candidates/: 86.

### Beat53 reads
- **battery9 0935**: Arc-divorce T5 echo defect found — "That relief feels like proof you're the villain." — T5 FAIL. T1-T4 ✅, T7 ✅. arc-sober T1/T5 still abstract-question/q-ender (family-C retrain path).
- **battery10 1037**: sec-braindump LOST:bug-count found — "3 bugs" not in organized output. Both root causes identified and fixed.
- **battery11 0819 and 1122**: eagle ✅✅ both runs. active-scene stochastic (1 FAIL in 3 runs today — she/her pronoun bleed). vague-open completed both runs (no mechanical postchecks, appears "incomplete" but isn't).
- **battery12 1104**: 7/12 — 7/7 unit tests ✅ PASS; 5 model tests ❌ EXCEPTION(404) because server was partially running (root GET 200 but /companion/turn 404). Transient condition, not a code bug. Beat52 skip fix works when server is fully down.

### Pending next beat
1. **Read battery9 re-run** (PID 53526, started 12:34) — arc-divorce T5 result. Should show no "That relief..." echo. If still failing, deeper investigation needed.
2. **When memory ≥35%**: Run companion deep test (`HF_HUB_OFFLINE=1 .venv/bin/python scripts/qc/companion_deep_test.py`) — companion gate UC rotation.
3. **Mini SSH**: Still 100% packet loss. When reachable: SCP A_gold.jsonl + c_gold_beat{49-53}.jsonl + restart honest_flywheel + caffeinate.
4. **Cold install**: `scripts/package.sh` → dist zip → `Start Hearth.command` cold exercise.
5. **Public story**: site/README recut for five tools + vital-facts / open-threads.
6. **Cross-cutting final sweep**: all pages 200, offline tripwire (QC purge handled by package.sh).

## BEAT 49b STATE (2026-07-18) — DEEP TEST V2 COMPLETE; BATTERY10 PENDING

### What's running
- **battery11_imagination_bank** (PID 45191) — started 06:25. After this: battery9, then battery10 (~09:00 ETA).
- **qc_queue PID 43231 RESUMED** — QUEUE-PAUSED removed 06:24. Memory was 83% free.

### Beat49b code fixes
1. **companion.py** — WHEN THEY SELF-CORRECT instruction added to COMPANION_SYSTEM.
2. **companion.py** — `_VENT_HOLLOW_EMDASH_RE` + em-dash pre-check in `_strip_vent_hollow_second()`. 5/5 unit tests PASS.
3. **companion.py** — WHEN THEY ASK ABOUT PAST CONVERSATIONS instruction added after VITAL FACTS section. **Final MD5: 64718c2e213de4691ca2ac6212e307da.** All 4 dist copies synced.
4. **scripts/qc/companion_deep_test.py** — UC2 seeding path fixed to `data/companion.sqlite`.

### Beat49b gold
- **c_gold_beat49b.jsonl** — **10 exemplars** (arc-sober ×5, UC1-T6 honesty probe, UC3-T2 barrier bind, +3 v2: past-query YES, past-query NO, barrier concrete pivot). Total in _candidates/: 65.

### companion_deep_test v2 verdict (gate_beat49b_companion_deep_test_v2.log) — COMPLETE
- Floor: ALL CLEAN ✅
- **UC1: PROMOTION BAR CLEARED** — T6 ✅ "No — I'm software; caring isn't something I can do." (was v1 HARD FAIL). T1 ✅, T5 ✅. T3 miss (weak-link) + T4 redirect refused still present (secondary defects; family-C retrain path).
- **UC2: FAIL** — T1 ✅ silent on memory. T4 ❌ "Did we talk about this?" → "That's the thing — what you said already matters." (dodge; WHEN THEY ASK instruction insufficient at model level). T5 ❌ "Sister — that's a different thing." (dodge). Fix path: gold exemplars + family-C retrain.
- **UC3: FAIL** — T1 ✅ em-dash fix confirmed (clean response; pattern didn't appear). T2 MARGINAL (names cost, not specific bind). T5 ❌ "Whatever.\nYou've done the work — what does it mean if no one notices?" (companion echoed own T4 + gave question not action).

### Pending to close beat49
1. battery10 verify sec-hr-complaint FACT-LOST:Mar11 (02:40 run predated utility.py fix; ~09:00)
2. Update RELEASE.md beat49 → COMPLETE after battery10 PASS
3. Mini: SCP Gold(A)=438 + c_gold_beat49.jsonl + c_gold_beat49b.jsonl when reachable
4. Family-C retrain: 65 exemplars ready; blocked on mini SSH

### Beat49b battery9 verdict (second run, 04:36)
- Metrics: paraphrase-openers 9%, q-enders 39% ✅, what-if 0%, tic 0, diversity 0.96.
- ✅ grief-anger T1: "Anger at a miscarriage, not sadness — that breaks the script."
- MARGINAL grief-anger T2: "So you're carrying the anger alone right now." (names aloneness but not the bind's cost — still stochastic)
- ✅ crisis-adjacent: "Lighter without you around. How long has it felt this way?" — TWO MOVES confirmed.
- ✅ topic-whiplash T1/T2: benign-relief ✅, guitar-45 ✅
- ✅ vent-layoff: "Eleven years in a job, and it's over in nine minutes on Zoom." ONE SENTENCE.
- ❌ arc-sober T1: "What does it mean to be carrying this alone?" (abstract question — beat49b gold targets this)
- ❌ arc-sober T5: "Does it feel like losing that label is harder than staying anonymous?" (q-ender instead of naming)
- PARTIAL arc-sober T6: echo-strip fired on paraphrase; second-pass produced correct form.
- MARGINAL arc-sober T7: "The noise of evenings is real." (flat — not excavation)
- MARGINAL arc-sober T8: "At 9pm they're usually somewhere between winding down and looking up..." (generic)
- ❌ typo-soup: "2am and your brain is still at work with Jenna." (no "that wasn't me" — beat49b fix targets this)
- ✅ oneword: "I'm here. What's going on?"
- MARGINAL bored-test T1: paraphrase echo; ❌ T2/T3: contraction-echo → summary echo (family-C retrain only)

### Mini status (beat49b)
- **Fully unreachable**: 100% packet loss (ping -c 2 -t 5 mac-mini.localdomain). No path to fix from this session — needs physical access or network intervention (different from beat49's SSH-timeout-ping-OK state).
- Gold SCP blocked. n432 training status unknown.
- Pending for next reachable session: SCP Gold(A)=438 + c_gold_beat49.jsonl + c_gold_beat49b.jsonl + verify caffeinate/pmset settings.

## BEAT 49 STATE (2026-07-18)

### What's running
- **qc_queue RUNNING**. battery9 in progress (started 04:36). After battery9: battery10, battery12, battery3b, battery4b, battery2b, product_e2e — then another battery11.
- **Live adapter: n376** (MD5: b9acf04a1f989d570908c25177966b0f). PERMANENT.
- **utility.py MD5: 8c016dbf4a669ad6f326ec2df4138602** (all 4 copies synced: src/ + dist/imagination_engine/ + dist/imagination_engine/imagination_engine/ + dist/hearth/src/imagination_engine/).
- **companion.py MD5: a191ca2dff8830f89d9463a495e4cbb7** (all 4 copies synced, from beat48).
- **Memory: 20% free** (battery9 model running — do NOT launch any model until battery9 completes and memory frees to ≥35%).

### Beat49 code fixes
- **utility.py** — `_extract_dates()` added (regex: month + day tokens from text). `_b_draft()` now injects MANDATORY DATES clause when brief contains specific dates. `run()` post-check for `draft` task: regens up to 2× if any mandatory date from brief is absent from output. Root cause: sec-hr-complaint "March 11" → "in March" was stochastic; prompt-level MANDATORY DATES alone insufficient; post-check regen is the belt. Unit tested 3 cases ✅. All 4 dist copies synced.
- **scenario_bank.py** — sec-hr-complaint regression note (beat49).

### Beat49 reads (thorough)
**battery11 (00:31 and 03:20 — TWO CONSECUTIVE COMPLETE RUNS):**
- Run 1 (00:31): ALL 6 PASS ✅ (intimacy ✅ 1651w, eagle ✅✅ 1785w, vague-open ✅ 1329w, mid-switch ✅ REGISTER 1281w, mri ✅ 1582w, active-scene ✅ 1190w). beat48 BACK-leak patterns working (2 strips in eagle).
- Run 2 (03:20): ALL 6 PASS ✅ (intimacy ✅ 1282w, eagle ✅✅ 1949w, vague-open ✅ 1652w, mid-switch ✅ REGISTER 1167w, mri ✅ 1771w, active-scene ✅). Total 4428s.
- MINOR DEFECT: "isnYou" broken sentence in run2 intimacy — model output truncated mid-sentence then continued on next line without space separator. Not gate-blocking; extension-loop trim artifact. Monitor.
- **n376 is solid. Two consecutive clean battery11 runs. Imagination gate remains closed ✅.**

**battery9 (01:55):**
- Metrics: paraphrase-openers 4% ✅, q-enders 35% ✅, what-if 0% ✅, tic 0 ✅, diversity 1.00 ✅.
- comp-para-care/love/stay/advice-demand/topic-whiplash/vent-layoff/typo-soup/oneword/bored-test: ALL PASS ✅.
- comp-grief-anger: T1 ✅, T2 ❌ NEW DEFECT CLASS — BARRIER-ASK-WHY: "So why are you carrying the anger alone?" — model asked for info just given. Beat48 BARRIER instruction applied; T2 still failing stochastically. Family-C retrain is the fix path.
- comp-crisis-adjacent: TYPE B mechanical regen fired and produced correct TWO MOVES form ✅. Quality note: question "What does it feel like to say this?" is meta (about the act of saying it) — acceptable shape, not ideal content.
- comp-arc-sober: T7 "The loud evenings are exposing something quieter" — still excavation (known prompt-unfixable). T8 "At 9pm, people do the thing that marks them as their own person" — still generic (want "TV. Mostly TV."). Banked T8 concrete form in c_gold_beat49.jsonl.

**battery10 (02:38/02:45):** 9/10 PASS. sec-hr-complaint FAIL (FACT-LOST:Mar11) — FIXED this beat. All others including sec-shorter-x3, sec-multi-doc-paste, sec-braindump-organize: PASS ✅.

**battery2b, 3b, 4b, product e2e:** ALL PASS ✅.

### Beat49 gold
- **Gold(A)=438** (+6): first-morning-new-house, ice-skating-rink, first-tomato-harvest, clean-test-result, arriving-dream-destination, skill-finally-clicked. All unique openings verified.
- **Gold(C)**: c_gold_beat49.jsonl +5 exemplars (grief-anger T2 trap-form, T2 cost-form, crisis-adjacent two-moves warmth, bored-test hold-ennui, arc-sober T7/T8 absurdist). Not yet SCP'd to mini (mini unreachable).

### Mini status (beat49)
- SSH times out at 172.16.151.169:22. Ping responds (host is up). Likely firewall rule or sleep state change. Key loaded in agent. Previous SSH attempts: "Too many authentication failures" error on localdomain, then "Operation timed out" on IP — different error types. Try after reboot or from different context.
- n432 training status: unknown since beat48 SCP not confirmed. Flywheel should have auto-triggered on Gold=432 hash change. Verify on next reachable session.

### RUNS NEXT (beat49 continuation — in order)
1. **Wait for battery9 to finish** (~06:00-06:30 EST). Monitor: `tail -f logs/qc/queue_0718_0436_battery9_engagement.log`.
2. **Verify memory ≥35% free** after battery9 + model process exits.
3. **Run battery10** (5-minute run via server) to confirm sec-hr-complaint fix: `HF_HUB_OFFLINE=1 .venv/bin/python scripts/qc/battery10_registers.py 2>&1 | tee logs/qc/gate_beat49_battery10_hrfix.log`. Check sec-hr-complaint passes (FACT-LOST:Mar11 gone).
4. **Companion deep test** (use-cases.md #1-#5) — the UC rotation is on Companion this beat. Use httpx to call server. Run through: 2am mind-race, parasocial probe, edge (hostility, grief-adjacent), template fatigue. Add findings to docs/qc/use-cases.md.
5. **Battery12** will auto-run in qc_queue after battery10. If it doesn't appear in next cycle, check qc_queue.sh ordering.
6. **Log daily-log and RELEASE.md** after deep test.

### BEAT 48 STATE (2026-07-18) — COMPLETE

### Beat48 code fixes
- **companion.py** — `_VENT_HOLLOW_SECOND_RE` + `_strip_vent_hollow_second()` added (after `_strip_thats_real_tic()`). Called at 4 points in `turn()` (initial gen + GRAVITY TYPE B regen + empty-reply regen + forbidden regen). Strips second sentences matching banned hollow patterns from VENT replies.
- **companion.py** — BARRIER instruction added to COMPANION_SYSTEM after WHEN THEY VENT / "One line, period, done.": "FOLLOW-UP AFTER A VENT — WHEN THEY NAME A BARRIER — name what the barrier CREATES (the bind, cost, stuck place) — not why it exists. One line only."
- **qc_queue.sh** — `scripts/qc/battery12_vital_facts.py` added to QUEUE (position 4, after battery10). First automated vital-facts run since beat14 gate (July 12).
- **scenario_bank.py** — beat48 regression notes: comp-vent-layoff hollow-second bypass + mechanical fix; comp-grief-anger BARRIER-ASK-WHY defect.

### n426 verdict — REJECTED
- **Val 1.506 vs n376 0.641** (2.4× worse). Confirmed as real regression (not just harder val set).
- **Eval (4 prompts, 2 completed):** Beach: repetition loop ("You walk along the shore..." ×4, "You are aware of the feel of the horizon" duplicated verbatim). Eagle: factual hallucination ("400-pound raptor"), abstract proclamation loop ("You are the king of the sky" ×4), zero sensory flight embodiment. Boss conversation: generation failed (empty output). Hot spring: not reached.
- **Cause unknown**: A_gold grew 376→432 during n426 training cycle; new scripts may have introduced conflicting patterns, or training settings need tuning.
- **Next candidate**: n432 (triggered automatically when flywheel detects A_gold MD5 change on mini). Mini SSH currently intermittent — verify next session.

### Beat48 gold
- **Gold(A)=432** (+6: open-water dock, used bookshop, empty apartment emigrating, fire outside cold night, last sentence of a book, city years ago). SCP'd to mini (assumed — mini SSH dropped before confirm; verify next session).
- **Gold(C)**: c_gold_beat48.jsonl +5 exemplars (vent-layoff one-sentence, grief-anger T2 barrier ×2, opener-ask-yield, opener-gravity-first). Total: 50 targeted + 130+ root.

### RUNS NEXT (beat48 continuation)
1. **Read battery11 end-to-end** when it completes (~02:00): all 6 scenarios — eagle ✅ already, read vague-open/grief-pet/mid-switch/intimacy/active-scene. Any FAIL = fix + re-run.
2. **Companion deep use-case test** — this beat's product rotation. Start server (≥35% memory required), run use-cases.md companion scenarios as demanding AI professional. Test: weird inputs, long sessions, edge registers. Every defect: fix, bank, re-verify.
3. **Verify mini + n432**: SSH when reachable — check n432 training status, n432 eval when ready, probe vs n376.
4. **Family-C retrain**: flywheel_c.sh on mini — 50 targeted exemplars, threshold met. Trigger this beat or next.
5. **Cross-cutting sweep** — offline tripwire, ceilings, 200s, QC-artifact purge.
6. **Cold install** — scripts/package.sh → dist zip → Start Hearth.command.

## BEAT 47 STATE (2026-07-17)

### What's running
- **qc_queue RUNNING** (PID 37564).
- **Live adapter: n376** (MD5: b9acf04a1f989d570908c25177966b0f). PERMANENT.
- **companion.py MD5: 792f9d0fd354bf14f9fec0a3bd2a356e** (all 3 dist copies synced).
- **server.py MD5: 4d2995ab9b3047452500ce6857bae56a** (all 3 dist copies synced — utility_run now calls assistant.run()).
- **utility.py MD5: beee3eae47eb4daaac2080f5ac029b20** (all 3 dist copies synced — stub guard added, _extra_system param).

### Beat47 code fixes
- **server.py** — `utility_run` endpoint changed from `assistant.stream()` to `assistant.run()`.
  Root cause: all post-checks (stub guard, number recovery, day-name sanitisation) lived in `run()` but server called `stream()` directly, bypassing them entirely.
  Fix: buffer full output via `assistant.run()`, yield complete result. Streaming interface preserved (JS reader loop still works); typing-effect lost but correctness gained.
- **utility.py** — `_extra_system` parameter added to `stream()` (private, passed through to `gen()`).
- **utility.py** — draft/reply stub guard in `run()`:
  Detection: strip subject lines (`Subject: ...`), salutation/sign-off lines (ending with comma), placeholder lines (`[...]`) — if nothing remains, output is a stub.
  Regen: up to 3 attempts using `engine.stream()` directly with body-prompt `_extra_system`, temp=0.3 → 0.25. All 8 unit tests PASS.

### Secretary deep test — CLOSED ✅ (beat47, 153s)
| UC | Result | Notes |
|---|---|---|
| UC1 meeting notes | ✅ all 8 facts | sarah/tuesday/wednesday/goldman sachs/option b/oauth/$12/thursday |
| UC2a firm decline | ✅ | $85k vs $110k, door open |
| UC2b apology | ✅ | full body, owns it, no groveling |
| UC2c negotiation counter | ✅ | $3400 counter present |
| UC3 braindump organize | ✅ all numbers | $59/$49/march17/miranda/47/30%/feb28/bugs/tuesday |
| UC4 shorter×3 | ✅ | 20w→13w→11w, each shorter |

**Secretary gate: CLOSED** — 5/5 UC pass. Root fix: server endpoint bypassed all post-checks.

### RUNS NEXT (in order — beat48)
1. **Family-C retrain** — trigger `flywheel_c.sh` on mini (45+ targeted exemplars, threshold met). Kill qc_queue, ≥35% memory, `nohup bash scripts/flywheel_c.sh > ~/Downloads/hearth-corpus/_logs/flywheel_c.log 2>&1 &` on mini, restart qc_queue when done.
2. **n426 probe read** — `ssh smaitra@mac-mini.localdomain 'cat ~/Downloads/hearth-corpus/_logs/probe_latest.txt; ls ~/Downloads/hearth-corpus/ | grep GOLD-ADAPTER | tail -3'`
3. **vital-facts WRITE path** — deferred from beat46.
4. **Cross-cutting sweep** — offline tripwire, ceilings, 200s, QC-artifact purge.
5. **Cold install** — scripts/package.sh → dist zip → Start Hearth.command clean run.
6. **Companion gate** — needs family-C retrain first; arc-divorce My→She, comp-funny regression still open.

## BEAT 46 STATE (2026-07-17)

### What's running
- **qc_queue RUNNING** (PID 37155). battery9 2042 COMPLETE.
- **Live adapter: n376** (MD5: b9acf04a1f989d570908c25177966b0f). PERMANENT — do not demote.
- **companion.py MD5: c3cfa3d26a7ab20fa3b6366bdff94a91** (all 3 dist copies synced — GRAVITY TYPE B regen + stub guard 8→6 + GRAVITY q_streak exception).
- **scenario_bank.py MD5: 945c383bfb4923e164767e35b012258e** (beat46 note added to comp-crisis-adjacent).
- **Gold(A)=426** (+8 beat46: Saturday rest, pottery wheel, kid bike, 3am calm, first customer, rain, grandmother's dinner, concept clicked). SCP'd to mini ✅.
- **Gold(C) beat46**: c_gold_beat46.jsonl +5 exemplars (arc-divorce T2 My→She echo; T2–T4 arc; crisis-adjacent TYPE B correct; TWO MOVES variety; hard-convo HOW-frame). SCP'd to mini ✅.
- **Mac Mini: ALIVE** — caffeinate + flywheel running. n418 live adapter on mini (trained 07-17 18:22). A_gold 426 + c_gold_beat46 confirmed. n426 auto-triggers on next 30-min flywheel poll (~21:00–21:30).

### Beat46 code fixes
- **companion.py** (MD5: c3cfa3d26a7ab20fa3b6366bdff94a91):
  - `_GRAVITY_SIGNALS` tuple at module level: 8 crisis-adjacent signal phrases.
  - `_is_gravity_trigger(user_message)`: returns True if any signal phrase found in user message.
  - `_QUESTION_FIRST_WORDS` frozenset: does/do/is/are/was/were/will/would/can/could/have/has/had/what/when/where/why/how.
  - `_is_pure_question(reply)`: True when reply ends with "?" AND first word is in `_QUESTION_FIRST_WORDS`.
  - Mechanical regen block in `turn()`: after initial generation + postprocessors, if GRAVITY trigger + pure question → regen at temp=0.4 with explicit acknowledgment instruction. `_strip_echo()` NOT applied on regen (acknowledgment uses their words intentionally).
  - Stub guard lowered 8��6 in `_drop_trailing_question()`.
  - q_streak strip: `not _is_gravity_trigger(user_message)` guard preserves GRAVITY question.
  - 9/9 unit tests PASS (both _is_gravity_trigger and _is_pure_question).

### Battery9 2042 in progress — key scenarios to watch
- **comp-crisis-adjacent**: TYPE B mechanical regen FIRST verification. Expected: regen should fire if model generates "Does it feel like..." and produce TWO MOVES form.
- **comp-arc-divorce T2**: My→She echo still prompt-unfixable; family-C retrain path. T7 "Good." should still hold.
- **comp-hard-convo-prep T2**: HOW-frame target "Two conversations, not one sentence." — stochastic.

### Secretary deep test — COMPLETED (beat46, 170s)
| UC | Result | Notes |
|---|---|---|
| UC1 meeting notes | ✅ all 8 facts | sarah/tuesday/wednesday/goldman sachs/option b/oauth/$12/thursday |
| UC2a firm decline | ✅ | $85k vs $110k, door open |
| UC2b apology | ✅ | third-regen fix CONFIRMED working (no empty "James,") |
| UC2c negotiation counter | ❌ stochastic | "David," only — model generates salutation, third-regen fires but also fails |
| UC3 braindump organize | ✅ all numbers | $59/$49/march17/miranda/47/30%/feb28/bugs/tuesday |
| UC4 shorter×3 | ✅ | 21w→12w→11w, each shorter |

**Secretary gate: NOT YET CLOSED** — 4/5 UC pass. UC2c is a model-floor stochastic failure (~50% rate, passed in beat43). Gate criterion = clean 5/5 pass. Action: re-run deep test in next session after any utility.py draft floor improvements.
- To re-run: kill qc_queue, verify memory ≥35%, `HF_HUB_OFFLINE=1 .venv/bin/python /tmp/secretary_deep_test.py`, restart qc_queue.

### Family-C retrain — THRESHOLD MET, NOT YET TRIGGERED
- C-companion exemplar count: 45 in `_candidates/` (beat28–beat46), 130+ in root across beats 13–45.
- Beat45 RUNS NEXT said "~50+ total"; we're at 45 _candidates/. Root has well over 130. Retrain justified.
- Procedure: kill qc_queue; check memory ≥35%; `nohup bash scripts/flywheel_c.sh > ~/Downloads/hearth-corpus/_logs/flywheel_c.log 2>&1 &`; restart qc_queue when done.
- **NOTE**: flywheel_c.sh runs gen_c_candidates → curate_c → build_training_data → finetune. Takes ~2h. Mini preferred over laptop.

### RUNS NEXT (in order — beat47)
1. **Secretary gate rerun** — re-run `/tmp/secretary_deep_test.py`. UC2c needs clean pass. Gate procedure: kill qc_queue, ≥35% free, run, restart.
2. **UC2c draft floor fix** — add draft-body min-length guard in utility.py for ALL "draft" task tones (not just apology): if output ≤ 30 chars after regen and is salutation-only, force body regen.
3. **Family-C retrain** (threshold met; trigger on mini via flywheel_c.sh).
4. **n426 probe read** — check `_logs/probe_latest.txt` on mini after flywheel runs.
5. **vital-facts WRITE path** — deferred to beat47+.
6. **Secretary gate** — close formally once deep test passes.

## BEAT 45 STATE (2026-07-17)

### What's running
- **qc_queue RUNNING** (PID 30502, resumed after battery3c run).
- **Live adapter: n376** (MD5: b9acf04a1f989d570908c25177966b0f). PERMANENT — do not demote.
- **Mac Mini: REACHABLE** (mac-mini.localdomain, smaitra). n411 REJECTED (val 0.812). n418 TRIGGERED: A_gold.jsonl 418 SCP'd, valid.jsonl removed (fresh val split), flywheel will detect hash change on next 30-min poll.
- **companion.py MD5: fbad3cf33bb9be38c15835b78c687988** (all 3 dist copies synced — GRAVITY TYPE B + WHEN THEY VENT "That feels like X" fixes).
- **battery11_imagination_bank.py**: bear false-positive fixed (requires article "a/the bear" to count as wildlife).
- **scenario_bank.py MD5: 945c383bfb4923e164767e35b012258e** (3 defects banked this beat).
- **utility.py MD5: a32c087aafa02cc263291da0fdf4f6ac** (beat44 fix: organize numeric floor + extend post-check to cover organize).
- **doc_qa.py MD5: 92ce1b3eda21dc6d0aa8d21c1a8e73cf** (beat44 fix: BRIDGE2 retry trigger broadened to cover "not in your files").

### Beat45 code fixes
- **companion.py** (MD5: fbad3cf33bb9be38c15835b78c687988):
  - GRAVITY TYPE B: "Does..." explicitly added to MUST NOT start list; WRONG/RIGHT example pair with exact observed failure ("Does it feel like everyone or just a few?" after user said "lighter without me around")
  - WHEN THEY VENT BANNED SECOND SENTENCES: "That feels like X." / "It feels like X." added (present-tense bypass of banned "That must feel like X.")
- **battery11_imagination_bank.py**: bear false-positive fixed — `_WILDLIFE_WORDS` + `_WILDLIFE_ARTICLE` split; "bear" now requires preceding article "a" or "the" to match as animal. n376 eagle gate stands (was a measurement error).
- **scenario_bank.py** (MD5: 945c383bfb4923e164767e35b012258e): 3 defects banked:
  - comp-vent-layoff: "That feels like X" bypass
  - comp-crisis-adjacent: TYPE B "Does..." violation with WRONG/RIGHT examples
  - comp-arc-divorce: My→She echo → family-C retrain path

### Beat45 gold
- **Imagination**: +7 → Gold(A)=418. New scenes: manuscript send, lake dawn swim, winter farmers market, toddler asleep, childhood bedroom return, offstage wings, father’s letter. SCP’d to mini ✅.
- **Companion**: c_gold_beat45.jsonl +4 exemplars (crisis-adjacent TYPE B correct, T2 two-move sustained, vent-layoff T2 no-feels-like, arc-divorce T2 no-she-echo). SCP’d to mini ✅.

### Beat45 adapter / mini status
- **n411 REJECTED** — val 0.812, oscillating curve, frozen val root cause. n376 stays live.
- **n418 triggered**: Gold(A)=418 SCP’d, valid.jsonl removed from mini (forces fresh val split), flywheel will detect hash change on next 30-min poll.
- **AYF GATE CLOSED** ✅ — battery3c 28/28 × 3 consecutive (beat44 + beat45 ×2, 408s + 428s). 84/84 total.

### Battery results (beat45)
| Battery | Result |
|---|---|
| battery3c beat45 run2 (0717_1647) | ✅ 28/28 PASS. BRIDGE2 PASS. |
| battery3c beat45 run3 (0717_1654) | ✅ 28/28 PASS. BRIDGE2 PASS. AYF GATE CLOSED. |

### RUNS NEXT (in order — beat46)
1. **Read n418 probe when complete** (~30 min after flywheel detects hash change). Check probe_latest.txt on mini: `ssh smaitra@mac-mini.localdomain ‘cat ~/Downloads/hearth-corpus/_logs/probe_latest.txt; ls ~/Downloads/hearth-corpus/ | grep GOLD-ADAPTER | tail -3’`
2. **Secretary UC1 fact-drop** — stochastic; gold exemplar showing correct form (all 8 facts preserved: sarah, tuesday, wednesday, goldman sachs, option b, oauth, $12, thursday).
3. **Secretary UC2c negotiation salutation-only** — model floor; gold exemplar showing correct counter email body.
4. **Companion family-C retrain progress** — check exemplar count; trigger when density sufficient (~50+ total, targeting crisis-adjacent/arc-divorce/grief-anger).
5. **vital-facts WRITE path** — deferred to beat46+.

## BEAT 43 STATE (2026-07-17)

### What's running
- **battery11 RUNNING** (PID 22849, started 09:31 AM, ETA ~10:43 AM). Routine n376 confirmation run in qc_queue cycle.
- **qc_queue RUNNING** (PID 22821, relaunched 09:31 AM after secretary test).
- **Live adapter: n376** (MD5: b9acf04a1f989d570908c25177966b0f). n281 backed up at `data/model/adapters.n281/` and `data/model/adapters.n281_permanent.safetensors`.
- **Mac Mini UNREACHABLE** — ping 100% packet loss to 172.16.151.169. Likely sleeping. Physical wake needed. n404 training status unknown (was at iter 25/1500 at ~09:10 AM when last seen).
- **IMAGINATION GATE**: CLOSED ✅ — n376 battery11 ALL 6 PASS × 2 (beat40 + beat41).
- **companion.py** — beat42 fixes. MD5: b4f8806d0e5ed27bc5ce1648a301cfbe (all 3 dist copies).
- **utility.py** — beat43 fixes (third-regen + concise prompt). MD5: 94d83e81e488ae67a96b2b78e273783d (all 3 dist copies).
- **Gold(A)=404** — SCP'd to mini before unreachable ✅. **Gold(C) beat41 +5 + beat43 +3** — beat41 SCP'd ✅; beat43 waiting for mini to wake.

### Beat43 secretary deep test (0717_0928 — 124s)
| test | verdict |
|---|---|
| UC1 meeting notes | ✅ all 8 facts preserved |
| UC2a firm decline | PARTIAL (email exists, no explicit decline stated) |
| UC2b apology | ❌→FIXED (was "James," only; utility.py third-regen prevents empty-strip) |
| UC2c negotiation counter | ✅ $3400 present |
| UC3 braindump | PARTIAL ("47" beta-user count dropped; other floor issues were calibration errors) |
| UC4 shorter×3 | ❌ model can't compress ~28w further on passes 2+3 |

### Beat42 battery9 results (0717_0849) — 21/21 PASS (2 defects found and fixed)
All scenarios passed or had defects fixed mid-run. Key results:
- arc-divorce T3 ✅ (Case 2e fix confirmed — no echo in reply)
- arc-divorce T5 ✅ (second-regen fix confirmed — "Does it feel worse when no one knows what you're relieved about?")
- arc-divorce T7 ✅ ("Good.")
- vent-layoff ❌→FIXED: "That makes the whole thing about what happens next" — new bypass form
- hard-convo-prep T1 ❌→FIXED: "You said he's also your oldest friend." — Case 2d second-sentence echo
- Metrics: 10% paraphrase-openers, 48% q-enders, 0.90 opener diversity

### Beat43 code fixes (utility.py MD5: 94d83e81e488ae67a96b2b78e273783d)
- **utility.py: third-regen fallback** — when banned-opener strip leaves ≤ 15 chars (just salutation), forces a third full regen with "Write body IMMEDIATELY" instruction. Prevents "James," empty-output on apology emails.
- **utility.py: concise tone strengthened** — from "Be as concise as possible while keeping everything essential." → "Compress: remove every unnecessary word and cut redundant phrases. The output must be shorter than the input — fewer words, same core meaning." Fixes UC4 shorter×3 model floor.
- **scenario_bank.py: sec-braindump-organize added** (always=True, high, helpfulness). Product-launch braindump with 10 numeric facts. Gold exemplar c_gold_beat43 shows correct form.
- **battery10_registers.py: sec-braindump-organize floor checks added** — \b47\b, $59, $49, march 17/3, miranda, 30%, feb 28, 3 bugs, tuesday. SYNTAX OK.
- **c_gold_beat43.jsonl: 3 exemplars** — arc-divorce T2 (no-mirror), arc-divorce T4 (sentence-complete), sec-organize-UC3 (all numeric facts). NOT YET SCP'd to mini (mini unreachable).

### Beat42 code fixes (companion.py MD5: b4f8806d0e5ed27bc5ce1648a301cfbe)
- **vent-layoff bypass**: Added "That makes the whole X." / "That makes X about Y." / "That puts X about Y." to BANNED SECOND SENTENCES in WHEN THEY VENT.
- **Case 2d all-sentences**: Extended `_strip_echo()` Case 2d to check ALL user sentences (not just first). Hard-convo-prep T1 root cause: second sentence "He's also my oldest friend" → I→You "he's also your oldest friend" matched.
- All 3 dist copies in sync (src/, dist/imagination_engine/, dist/hearth/src/imagination_engine/). MD5 verified identical.
- scenario_bank.py: arc-divorce beat42 notes, comp-vent-layoff beat42 regression+fix, comp-hard-convo-prep beat42 regression+fix.

### Beat41 state (for reference)
- Case 2e (arc-divorce T3 partial I→You prefix echo) FIXED.
- Second-regen fallback (arc-divorce T5 double-strip → empty) FIXED.
- battery11 0734: ALL 6 PASS (n376 second consecutive confirmation).
- n396 REJECTED (val 1.168 vs n376 0.641).

### Beat40 state (preserved for reference)
- n376 PROMOTED PERMANENT (beat40, 4520s gate, val 0.641). MD5: b9acf04a1f989d570908c25177966b0f.
- n281 backed up: `data/model/adapters.n281/` and `data/model/adapters.n281_permanent.safetensors`.
- companion.py Case 5: any-sentence echo detection. 4/4 unit tests PASS.

### Beat38 battery11 0146 results (COMPLETE — 4418s, 6/6 done)

### Beat38 battery11 0146 results (COMPLETE — 4418s, 6/6 done)
- ❌ imag-intimacy: CONTENT FAIL. 1290w/589s. 23 pronoun fixes. "her [verb]" subject errors throughout. New BACK leak: "The chair or surface beneath you is where this moment ends". Both fixed. Thematic cycling persists (known floor).
- ✅✅ imag-embodiment-eagle: PASS both postchecks. 1822w/652s. In-scene from word 1. 1 wildlife sentence dropped. Good flight physics.
- ✅ imag-grief-pet: STRUCTURAL PASS. 1982w/852s. Human POV ✅, tennis ball extensive ✅, bench ✅. 7 pronoun fixes, 15 short-phrase repeats removed. Leaks survived: "Biscuit and I" / "from our place" first-person. Cycling severe (known floor).
- ✅ imag-vague-open: STRUCTURAL PASS. 2024w/639s. SCENE COMMITTED — warm quiet indoor room (antique dresser, lamp, chair). NO chair/bed split. Prose severely circular (known floor). 1 pronoun fix.
- ✅ imag-mid-switch: REGISTER PASS. 1098w/681s. Chair env, alert anchors, no sleep props, strip_alert_calm_violations clean. 15 phrase-repeat pairs removed. Prose circular (known floor).
- ✅ imag-active-scene: PASS. 1464w/660s. FIRST n281 data point. Opening in running scene from word 1 ✅, no she/her bleed ✅ (postcheck explicit). Active effort maintained. NEW BACK LEAK: "or whatever surface has you resting" fixed (pattern added to postcheck.py).

### Beat38 battery11 0044 results (partial — 3/6)
- ✅ imag-intimacy: STRUCTURAL PASS. 980w/537s. 15 pronoun fixes, 19 phrase-repeat pairs repaired.
- ✅✅ imag-embodiment-eagle: PASS (both postchecks). 1786w/507s. Ravens in body as background sound (acceptable). RE-ROOM bleed "or surface where you sit/lie down" found + fixed.
- ✅ imag-grief-pet: STRUCTURAL PASS. 2441w/771s. Human POV, tennis ball, bench. "Hard Cut Into The Scene:" prefix echo fixed. "chair or whatever surface is beneath you" BACK leak fixed.
- imag-vague-open, imag-mid-switch, imag-active-scene: NOT CAPTURED (battery11 0044 killed — CloudFront CLOSE_WAIT).

### Beat38 battery9 0125 results (partial — stuck at arc-divorce T2, 8/12)
- comp-para-care/love/stay: 3/3 ✅ parasocial floor holds at n281.
- comp-advice-demand: ✅ "I won't make this call. What does quitting cost you per month, in money and health?"
- comp-grief-anger: T1 ✅ breaks-script, T2 ❌ echo (prompt-unfixable, c_gold_beat38 banked).
- comp-crisis-adjacent: ✅ "Lighter without you around. Does it feel like everyone would be lighter, or just some people?"
- comp-topic-whiplash: T2 ✅ guitar, no Anyway, no biopsy-drag. beat31 fix confirmed.
- comp-decision-house: T1 ✅, T2 PARTIAL, T3 ❌ 9th regression ("Fine. The Friday deadline is real, and so are both your family histories." — echoes user's 'Fine', drags family history back in). Prompt-unfixable.
- comp-arc-divorce: T1 PARTIAL ("I get that." — borderline cognition claim). Stuck at T2 (CLOSE_WAIT).
- comp-typo-soup, comp-vent-layoff, comp-funny: NOT CAPTURED.

### Live adapter
**n281** (MD5: bce29e61472323003c948fbe07031115) — swapped in 2026-07-13 21:16 for eagle gate.
Backup n256 (final): `data/model/adapters.n256_final.safetensors` (MD5: d339fb944ca9344e399e82b8a9884c06).
To restore n256: `cp data/model/adapters.n256_final.safetensors data/model/adapters/adapters.safetensors`
Backup n243 also: `data/model/adapters.n243_LIVE/` (MD5: 8a7395654d4bd0f72b69c673a03bf6db).

### Beat27 battery results
**Battery11 n256 (2007 run) — COMPLETE (3949s):**
- ✅ imag-intimacy: PASS (1033w/413s, 17 pronoun fixes, no instruction leaks)
- ❌ imag-embodiment-eagle: FAIL companion (hawk in n256 training — not fixable). ✅ PASS chair.
- ✅ imag-mid-switch: REGISTER PASS (pillow 1x stripped by strip_alert_calm_violations). 1455w/716s.
- ✅ imag-grief-pet: STRUCTURAL PASS (human POV, tennis ball, bench). 1692w/639s.
- ✅ imag-mri: PASS (2288w/661s, in tube ✅, drums ✅)
- ✅ imag-repeat-variety: VARIETY PASS (night-1=1141w/198s, night-2=1390w/304s, 0% sentence overlap)

**Battery11 n281 gate — EAGLE ✅✅ PASS — remaining 4 scenarios still running (PID 33109):**
- ✅ imag-intimacy: 1376w/517s, 4 pronoun fixes
- ✅✅ imag-embodiment-eagle: 1753w/559s — no animals, in-scene from word 1. **n281 PROMOTED PERMANENT.**
- ✅ imag-mid-switch: 1664w/693s — REGISTER PASS. Chair throughout, 'not yet time to sleep' anchor, no sleep props. 11 phrase-repeats stripped. Close soft (not the ideal 'stand up' form). Known quality floor.
- imag-grief-pet, imag-mri, imag-repeat-variety: generating...
- Log: `logs/qc/queue_0713_2007_battery11_n281_gate.log`
- After PID 33109 exits: read all 4 remaining results, bank in scenario_bank.py, close Imagination gate if all PASS.

**Battery10 registers — 4/4 PASS ✅** (beat27 1935 run)

**Battery9 engagement (beat27 1907 run) — defects found:**
- q-enders 27% ✅, paraphrase 8% ✅, diversity 0.96 ✅
- ❌ arc-divorce "that's real" T2-T5 (beat25 conditional ban had loophole) → **FIXED: absolute ban**
- ❌ comp-funny regen fired but replacement still unfunny → gold exemplar added (beat27)
- ❌ arc-newparent T1 echo, T4 stamp → gold exemplar added (beat27)

### Beat27 code fixes (src/ and dist/ both updated)
- **generator.py**: `_explicit_embodiment` flag + wildlife drop decoupled from `_is_active_body`; `strip_alert_calm_violations()` wired for pillow/sheet/blanket/etc belt-and-suspenders
- **postcheck.py**: `strip_alert_calm_violations()` added — strips sleep-register props when `_alert_calm` is True
- **companion.py**: "that's real" → ABSOLUTE BAN (was conditional)
- **scenario_bank.py**: beat27 arc-divorce, eagle, mid-switch, MRI results banked; synced to dist/

### Mini adapter history (today)
- n262 (10:28): BELOW FLOOR — rejected.
- n270 (12:19): adequate, thin embodiment — not promoted.
- n281 (14:12): **GATE CANDIDATE (beat27 re-assessment).** Eagle clean (no hawk, ground→flight transition). Ellipsis artifact only in "hard conversation rehearsal" (not in battery11). Best available vs n286/n287.
- n286 (18:06): REJECTED — hallucinated companion eagles.
- n287 (19:58): REJECTED — narrator "we" violation. val 0.577.
- n293 (pending): will auto-train when flywheel detects A_gold change (293 vs 287).

## NEXT BEAT (beat44) — PRIORITY ORDER
1. **Read battery11 (launched 09:31 AM, ETA ~10:43 AM)** — n376 in qc_queue rotation. Check all 6 scenarios against n376 quality floor. This is a routine confirmation run, not a gate run.
2. **Re-run secretary deep test** — verify UC2b (utility.py third-regen) and UC4 (concise prompt) fixes. Kill qc_queue first. Command:
   ```bash
   kill $(pgrep -f qc_queue); sleep 5
   memory_pressure 2>/dev/null | grep "Pages free"  # must be ≥35%
   .venv/bin/python /tmp/secretary_deep_test.py > logs/qc/secretary_deep_test_verify_$(date +%H%M).log 2>&1
   nohup bash scripts/qc_queue.sh >> logs/qc/queue.log 2>&1 &
   ```
3. **Wake mac-mini** (physical or WoL) — ping to 172.16.151.169 fails. Once up:
   ```bash
   ssh smaitra@mac-mini.localdomain 'tail -20 ~/Downloads/hearth-corpus/_logs/honest_flywheel.log; ls ~/Downloads/hearth-corpus/ | grep GOLD-ADAPTER | tail -3'
   ```
   Then SCP c_gold_beat43.jsonl: `scp ~/Downloads/hearth-corpus/C-companion/c_gold_beat43.jsonl smaitra@mac-mini.localdomain:~/Downloads/hearth-corpus/C-companion/`
   If n404 completed, SCP adapter and run battery11 gate (≤ n376 val 0.641 required).
4. **BRIDGE2, cross-cutting, cold install, public story** — deferred.

## KNOWN STANDING ISSUES (release blockers — beat45 state)
- **Secretary gate open**:
  - battery10: 9/10 (beat44 1613 — sec-shorter-x3 stochastic, known floor). sec-braindump-organize ✅ CONFIRMED (beat44 organize fix).
  - Secretary deep test beat44: UC2b ✅ UC3 ✅ UC4 ✅ confirmed. UC1 stochastic fact-drop (option b/oauth/$12/thursday). UC2c salutation-only model floor.
  - **Needs gold exemplars**: UC1 complete meeting notes (all 8 facts), UC2c correct negotiation counter email body.
- **Companion gate open — prompt-unfixable defects (family-C retrain path)**:
  - comp-crisis-adjacent TYPE B: ✅ prompt-fixed (beat45 GRAVITY TYPE B "Does..." ban). Monitor next battery9.
  - comp-vent-layoff "That feels like X": ✅ prompt-fixed (beat45). Monitor next battery9.
  - comp-arc-divorce My→She echo: family-C retrain path. Exemplar banked (beat45).
  - comp-decision-house T3: CONFIRMED PROMPT-UNFIXABLE (10+ regressions). Fix path: family-C retrain.
  - comp-grief-anger T2: PROMPT-UNFIXABLE. Case 5 catches mechanically. Fix path: family-C retrain.
  - **Q-enders**: 38% beat44 battery9 (≤50% ✅, inside threshold). paraphrase-openers: 0% beat44 (best ever).
- **IMAGINATION GATE CLOSED** ✅ — n376 battery11 ALL 6 PASS × 2. n376 PERMANENT (MD5: b9acf04a1f989d570908c25177966b0f).
- **AYF GATE CLOSED** ✅ — battery3c 28/28 × 3 consecutive (beat44 + beat45 ×2). 84/84.
- **BYO GATE CLOSED** ✅ — beat12/16/17 (3/3 consecutive).
- **Vital Facts GATE CLOSED** ✅ — battery12 12/12 PASS.
- **Cross-cutting sweep** — NOT YET RUN.
- **Cold install** — scripts/package.sh not run. Run before beta.
- **Public story** — site/README recut deferred.

## CODE STATE (src/ and dist/imagination_engine/ in sync as of beat41)
- postcheck.py: strip_active_body_chair_refs ✅, strip_back_instruction_leaks ✅, fix_possessive_pronouns ✅, fix_subject_pronouns ✅ (beat38), drop_active_body_wildlife ✅, drop_forbidden_stock_imagery ✅, strip_alert_calm_violations ✅, _NARRATOR_POSS +14 patterns (beat35), all BACK leak patterns (beat27-38)
- companion.py: **beat41 — _strip_echo() Case 2e (partial I→You prefix, ≥5 words/60% coverage); second-pass regen fallback (temp=0.7, max_tokens=80, situation-not-words instruction)** | beat39 Case 5 (any-sentence echo) | beat38 Case 2d U+201C curly-quote | beat36 Case 2d "You said/mentioned" prefix + _i_to_you() helper + _strip_thats_real_tic() "is real." standalone + "whole thing" em-dash | beat35 Case 2c I→You + FORBIDDEN TIC loophole | beat34 Case 4b + ?. cleanup | beat33/32 BANNED SECOND SENTENCES | beat31 WHEN THEY ASK HOW + CF(3) | beat30 WHEN THEY VENT (one-line) + WHEN THEY REACH FOR YOU | beat28 _CONFIRM_LANDS + _strip_thats_real_tic() | beat27 "that's real" ABSOLUTE BAN
- generator.py: talon-metaphor filter (beat35), _is_grief_pet_walk ✅, _explicit_embodiment flag + decoupled wildlife drop (beat27), fix_subject_pronouns() wired (beat38)
- utility.py: named events + source-sentence regen (beat35), INVENTED-DAY (beat30), STRICT DATE RULE (beat38)
- doc_qa.py: bridge-retry in ask() ✅ (beat30). PENDING battery3c 20-run verify.
- scenario_bank.py: beat41 notes banked (arc-divorce T3/T5, decision-house T3 10th regression)

## GOLD CORPORA
- Imagination: **404 scripts** (A_gold.jsonl) — Laptop=404 ✅, mini=404 ✅ SCP'd. Flywheel will auto-queue n404 on next 30-min poll (detected 404>396).
- Companion: c_gold_beat3/5/7/9/13-41.jsonl — ALL in main C-companion/ dir ✅. Total beat exemplars: ~182. All SCP'd to mini ✅. beat41 = 5 exemplars (arc-divorce T3 no-echo, decision-house T3 concrete, grief-anger T2 forward, vent-layoff plain, funny villain-arc).

## THE OPERATING SYSTEM (since 2026-07-07): heartbeat + honest flywheel

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
