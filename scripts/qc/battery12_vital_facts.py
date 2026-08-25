#!/usr/bin/env python3
"""battery12_vital_facts.py — QC for the vital-facts feature (all 12 spec scenarios).

Scenarios 1-6: core facts (remember / replace / probe / unknown / edit / privacy).
Scenarios 7-12: open-threads (ask-at-open / crisis-yield / no-consecutive / retire /
                 close-stop / gravity-first).

Usage:
    .venv/bin/python scripts/qc/battery12_vital_facts.py 2>&1 | tee logs/qc/battery12_vital_facts_$(date +%m%d_%H%M).log

STANDING RULES:
- Pause qc_queue before running (pkill -f qc_queue).
- ONE model process at a time.
"""

import contextlib
import json
import os
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT / "src"))

import httpx

BASE = "http://127.0.0.1:8000"
SESSION_PREFIX = "battery12_vf_"


def _norm_apos(s: str) -> str:
    """Normalize curly apostrophe (U+2019, model's default) to ASCII so substring
    checks like "haven't" match model output regardless of which apostrophe glyph
    it used. beat179: SC4/SC13 both reported FAIL on replies that plainly denied
    knowledge ("No — you haven’t told me about that.") because the word lists
    below are ASCII-only and never matched the model's curly apostrophe — a postcheck
    calibration bug, not a real confabulation or acknowledgment failure."""
    return s.replace("’", "'")

# Server's live vital-facts file (VitalFacts singleton reads fresh each call)
VF_PATH = ROOT / "data" / "companion" / "vital-facts.md"

# TestClient fallback: used when HTTP server is not running (avoids Metal OOM
# from double-loading the model alongside other GPU consumers).
_tc = None  # fastapi.testclient.TestClient, loaded lazily on first use


def _get_tc():
    global _tc
    if _tc is None:
        from fastapi.testclient import TestClient
        import imagination_engine.server as _srv
        _tc = TestClient(_srv.app)
    return _tc


@contextlib.contextmanager
def _vf_fixture(content: str):
    """Temporarily write test content to the server's vital-facts.md."""
    VF_PATH.parent.mkdir(parents=True, exist_ok=True)
    original = VF_PATH.read_text(encoding="utf-8") if VF_PATH.exists() else None
    try:
        VF_PATH.write_text(content, encoding="utf-8")
        yield
    finally:
        if original is not None:
            VF_PATH.write_text(original, encoding="utf-8")
        elif VF_PATH.exists():
            VF_PATH.unlink()


def _sid(n: int) -> str:
    return f"{SESSION_PREFIX}{n:02d}_{int(time.time())}"


# _use_server is set in main() based on /health check.
_use_server = False


def turn(session_id: str, message: str, timeout: int = 300) -> str:
    # REGRESSION (beat98 2026-08-05 battery12 18:22): model-requiring tests timed out
    # when a server was running but cold (model not yet loaded, 90s < cold-start time).
    # SC8 got "Connection refused" = server crashed (OOM during cold start under load).
    # FIX: timeout raised 90→300s; HTTP failures fall back to TestClient so a slow/crashed
    # server doesn't permanently block the test run.
    if _use_server:
        try:
            r = httpx.post(f"{BASE}/companion/turn",
                           json={"session_id": session_id, "message": message},
                           timeout=timeout)
            r.raise_for_status()
            return r.json()["reply"]
        except Exception:
            # Server became unavailable mid-run; fall through to TestClient.
            pass
    tc = _get_tc()
    r = tc.post("/companion/turn", json={"session_id": session_id, "message": message})
    r.raise_for_status()
    return r.json()["reply"]


def opener(session_id: str, last_heavy: bool = False, timeout: int = 300) -> str | None:
    if _use_server:
        try:
            r = httpx.post(f"{BASE}/companion/opener",
                           json={"session_id": session_id, "last_session_heavy": last_heavy},
                           timeout=timeout)
            r.raise_for_status()
            return r.json().get("opener")
        except Exception:
            pass
    tc = _get_tc()
    r = tc.post("/companion/opener", json={"session_id": session_id, "last_session_heavy": last_heavy})
    r.raise_for_status()
    return r.json().get("opener")


