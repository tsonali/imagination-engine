#!/usr/bin/env python3
"""Targeted verification: the 3 generator.py defects fixed in beat 3.

- imag-deposition: check OPEN labels don't appear in output (Move 1/2/3, Utilization, etc.)
- imag-mri: check scene is THE TUBE, not a relocated cozy room
- imag-mid-switch: check alert-calm register (no sleep language) + no verbatim repeat

Uses the same API pattern as battery11 (intake/start → intake/turn → generate_session).
Run after compare_adapters.py frees the model.
PYTHONPATH=src python scripts/qc/verify_generator_fixes.py
"""
import re, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from fastapi.testclient import TestClient
import imagination_engine.server as s
from imagination_engine.generator import generate_session
from imagination_engine.postcheck import phrase_repeat_count

c = TestClient(s.app)


def hdr(t):
    print("\n" + "=" * 72 + f"\n# {t}\n" + "=" * 72, flush=True)


def run_scenario(turns, protocol="immersion"):
    """Run intake + generate_session. Returns (script, None) or (None, error_msg)."""
    sid = c.post(f"/intake/start?protocol={protocol}").json()["session_id"]
    ready = False
    for msg in turns:
        r = c.post("/intake/turn", json={"session_id": sid, "message": msg}).json()
        print(f"[user] {msg}\n[engine] {r.get('response', '')}", flush=True)
        if r.get("ready"):
            ready = True
            break
    if not ready:
        r = c.post("/intake/turn", json={"session_id": sid, "message": "I'm ready — begin."}).json()
        ready = bool(r.get("ready"))
    if not ready:
        return None, "INTAKE NEVER READY"
    session_obj = s.get_intake_manager().get(sid)
    t0 = time.time()
    script = generate_session(s.get_engine(), session_obj.messages, protocol=protocol)
    print(f"\n--- SCRIPT ({len(script.split())} words, {time.time()-t0:.0f}s) ---", flush=True)
    print(script[:3000], flush=True)
    if len(script) > 3000:
        print(f"... [{len(script.split())-600} more words]", flush=True)
    return script, None


# ── imag-deposition: label leakage fix ─────────────────────────────────────
hdr("imag-deposition — OPEN label leakage fix")
print("CHECK: 'MOVE 1', 'MOVE 2', 'MOVE 3', 'UTILIZATION', 'SENSORY ANCHOR' must NOT appear")
deposition_script, err = run_scenario([
    "I'm being deposed next month in a lawsuit against my old employer. Their lawyer will try to rattle me. I want to rehearse staying flat and factual",
    "the conference room, the court reporter typing, their lawyer smiling like we're friends. I answer only what was asked and then I stop talking",
], protocol="immersion")
if err:
    print(f"\n  !! {err}")
elif deposition_script:
    leak_patterns = ["MOVE 1", "MOVE 2", "MOVE 3", "UTILIZATION", "SINGLE-POINT SENSORY ANCHOR", "HARD CUT INTO THE SCENE"]
    leaks = [p for p in leak_patterns if p in deposition_script.upper()]
    if leaks:
        print(f"\n  !! FAIL — labels still leaking: {leaks}")
    else:
        print(f"\n  ✓ PASS — no move labels in output")


# ── imag-mri: scene relocation fix ─────────────────────────────────────────
hdr("imag-mri — scene must be THE TUBE, not a relocated room")
print("CHECK: script must mention tube/bore/scanner/narrow, NOT relocate user to cozy/cushioned/stool/room")
mri_script, err = run_scenario([
    "I have an MRI Friday and I'm claustrophobic. 40 minutes in the tube. I want to practice being okay in a narrow space",
    "I want the machine sounds to become something else. Drums maybe. Something with a reason",
    "I'm ready",
], protocol="immersion")
if err:
    print(f"\n  !! {err}")
elif mri_script:
    in_tube = any(w in mri_script.lower() for w in ["tube", "bore", "scanner", "narrow space", "mri", "claus"])
    relocated = any(w in mri_script.lower() for w in ["cozy room", "cushioned stool", "music studio", "soft lighting", "warm room"])
    if in_tube and not relocated:
        print(f"\n  ✓ PASS — scene in tube, no relocation")
    elif relocated:
        print(f"\n  !! FAIL — user relocated away from tube")
    elif not in_tube:
        print(f"\n  !! WARN — no tube reference found; check script manually")


# ── imag-mid-switch: alert-calm register + no repeat ───────────────────────
hdr("imag-mid-switch — ALERT-CALM: no sleep language, no verbatim repeat")
print("CHECK: no 'drift to sleep/let your eyes grow heavy/fade'; final line must orient to alertness")
midswitch_script, err = run_scenario([
    "help me wind down for sleep",
    "actually no — not sleep. I have to be UP in an hour for a night shift. I need calm but awake",
    "yes, alert-calm. begin",
], protocol="settling")
if err:
    print(f"\n  !! {err}")
elif midswitch_script:
    sleep_phrases = ["let your eyes grow heavy", "drift toward sleep", "drift to sleep",
                     "fade toward rest", "no need to think", "drift off", "fall asleep",
                     "let go and sleep", "slip into rest"]
    alert_markers = ["awake", "alert", "ready", "grounded", "clear", "present", "night shift"]
    sleep_hits = [p for p in sleep_phrases if p in midswitch_script.lower()]
    alert_hits = [m for m in alert_markers if m in midswitch_script.lower()]
    n_rep = phrase_repeat_count(midswitch_script)
    if sleep_hits:
        print(f"\n  !! FAIL — sleep language found: {sleep_hits}")
    else:
        print(f"\n  ✓ PASS — no sleep language")
    if alert_hits:
        print(f"  ✓ alert markers present: {alert_hits}")
    else:
        print(f"  !! WARN — no alert markers found; script may still be lullaby")
    if n_rep == 0:
        print(f"  ✓ PASS — phrase repeat count: 0")
    else:
        print(f"  !! phrase repeat count: {n_rep} (should be 0 after repair)")

print(f"\n\nDone. Check output above for PASS/FAIL on each fix.")
