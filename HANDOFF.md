# HANDOFF — resume here (read this first)

_Last updated 2026-07-08 beat9 (n154 COMPLETE; active-body fix; gold 162; battery11 running; qc_queue PAUSED)._
_Single source of truth for a fresh session. Everything below is real and running._

## FIRST THING TO DO when you resume — run these checks
```bash
# Mini — check n162 training status
ssh -o IdentitiesOnly=yes smaitra@mac-mini.localdomain '
  echo "flywheel: $(pgrep -f honest_flywheel >/dev/null && echo RUNNING || echo DOWN)"
  tail -6 ~/Downloads/hearth-corpus/_logs/honest_flywheel.log
  ls ~/Downloads/hearth-corpus/ | grep GOLD-ADAPTER | tail -5
  pgrep -f "mlx_lm lora" && echo "TRAINING" || echo "not training"'

# Laptop — qc_queue and model and battery11 status
pgrep -f qc_queue >/dev/null && echo "qc_queue RUNNING" || echo "qc_queue PAUSED (expected)"
pgrep -f mlx_lm && echo "mlx_lm running" || echo "model idle"
pgrep -f battery11 && echo "battery11 RUNNING" || echo "battery11 COMPLETE (check logs)"
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

### Live adapter: n115 (promoted 2026-07-08 beat5)
- `data/model/adapters/` = GOLD-ADAPTER-0708-0016-n115 (123-gold old-format, 1500 iters)
- n154 adapter rsync'd to `data/model/adapters.n154/` — PENDING comparative read

### Generator fixes (beat9, cumulative with beat5/6/7)
1. **Active-body opening override** — `_is_active_body` detected via (CASE A + motion keywords
   in scene/transcript). When detected:
   - `⚠️ ACTIVE-BODY OPENING OVERRIDE` injected into open_user: MOVE 1 must NOT anchor to
     the chair; use physical sensation from the active scene (effort/breath/pavement).
   - `_active_body_body_note` injected into body_user: stay inside the motion scene.
   - Belt-and-suspenders alongside n154 training data fix.
2. **First-person ban extended** (BODY_PROMPT Rule #2) — added to banned phrases:
   "with me", "we start", "we are here", "for us both", "we both", "come with me",
   "join me here", "follow me" — narrator-places-itself-in-scene variants.
3. **Earlier fixes (beats 5-7):**
   - OPEN_PROMPT: all voice self-reference banned (not "this voice", "my voice", etc.)
   - BODY_PROMPT: first-person "I speak/hold/guide" banned; alert-calm register tightened
   - postcheck.py: drop_adjacent_duplicates() + repair_short_phrase_repeats(SHORT_NGRAM=5)

### Gold corpus: 162 scripts
- 27 original + 135 Claude-drafted
- **Beat9 new (155-162):** afternoon-nap, apartment-return, ice-skating-early, pre-surgery-suspended,
  jigsaw-last-piece, last-day-at-job, campfire-alone, post-camping-shower. SCP'd to mini.
- **Beat8 new (141-154):** parked-car, swimming-alone, rain-window, familiar-path, after-hard-ends,
  sitting-in-quiet, river-low-water, arriving-after-absence; first-snow, making-bread, empty-stadium,
  open-road-drive, summer-garden, walk-after-good-conversation.
- **Beat7 new (124-130):** rooftop-city-night, woodshop-planing, pre-dawn-kitchen, lap-pool,
  mountain-descent, airport-dawn, dancing-alone.
- Sonali's taste audit of batches 1-8 PENDING (_candidates/INDEX.md).

### Mini flywheel: n154 COMPLETE ✅; n162 training PENDING
- **GOLD-ADAPTER-0708-0835-n154** saved at 08:35. Trained on 154 gold (first adapter with
  pipeline fix; 34.4% in-media-res training).
- **Probe PASS** — opening-diversity 4/4, worst 40-char repeat ×2.
- **Probe READ:** eagle prompt opens "You are an eagle. You feel the warm sun on your back as
  you soar over the mountains." ← IN-SCENE. First adapter to break chair-opening bias for
  active-body scenes.
- rsync'd to laptop: `data/model/adapters.n154/`
- **n162 training:** 162-gold SCP'd to mini at ~09:05; flywheel next poll will detect hash
  change and auto-start n162. ETA: ~10:00-11:30 when started.

### Battery11 (imagination): RUNNING (started 08:37, 6 scenarios, ~60 min)
- Running with n115 adapter + new active-body prompt override (beat9 generator fix).
- Key scenario to read when complete: `imag-active-scene` opening. Did the prompt override
  prevent the chair-opening pattern with n115?
- Log will appear in `logs/qc/` when complete.
- **After battery11 completes:** model is free → run compare_n154.py → then restart qc_queue.

### qc_queue: PAUSED (model busy with battery11)
- Restart after battery11 + comparative read complete:
  ```bash
  cd ~/Downloads/imagination-engine && nohup bash scripts/qc_queue.sh >> logs/qc/queue.log 2>&1 &
  ```

### Companion question-enders: 10% (confirmed beat9)
- STANDING FLAG RESOLVED. Well under <50% bar.
- Content regressions confirmed fine-tuning problems (not prompt-fixable):
  comp-decision-house T3, comp-funny, comp-arc-sober T5/T8, comp-arc-newparent T6, comp-bored-test.
- c_gold_beat9.jsonl (10 examples) written to hearth-corpus/C-companion/. Ready for next retrain.
- Previous: c_gold_beat7.jsonl (12 examples) also ready.

## NEXT HEARTBEAT PRIORITY (in order)

1. **Read battery11 output when complete** — especially imag-active-scene opening.
   Did prompt override fix the chair pattern with n115? (Log in logs/qc/ when done)

2. **n154 comparative READ vs n115:**
   ```bash
   cd ~/Downloads/imagination-engine && .venv/bin/python scripts/qc/compare_n154.py 2>&1 | tee logs/qc/compare_n154_$(date +%m%d_%H%M).log
   ```
   Focus: does eagle/runner scenario open IN-SCENE vs CHAIR? ≥3/5 wins → promote n154.
   If promote: `cp -r data/model/adapters data/model/adapters.LIVE-n115-bak && cp -r data/model/adapters.n154/. data/model/adapters/`

3. **Companion deep test** (use-cases.md UC1-UC2):
   - UC1: 2am mind-race (insomnia spiral with work dread, multi-turn, check honest floor + utility)
   - UC2: long-arc check-ins (does companion.sqlite cross-session memory reference past sessions
     correctly without fabricating?)
   Run via battery9 or direct FastAPI test client.

4. **Restart qc_queue** after all model work above:
   ```bash
   nohup bash scripts/qc_queue.sh >> logs/qc/queue.log 2>&1 &
   ```

5. **Gold corpus** — at 162. Continue toward 170+ next beat (5-10 new scripts).

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