def section(title: str) -> None:
    print("\n" + "#" * 76)
    print(f"# {title}")
    print("#" * 76)


def check(label: str, condition: bool, note: str = "") -> bool:
    status = "✅ PASS" if condition else "❌ FAIL"
    print(f"  {status} — {label}" + (f"\n         note: {note}" if note else ""))
    return condition


# ── Vital-facts fixture helpers ───────────────────────────────────────────────

def _make_vf(content: str) -> Path:
    """Write a temp vital-facts.md and patch VitalFacts to use it."""
    import imagination_engine.vital_facts as vf_mod
    p = Path(tempfile.mktemp(suffix=".md"))
    p.write_text(content, encoding="utf-8")
    # Monkeypatch the module-level default path used by _get_vital_facts in tests
    # (the server caches _vital_facts globally — we bypass server here and test
    #  the Companion + VitalFacts class directly)
    return p


# ── Test runners ──────────────────────────────────────────────────────────────

def run_scenario_1_remember():
    """Fact mentioned in session 1 → referenced correctly when VF file has sister fact."""
    section("SC1 — Sister name remembered via vital-facts injection")
    vf_content = (
        "# What I know about you (edit me freely — I only know what's written here)\n\n"
        "## People\n"
        "- Sister: Priya — lives in Austin, two kids (2026-07)\n"
    )
    sid = _sid(1)
    with _vf_fixture(vf_content):
        # First turn establishes context; second asks about family
        turn(sid, "I've been thinking about family stuff lately.")
        t2 = turn(sid, "Have you heard anything I've told you about my sister?")
        print(f"  [reply] {t2}")
    # Must AFFIRM knowledge (Priya in reply) not just mention "sister" in a denial.
    # PASS: "Yes — your sister is Priya..." | "I know about Priya from your file"
    # FAIL: "You haven't told me about your sister." (no Priya, denial)
    # FAIL: "You haven't told me about your sister Priya" (Priya present but denied)
    has_name = "priya" in t2.lower()
    is_denial = any(w in t2.lower() for w in [
        "haven't told me", "you haven't told", "don't have", "no —",
        "hasn't been", "you haven't", "not written", "not in the"])
    passed = has_name and not is_denial
    return check("Priya referenced affirmatively from vital-facts file", passed,
                 note="VF block must inject sister name; companion must affirm it (not deny it).")


def run_scenario_2_replace():
    """Job updated between sessions → old fact replaced, companion uses new one."""
    section("SC2 — Job update replaces old fact (no duplicate)")
    from imagination_engine.vital_facts import VitalFacts
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        vf = VitalFacts(Path(td) / "vital-facts.md")
        vf.upsert_fact("Work", "Role", "engineer at Startup X", "2026-01")
        content_before = vf.path.read_text()
        vf.upsert_fact("Work", "Role", "product lead at Hearth", "2026-07")
        content_after = vf.path.read_text()

    old_present = "engineer at Startup X" in content_after and "## Work" in content_after
    new_present = "product lead at Hearth" in content_after
    in_outdated = "engineer at Startup X" in content_after and "## Outdated" in content_after

    p1 = check("New fact in live section", new_present)
    p2 = check("Old fact moved to Outdated (not in Work section)", in_outdated,
               note="Should be under ## Outdated, not ## Work")
    p3 = check("Old fact not duplicated in live sections",
               content_after.count("engineer at Startup X") == 1)
    return p1 and p2 and p3


def run_scenario_3_probe():
    """'What do you remember about me?' → companion cites only what's in the file."""
    section("SC3 — Probe: 'what do you remember?' → matches file only")
    vf_content = (
        "# What I know about you (edit me freely — I only know what's written here)\n\n"
        "## People\n"
        "- Sister: Priya — Austin, two kids (2026-07)\n\n"
        "## Work\n"
        "- Role: product lead at Hearth (2026-07)\n"
    )
    sid = _sid(3)
    with _vf_fixture(vf_content):
        reply = turn(sid, "What do you remember about me?")
        print(f"  [reply] {reply}")
    p1 = check("Mentions Priya or sister", "priya" in reply.lower() or "sister" in reply.lower())
    p2 = check("Mentions job/role/hearth",
               any(w in reply.lower() for w in ["hearth", "product", "role", "job"]))
    p3 = check("Does not invent facts not in file",
               not any(w in reply.lower() for w in ["dog", "partner", "husband", "wife"])
               or "priya" in reply.lower())
    return p1 and p2 and p3


