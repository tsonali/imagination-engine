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
        if sc.id in ("imag-active-scene", "imag-active-scene-back-leak-chair-couch") and first:
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
        if sc.id in ("imag-embodiment-eagle", "imag-eagle-wildlife-plural",
                      "imag-eagle-back-leak-chair-whatever", "imag-eagle-crow-agency",
                      "imag-eagle-osprey-wildlife", "imag-eagle-golden-eagle-wildlife",
                      "imag-eagle-companion-bird-he") and first:
            # Check for hallucinated companion animals (user only said 'eagle')
            lower = first.lower()
            # Named companion wildlife — automatic failure if present as characters
            # NOTE: word-boundary match prevents false positives from substrings
            #       (e.g. "slowly" contains "owl", "flow" contains "owl") — must
            #       match the whole word, not just the substring.
            # "bear" is also a common verb ("bear something real") — require article
            # to distinguish noun from verb: "a bear" / "the bear" only.
            # beat86: added "golden eagle", "golden eagles", "mountain lion", "mountain lions"
            # (beat84 added these to generator.py _wildlife_tokens but battery11 was not updated).
            # beat87: added "another bird", "another birds" — beat87 0802 1039 battery11 run showed
            # wildlife-plural script with "another bird far beneath you now, who looks like..." and
            # "an eagle moving steadily through air beneath yours... acknowledging his presence" —
            # companion with agency that slipped past named-token check. "another bird" added to
            # catch generic species-agnostic companion references.
            _WILDLIFE_WORDS = ("hawk", "falcon", "owl", "osprey", "ospreys", "wolf", "raven",
                               "crow", "crows", "another eagle", "second eagle", "other eagle",
                               "golden eagle", "golden eagles", "mountain lion", "mountain lions",
                               "another bird", "another birds", "young eagle", "young eagles",
                               "young bird", "young birds", "younger bird", "younger eagle",
                               "the larger one")
            _WILDLIFE_ARTICLE = ("bear",)
            hallucinated_wildlife = (
                any(re.search(r"\b" + re.escape(w) + r"\b", lower)
                    for w in _WILDLIFE_WORDS)
                or any(re.search(r"\b(?:a|the)\s+" + re.escape(w) + r"\b", lower)
                       for w in _WILDLIFE_ARTICLE)
            )
            # Anonymous companion: "you both" / "we both" implies a second bird without naming
            # the species — slips past named-wildlife token check. Seen: beat86 0802 0642 run
            # wildlife-plural script "You both continue in different directions... between birds."
            # generator.py now drops these sentences (beat86 fix), postcheck verifies the drop.
            # beat105: "both of you" added (complement to "you both"/"we both")
            anon_companion = bool(re.search(r"\b(you both|we both|both of you)\b", lower))
            chair_open = "chair" in first[:200].lower()
            # beat96: companion-bird-he scenario found two new escape forms not caught by
            # he/him/his filter: "a second pair to your right" (wings of a companion bird)
            # and "your mate" (eagle mate reference). These survive drop_hallucinated_he_eagle()
            # because they use no gendered pronouns. postcheck.py extended with
            # _EAGLE_ANON_COMPANION_PATTERN; verify the drop here too.
            # beat105: "fellow eagle", "both of you", "birds who share" added (new escape forms
            # found in pass 6 battery11: "your fellow eagle way up there in kind" /
            # "this moment of flight belongs to both of you" / "birds who share these heights").
            import re as _re
            anon_companion_pattern = bool(_re.search(
                r'\ba\s+second\s+pair\b|\byour\s+mate\b|\ba\s+second\s+bird\b'
                r'|\bsecond\s+pair\s+(?:of|to)\b'
                r'|\bfellow\s+eagle\b|\bboth\s+of\s+you\b|\bbirds\s+who\s+share\b'
                r'|\byour\s+partner\b'
                r'|\btwo\s+(?:separate\s+)?eagles\b'
                r'|\bwe\s+make\s+our\s+way\b'
                r'|\bshares?\s+(?:your|this|the|our)\s+sky\b',
                lower, _re.IGNORECASE
            ))
            print(f"\n>>> EAGLE POSTCHECKS:", flush=True)
            print(f"  {'❌ FAIL' if hallucinated_wildlife else '✅ PASS'} — no hallucinated companion animal", flush=True)
            print(f"  {'❌ FAIL' if anon_companion else '✅ PASS'} — no anonymous companion ('you both'/'we both')", flush=True)
            print(f"  {'❌ FAIL' if anon_companion_pattern else '✅ PASS'} — no anon companion ('a second pair'/'your mate')", flush=True)
            print(f"  {'❌ FAIL' if chair_open else '✅ PASS'} — opening not chair-anchored", flush=True)
        if sc.id == "imag-calm-settle" and first:
            # Furniture enumeration postcheck (beat90 0802).
            # The core Qwen2.5 defect: defaults to room-inventory when asked to settle —
            # "The walls are a light blue, the floor is carpeted, the chair is comfortable..."
            # These sentences are "The [room-noun] is [predicate]" in the opening 250 words.
            # ≥3 matches in opening = furniture enumeration loop = FAIL.
            opening = " ".join(first.split()[:250]).lower()
            _ROOM_NOUNS = ("walls", "floor", "ceiling", "lamp", "chair", "carpet", "bed",
                           "desk", "window", "room", "table", "curtain", "sofa", "couch",
                           "cushion", "pillow", "light", "rug", "shelf")
            enum_hits = sum(
                1 for noun in _ROOM_NOUNS
                if re.search(r"\bthe\s+" + re.escape(noun) + r"\b.{0,20}\bis\b", opening)
            )
            print(f"\n>>> CALM-SETTLE POSTCHECKS:", flush=True)
            print(f"  {'❌ FAIL' if enum_hits >= 3 else '✅ PASS'} — "
                  f"no furniture-enumeration loop in opening ({enum_hits} 'The [noun] is' matches "
                  f"in first 250 words; threshold=3)", flush=True)
        if sc.id == "imag-mri" and first:
            # MRI rehearsal fidelity postchecks (beat86 0802).
            # BUG FOUND: 0256 battery11 MRI script had 'chair' in the body ('You feel the
            # chair beneath you; cushioned and supportive') — user should be lying in the
            # MRI tube, not sitting in a chair. chair_open only checks first 200 chars; this
            # chair was mid-script. Also need to verify drums transformation honored and tube
            # is present and enclosing (not far behind — beat64 stochastic fail).
            lower = first.lower()
            # Chair-in-body: check full script, not just opening (MRI tube has a sliding
            # table, not a chair — any chair mention is a structural scene error).
            chair_in_body = bool(re.search(r"\bchair\b", lower))
            # Tube present and enclosing: must mention tube and it must be described as
            # surrounding/enclosing, not as a distant background sound.
            tube_present = bool(re.search(r"\btube\b", lower))
            # Drums: user's specified coping design must appear (machine hum → drums).
            drums_present = bool(re.search(r"\bdrum", lower))
            print(f"\n>>> MRI POSTCHECKS:", flush=True)
            print(f"  {'❌ FAIL' if chair_in_body else '✅ PASS'} — no chair in script body (must be in tube)", flush=True)
            print(f"  {'❌ FAIL' if not tube_present else '✅ PASS'} — MRI tube referenced", flush=True)
            print(f"  {'❌ FAIL' if not drums_present else '✅ PASS'} — drums transformation honored", flush=True)
        if sc.id == "imag-mid-switch" and first:
            # Verify alert-calm register held after mid-intake switch.
            # Gate: no sleep props + at least one alert anchor present.
            lower = first.lower()
            _SLEEP_PROPS = ("bedroom", "sheets", "sheet", "pillow", "blanket", "quilt",
                            "pajama", "soothing", "heavy eyelid", "fall asleep", "going to sleep")
            _ALERT_ANCHORS = ("armchair", "chair", "couch", "not sleeping", "not asleep",
                              "awake", "alert", "night shift", "sharp", "ready to")
            sleep_fail = any(re.search(r'\b' + re.escape(w) + r'\b', lower) for w in _SLEEP_PROPS)
            alert_ok = any(re.search(r'\b' + re.escape(w) + r'\b', lower) for w in _ALERT_ANCHORS)
            print(f"\n>>> MID-SWITCH POSTCHECKS:", flush=True)
            print(f"  {'❌ FAIL' if sleep_fail else '✅ PASS'} — REGISTER: no sleep props", flush=True)
            print(f"  {'❌ FAIL' if not alert_ok else '✅ PASS'} — REGISTER: alert anchors present", flush=True)
    except Exception as e:
        traceback.print_exc()

print(f"\ntotal {time.time()-t0:.0f}s", flush=True)
