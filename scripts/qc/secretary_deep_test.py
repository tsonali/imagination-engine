#!/usr/bin/env python3
"""Secretary (Family B) deep use-case test.
Tests all five use-case categories from docs/qc/use-cases.md like a hostile AI professional.
Run after battery10_registers for a broader signal.
"""
import re, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fastapi.testclient import TestClient
import imagination_engine.server as s

c = TestClient(s.app)
t0 = time.time()

def hdr(t): print(f"\n{'#'*76}\n# {t}\n{'#'*76}", flush=True)

def run(task, text, instruction="", tone=""):
    r = c.post("/utility/run", json={
        "task": task, "text": text,
        "instruction": instruction, "tone": tone
    })
    out = r.text if hasattr(r, 'text') else r.content.decode()
    return out.strip()

def check(label, output, must_contain=None, must_not_contain=None, max_words=None):
    ok = True
    if must_contain:
        for m in must_contain:
            if m.lower() not in output.lower():
                print(f"  FAIL [must_contain]: {repr(m)} not found", flush=True)
                ok = False
    if must_not_contain:
        for m in must_not_contain:
            if m.lower() in output.lower():
                print(f"  FAIL [must_not_contain]: {repr(m)} found", flush=True)
                ok = False
    if max_words:
        wc = len(output.split())
        if wc > max_words:
            print(f"  WARN [length]: {wc} words (max {max_words})", flush=True)
    if ok:
        print(f"  floors: CLEAN", flush=True)
    return ok


# ─────────────────────────────────────────────────────────────────────────────
# USE CASE 1: Meeting notes → clean minutes
# ─────────────────────────────────────────────────────────────────────────────
hdr("UC1: Meeting notes → clean minutes [names/dates lossless, nothing invented]")
MEETING_NOTES = """
Product sync — March 14 2026
Attendees: Priya (PM), Deshawn (Eng lead), Camille (Design)

Priya: Q2 OKRs need to be locked by end of month.
Deshawn: Backend migration still 3 weeks out, need to push auth deadline to April 7.
Camille: Redesign mockups ready for review. Needs Priya sign-off by March 20.
Priya: Sign-off confirmed for March 20. Deshawn please add the April 7 date to the tracking doc.
Camille: Will send updated assets by March 18.
Action: Deshawn updates tracking doc with new auth deadline April 7.
Action: Camille sends design assets by March 18.
Action: Priya reviews mockups by March 20.
""".strip()
out = run("organize", MEETING_NOTES, instruction="Format as clean meeting minutes with action items clearly labeled")
print(out)
print()
check("meeting-minutes",
      out,
      must_contain=["March 14", "Priya", "Deshawn", "Camille", "April 7", "March 18", "March 20"],
      must_not_contain=["[error"])


# ─────────────────────────────────────────────────────────────────────────────
# USE CASE 2: Messy braindump → organized doc (lossless organize contract)
# ─────────────────────────────────────────────────────────────────────────────
hdr("UC2: Messy braindump → organized doc [lossless, no invented facts]")
BRAINDUMP = """
ok so the thing is i think the pricing is wrong but also the messaging is wrong.
like we're charging 49 a month but our competitor is 29 and we keep losing deals
because of it. but also people who DO pay love it and the NPS is like 72 which is insane.
the other thing is the enterprise tier is confusing — nobody knows what they get.
oh and also i had a call with someone from fintech and they said they'd pay 200/mo
for SOC2 compliance. we don't have SOC2. i dont know if that's worth pursuing.
messaging: we say "the best tool" but we dont say best at what. need to sharpen.
""".strip()
out = run("organize", BRAINDUMP)
print(out)
print()
check("braindump-org",
      out,
      must_contain=["49", "29", "72", "200", "SOC2"],  # load-bearing numbers must survive
      must_not_contain=["[error"])


# ─────────────────────────────────────────────────────────────────────────────
# USE CASE 3a: Draft the hard email — firm-but-warm decline
# ─────────────────────────────────────────────────────────────────────────────
hdr("UC3a: Hard email — firm-but-warm decline [no groveling, no invented reasons]")
out = run("draft",
          "My cofounder wants me to take his brother-in-law on as a paid advisor. "
          "He has no relevant experience and I've already said no twice. "
          "I need to decline once more, firmly but without blowing up the partnership.",
          tone="firm but warm")
print(out)
print()
check("firm-decline",
      out,
      must_not_contain=["[error", "I apologize for"])


# ─────────────────────────────────────────────────────────────────────────────
# USE CASE 3b: Hard email — apology without groveling
# ─────────────────────────────────────────────────────────────────────────────
hdr("UC3b: Hard email — apology without groveling [owns it, no excessive sorry]")
out = run("draft",
          "I missed a client deadline. The deliverable was 3 days late due to scope "
          "creep I didn't communicate. Need to apologize and restore trust.",
          tone="professional, accountable, not groveling")
print(out)
print()
# Count "sorry/apologize" — more than 2 instances = groveling
apology_count = len(re.findall(r'\b(sorry|apologize|apologies)\b', out.lower()))
if apology_count > 2:
    print(f"  WARN [groveling]: {apology_count} apology words (target ≤2)", flush=True)