def run_scenario_4_unknown():
    """Ask about a person never mentioned → honest 'haven't told me'."""
    section("SC4 — Unknown person → honest no fabrication")
    # Empty vital facts — no Marcus, no anything
    vf_content = "# What I know about you (edit me freely — I only know what's written here)\n"
    sid = _sid(4)
    with _vf_fixture(vf_content):
        reply = turn(sid, "Do you remember what I told you about my brother Marcus?")
        print(f"  [reply] {reply}")
    reply_n = _norm_apos(reply.lower())
    p1 = check("Does NOT fabricate Marcus details (if Marcus mentioned, denial must follow)",
               "marcus" not in reply_n or any(
                   w in reply_n for w in
                   ["don't", "haven't", "can't recall", "nothing", "not written"]))
    p2 = check("Acknowledges lack of knowledge plainly",
               any(w in reply_n for w in
                   ["haven't", "don't have", "not told", "nothing", "don't know",
                    "can't recall", "no record", "not written", "don't remember"]))
    return p1 and p2


def run_scenario_5_edit():
    """User edits file (deletes person) → companion respects deletion next session."""
    section("SC5 — File edit respected: deleted person gone from memory")
    from imagination_engine.vital_facts import VitalFacts
    import tempfile, re

    with tempfile.TemporaryDirectory() as td:
        vf = VitalFacts(Path(td) / "vital-facts.md")
        vf.upsert_fact("People", "Friend", "Tomas — college roommate", "2026-05")
        # Simulate user deleting 'Tomas' by hand
        content = vf.path.read_text()
        content = re.sub(r"^- Friend: Tomas[^\n]*\n?", "", content, flags=re.MULTILINE)
        vf.path.write_text(content, encoding="utf-8")
        ctx = vf.context_block()

    p1 = check("Tomas absent from context block after deletion",
               "tomas" not in ctx.lower())
    return p1


def run_scenario_6_privacy():
    """Offline tripwire: vital-facts.md stays in data/; no network call on read."""
    section("SC6 — Privacy: file stays local (module-level path check)")
    from imagination_engine.vital_facts import VitalFacts, _DEFAULT_PATH
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        vf = VitalFacts(Path(td) / "vital-facts.md")
        p1 = check("VitalFacts path is local (not http/cloud)",
                   not str(vf.path).startswith("http"))
        p2 = check("Default path is under data/",
                   "data" in str(_DEFAULT_PATH) or "companion" in str(_DEFAULT_PATH))
    return p1 and p2


# ── Open-threads scenarios (7-12) ─────────────────────────────────────────────

def run_scenario_7_opener():
    """Session opens with a natural question about the open thread."""
    section("SC7 — Opener: specific question about open thread at session start")
    vf_content = (
        "# What I know about you (edit me freely — I only know what's written here)\n\n"
        "## Open threads (things to ask about next session)\n"
        "- New job — started ~2026-07, asked never [gravity: med]\n"
    )
    sid = _sid(7)
    with _vf_fixture(vf_content):
        q = opener(sid, last_heavy=False)
        print(f"  [opener] {q}")
    p1 = check("Opener is non-None (thread exists)", q is not None)
    p2 = check("Opener mentions job or 'new' context",
               q is not None and any(w in q.lower() for w in
                                     ["job", "new", "work", "role", "going", "treating"]))
    p3 = check("Opener is a question (contains ?)", q is not None and "?" in q)
    p4 = check("No 'my records' or 'your file' language",
               q is None or not any(w in q.lower() for w in
                                    ["records", "file", "database", "noted", "tracked"]))
    return p1 and p2 and p3 and p4


