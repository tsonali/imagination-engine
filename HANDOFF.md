# HANDOFF — resume here (read this first)

_Last updated 2026-07-08 beat7 (alert-calm root-cause fixed; gold 130; n130 training on mini; n115/n123 comparative read in progress)._
_Single source of truth for a fresh session. Everything below is real and running._

## FIRST THING TO DO when you resume — run these checks
```bash
# Mini
ssh -o IdentitiesOnly=yes smaitra@mac-mini.localdomain '
  echo "flywheel: $(pgrep -f honest_flywheel >/dev/null && echo RUNNING || echo DOWN)"
  tail -5 ~/Downloads/hearth-corpus/_logs/honest_flywheel.log
  ls ~/Downloads/hearth-corpus/GOLD-ADAPTER-*-n130 2>/dev/null && echo "n130 EXISTS" || echo "n130 not yet"
  ls -lt ~/Downloads/hearth-corpus/_train/adapters/ | head -3'

# Laptop — check if n115/n123 comparative read completed
ls /tmp/n115_compare.log /tmp/n123_compare.log 2>/dev/null && echo "reads DONE" || echo "reads PENDING"
pgrep -f qc_queue >/dev/null && echo "qc_queue RUNNING" || echo "qc_queue DOWN"
```

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

### Live adapter: n115 (promoted 2026-07-08 beat5, confirmed beat6/7)
- `data/model/adapters/` = GOLD-ADAPTER-0708-0016-n115 (123-gold, 1500 iters)
- n123 adapter rsync'd to `data/model/adapters.n123/` (123-gold, different random seed effectively)
- **Battery11 beat5 verify COMPLETE** (log: `logs/qc/20260708_0102_battery11_beat5_verify.log`)
  - imag-deposition: "As soon as I speak next" first-person slip found → FIXED (beat7 verify PASS)
  - imag-mid-switch: Full sleep register throughout → ROOT CAUSE FOUND + FIXED (beat7 verify PASS)
- **Battery11 beat6 targeted verify COMPLETE** (log: `logs/qc/20260708_0441_beat6_alertcalm_verify.log`)
  - imag-deposition: ✅ PASS — no "I speak/hold/guide"
  - imag-mid-switch: ✅ REGISTER PASS — "Calm and awake now", "stay sharp", no sleep vocabulary

### Generator fixes (beat7, 2026-07-08) — cumulative with beat5/6 fixes
1. **Alert-calm root cause fixed** (3 changes to generator.py):
   - `_alert_calm` detection moved BEFORE protocol branch (was only inside `if protocol == "settling":`)
   - Explicit `⚠️ ALERT-CALM OVERRIDE` block injected into body_user when flag is set
   - BODY_PROMPT alert-calm section strengthened: SCENE TYPE + GENRE + explicit/semantic ban list
2. **First-person "I speak" ban extended** — added "as soon as I speak", "when I say", "I will
   take you", "I am here" to explicit banned phrases in BODY_PROMPT.

### Gold corpus: 130 scripts
- 27 original + 103 Claude-drafted
- **Beat7 new (124-130):** rooftop-city-night, woodshop-planing, pre-dawn-kitchen, lap-pool,
  mountain-descent, airport-dawn, dancing-alone. SCP'd to mini.
- Sonali's taste audit of batches 1-8 PENDING (_candidates/INDEX.md).

### Mini flywheel: n130 training RUNNING
- Flywheel detected 130-gold at 05:08, started n130 training.
- HUNG after iter-200 checkpoint (OOM at iter-300 eval pass).
- RESTARTED: fresh n130 run started at 05:20. Past iter 75 (10.8GB peak, healthy).
- ETA: ~90 min from start → adapter saved as GOLD-ADAPTER-*-n130 if it completes without OOM.
- **CRITICAL WATCH:** if it hangs again at iter-300, reduce `--val-batches` from 8 to 4 in
  `scripts/finetune.sh` and restart manually. The iter-300 eval pass is the OOM trigger.
- After adapter exists: `rsync` to laptop, run probe, then comparative READ vs n115.

### Comparative read: IN PROGRESS
- n115 (live): 5-prompt comparison running (background), log: `/tmp/n115_compare.log`
- n123: will run immediately after n115 completes
- Verdict pending. Promotion gate: must win ≥3/5 prompts clearly.

### Companion question-enders: 14% (confirmed beat7)
- Battery9 authoritative: 14% (not 83% — that was a stale run). Well under <50% bar.
- Content regressions need fine-tuning data (comp-decision-house, comp-funny, comp-arc-sober
  T5/T8, comp-arc-newparent T6, comp-bored-test). All banked in scenario_bank.py.

## NEXT HEARTBEAT PRIORITY (in order)
1. **Read n115 + n123 comparative logs** and make promotion verdict. Both logs at `/tmp/n{x}_compare.log`.
   If n123 wins ≥3/5: copy adapters.n123 → adapters, back up n115, run battery11 on n123.
   Run command for n123 (after n115 completes):
   ```bash
   cd ~/Downloads/imagination-engine && source .venv/bin/activate
   HEARTH_ADAPTER="data/model/adapters.n123" ADAPTER_LABEL="n123-CANDIDATE" PYTHONPATH=src python /tmp/compare_adapters.py 2>&1 | tee /tmp/n123_compare.log
   ```
2. **Run battery3c AYF deep test** (this beat's use-case rotation — queued since beat5):
   ```bash
   pkill -f qc_queue; sleep 2
   cd ~/Downloads/imagination-engine && source .venv/bin/activate
   LOG=logs/qc/$(date +%Y%m%d_%H%M)_battery3c_ask_usecases.log
   PYTHONPATH=src python scripts/qc/battery3c_ask_usecases.py 2>&1 | tee "$LOG"
   ```
3. **Check mini n130**: `ssh smaitra@mac-mini.localdomain 'tail -8 ~/Downloads/hearth-corpus/_logs/honest_flywheel.log; ls ~/Downloads/hearth-corpus/GOLD-ADAPTER-*-n130 2>/dev/null'`
   If hangs at iter-300: edit `scripts/finetune.sh` to `--val-batches 4`, kill flywheel+training, restart flywheel.
4. **Companion fine-tuning examples** — write c_gold_beat7.jsonl (5 scenarios: decision-house,
   funny, sober-echo, newparent-say-what-it-is, bored-crisis). Incorporate when companion retrain needed.
5. **Restart qc_queue** after model is free:
   `nohup bash scripts/qc_queue.sh >/dev/null 2>&1 &`

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
- Taste audit of the 96 Claude-drafted gold candidates (_candidates/INDEX.md; batches 1-8).
- docs/internal/why-public-domain.md — do not publish before her review.
- Companion fine-tuning examples from beat5: does the arc-sober echo response and grief-anger
  generic validation read as bad as I called them? (review-queue.md 2026-07-08 section)

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
  Mini: flywheel will detect n123 at ~01:46 Jul 8.
- 07-08 (beat7): Alert-calm root cause found + fixed (3 generator.py changes: detection moved
  before protocol branch, override injected into body_user, BODY_PROMPT strengthened). First-
  person "I speak" ban extended. Beat6 targeted verify: both imag-deposition and imag-mid-switch
  PASS. Gold 123→130 (7 new scripts, diverse gap scenes, SCP'd). n130 training on mini (hung
  at iter-300, restarted). n115/n123 comparative read in progress.
