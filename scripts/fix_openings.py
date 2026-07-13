#!/usr/bin/env python3
"""Give every gold candidate its OWN opening. All scripts had shared the identical
settle — the exact template-collapse fingerprint the diversity filter keys on.
This replaces the shared settle with a unique doorway per script (asserted distinct),
rewrites each candidate JSON, the staged gold jsonl, and INDEX.md.
"""
import json, sys
from pathlib import Path

CAND = Path.home()/"Downloads/hearth-corpus/A-imagination/_candidates"
GOLD = Path.home()/"Downloads/hearth-corpus/A-imagination/A_gold_candidates.jsonl"
SHARED = ("Close your eyes, and let yourself arrive. …… One slow breath in through your nose … "
          "and a longer one out through your mouth. … Let the chair take your weight. … "
          "One more breath, and set down the day you were just in. ……")

# Distinct doorways — first words deliberately varied so even the first 40 chars differ.
OPENINGS = [
"Let your eyes fall closed, and let the day go quiet behind them. … A slow breath in … and a slower one out. … Let the chair hold all of your weight now. ……",
"Close your eyes. … For this little while, there is nowhere you have to be. … Breathe in, easy … and out, long. … Feel your shoulders come down. ……",
"Settle back, and let your eyes close. … Feel the floor beneath you, steady and sure. … One deep breath, and let the day begin to loosen its grip. ……",
"Soften your eyes closed. … Notice the weight of your body where it rests, and let it grow heavy. … Breathe out, slow, and simply land here. ……",
"Allow your eyes to close, gently. … Let the sounds of the room drift to the edges. … Draw one long breath, and let it carry the day off as it leaves. ……",
"Ease back into where you're sitting and let your eyes close. … Unclench your jaw. … Let a slow breath move through you and take the hurry with it. ……",
"When you're ready, let your eyes drift shut. … Feel the chair under you, the floor under that. … Breathe in slowly … hold a beat … and let it all go. ……",
"Take a moment, and let your eyes close. … There's nothing to do here but arrive. … One easy breath in, one long breath out, and you're here. ……",
"Let yourself land. … Eyes closed, shoulders soft, hands resting open. … Breathe in through your nose … and sigh it out … and feel the day step back. ……",
"Rest your eyes closed, and let the room fall away a little. … Feel your breath where it enters and leaves. … Let each out-breath set you down a half-inch deeper. ……",
"Sink back, and close your eyes. … Let your face go slack — forehead, jaw, the space between your brows. … Breathe slow, and let yourself settle. ……",
"Lower your eyes closed and let everything slow. … Feel the steady in and out of your own breath. … There's time. Let your body believe that for a moment. ……",
"Let the day fall away as your eyes close. … Feel how the chair holds you, completely. … One breath in, drawn deep … and a long breath out, drawn longer. ……",
"Draw a slow breath, and on the out-breath, let your eyes close. … Let the floor take your feet, the chair take your back. … Soften, and stay a while. ……",
"Find a little stillness, and let your eyes close into it. … Notice the weight of your hands, your legs, your head. … Breathe, and let the stillness widen. ……",
"Close your eyes and let your breathing find its own slow pace. … No need to deepen it; just follow it, in and out. … Let your shoulders drop on each exhale. ……",
"Let your eyelids grow heavy and close. … Feel where your body meets the chair, warm and supported. … Take a long breath, and let the day's noise quiet down. ……",
"Gently shut your eyes. … Let the muscles of your face, your neck, your shoulders, all let go at once. … Breathe out slowly, and arrive where you are. ……",
"Let your eyes close, and your attention turn inward. … Feel your breath rising and falling, easy and unforced. … With each one, let a little more of the day go. ……",
"Begin by letting your eyes fall shut and your weight settle down. … Feel the ground holding you up. … One slow breath, and let your whole body grow a shade heavier. ……",
"Close your eyes, and let the room go soft around you. … Feel your feet, your seat, your hands — all held, all at rest. … Breathe in, and let the breath out take the tension. ……",
"Let your eyes drift closed like a slow curtain. … Notice the quiet underneath the sounds. … Take an easy breath, and let your jaw and your hands unclench. ……",
"Settle in, eyes closed, and let yourself stop. … Feel the breath at the tip of your nose, cool going in, warm coming out. … Let each exhale loosen you further. ……",
"Let your eyes close and your shoulders fall. … There is nowhere to rush to from here. … Breathe slowly, and feel the chair take more of your weight with each breath. ……",
"Close your eyes, and feel the day set itself down. … Let your breath go long and unhurried. … Notice your body softening, piece by piece, into where it rests. ……",
"Let your eyelids lower and close. … Feel the steady weight of yourself, held and supported. … Draw a breath all the way down, and let it sigh all the way out. ……",
"Eyes closed now, and let the world step back a pace. … Feel your breath move, slow and sure. … Let your forehead smooth, your jaw loosen, your hands fall open. ……",
"Let your eyes close softly, and let the day exhale out of you. … Feel the floor beneath your feet. … One slow breath in, and a longer, looser breath out. ……",
"Close your eyes and let yourself grow quiet. … Feel the rise and the fall of your own chest. … With each fall, let a little more weight pour down into the chair. ……",
"Let your eyes fall shut and your breathing slow on its own. … Feel where you are held — back, seat, feet. … Take a long breath, and set the day gently aside. ……",
"Let your gaze drop and your eyes close. … Feel your body get heavier, more here. … Breathe in slowly through your nose, and let the out-breath be twice as long. ……",
"Close your eyes, and let the next breath be slower than the last. … And the one after that, slower still. … Let your shoulders, your hands, your face all let go. ……",
"Let your eyes close and the day grow distant. … Notice how the chair carries you, how little you have to do. … Breathe, easy and low, and simply be here a while. ……",
"Soften your gaze, then close your eyes entirely. … Let the breath settle into a slow, even rhythm. … With each out-breath, let yourself sink a little deeper down. ……",
"Let your eyes close, and let the quiet in. … Feel your weight, your warmth, your slow breath. … There's nothing to reach for now — just let yourself arrive. ……",
"Close your eyes, and take the first real breath of stillness. … Feel it fill you, and feel it leave. … Let the floor hold your feet and the chair hold the rest. ……",
"Let your eyelids close and your breathing lengthen. … Feel the small, steady movement of your own ribs. … Let the day's grip on your shoulders simply loosen and fall. ……",
"Ease your eyes shut, and let yourself go still. … Feel the breath at your nostrils, the weight in your seat. … Each slow exhale lets a little more of the world go quiet. ……",
"Let your eyes close, unhurried. … Feel your whole body supported, nothing to hold up. … Draw a breath down low, and let it out slow, and let yourself land. ……",
"Close your eyes and let the stillness find you. … Notice your breath without changing it, just riding it. … Let each out-breath carry off a little more of the day. ……",
]