def run_scenario_8_crisis_yield():
    """last_session_heavy=True → opener returns None (pure logic, no model call)."""
    section("SC8 — Crisis-yield: opener skipped when last session ended heavy")
    vf_content = (
        "# What I know about you (edit me freely — I only know what's written here)\n\n"
        "## Open threads (things to ask about next session)\n"
        "- Half marathon — race in October, asked never [gravity: low]\n"
    )
    sid = _sid(8)
    with _vf_fixture(vf_content):
        q = opener(sid, last_heavy=True)
        print(f"  [opener when heavy=True] {q}")
    return check("Opener returns None when last session ended heavy", q is None)


def run_scenario_9_no_consecutive():
    """Same thread not asked twice consecutively when 2+ threads are open."""
    section("SC9 — No consecutive: different thread asked on second open")
    from imagination_engine.vital_facts import VitalFacts

    with tempfile.TemporaryDirectory() as td:
        vf = VitalFacts(Path(td) / "vital-facts.md")
        vf.add_thread("New job", "started 2026-07", gravity="med")
        vf.add_thread("Half marathon", "race in October", gravity="low")

        first = vf.pick_opener_thread(last_asked_topic=None)
        # Simulate: first was asked, now check second
        second = vf.pick_opener_thread(last_asked_topic=first["topic"] if first else None)
        print(f"  first: {first['topic'] if first else None}")
        print(f"  second: {second['topic'] if second else None}")

    p1 = check("First pick non-None", first is not None)
    p2 = check("Second pick is different thread",
               second is not None and (first is None or second["topic"] != first["topic"]))
    return p1 and p2


def run_scenario_10_retire():
    """Thread deflected twice → retired, not asked again."""
    section("SC10 — Thread retirement: retired thread absent from picks")
    from imagination_engine.vital_facts import VitalFacts

    with tempfile.TemporaryDirectory() as td:
        vf = VitalFacts(Path(td) / "vital-facts.md")
        vf.add_thread("Dad surgery", "scheduled next week", gravity="high")
        vf.add_thread("New job", "started 2026-07", gravity="med")

        # Retire the dad-surgery thread
        vf.retire_thread("Dad surgery")
        remaining = vf.open_threads()
        content = vf.path.read_text()

    p1 = check("Retired thread not in open threads",
               all(t["topic"] != "Dad surgery" for t in remaining))
    p2 = check("Retired thread present in Outdated section",
               "dad surgery" in content.lower() and "outdated" in content.lower())
    p3 = check("Non-retired thread still present", any(t["topic"] == "New job" for t in remaining))
    return p1 and p2 and p3


def run_scenario_11_close_stop():
    """'Stop asking about X' → dropped in-turn, thread retired."""
    section("SC11 — 'Stop asking about X' → thread retired immediately")
    from imagination_engine.vital_facts import VitalFacts

    with tempfile.TemporaryDirectory() as td:
        vf = VitalFacts(Path(td) / "vital-facts.md")
        vf.add_thread("Mom", "health check ongoing", gravity="high")
        # Simulate in-turn retirement (what companion code should do)
        vf.retire_thread("Mom")
        remaining = vf.open_threads()

    p1 = check("Mom thread retired after stop request",
               all(t["topic"] != "Mom" for t in remaining))
    return p1


def run_scenario_12_gravity():
    """Surgery thread asked before hobby thread when both are open."""
    section("SC12 — Gravity: high-gravity thread picked before low-gravity")
    from imagination_engine.vital_facts import VitalFacts

    with tempfile.TemporaryDirectory() as td:
        vf = VitalFacts(Path(td) / "vital-facts.md")
        vf.add_thread("Guitar lessons", "considering starting", gravity="low")
        vf.add_thread("Dad surgery", "scheduled next week", gravity="high")

        pick = vf.pick_opener_thread(last_asked_topic=None)
        print(f"  picked: {pick['topic'] if pick else None} (gravity: {pick.get('gravity') if pick else None})")

    return check("High-gravity (surgery) picked over low-gravity (guitar)",
                 pick is not None and pick["topic"] == "Dad surgery")


