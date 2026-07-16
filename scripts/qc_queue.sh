#!/usr/bin/env bash
# The QC queue-runner — keeps the laptop's single model lane busy FOREVER,
# independent of any Claude session. Runs the battery queue in rotation;
# each pass re-runs everything (the scenario bank samples by date, so each
# day's pass covers a different slice of the usage universe). One model
# process at a time — this is a 16GB machine and that is the law.
#
# Installed as launchd job com.hearth.qcqueue (RunAtLoad + KeepAlive), so it
# survives reboots and crashes. Logs: logs/qc/queue_<timestamp>_<battery>.log
# Claude reads the logs and does the judging whenever a session is alive.
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1
source .venv/bin/activate 2>/dev/null || true

# MEMORY HEADROOM GATE (added 2026-07-12 after the 12:37 kernel panic — wired-GPU exhaustion):
# never launch a model battery without >=35% system memory free; kill ghosts and wait if needed.
mem_ok() {
  for i in 1 2 3 4; do
    PCT=$(memory_pressure 2>/dev/null | grep -oE "free percentage: [0-9]+" | grep -oE "[0-9]+")
    [ -n "$PCT" ] && [ "$PCT" -ge 35 ] && return 0
    pkill -9 -f "battery11_imagination|battery9_engagement|battery10_registers|battery12_vital|battery3c_ask|byo_deep_test|companion_deep_test|product_e2e_test" 2>/dev/null
    sleep 45
  done
  echo "[$(date '+%m-%d %H:%M')] MEMORY GATE: still <35% free after ghost kills — skipping this battery" >> logs/qc/queue.log
  return 1
}

mkdir -p logs/qc

QUEUE=(
  scripts/qc/battery11_imagination_bank.py
  scripts/qc/battery9_engagement.py
  scripts/qc/battery10_registers.py
  scripts/qc/battery2b_honesty.py
  scripts/qc/battery4b_floor.py
  scripts/qc/battery3b_ask_retest.py
  scripts/product_e2e_test.py
)

say() { echo "[$(date '+%m-%d %H:%M:%S')] $*" >> logs/qc/queue.log; }
say "qc-queue runner started (pid $$)"

while true; do
  for b in "${QUEUE[@]}"; do
    # the 16GB rule: never start while another model process lives
    # IMPORTANT: match scripts/ prefix to avoid matching the Claude heartbeat node process,
    # whose prompt text contains the word "battery" and would otherwise block this loop forever.
    while pgrep -f "scripts/qc/battery\|scripts/product_e2e\|gen_.*candidates\|bench_spec\|mlx_lm" | grep -v $$ | grep -qv "^$"; do
      sleep 60
    done
    # OOM ghost-process guard: kill any model or battery processes left in zombie/sleeping
    # state after a crash (they hold GPU wired Metal memory for 30+ min otherwise).
    # Must kill by script name (battery*/product_e2e) since Python processes aren't named mlx_lm.
    pkill -f "mlx_lm" 2>/dev/null
    pkill -f "battery11_imagination\|battery9_engagement\|battery10_registers\|product_e2e_test" 2>/dev/null
    sleep 5
    # Syntax guard: abort entire pass if scenario_bank.py is broken (prevents silent empty runs)
    if ! .venv/bin/python -c "import ast; ast.parse(open('scripts/qc/scenario_bank.py').read())" 2>/dev/null; then
      say "SCENARIO_BANK SYNTAX ERROR — skipping all batteries this pass; fix scenario_bank.py"
      break
    fi
    name=$(basename "$b" .py)
    log="logs/qc/queue_$(date +%m%d_%H%M)_${name}.log"
    say "running $name -> $log"
    mem_ok || continue
    # HF_HUB_OFFLINE=1: prevents huggingface_hub (imported by mlx_lm) from making
    # network calls to HuggingFace CDN (CloudFront) during model load. Without this,
    # the process can get stuck in CLOSE_WAIT when CloudFront drops a long-idle connection,
    # causing battery runs to hang silently mid-generation (observed beat38 battery11 0044).
    HF_HUB_OFFLINE=1 .venv/bin/python "$b" > "$log" 2>&1
    say "$name exit $? ($(grep -c 'PASS' "$log" 2>/dev/null || echo 0) PASS / $(grep -c 'FAIL' "$log" 2>/dev/null || echo 0) FAIL lines)"
    sleep 120  # let memory settle between model loads
  done
  # once per pass: watchdog the mini's flywheel (sshd has disk access; launchd
  # on either machine can't touch ~/Downloads under TCC). If the trainer
  # stopped — plateau or crash — restart it: each fresh run regrows candidates
  # with the current corpus, so restarts are productive, not spinning.
  # PAUSE GATE (added 2026-06-14): if scripts/FLYWHEEL-PAUSED exists, do NOT restart.
  # The self-training flywheel was Goodharting its val metric (training on its own
  # generated output -> imagination collapse). Paused pending the rebuilt read-driven
  # loop. Resume = delete scripts/FLYWHEEL-PAUSED.
  if [ -f scripts/FLYWHEEL-PAUSED ]; then
    say "flywheel PAUSED (scripts/FLYWHEEL-PAUSED present) — not restarting"
  elif ! ssh -o IdentitiesOnly=yes -o ConnectTimeout=10 smaitra@mac-mini.localdomain       'pgrep -f recursive_flywheel >/dev/null' 2>/dev/null; then
    say "mini flywheel stopped — restarting it"
    ssh -o IdentitiesOnly=yes smaitra@mac-mini.localdomain       'cd ~/imagination-engine && git pull -q origin main; rm -f ~/Downloads/hearth-corpus/_logs/RECURSIVE_DONE; nohup bash scripts/recursive_flywheel.sh > /dev/null 2>&1 & sleep 2; pgrep -f recursive_flywheel >/dev/null && echo restarted'       >> logs/qc/queue.log 2>&1 || say "mini restart FAILED (unreachable?)"
  fi
  say "full pass complete — starting the next (there is no done)"
  sleep 300
done