cands = sorted(CAND.glob("*.json"))
assert len(OPENINGS) >= len(cands), f"need >= {len(cands)} openings, have {len(OPENINGS)}"
seen_open = set()
recs = []
idx = ["# Gold candidate scripts — VIVID, prompt-matched, UNIQUE openings\n"]
for i, f in enumerate(cands):
    d = json.loads(f.read_text())
    op = OPENINGS[i]
    head = op[:40]
    assert head not in seen_open, f"duplicate opening head at {f.name}"
    seen_open.add(head)
    if d["text"].startswith(SHARED):
        d["text"] = op + d["text"][len(SHARED):]
    f.write_text(json.dumps(d, ensure_ascii=False, indent=1))
    recs.append({"text": d["text"], "prompt": d.get("prompt",""), "src": f"candidates/{d['id']}", "tier":"gold"})
    idx.append(f"\n## {d['id']}  ·  {len(d['text'].split())} words\n\n**Prompt:** _{d.get('prompt','')}_\n\n{d['text']}\n")

GOLD.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in recs)+"\n")
(CAND/"INDEX.md").write_text("\n".join(idx))
distinct = len({r["text"][:40] for r in recs})
print(f"rewrote {len(recs)} candidates with unique openings")
print(f"distinct openings now: {distinct}/{len(recs)}  (was 1/{len(recs)})")
