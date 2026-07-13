#!/usr/bin/env python3
"""Targeted verify for companion prompt fixes from beat10.

Checks:
1. comp-grief-anger T1: should name the gap (anger not translating back to sadness/protection)
2. comp-decision-house T3: after redirect should go concrete, not therapy-frame
3. comp-bored-test T3: should hold ennui as ennui, not expand to existential void
4. comp-arc-newparent T6: after explicit redirect should say it plainly

Run with model idle.
"""
import sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from fastapi.testclient import TestClient
import imagination_engine.server as s
from scenario_bank import BANK

c = TestClient(s.app)

SEP = "#" * 70

def hdr(t):
    print(f"\n{SEP}\n# {t}\n{SEP}", flush=True)

def turn(session_id, msg):
    r = c.post("/companion/turn", json={"session_id": session_id, "message": msg}).json()
    return r.get("reply", f"[ERROR: {r}]")

t0 = time.time()

# ============================================================
# comp-grief-anger: check T1 doesn't reframe anger as protection
# ============================================================
hdr("comp-grief-anger T1 — RECEIVE UNEXPECTED FEELING test (beat10 fix)")
print("Target: name the gap ('anger is the part the grief script doesn't have a word for')")
print("Failure: 'anger might be protecting you from pain' (translates back to sadness)")
print()

sid = "verify-grief-anger"
msg = "Since the miscarriage I haven't told anyone how angry I am. Not sad. Angry."
reply = turn(sid, msg)
print(f"[user] {msg}\n[companion] {reply}")
if "protect" in reply.lower() and "pain" in reply.lower():
    print("  ❌ FAIL — still reframing anger as protection from pain")
elif "anger" in reply.lower() and ("script" in reply.lower() or "word for" in reply.lower() or "template" in reply.lower() or "grief" in reply.lower()):
    print("  ✅ PASS — names the gap specifically")
elif "protect" in reply.lower() or "sounds like" in reply.lower():
    print("  ❌ FAIL — therapy-speak reframe or paraphrase opener")
else:
    print("  ⚠️  AMBIGUOUS — read carefully")

# ============================================================
# comp-decision-house T3: after redirect go concrete
# ============================================================
hdr("comp-decision-house T3 — REDIRECT CONCRETE test (beat10 fix)")
print("Target: concrete (deadline/number/risk), NOT meta ('how you feel about risk')")
print("Failure: any version of 'how you feel' or 'identity' or 'childhood' framing after redirect")
print()

sid2 = "verify-decision-house"
for msg in [
    "We can afford the house if nothing goes wrong for five years. My wife says jump. I can't sleep.",
    "Her family did fine taking risks like this. Mine lost everything in 2009.",
    "So it's not about the house. Fine. But the offer is due Friday and 'it's about your childhood' doesn't write the check.",
]:
    reply = turn(sid2, msg)
    print(f"[user] {msg}\n[companion] {reply}\n")

# Check T3 specifically
r3 = c.post("/companion/turn",
            json={"session_id": "verify-dh-check", "message":
                  "So it's not about the house. Fine. But the offer is due Friday and 'it's about your childhood' doesn't write the check."}).json().get("reply", "")
if any(w in r3.lower() for w in ["how you feel", "identity", "childhood", "who you are", "feels like"]):
    print("  ❌ FAIL — still in feelings/identity frame after redirect")
elif any(w in r3.lower() for w in ["friday", "number", "breaks", "income", "afford", "risk", "worst case", "concrete"]):
    print("  ✅ PASS — pivoted to concrete decision frame")
else:
    print("  ⚠️  AMBIGUOUS — read above")

# ============================================================
# comp-bored-test T3: hold ennui, don't expand it
# ============================================================
hdr("comp-bored-test T3 — HOLD ENNUI test")
print("Target: boredom stays boredom ('That's an odd place to be — wanting the wanting back.')")
print("Failure: 'maybe what you're missing...' / existential void / purpose question")
print()

sid3 = "verify-bored"
bored_replies = []
for msg in [
    "Nothing's wrong. I'm just bored out of my mind lately.",
    "Job's fine. Marriage is fine. Everything is fine. That's the problem.",
    "I keep waiting to want something.",
]:
    reply = turn(sid3, msg)
    bored_replies.append(reply)
    print(f"[user] {msg}\n[companion] {reply}\n")

# Check: does any turn manufacture a deeper problem?
fail_patterns = ["sign of something else", "might be hiding", "something else going on",
                 "meaning", "direction where it feels", "looking for", "missing piece",
                 "something more", "what it might mean", "something else"]
fail_found = [p for r in bored_replies for p in fail_patterns if p in r.lower()]
if fail_found:
    print(f"  ❌ FAIL — manufactured deeper problem ({fail_found[0]!r})")
elif any("bored" in r.lower() or "wait" in r.lower() for r in bored_replies):
    print("  ✅ PASS — holds ennui at face value")
else:
    print("  ⚠️  AMBIGUOUS — read above")

# ============================================================
# comp-arc-newparent T6: plain statement when user says 'just say what it is'
# ============================================================
hdr("comp-arc-newparent T6 — JUST SAY WHAT IT IS test")
print("Target: plain statement — 'Six weeks in. You love her and your old life is gone. Both are true.'")
print("Failure: vague reflection / 'your heart has been closed off' / misses the redirect")
print()

sid4 = "verify-newparent"
np_replies = []
for msg in [
    "Baby is 6 weeks old. I love her and I miss my life. Both are true.",
    "Everyone said it would be hard. Nobody said it would be boring AND terrifying at once.",
    "My partner gets to go to work and I hate him for it. He's doing nothing wrong.",
    "I had a whole personality in February.",
    "Today she smiled at me and I cried for an hour. Hormones or truth? Can't tell.",
    "I don't want advice. I want someone to say this is what it is.",
]:
    reply = turn(sid4, msg)
    np_replies.append(reply)
    print(f"[user] {msg}\n[companion] {reply}\n")

# Check T6 (last reply): is it a plain statement or a vague reflection?
t6 = np_replies[-1].lower() if np_replies else ""
vague_fail = ["trying to make sense", "heart has been closed", "sounds like", "feels like",
              "it sounds", "it seems", "perhaps", "maybe", "might be"]
plain_pass = ["love her", "old life", "both are true", "both are", "what it is",
              "this is", "weeks in", "you have", "you love"]
if any(p in t6 for p in vague_fail):
    print(f"  ❌ FAIL T6 — vague reflection after explicit redirect")
elif any(p in t6 for p in plain_pass):
    print(f"  ✅ PASS T6 — plain statement received the redirect")
else:
    print(f"  ⚠️  AMBIGUOUS T6 — read above: {t6[:80]!r}")

print(f"\ntotal {time.time()-t0:.0f}s")