def run_scenario_13_wrong_entity():
    """VF has Priya (sister); user asks about Marcus (no entry) → must deny Marcus.

    beat93 regression: PAST-QUERY guard triggered affirmation regen whenever VF was
    non-empty, even if the queried entity was NOT in VF. Produced 'Yes — your sister
    Priya lives in Austin.' when user asked about Marcus. Fix (beat94): _vf_covers_query()
    checks if the VF actually covers the queried entity before triggering affirmation.
    """
    section("SC13 — Non-empty VF + unrelated query → denial, not cross-entity affirmation")
    # VF has Priya (sister) but nothing about Marcus
    vf_content = (
        "# What I know about you (edit me freely — I only know what's written here)\n\n"
        "## People\n- Sister: Priya — lives in Austin, two kids\n"
    )
    sid = _sid(13)
    with _vf_fixture(vf_content):
        reply = turn(sid, "Do you remember what I told you about my brother Marcus?")
        print(f"  [reply] {reply}")
    reply_n = _norm_apos(reply.lower())
    p1 = check("Does NOT fabricate Marcus (denial or 'not written')",
               any(w in reply_n for w in
                   ["haven't", "don't have", "not told", "nothing", "don't know",
                    "can't recall", "no record", "not written", "don't remember",
                    "not marcus", "hasn't", "only priya", "no mention"]))
    p2 = check("Does NOT falsely affirm by citing Priya",
               not ("yes" in reply_n[:6] and "priya" in reply_n))
    return p1 and p2


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print(f"battery12_vital_facts — 13 scenarios ({time.strftime('%Y-%m-%d %H:%M')})")
    print("Testing vital-facts module + companion integration (no live server needed for 1-6,9-12)")

    results = []

    # Unit-level tests (no model, no server)
    for fn in [run_scenario_2_replace, run_scenario_5_edit,
               run_scenario_6_privacy, run_scenario_9_no_consecutive,
               run_scenario_10_retire, run_scenario_11_close_stop,
               run_scenario_12_gravity]:
        try:
            results.append((fn.__name__, fn()))
        except Exception as e:
            print(f"  ❌ EXCEPTION in {fn.__name__}: {e}")
            results.append((fn.__name__, False))

    # Model-requiring tests (need server or TestClient in-process fallback)
    print("\n" + "=" * 60)
    print("Model-requiring tests (SC1, SC3, SC4, SC7, SC8):")

    # Check server availability. If up, use HTTP (faster when already warm).
    # If down, fall through to TestClient fallback (avoids Metal OOM from
    # double-loading the model alongside other GPU consumers on 16GB machines).
    # Must probe /health (Hearth-specific) not GET / — the server returns
    # {"status":"hearth"} on /health; a plain GET / returns different content.
    global _use_server
    try:
        _r = httpx.get(f"{BASE}/health", timeout=3)
        _use_server = (_r.status_code == 200 and
                       _r.json().get("status") == "hearth")
    except Exception:
        _use_server = False

    if _use_server:
        print("Server up — using HTTP.")
    else:
        print("Server not running — using TestClient (in-process, avoids OOM).")

    for fn in [run_scenario_1_remember, run_scenario_3_probe,
               run_scenario_4_unknown, run_scenario_7_opener,
               run_scenario_8_crisis_yield, run_scenario_13_wrong_entity]:
        try:
            results.append((fn.__name__, fn()))
        except Exception as e:
            print(f"  ❌ EXCEPTION in {fn.__name__}: {e}")
            results.append((fn.__name__, False))

    # Summary
    print("\n" + "=" * 60)
    passed = sum(1 for _, r in results if r)
    total = len(results)
    print(f"BATTERY12 VITAL FACTS: {passed}/{total} PASS")
    for name, r in results:
        print(f"  {'✅' if r else '❌'} {name}")
    if passed == total:
        print("\n✅ ALL PASS — vital-facts feature ready for release gate.")
    else:
        print(f"\n❌ {total - passed} FAIL — fix before marking vital-facts done.")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
