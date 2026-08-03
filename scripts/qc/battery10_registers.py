#!/usr/bin/env python3
"""QC Battery 10 — Secretary REGISTER GAUNTLET, sampled from the bank.

The same draft box writes the grocery list and the custody email. High-stakes
registers (eulogy, HR complaint, condolence, custody, ESL voice-keeping) are
always-include; the rest of the slice rotates by date. Judged on the doctrine's
bar: would you actually SEND this, and does it know what this moment is?
Mechanical floors (no invented facts where checkable, blanks present, banned
openers) print inline; the verdict is the read.
"""
import re, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fastapi.testclient import TestClient
import imagination_engine.server as s
from scenario_bank import sample

c = TestClient(s.app)

def hdr(t):
    print("\n" + "#" * 76 + f"\n# {t}\n" + "#" * 76, flush=True)

t0 = time.time()
scenarios = sample(product="secretary", n=10)
print(f"running {len(scenarios)}: {[x.id for x in scenarios]}", flush=True)
for sc in scenarios:
    hdr(f"{sc.id} [{sc.dim}/{sc.stakes}]" + (f" — {sc.note}" if sc.note else ""))
    r = c.post("/utility/run", json=sc.payload)
    out = r.text.strip()
    print(out, flush=True)
    # inline mechanical floors
    floors = []
    if re.search(r"i hope (this (email|message|letter) finds you|you('?re| are) (doing )?well)", out, re.I):
        floors.append("BANNED-OPENER")
    if sc.id == "sec-hr-complaint":
        for pat, label in [(r"jan", "Jan12"), (r"feb(ruary)? 3", "Feb3"),
                           (r"march 11", "Mar11"), (r"priya", "Priya"),
                           (r"okafor", "Okafor"), (r"doug", "Doug")]:
            if not re.search(pat, out, re.I):
                floors.append(f"FACT-LOST:{label}")
    if sc.id == "sec-missing-facts":
        if "[" not in out:
            floors.append("NO-BLANKS")
        brief = sc.payload["text"].lower()
        for day in ["monday", "tuesday", "wednesday", "thursday", "friday",
                    "saturday", "sunday"]:
            if day in out.lower() and day not in brief:
                floors.append(f"INVENTED-DAY:{day}")
    if sc.id == "sec-thread-decision":
        for month in ["january", "february", "march", "april", "may", "june",
                      "august", "september", "october", "november", "december"]:
            if month in out.lower() and month not in sc.payload["text"].lower():
                floors.append(f"FABRICATED-MONTH:{month}")
    if sc.id == "sec-thread-decision":
        for fact, label in [("dog", "dog-condition"), ("boat", "no-boat"),
                            ("memorial", "memorial"), ("friday", "deadline")]:
            if fact not in out.lower():
                floors.append(f"LOST:{label}")
    if sc.id == "sec-condolence-close":
        grief_platitudes = [
            "better place", "his love remains", "her love remains",
            "time heals", "looking down on", "precious gift",
            "always be with you in your heart", "would have wanted",
        ]
        for plat in grief_platitudes:
            if plat in out.lower():
                floors.append(f"GRIEF-PLATITUDE:{plat}")
        # brief says "I want her to know I'm not going anywhere" — that INTENT must land.
        # Accept: exact phrase, or forward commitment ("I'll", "I will", "I'm not going",
        # "I am here for you", "I'm here for you", "here for you").
        has_commitment = (
            "not going anywhere" in out.lower()
            or re.search(r"\bi'?ll\b|\bi will\b", out, re.I)
            or re.search(r"\bi(?:'m| am) here for you\b|here for you\b", out, re.I)
        )
        if not has_commitment:
            floors.append("MISSING-COMMITMENT:brief-said-not-going-anywhere")
    if sc.id == "sec-summarize-lossless":
        required = ["$2.4", "$380", "3.2%", "$28", "18%", "$400", "11 months"]
        # Normalize hyphenated adjective form "11-month" → "11 months" before checking
        out_check = re.sub(r'(\d+)-month\b', r'\1 months', out)
        for num in required:
            if num not in out and num not in out_check:
                floors.append(f"NUMBER-LOST:{num}")
    if sc.id == "sec-shorter-x3":
        # Multi-pass: run rewrite 3 times; each must be shorter than previous
        prev_words = len(out.split())
        for i in range(2, 4):
            r2 = c.post("/utility/run", json={"task": "rewrite", "text": out,
                                               "tone": "concise", "instruction": "make it shorter"})
            out2 = r2.text.strip()
            cur_words = len(out2.split())
            if prev_words <= 8:
                print(f"  pass {i}: {prev_words}w (floor — already minimal, skip)", flush=True)
            elif cur_words >= prev_words:
                floors.append(f"NOT-SHORTER-PASS-{i}:{prev_words}w->{cur_words}w")
            else:
                print(f"  pass {i}: {prev_words}w -> {cur_words}w ✓", flush=True)
            if len(out2) < 5:
                floors.append(f"EMPTY-PASS-{i}")
            prev_words = cur_words
            out = out2
    if sc.id == "sec-multi-doc-paste":
        # Both docs must contribute to the summary
        must_survive = [("Q3", "Q3-launch-delay"), ("Sarah", "Sarah-owns-timeline"),
                        ("legal", "compliance-legal-risk"), ("Q4", "Q4-slip-risk")]
        for term, label in must_survive:
            if term.lower() not in out.lower():
                floors.append(f"LOST:{label}")
    if sc.id == "sec-lease-extract":
        # June 31 is impossible (June has 30 days) — correct answer is July 2
        if re.search(r'\bJune\s+31\b', out, re.I):
            floors.append("IMPOSSIBLE-DATE:June-31")
        if not re.search(r'\bJuly\s+2\b', out, re.I):
            floors.append("WRONG-DEADLINE:should-be-July-2")
    if sc.id == "sec-braindump-organize":
        # All numeric facts from source must survive
        for fact, label in [
            (r"\$59", "price-new"), (r"\$49", "price-old"), (r"march\s+17|mar\s+17", "launch-date"),
            (r"march\s+3|mar\s+3", "brief-deadline"), (r"miranda", "pr-contact"),
            (r"\b47\b", "beta-user-count"), (r"30%", "beta-discount"),
            (r"feb(ruary)?\.?\s+28", "legal-deadline"), (r"\b3\b|three", "bug-count"), (r"tuesday", "check-in"),
        ]:
            if not re.search(fact, out, re.I):
                floors.append(f"LOST:{label}")
    print(f"\n  floors: {floors or 'clean'}", flush=True)

print(f"\ntotal {time.time()-t0:.0f}s", flush=True)
