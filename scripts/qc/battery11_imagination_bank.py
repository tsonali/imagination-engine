#!/usr/bin/env python3
"""QC Battery 11 — the imagination slice of the scenario bank.

Runs the bank's imagination scenarios (always-includes locked, rest by date
seed). imag-repeat-variety runs TWICE and the two scripts are diffed:
night 2 must not be night 1 reheated — sentence-level overlap is measured.
Score afterwards with score_scripts.py; read the register cases by hand.
"""
import sys, time, traceback, argparse, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from fastapi.testclient import TestClient
import imagination_engine.server as s
from imagination_engine.generator import generate_session
from imagination_engine.postcheck import _sentences, _words, _similarity
from scenario_bank import sample, BANK

ap = argparse.ArgumentParser()
ap.add_argument("--scenarios", nargs="+", help="Run only these scenario IDs")
args = ap.parse_args()

c = TestClient(s.app)

def hdr(t):
    print("\n" + "#" * 76 + f"\n# SCENARIO: {t}\n" + "#" * 76, flush=True)

def run_one(sc, tag=""):
    sid = c.post(f"/intake/start?protocol={sc.protocol}").json()["session_id"]
    ready = False
    for msg in sc.turns:
        r = c.post("/intake/turn", json={"session_id": sid, "message": msg}).json()
        print(f"\n[user] {msg}\n[engine] {r.get('response')}", flush=True)
        if r.get("ready"):
            ready = True
            break
    if not ready:
        r = c.post("/intake/turn", json={"session_id": sid, "message": "I'm ready — begin."}).json()
        ready = bool(r.get("ready"))
    if not ready:
        print(">>> INTAKE NEVER READY", flush=True)
        return None
    session = s.get_intake_manager().get(sid)
    t0 = time.time()
    script = generate_session(s.get_engine(), session.messages, protocol=sc.protocol)
    print(f"\n----- GENERATED SCRIPT{tag} ({len(script.split())} words, "
          f"{time.time()-t0:.0f}s) -----\n{script}\n----- END SCRIPT -----", flush=True)
    return script

t0 = time.time()
if args.scenarios:
    id_set = set(args.scenarios)
    scenarios = [sc for sc in BANK if sc.id in id_set]
    if not scenarios:
        print(f"ERROR: no scenarios found for {args.scenarios}", flush=True)
        sys.exit(1)
else:
    scenarios = sample(product="imagination", n=6)
print(f"running {[x.id for x in scenarios]}", flush=True)
for sc in scenarios:
    hdr(f"{sc.id} [{sc.dim}/{sc.stakes}] — {sc.note}")
    try:
        first = run_one(sc, " night-1" if sc.id == "imag-repeat-variety" else "")
        if sc.id == "imag-repeat-variety" and first:
            print("\n>>> SAME REQUEST, SECOND NIGHT:", flush=True)
            second = run_one(sc, " night-2")
            if second:
                a = [w for w in (_words(x) for x in _sentences(first)) if len(w) >= 6]
                b = [w for w in (_words(x) for x in _sentences(second)) if len(w) >= 6]
                dup = sum(1 for wb in b if any(_similarity(wb, wa) >= 0.7 for wa in a))
                rate = dup / max(len(b), 1)
                print(f"\n>>> NIGHT-2 SENTENCE OVERLAP WITH NIGHT-1: {rate:.0%} "
                      f"({dup}/{len(b)} sentences near-duplicate)"
                      f"{'  <-- RERUN FATIGUE' if rate > 0.35 else '  (varied)'}", flush=True)
        if sc.id == "imag-active-scene" and first:
            # In a solo active-scene (user is the only person), any 'she/her' is pronoun
            # bleed — the model is treating the runner as a third party instead of 'you'.
            lower = first.lower()
            she_bleed = bool(re.search(r'\bshe\b', lower))
            her_body_bleed = bool(re.search(
                r'\bher\s+(?:legs?|arms?|hands?|feet|foot|lungs?|breath|body|muscles?|'
                r'strides?|steps?|chest|heart|back|shoulders?|knees?|thighs?|calves?|'
                r'pace|push|run|sprint|cross)',
                lower
            ))
            bleed = she_bleed or her_body_bleed
            print(f"\n>>> ACTIVE-SCENE POSTCHECKS:", flush=True)
            print(f"  {'❌ FAIL' if bleed else '✅ PASS'} — no she/her pronoun bleed (user in own body)", flush=True)
        if sc.id == "imag-embodiment-eagle" and first:
            # Check for hallucinated companion animals (user only said 'eagle')
            lower = first.lower()
            # Named companion wildlife — automatic failure if present as characters
            # NOTE: word-boundary match prevents false positives from substrings
            #       (e.g. "slowly" contains "owl", "flow" contains "owl") — must
            #       match the whole word, not just the substring.
            # "bear" is also a common verb ("bear something real") — require article
            # to distinguish noun from verb: "a bear" / "the bear" only.
            _WILDLIFE_WORDS = ("hawk", "falcon", "owl", "wolf", "raven",
                               "another eagle", "second eagle")
            _WILDLIFE_ARTICLE = ("bear",)
            hallucinated_wildlife = (
                any(re.search(r"\b" + re.escape(w) + r"\b", lower)
                    for w in _WILDLIFE_WORDS)
                or any(re.search(r"\b(?:a|the)\s+" + re.escape(w) + r"\b", lower)
                       for w in _WILDLIFE_ARTICLE)
            )
            chair_open = "chair" in first[:200].lower()
            print(f"\n>>> EAGLE POSTCHECKS:", flush=True)
            print(f"  {'❌ FAIL' if hallucinated_wildlife else '✅ PASS'} — no hallucinated companion animal", flush=True)
            print(f"  {'❌ FAIL' if chair_open else '✅ PASS'} — opening not chair-anchored", flush=True)
    except Exception as e:
        traceback.print_exc()

print(f"\ntotal {time.time()-t0:.0f}s", flush=True)
