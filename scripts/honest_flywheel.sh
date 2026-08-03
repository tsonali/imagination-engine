#!/usr/bin/env bash
# HONEST FLYWHEEL — gold-only A-family retrain on the mini.
# Watches A_gold.jsonl for hash changes; retrains on curated gold only.
# No generation, no auto-promote, no taste-cull — prevents self-poisoning.
# Run: nohup bash scripts/honest_flywheel.sh >> ~/Downloads/hearth-corpus/_logs/honest_flywheel.log 2>&1 &
set -uo pipefail
cd ~/imagination-engine && source .venv/bin/activate

L=~/Downloads/hearth-corpus/_logs; mkdir -p "$L"
GOLD=~/Downloads/hearth-corpus/A-imagination/A_gold.jsonl
ADAPTERS_DIR=~/Downloads/hearth-corpus/_train/adapters
CORPUS=~/Downloads/hearth-corpus

say(){ echo "[$(date '+%m-%d %H:%M:%S')] $*"; }
say "honest_flywheel started (pid $$) — gold-only, no self-generation"

# Snapshot counter: increment each completed retrain
N=$(ls "$CORPUS"/GOLD-ADAPTER-* 2>/dev/null | wc -l | tr -d ' ')

PREV_HASH=""
while true; do
    CURR_HASH=$(md5 -q "$GOLD" 2>/dev/null || echo "NO_GOLD")
    if [ "$CURR_HASH" = "NO_GOLD" ]; then
        say "A_gold.jsonl not found — waiting"
        sleep 60; continue
    fi
    if [ "$CURR_HASH" = "$PREV_HASH" ]; then
        sleep 300; continue
    fi

    say "A_gold.jsonl changed ($PREV_HASH -> $CURR_HASH) — starting retrain"
    PREV_HASH="$CURR_HASH"
    N=$(( N + 1 ))
    LABEL="n$(printf '%03d' $N)"
    TS=$(date '+%Y%m%d-%H%M')

    say "1/3 rebuild training data"
    python scripts/build_training_data.py 2>&1 | tail -2

    say "2/3 fine-tune ($LABEL)"
    FT_LOG="$L/finetune_honest_${TS}.log"
    rm -f "$ADAPTERS_DIR"/*.safetensors
    bash scripts/finetune.sh > "$FT_LOG" 2>&1
    # Print key lines: val loss and iteration checkpoints
    tr '\r' '\n' < "$FT_LOG" | grep -iE "Iter [0-9]+:|val loss|out of memory" | tail -5

    say "3/3 probe eval ($LABEL)"
    python scripts/test_finetuned.py both > "$L/probe_latest.txt" 2>&1
    say "$LABEL probe written to probe_latest.txt"

    # Archive adapter
    SAVE="$CORPUS/GOLD-ADAPTER-$TS-$LABEL"
    mkdir -p "$SAVE"
    cp "$ADAPTERS_DIR"/*.safetensors "$SAVE/" 2>/dev/null && \
        say "adapter archived: $SAVE" || \
        say "WARNING: no adapter file to archive"

    touch "$L/FLYWHEEL_DONE"
    say "retrain complete — honest flywheel sleeping"
    sleep 300
done
