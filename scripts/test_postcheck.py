#!/usr/bin/env python3
"""Tests for postcheck.py — the degeneration detector.

The DEGENERATE fixture is a real failure: produced by our own model during the
2026-06-09 QC battery (settling protocol, insomnia scenario). The clean opening
is also real model output from the same script — cadence-style repetition that
must NOT trip the detector.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from imagination_engine.postcheck import (
    find_degeneration_start, trim_degenerate_tail, degeneration_report,
    drop_hallucinated_he_eagle)

CLEAN_OPENING = """\
Lie back on your bed and allow yourself to sink down beneath the weight of a cool sheet against you. Your eyelids flutter softly as they close, shielding out light for now. The only noise is raindrops pelleting steadily against tin roofing — each tap easing into a gentle rhythm that swallows up racing thoughts about work.

Feel where you lie: perhaps it's in your bedroom at home or somewhere else peaceful and quiet; either way this moment belongs just to resting here, settling deeper inside yourself with every breath drawn inward through nostrils. Notice the weight of heavy eyelids as they drift shut over eyes.

Start by sinking down into whichever pillow cushions your head lightly; let that support lull away any tension held within neck muscles. Notice how the jaw unclenches gently as it finds release — softening gradually until lips part slightly and rest easy against each other.

Feel toes curl softly up inside socks perhaps or barefoot beneath sheets; let feet find softness in soles pressing down gently into the bed below as the body sinks further still toward a restful state."""

DEGENERATE_TAIL = """\

Let yourself simply drift further still toward that soothing sound now…inhaling deeply drawing cool air through nostrils releasing it again steadily outward gradually allowing mind wander back up briefly perhaps thoughts about work but then returning focus instead solely moment right here inhale exhale slowly gently against sheets beneath skin steadily until only steady patter raindrops remains tapping roof above head along with breath drawn steadily inward out nose once more…

and allow yourself simply drift further still toward that soothing sound now…inhaling deeply drawing cool air through nostrils releasing it again steadily outward gradually allowing mind wander back up briefly perhaps thoughts about work but then returning focus instead solely moment right here inhale exhale slowly gently against sheets beneath skin steadily until only steady patter raindrops remains tapping roof above head along with breath drawn steadily inward out nose once more…

Let yourself simply drift further still toward that soothing sound now…inhaling deeply drawing cool air through nostrils releasing it again steadily outward gradually allowing mind wander back up briefly perhaps thoughts about work but then returning focus instead solely moment right here inhale exhale slowly gently against sheets beneath skin steadily until only steady patter raindrops remains tapping roof above head along with breath drawn steadily inward out nose once more…

Let yourself simply drift further still toward that soothing sound now…inhaling deeply drawing cool air through nostrils releasing it again steadily outward gradually allowing mind wander back up briefly perhaps thoughts about work but then returning focus instead solely moment right here inhale exhale slowly gently against sheets beneath skin steadily until only steady patter raindrops remains tapping roof above head along with breath drawn steadily inward out nose once more…"""

# Cadence: anchor phrases repeat, full sentences don't.
CADENCE = """\
Breathe in slowly. Feel the cool air move through your nose, down into the bottom of your lungs, and let it go. Once more. Breathe in slowly. This time follow the warmth of the air as it leaves, the small heat of it on your upper lip as you exhale. Let go a little further. Your shoulders drop a centimeter you didn't know they were holding. The mattress takes more of your weight now than it did a minute ago. Once more. The night outside the window has its own slow sounds — a car far away, leaves, nothing that needs you. Everything that needs you has been put down for the night."""

fails = 0
def check(name, cond, detail=""):
    global fails
    print(f"  {'PASS' if cond else 'FAIL'}  {name}" + (f" — {detail}" if detail else ""), flush=True)
    if not cond:
        fails += 1

print("clean opening alone:")
check("not flagged", find_degeneration_start(CLEAN_OPENING) is None)

print("cadence-style repetition (anchors, not sentences):")
check("not flagged", find_degeneration_start(CADENCE) is None)

print("real degenerate script (clean opening + loop tail):")
full = CLEAN_OPENING + "\n" + DEGENERATE_TAIL
start = find_degeneration_start(full)
check("flagged", start is not None)
if start is not None:
    check("flag lands in the tail, not the clean part", start > len(CLEAN_OPENING) - 80,
          f"start={start}, clean ends ~{len(CLEAN_OPENING)}")
trimmed, did = trim_degenerate_tail(full)
check("trims", did)
check("keeps the clean opening", trimmed.startswith("Lie back on your bed"))
check("drops the loop", "once more…" not in trimmed.split("\n")[-1])
rep = degeneration_report(full)
print(f"  report: {rep}", flush=True)
check("report sane", rep["degenerate"] and 0.3 < rep["lost_fraction"] < 0.9)

print("trim on already-clean text is a no-op:")
t2, did2 = trim_degenerate_tail(CLEAN_OPENING)
check("no-op", not did2 and t2 == CLEAN_OPENING)

print("beat181 eagle anon-companion escape (drop_hallucinated_he_eagle):")
# True positives — the exact/near escape found in battery11_0825_0231 imag-eagle-
# companion-bird-he (slipped past all 6 eagle postchecks that run).
TP_181 = [
    "You turn your head slightly to see a pair soaring low over what looks like a stream.",
    "Something about their flight tells you these are not alone in the sky this morning.",
    "Eagles that have been on patrol before you arrived will wait for food at lower altitudes now.",
    "Eagles that have been on patrol circle below without you.",
]
for s in TP_181:
    cleaned, dropped = drop_hallucinated_he_eagle(s)
    check(f"TP dropped: {s[:50]!r}...", dropped == 1 and cleaned == "")

# False positives — plausible solo-eagle sentences that must survive untouched.
FP_181 = [
    "You are entirely alone up here, the sky belonging only to you.",
    "The ranger's truck idles on patrol far below, tiny against the valley floor.",
    "You soar past a pairing of clouds low on the horizon.",
]
for s in FP_181:
    cleaned, dropped = drop_hallucinated_he_eagle(s)
    check(f"FP kept: {s[:50]!r}...", dropped == 0 and cleaned == s)

print(f"\n{'ALL PASS' if fails == 0 else f'{fails} FAILURES'}", flush=True)
sys.exit(1 if fails else 0)