else:
    print(f"  apology words: {apology_count} (OK)", flush=True)
check("apology-no-groveling",
      out,
      must_not_contain=["[error"])


# ─────────────────────────────────────────────────────────────────────────────
# USE CASE 3c: Hard email — negotiation counter
# ─────────────────────────────────────────────────────────────────────────────
hdr("UC3c: Hard email — negotiation counter [firm, not aggressive, opens dialogue]")
out = run("draft",
          "Vendor just sent a renewal quote 40% higher than last year. No new features, "
          "same contract. I want to counter at last year's rate or walk.",
          tone="firm, businesslike")
print(out)
print()
check("negotiation-counter",
      out,
      must_contain=["40"],  # should reference the increase
      must_not_contain=["[error"])


# ─────────────────────────────────────────────────────────────────────────────
# USE CASE 4: Summarize long doc for a decision (load-bearing numbers must survive)
# ─────────────────────────────────────────────────────────────────────────────
hdr("UC4: Summarize for decision [numbers survive, fluff killed, no banned openers]")
LONG_DOC = """
Q1 2026 Quarterly Business Review — Acme Corp

FINANCIAL SUMMARY
Revenue: $2.4M (vs $2.1M prior year, +14% YoY)
Gross margin: 68% (flat vs prior year)
Burn rate: $380K/month
Runway: 11 months at current burn

PRODUCT METRICS
Monthly Active Users: 4,200 (up from 3,100 a year ago)
Churn: 3.2% monthly (industry median: 2.1%)
NPS: 54

KEY RISKS
1. Churn at 3.2% is materially above industry median (2.1%). Each point of
   churn costs approximately $28K ARR/month.
2. Runway of 11 months assumes no acceleration of hiring. We planned to hire
   3 engineers in Q2; delaying to Q3 extends runway to 16 months.
3. Two enterprise accounts (combined 18% of ARR) are up for renewal in April.

KEY OPPORTUNITIES
1. Channel partnership with Stripe: pilot in Q2, could add $400K ARR by EOY.
2. LATAM expansion: 23% of new signups are from Brazil/Mexico with no
   localization investment yet.

RECOMMENDATION
Hold hiring until April renewal outcomes are known. Authorize Stripe partnership
pilot ($45K investment, $400K upside). Assign one PM to LATAM localization scoping.
""".strip()
out = run("summarize", LONG_DOC, instruction="Summarize for a board member making a funding decision — keep the numbers, cut the fluff")
print(out)
print()
banned_openers = ["certainly", "of course", "absolutely", "sure", "great question"]
for b in banned_openers:
    if out.lower().startswith(b):
        print(f"  FAIL [banned opener]: starts with '{b}'", flush=True)
        break
check("summarize-decision",
      out,
      must_contain=["2.4", "11", "3.2", "380", "400"],  # key numbers
      must_not_contain=["[error"])


# ─────────────────────────────────────────────────────────────────────────────
# USE CASE 5a: Voice-note-style input
# ─────────────────────────────────────────────────────────────────────────────
hdr("UC5a: Voice-note input [half-formed, hedged, 'umm'] → organized")
VOICE_NOTE = """
umm so basically what I'm trying to figure out is like, okay so we have this feature
that people seem to love? but also sometimes I wonder if it's actually like the thing
they love or if it's just the novelty. and there's also this question of like do we
build the mobile app next or do we do the, umm, the integrations thing. I think maybe
integrations first because like, we keep getting requests? but also mobile is, I don't
know, it feels more strategic. Priya thinks mobile. I'm not sure. Let me think about it.
""".strip()
out = run("organize", VOICE_NOTE)
print(out)
print()
check("voice-note-org",
      out,
      must_not_contain=["[error", "umm", "I'm not sure. Let me think"])  # should clean the ums


# ─────────────────────────────────────────────────────────────────────────────
# USE CASE 5b: "Make it shorter" x3 (iterative rewrite)
# ─────────────────────────────────────────────────────────────────────────────
hdr("UC5b: 'Make it shorter' x3 [each pass genuinely shorter, no meaning invented]")
ORIGINAL = ("We are writing to inform you that after careful consideration and "
            "extensive review of your application materials, we have determined "
            "that we will not be moving forward with your candidacy at this time. "
            "We appreciate the time and effort you invested in our process and "
            "wish you all the best in your future endeavors.")
current = ORIGINAL
wc_history = [len(current.split())]
for i in range(3):
    current = run("rewrite", current, instruction="Make it shorter and more direct")
    wc = len(current.split())
    wc_history.append(wc)
    print(f"  Pass {i+1} ({wc} words): {current}", flush=True)
print(f"\n  Word counts: {wc_history}")
if all(wc_history[i] > wc_history[i+1] for i in range(len(wc_history)-1)):
    print("  PASS: each pass shorter than the last", flush=True)
else:
    print("  FAIL: not monotonically shorter", flush=True)

print(f"\ntotal {time.time()-t0:.0f}s", flush=True)
