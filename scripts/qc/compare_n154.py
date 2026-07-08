#!/usr/bin/env python3
"""Comparative read: n154 vs n115 on active-body and eagle scenarios.

n154 is the FIRST adapter trained with the build_training_data.py pipeline fix:
- 154 gold scripts (vs 100 old settling-intro scripts for n115)
- 34.4% in-media-res training data (new {intake,script} format)
- Expected improvement: reduced chair-opening bias on active-body scenes

Focus questions:
1. Does any of the 5 prompts NOT open with 'eyes closed, body in chair'?
2. Does the eagle/active-runner scenario open in-scene vs chair?

Protocol:
- Run 5 scenarios under n154
- Compare opening lines to n115 runs (from battery11 running now or logs)
- Score each: CHAIR (training artifact) vs IN-SCENE (target)
- 3/5 clear wins → promote; else keep n115
"""
import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from fastapi.testclient import TestClient
import imagination_engine.server as s
from imagination_engine.config import cfg
from scenario_bank import BANK

N154_ADAPTER = str(Path(__file__).resolve().parents[2] / "data" / "model" / "adapters.n154")

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
    """Run one scenario and return the opening lines of the generated script."""
    sid = c.post(f"/intake/start?protocol={sc.protocol}").json()["session_id"]
    for msg in sc.turns:
        r = c.post("/intake/turn", json={"session_id": sid, "message": msg}).json()
        if r.get("ready"):
            # generate
            gen_r = c.post("/generate", json={"session_id": sid}).json()
            script = gen_r.get("script", "")
            # Return first 200 chars of opening
            return script[:300] if script else "(no script generated)"
    return "(never reached ready state)"

def main():
    print(f"\n{'='*70}")
    print("n154 COMPARATIVE READ — active-body chair-opening test")
    print(f"Adapter: {N154_ADAPTER}")
    print(f"{'='*70}\n")

    # Override the adapter path to n154
    original_adapter = cfg.adapter_path
    cfg.adapter_path = N154_ADAPTER

    # Force reload of the engine (clear any cached instance)
    import imagination_engine.server as srv
    if hasattr(srv, "_engine"):
        srv._engine = None  # type: ignore

    c = TestClient(s.app)

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

        # Chair-opening check
        chair_words = ["eyes are closed and you can feel the chair", "chair beneath you",
                       "feel the chair", "hands rest at your side", "hands rest in your lap",
                       "your eyes are closed. your hands"]
        in_scene_words = ["you feel the wind", "you are an eagle", "you are soaring",
                          "the track", "the pavement", "your feet hit", "the effort in",
                          "your lungs", "you feel the warm sun on your back"]

        opening_lc = opening.lower()
        chair_hit = any(w in opening_lc for w in chair_words)
        scene_hit = any(w in opening_lc for w in in_scene_words)

        if scene_hit and not chair_hit:
            verdict = "✅ IN-SCENE (no chair)"
        elif chair_hit:
            verdict = "❌ CHAIR-OPENING (training artifact)"
        else:
            verdict = "⚠️  AMBIGUOUS"
        print(f"\n[VERDICT]: {verdict}\n")

    # Restore adapter
    cfg.adapter_path = original_adapter
    print(f"\n{'='*70}")
    print("Done. Compare these openings to n115 battery11 run for verdict.")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    main()
