#!/usr/bin/env python3
"""Comparative read: n170v2 (GOLD-ADAPTER-0708-1407-n170) vs n154 (current live).

n170v2 is a SECOND training run on 170 gold scripts. First n170 run = cliff-edge eagle.
This run produced a dramatically better probe:
  Eagle: "You are an eagle, soaring above the mountains. Your wings are outstretched..."
  NO eyes-closed, NO chair, fully in-scene from word 1. Best probe yet.

Protocol:
- Run 5 scenarios under n170v2 (adapters.n170v2/)
- Compare opening lines to n154 (current live adapter)
- Score each: CHAIR (fail) vs IN-SCENE (win)
- 3/5 clear wins vs n154 → promote n170v2; else keep n154
"""
import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from fastapi.testclient import TestClient
import imagination_engine.server as s
from imagination_engine.config import config as cfg
from imagination_engine.generator import generate_session
from scenario_bank import BANK

N170_ADAPTER = str(Path(__file__).resolve().parents[2] / "data" / "model" / "adapters.n170v2")

# 5 scenarios to test, in order of importance for this comparison
TEST_SCENARIOS = [
    "imag-embodiment-eagle",   # CASE A in-motion — pure chair-test
    "imag-active-scene",       # CASE A in-motion (running) — with prompt override
    "imag-intimacy",           # CASE B sedentary — should be unchanged
    "imag-grief-pet",          # CASE C walk — partial motion
    "imag-deposition",         # CASE C rehearsal — NOT active-body
]


def find_scenario(sid: str):
    for sc in BANK:
        if sc.id == sid:
            return sc
    raise ValueError(f"scenario {sid!r} not found in bank")


def run_scenario(c, sc):
    """Run one scenario and return the opening 300 chars of the generated script."""
    sid = c.post(f"/intake/start?protocol={sc.protocol}").json()["session_id"]
    ready = False
    for msg in sc.turns:
        r = c.post("/intake/turn", json={"session_id": sid, "message": msg}).json()
        if r.get("ready"):
            ready = True
            break
    if not ready:
        r = c.post("/intake/turn",
                   json={"session_id": sid, "message": "I'm ready — begin."}).json()
        ready = bool(r.get("ready"))
    if not ready:
        return "(never reached ready state)"
    session = s.get_intake_manager().get(sid)
    script = generate_session(s.get_engine(), session.messages, protocol=sc.protocol)
    return script[:300] if script else "(no script generated)"


def main():
    print(f"\n{'='*70}")
    print("n170v2 COMPARATIVE READ — active-body chair-opening test")
    print(f"Adapter: {N170_ADAPTER}")
    print(f"{'='*70}\n")

    # Override the adapter path to n170 (frozen dataclass — bypass with object.__setattr__)
    original_adapter = cfg.adapter_path
    object.__setattr__(cfg, 'adapter_path', N170_ADAPTER)

    # Force reload of the engine (clear any cached instance)
    if hasattr(s, "_engine"):
        s._engine = None  # type: ignore

    c = TestClient(s.app)

    wins = 0
    for sc_id in TEST_SCENARIOS:
        sc = find_scenario(sc_id)
        print(f"\n{'#'*70}")
        print(f"# {sc_id}")
        print(f"# Note: {sc.note[:80]}")
        print(f"{'#'*70}")
        t0 = time.time()
        opening = run_scenario(c, sc)
        elapsed = time.time() - t0
        print(f"\n[OPENING — first 300 chars] ({elapsed:.0f}s):")
        print(opening)

        # Chair-opening check.
        # NOTE (beat11 lesson): in_scene_words captures active-body anchors only.
        # For sedentary scenarios, "no chair + setting anchor" is also an IN-SCENE win.
        # The human read matters more than this automated score.
        chair_words = ["eyes are closed and you can feel the chair", "chair beneath you",
                       "feel the chair", "hands rest at your side", "hands rest in your lap",
                       "your eyes are closed. your hands", "the chair you",
                       "supporting your weight"]
        # Active-body in-scene markers
        in_scene_active = ["you feel the wind", "you are an eagle", "you are soaring",
                           "the track", "the pavement", "your feet hit", "the effort in",
                           "your lungs", "you feel the warm sun on your back",
                           "spread your wings", "the cliff", "soaring",
                           "the run", "the race", "each breath", "already running",
                           "beat of your wings", "with each step", "your stride"]
        # Sedentary in-scene markers (setting anchors that mean we're IN the scene)
        in_scene_sedentary = ["you are standing", "you're in the", "your feet bare",
                              "the smell of", "the scent of", "the sound of",
                              "fills the room", "at the start of", "around the reservoir",
                              "beside you on", "your hands are", "clenched in",
                              "you are at", "you sit ", "you walk ", "you stand "]

        opening_lc = opening.lower()
        chair_hit = any(w in opening_lc for w in chair_words)
        active_hit = any(w in opening_lc for w in in_scene_active)
        sedentary_hit = any(w in opening_lc for w in in_scene_sedentary)
        scene_hit = active_hit or sedentary_hit

        if scene_hit and not chair_hit:
            verdict = "✅ IN-SCENE (no chair)"
            wins += 1
        elif chair_hit:
            verdict = "❌ CHAIR-OPENING (training artifact)"
        else:
            # Eyes-closed without chair + without explicit setting anchor → AMBIGUOUS
            # Still likely in-scene; read the opening. Compare to n115 for final call.
            verdict = "⚠️  AMBIGUOUS — read opening; if no chair + setting anchor → probable win"
        print(f"\n[VERDICT]: {verdict}\n")

    print(f"\n{'='*70}")
    print(f"SCORE: {wins}/5 clear IN-SCENE wins")
    if wins >= 3:
        print("RECOMMENDATION: PROMOTE n170v2 (≥3/5 wins)")
    else:
        print(f"RECOMMENDATION: HOLD — n170v2 only won {wins}/5")
    print("Compare these openings to n115 battery11 run for final verdict.")
    print(f"{'='*70}\n")

    # Restore adapter
    object.__setattr__(cfg, 'adapter_path', original_adapter)
    if hasattr(s, "_engine"):
        s._engine = None  # type: ignore


if __name__ == "__main__":
    main()
