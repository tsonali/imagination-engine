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
from imagination_engine.postcheck import (
    _sentences, _words, _similarity,
    check_furniture_consistency, check_presence_continuity,
    check_hallucinated_companion_presence,
    check_return_to_room_closing)
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
                      "imag-eagle-companion-bird-he",
                      # beat225: this regression scenario (added beat221) had
                      # zero postcheck coverage — it wasn't in this tuple, and
                      # was separately found running with an empty intake
                      # (fixed in scenario_bank.py). Now that it has a real
                      # eagle intake, it needs the same eagle postchecks as
                      # the base scenario it protects.
                      "imag-embodiment-eagle-counterpart-you-two") and first:
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
                               "the larger one", "bird of prey", "birds of prey",
                               # beat135: ground wildlife with agency in eagle scripts
                               "mountain sheep", "mountain goat", "bighorn sheep", "bighorn",
                               # beat163: "raptor"/"raptors" escape found in battery11_2038
                               # imag-eagle-companion-bird-he: "a circling raptor" used the genus
                               # name rather than a specific species, slipping the token filter.
                               "raptor", "raptors",
                               # beat189: bare "goat" escape found in battery11_0826_1712
                               # imag-eagle-wildlife-plural — same class as beat135's mountain-
                               # goat/bighorn fix but without the qualifier.
                               "goat", "goats",
                               # beat228: "a small white rabbit darts across the terrain far
                               # below" — battery11_0905_0112 golden-eagle-wildlife honest read.
                               # Parity with generator.py's _wildlife_tokens.
                               "rabbit", "rabbits")
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
            # beat136 (0817): "us both" / "us all" added — escaped battery11 1818 companion-bird-he
            anon_companion = bool(re.search(r"\b(you both|we both|both of you|us both|us all)\b", lower))
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
                r'|\btwo\s+(?:separate\s+)?eagles\b|\btwo\s+birds\b'
                r'|\bwe\s+make\s+our\s+way\b'
                r'|\bshares?\s+(?:your|this|the|our)\s+sky\b'
                r'|\bsharing\s+(?:one\s+part\s+of|this|the|your)\s+sky\b'
                # beat122: companion-presence assertion escape vectors (not caught by token drop
                # because they use no named species or pronoun — just presence assertion):
                # "you're not alone up here after all" / "another flapping wing" / "old friend passing"
                r'|\bnot\s+alone\s+up\s+here\b'
                r'|\byou.re\s+not\s+alone\b|\byou\s+are\s+not\s+alone\b'
                r'|\banother\s+flapping\s+wing\b'
                r'|\bold\s+friend\s+passing\b'
                # beat134: three new escape forms found in 0826 battery11 golden-eagle-wildlife 2121w:
                # "someone else who might join you in sky as silent partner"
                # "you fly with someone else" / "a fellow traveler at such height"
                r'|\bsilent\s+partner\b'
                r'|\bfellow\s+traveler\b'
                r'|\bfly\s+with\s+someone\b'
                # beat135: same-species bystander at altitude — "a pair of eagles flying opposite
                # directions below" implies other-eagle presence in a solo-eagle script
                r'|\ba\s+pair\s+of\s+eagles\b|\bpair\s+of\s+eagles\b'
                # beat136 (0817): us both/all/we fly/our flight escaped battery11 1818
                r'|\bus\s+both\b|\bus\s+all\b'
                r'|\bwe\s+fly\b|\bwe\s+soar\b|\bwe\s+glide\b|\bwe\s+circle\b|\bwe\s+drift\b'
                r'|\bour\s+flight\b'
                # beat143: companion-by-sound escape — "a call identical but not yours" in
                # imag-embodiment-eagle battery11 1527 (2026-08-18). Acoustic companion assertion.
                r'|\bcall\s+identical\b'
                r'|\bidentical\s+but\s+not\s+yours\b'
                r'|\banother\s+call\b|\ba\s+second\s+call\b'
                r'|\banother\s+wing\b'
                # beat153: "distant bird" acoustic companion escape — 0820_1039 battery11:
                # "you call out in turn toward that distant bird overhead" / "The distant bird
                # remains somewhere unseen through the clouds" — unnamed companion implied.
                r'|\b(?:that\s+)?distant\s+bird\b'
                r'|\bin\s+turn\s+toward\b'
                r'|\bcall\s+out\s+in\s+turn\b'
                # beat158 (2026-08-21): three new escape forms found in battery11_0529:
                # "another pair of wings" (eagle-wildlife-plural) — "a second pair" (beat96) blocked;
                # "two separate birds" (eagle-wildlife-plural) — "two birds"/"two separate eagles" blocked;
                # "both birds" (golden-eagle-wildlife) — "both of you"/"you both" blocked but not this.
                r'|\banother\s+pair\s+of\s+wings\b'
                r'|\btwo\s+separate\s+birds\b'
                r'|\bboth\s+birds\b'
                # beat159 (2026-08-21): battery11_1003 golden-eagle-wildlife honest read
                # found two escapes that passed mechanical 5/5 postchecks:
                # "another shape joining your for company" / "fly together without words,
                # moving as one entity across this sky"
                r'|\bfly\s+together\b'
                r'|\bas\s+one\s+entity\b'
                r'|\bfor\s+company\b'
                r'|\banother\s+shape\b'
                # beat163 (2026-08-21): new escape forms found in battery11_2038 honest read.
                # GOLDEN-EAGLE-WILDLIFE: "your companion" / "wingtip to wingtip" — companion
                # bird asserted by direct reference and formation-flight geometry.
                # COMPANION-BIRD-HE: "fellow hunter" / "another eye on" / "competitor or ally" /
                # "companionship in altitude" — companion entity framed as co-hunter/co-observer.
                r'|\byour\s+companion\b'
                r'|\bwingtip\s+to\s+wingtip\b'
                r'|\bfellow\s+hunter\b'
                r'|\banother\s+eye\s+on\b'
                r'|\bcompetitor\s+or\s+ally\b'
                r'|\bcompanionship\s+in\b'
                # beat169 (2026-08-23): "the other bird" and "other's call" escape vectors.
                # Found in battery11_0823_0259 imag-eagle-wildlife-plural honest read.
                r'|\bthe\s+other\s+bird\b'
                r'|\bthe\s+other\s+eagle\b'
                r"|\bother['']\s*s\s+call\b"
                # beat178 (2026-08-24): battery11_0824_1434 honest read, 35/35 mechanical PASS
                # but two new escapes found: "your presence was different now that someone has
                # gone away" (implied departed companion, imag-eagle-wildlife-plural) and
                # "someone has started campfire as first step toward settling for evening meal
                # and shelter" (hallucinated human bystander, imag-eagle-golden-eagle-wildlife —
                # a new escape class: a human character, not another eagle).
                r'|\bsomeone\s+has\s+gone\s+away\b'
                r'|\bsomeone\s+has\s+started\b'
                # beat181 (2026-08-25): battery11_0825_0231 honest read, imag-eagle-
                # companion-bird-he — passed all 6 eagle postchecks but contained "a pair
                # soaring low ... not alone in the sky ... Eagles that have been on patrol
                # before your arrived".
                r'|\ba\s+pair\s+soaring\b'
                r'|\bnot\s+alone\s+in\s+the\s+sky\b'
                r'|\beagles?\s+that\s+have\s+been\s+on\s+patrol\b'
                # beat183 (2026-08-25): battery11_0825_0950 honest read, imag-eagle-
                # companion-bird-he — "it feels like something new without needing
                # words between birds" (plural "birds" implies a second bird).
                r'|\bwords\s+between\s+birds\b'
                # beat186 (2026-08-26): battery11_2235 honest read, imag-embodiment-
                # eagle — 3rd occurrence of the beat178 human-bystander class, new
                # phrasing: "there is a figure below... someone sitting on their
                # knees", "before you realize it's not a hiker", "someone has been
                # walking near the smoke... a human presence beneath everything else".
                r'|\ba\s+figure\s+below\b'
                r'|\bsomeone\s+sitting\b'
                r'|\bnot\s+a\s+hiker\b'
                r'|\bsomeone\s+has\s+been\s+walking\b'
                r'|\bhuman\s+presence\b'
                # beat187 (2026-08-26): battery11_0826_0355 honest read, imag-eagle-
                # wildlife-plural — 4th occurrence of the human-bystander class, new
                # scenario, 5 new phrasings.
                r'|\bwants?\s+to\s+be\s+seen\b'
                r'|\brock\s+climber\b'
                r'|\bhumans?\s+come\s+into\s+(?:your\s+)?vision\b'
                r'|\bplaced\s+by\s+(?:someone|humans?)\b'
                r'|\bpeople\s+would\s+have\s+been\s+walking\b'
                # beat188 (battery11_0826_0920 honest read): acoustic anon-
                # companion escape — "the cry from above is answered by
                # another... draws birds towards it"; "the cry from below
                # returns then".
                r'|\banswered\s+by\s+another\b'
                r'|\bdraws\s+birds\s+towards\b'
                r'|\bcry\s+from\s+(?:above|below)\s+returns\b'
                # beat189 (battery11_0826_1712): "acknowledgment between birds
                # flying their respective paths" — same family as the "words
                # between birds" pattern above, different verb.
                r'|\backnowledgment\s+between\s+birds\b'
                # beat191 (battery11_0826_1854): "not just one bird but two"
                # (explicit second-bird count) and "dropping back into
                # formation with you at its side... this pairing that feels
                # natural" (full companion-flight moment, no species/pronoun).
                r'|\bnot\s+(?:just\s+)?one\s+bird\s+but\s+two\b'
                r'|\bformation\s+with\s+you\b'
                r'|\bthis\s+pairing\b'
                r'|\bat\s+its\s+side\b'
                # beat192 (battery11_0826_2346, imag-eagle-wildlife-plural):
                # "it's knowing this other animal shares the same sky above"
                r'|\bthis\s+other\s+animal\b'
                # beat193 (battery11_0827_0453): "both of your figures" /
                # "matching theirs" / "both move together" (golden-eagle-
                # wildlife) and "either of you" (companion-bird-he).
                r'|\bboth\s+of\s+your\s+figures\b'
                r'|\bmatching\s+theirs\b'
                r'|\bboth\s+move\s+together\b'
                r'|\beither\s+of\s+you\b'
                # beat196 (battery11_2152): "proof someone else has found their
                # way to these heights" (golden-eagle-wildlife); "distance
                # closes between the two of you" / "nothing is said between
                # two of us" (companion-bird-he).
                r'|\bsomeone\s+else\s+has\s+found\s+their\s+way\b'
                r'|\bthe\s+two\s+of\s+you\b'
                r'|\btwo\s+of\s+us\b'
                # beat197 (battery11_0828_0818, imag-embodiment-eagle): "The call
                # of the distant eagle is still there" — acoustic anon-companion
                # escape naming the species directly.
                r'|\bdistant\s+eagle\b'
                # beat198 (battery11_1317, imag-eagle-wildlife-plural + imag-eagle-
                # golden-eagle-wildlife): "You're both above the pine trees now"
                # (contraction form of the already-banned "both of you"/"you both");
                # "the flock" acting as an agentic guide for nearly the whole script
                # ("flock leads with confidence... you follow close behind them",
                # "the flock remains ahead", "a specific bird leads slightly ahead").
                # Scoped to "flock LEADS/GUIDES you" / "you FOLLOW the flock" framing,
                # not a blanket "flock" ban — A_gold.jsonl has a legitimate, unrelated
                # murmuration-embodiment scenario type ("Your flock, your murder")
                # with zero "you follow"/"flock leads" framing; verified 0 hits
                # against the full gold corpus before adding (see postcheck.py).
                r'|\byou[\x27’]re\s+both\b|\byou\s+are\s+both\b'
                r'|\bflock\s+(?:leads?|guides?)\b'
                r'|\byou\s+follow\s+(?:the\s+|this\s+)?flock\b'
                r'|\bthe\s+flock\s+(?:remains\s+ahead|ahead\s+of\s+you)\b'
                r'|\ba\s+specific\s+bird\s+leads\b'
                r'|\bflock\s+ahead\b'
                # beat206 (queue_0829_1746, imag-eagle-companion-bird-he — the
                # scenario built specifically to stress-test this defect class):
                # "There is company here; someone whose voice echoes back and
                # forth between peaks without needing words or distance between
                # them." A full 3-passage acoustic companion-bird arc, explicit
                # and unambiguous ("there is company here") — no prior phrase
                # in this list matched it. Parity with generator.py's beat206 entry.
                r'|\bcompany\s+here\b'
                r'|\bsomeone\s+whose\s+voice\b'
                # beat207 (queue_0829_2347_battery11_imagination_bank.log honest
                # read): golden-eagle-wildlife "the smaller bird passes in
                # front... matches altitude" (visual companion, no named
                # species) + companion-bird-he "answer to that cry exists
                # too... another hears the same sound" (acoustic companion).
                # Parity with generator.py + postcheck.py.
                r'|\bthe\s+smaller\s+bird\b'
                r'|\bmatches\s+altitude\b'
                r'|\banswer\s+to\s+that\s+cry\b'
                r'|\banother\s+hears\s+the\s+same\s+sound\b'
                # beat238 (verify_beat237_0907_1835.log honest read, imag-eagle-
                # golden-eagle-wildlife): ALL 6 EAGLE POSTCHECKS PASSED despite
                # "The cry from that other bird rings out again", "a conversation
                # happening between them, one that doesn't involve anyone else",
                # and "birds like yourself"/"birds like yourselves" (both
                # determiner forms, appeared twice). Parity with postcheck.py's
                # _EAGLE_ANON_COMPANION_PATTERN beat238 entry. 0 hits in
                # A_gold.jsonl confirmed before adding.
                r'|\bthat\s+other\s+bird\b'
                r'|\ba\s+conversation\s+happening\s+between\s+them\b'
                r'|\bbirds\s+like\s+yourself\b|\bbirds\s+like\s+yourselves\b',
                lower, _re.IGNORECASE
            ))
            # beat153: Chair-body reminder in eagle script (not just opening).
            # "held by your chair below" appeared in closing line of companion-bird-he
            # script — immersion-breaking chair reference in the body, not caught by
            # opening-only check. Check full script for "your chair" in eagle context.
            # beat158: extended "in a chair" — battery11_0529 companion-bird-he generated
            # "You are not in a chair." (constraint-bleed from FORBIDDEN note). The prior
            # regex had (?:the\s+)? which matched "in the chair" / "in chair" but not "in a chair".
            # beat207: bare "chair or bed or surface" furniture-enumeration in a
            # closing line ("You notice what's under you — chair or bed or
            # surface that holds you steady...") matched none of the 3 prior
            # patterns. Parity with generator.py.
            # beat207: "seated" ("...where you are seated here") added — on
            # generator.py's own FORBIDDEN-THROUGHOUT list for active-body
            # scenes but had no mechanical check at all. Parity with generator.py.
            chair_body = bool(_re.search(
                r'\byour\s+chair\b|\bin\s+(?:a\s+|the\s+)?chair\b|\bfrom\s+(?:your\s+)?chair\b|\bchair\s+or\s+(?:bed|surface)\b|\bseated\b',
                lower, _re.IGNORECASE
            ))
            # beat165 (2026-08-22): "her" object/possessive pronoun as companion signal.
            # battery11_0822 imag-embodiment-eagle script contained "beak touches her at
            # nose-soft distance" / "watching her depart" / "looking up at her from below"
            # — she/hers sentences were dropped (3 dropped) but "her" survived. In solo
            # active-body eagle scripts the user is always "you/your", so any "she/her/hers"
            # = fabricated companion. postcheck.py _SHE_HER_PATTERN now includes "her" (beat165).
            she_her_companion = bool(_re.search(r'\b(she|her|hers)\b', lower))
            print(f"\n>>> EAGLE POSTCHECKS:", flush=True)
            print(f"  {'❌ FAIL' if hallucinated_wildlife else '✅ PASS'} — no hallucinated companion animal", flush=True)
            print(f"  {'❌ FAIL' if anon_companion else '✅ PASS'} — no anonymous companion ('you both'/'we both')", flush=True)
            print(f"  {'❌ FAIL' if anon_companion_pattern else '✅ PASS'} — no anon companion ('a second pair'/'your mate')", flush=True)
            print(f"  {'❌ FAIL' if she_her_companion else '✅ PASS'} — no she/her/hers companion pronoun in eagle script", flush=True)
            print(f"  {'❌ FAIL' if chair_open else '✅ PASS'} — opening not chair-anchored", flush=True)
            print(f"  {'❌ FAIL' if chair_body else '✅ PASS'} — no chair-body-reminder in full script", flush=True)
        if sc.id == "imag-calm-settle" and first:
            # Furniture enumeration postcheck (beat90 0802).
            # The core Qwen2.5 defect: defaults to room-inventory when asked to settle —
            # "The walls are a light blue, the floor is carpeted, the chair is comfortable..."
            # These sentences are "The [room-noun] is [predicate]" in the opening 250 words.
            # ≥3 matches in opening = furniture enumeration loop = FAIL.
            _ROOM_NOUNS = ("walls", "floor", "ceiling", "lamp", "chair", "carpet", "bed",
                           "desk", "window", "room", "table", "curtain", "sofa", "couch",
                           "cushion", "pillow", "light", "rug", "shelf")
            # Split first 250 words into sentences; require sentence-INITIAL "The [noun] is"
            # to avoid false positives from cross-sentence matches like "the bed. your back is"
            # where "is" belongs to the NEXT sentence, not to the bed clause.
            opening_sents = re.split(r"(?<=[.!?])\s+",
                                     " ".join(first.split()[:250]).lower())
            enum_hits = sum(
                1 for sent in opening_sents
                for noun in _ROOM_NOUNS
                if re.match(r"^the\s+" + re.escape(noun) + r"\b.{0,20}\b(?:is|are)\b", sent)
            )
            # beat238 (verify_beat237_0907_1835.log honest read): calm-settle
            # had zero postcheck coverage for hallucinated-companion content —
            # user's intake said only "I had a long day... nothing specific",
            # but the script closed with "since last you arrived together in
            # this room tonight." See postcheck.py's beat238 comment above
            # check_hallucinated_companion_presence for why this is scoped to
            # one literal phrase rather than the full "you both" family.
            companion_issue = check_hallucinated_companion_presence(first)
            print(f"\n>>> CALM-SETTLE POSTCHECKS:", flush=True)
            print(f"  {'❌ FAIL' if enum_hits >= 3 else '✅ PASS'} — "
                  f"no furniture-enumeration loop in opening ({enum_hits} 'The [noun] is' matches "
                  f"in first 250 words; threshold=3)", flush=True)
            print(f"  {'❌ FAIL' if companion_issue else '✅ PASS'} — no hallucinated companion-arrival"
                  + (f" ({companion_issue})" if companion_issue else ""), flush=True)
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
        if sc.id in ("imag-intimacy", "imag-intimacy-finds-your-across") and first:
            # beat233: imag-intimacy had ZERO dedicated postcheck coverage despite
            # being flagged 6+ beats (216-232) as the source of the most severe
            # uncaught defects in the whole battery. These two checks are report-only
            # (no safe mechanical rewrite exists for either) — a FAIL here means the
            # scene needs a regen or a prompt-engineering pass, logged for that.
            furniture_issue = check_furniture_consistency(first)
            presence_issue = check_presence_continuity(first)
            print(f"\n>>> INTIMACY POSTCHECKS:", flush=True)
            print(f"  {'❌ FAIL' if furniture_issue else '✅ PASS'} — seating furniture consistent"
                  + (f" ({furniture_issue})" if furniture_issue else ""), flush=True)
            print(f"  {'❌ FAIL' if presence_issue else '✅ PASS'} — no presence-continuity break"
                  + (f" ({presence_issue})" if presence_issue else ""), flush=True)
        # Global truncation check (all scenarios): script must end with a sentence
        # terminator. Missing terminator = model hit max_tokens mid-sentence.
        # beat123: found in imag-eagle-wildlife-plural 0812 run — 2737-word script
        # ended with "that doesn" (token-limit truncation, not caught by any prior guard).
        # Fix: trim_truncated_tail() in generator.py; postcheck here detects escapes.
        if first:
            truncated = first.rstrip() and first.rstrip()[-1] not in '.!?"…'
            # beat233: closing-beat gap flagged since beat167, reconfirmed beat232
            # (4/9 scenarios in one battery11 run had no eyes-open/return cue at all).
            # Report-only — no safe mechanical way to append a real closing beat.
            has_closing = check_return_to_room_closing(first)
            print(f"\n>>> GLOBAL POSTCHECKS:", flush=True)
            print(f"  {'❌ FAIL' if truncated else '✅ PASS'} — script ends with sentence terminator (no token-limit truncation)", flush=True)
            print(f"  {'❌ FAIL' if not has_closing else '✅ PASS'} — return-to-room/eyes-open closing beat present", flush=True)
    except Exception as e:
        traceback.print_exc()

print(f"\ntotal {time.time()-t0:.0f}s", flush=True)
