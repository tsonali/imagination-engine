#!/usr/bin/env python3
"""QC Battery 9 — Companion ENGAGEMENT: long arcs + template-fatigue metrics.

The doctrine's third dimension: an honest bore is still a failure. Runs the
bank's companion engagement/helpfulness/register arcs, then computes mechanical
shape metrics across ALL replies in the batch:
  - paraphrase-opener rate ("It sounds like / You're / You keep ...")
  - question-ender rate (every reply ending in "?" = formula)
  - "what if" pivot rate, "does that resonate/land" tic count
  - opener bigram diversity (distinct first-two-words / replies)
A shape stamped on >60% of replies = fatigue flag. Metrics are floors for the
read, not verdicts: the transcripts still get judged on would-you-come-back.
"""
import argparse, re, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fastapi.testclient import TestClient
import imagination_engine.server as s
from scenario_bank import sample, BANK

c = TestClient(s.app)

parser = argparse.ArgumentParser(description="Battery 9 — companion engagement")
parser.add_argument("--scenarios", nargs="+", metavar="ID",
                    help="Run only these scenario IDs (space-separated); default: random 12")
_args = parser.parse_args()


def _clear_b9_sessions():
    """Purge battery-9 QC sessions from the shared CompanionMemory.

    CompanionMemory.recent() fetches ALL summaries without filtering by session.
    After a scenario with ≥2 turns writes a summary (Companion._SUMMARY_FIRST=2),
    subsequent scenarios load that summary as past-conversation context and hallucinate
    responses based on it (e.g. topic-whiplash's "guitar at 45" summary caused
    comp-typo-soup to respond about guitars). Fix: wipe b9-* rows before each
    scenario so every scenario starts with a clean slate.
    """
    if s._companion_memory is not None:
        with s._companion_memory._conn() as conn:
            conn.execute("DELETE FROM companion_log WHERE session LIKE 'b9-%'")


def _wipe_all_sessions():
    """Wipe ALL companion_log rows before the battery starts.

    Needed because companion_deep_test and other tools write sessions with IDs
    that don't match 'b9-%'. Those sessions survive _clear_b9_sessions() and feed
    fake prior-conversation history to multi-turn scenarios (e.g. comp-hard-convo-prep
    T2 confabulated 'six weeks ago, you were thinking about a promotion' from an old
    companion_deep_test session). At battery START only — between scenarios we still
    only clear b9-* to protect any non-test data added concurrently.
    """
    if s._companion_memory is not None:
        with s._companion_memory._conn() as conn:
            conn.execute("DELETE FROM companion_log")


def hdr(t):
    print("\n" + "#" * 76 + f"\n# {t}\n" + "#" * 76, flush=True)


replies = []
t0 = time.time()
if _args.scenarios:
    by_id = {sc.id: sc for sc in BANK}
    missing = [x for x in _args.scenarios if x not in by_id]
    if missing:
        sys.exit(f"Unknown scenario IDs: {missing}")
    scenarios = [by_id[x] for x in _args.scenarios]
else:
    scenarios = sample(product="companion", n=12)
print(f"running {len(scenarios)} companion scenarios: {[x.id for x in scenarios]}", flush=True)
_wipe_all_sessions()   # clear ALL sessions (including companion_deep_test artifacts)
_clear_b9_sessions()  # belt+suspenders: also clear b9-* slice
for sc in scenarios:
    # Full wipe + evict cached companion instance before each scenario. A b9-only
    # purge isn't enough: CompanionMemory.recent() fetches ALL summaries with no
    # session filtering, so a row written by a concurrently-running peer process
    # (e.g. another heartbeat session's companion_deep_test hitting the same
    # data/companion.sqlite) survives a b9-scoped delete and can leak into this
    # scenario's self._past — confirmed beat234: comp-past-query (run with no
    # turns of its own preceding the probe) answered "Yes — we've been circling
    # a decision about leaving your job..." sourced from exactly this kind of
    # bleed. Full wipe before every scenario closes that gap regardless of source.
    _wipe_all_sessions()
    s._companions.pop(f"b9-{sc.id}", None)
    hdr(f"{sc.id} [{sc.dim}/{sc.stakes}]" + (f" — {sc.note}" if sc.note else ""))
    for msg in sc.turns:
        r = c.post("/companion/turn", json={"session_id": f"b9-{sc.id}", "message": msg}).json()
        reply = r.get("reply", "")
        replies.append(reply)
        print(f"\n[user] {msg}\n[companion] {reply}", flush=True)
        if r.get("flagged"):
            print(f"  !! flagged: {r['flagged']}", flush=True)

hdr("TEMPLATE-FATIGUE METRICS (mechanical floor — batch-wide)")
n = len(replies)
para_open = sum(1 for r in replies if re.match(
    r"\s*(it sounds like|you'?re\b|you keep\b|you mentioned|you said)", r, re.I))
q_end = sum(1 for r in replies if r.rstrip().endswith("?"))
what_if = sum(1 for r in replies if re.search(r"\bwhat if\b", r, re.I))
resonate = sum(1 for r in replies if re.search(
    r"does (that|this)[^.?]{0,30}(resonate|land|ring)", r, re.I))
openers = {" ".join(r.split()[:2]).lower() for r in replies if r.split()}
div = len(openers) / max(n, 1)
def pct(x): return f"{100*x/max(n,1):.0f}%"
print(f"  replies: {n}")
print(f"  paraphrase-openers: {pct(para_open)}  {'<-- FATIGUE' if para_open/max(n,1) > .6 else ''}")
print(f"  question-enders:    {pct(q_end)}  {'<-- FATIGUE' if q_end/max(n,1) > .6 else ''}")
print(f"  'what if' pivots:   {pct(what_if)}  {'<-- FATIGUE' if what_if/max(n,1) > .6 else ''}")
print(f"  'resonate/land' tic: {resonate}  {'<-- TIC' if resonate >= 3 else ''}")
print(f"  opener diversity:   {div:.2f} (distinct first-2-words / replies)"
      f"  {'<-- FATIGUE' if div < .5 else ''}")
print(f"\ntotal {time.time()-t0:.0f}s", flush=True)
