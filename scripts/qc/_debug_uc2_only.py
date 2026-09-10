#!/usr/bin/env python3
"""TEMP debug driver — UC2 only, isolated, to trace the T4 memory-probe regression.
Not a permanent QC battery. Delete after the investigation closes.
"""
import sys, logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
logging.basicConfig(level=logging.WARNING, format="%(message)s")

from fastapi.testclient import TestClient
import imagination_engine.server as srv
from imagination_engine.server import app

c = TestClient(app)

import tempfile
from imagination_engine.vital_facts import VitalFacts
_vf_tmp = Path(tempfile.mkdtemp()) / "vital-facts.md"
srv._vital_facts = VitalFacts(_vf_tmp)

def turn(session_id: str, msg: str) -> str:
    r = c.post("/companion/turn", json={"session_id": session_id, "message": msg}).json()
    return r.get("reply", f"[ERROR: {r}]")

from imagination_engine.companion import CompanionMemory
db_path = Path(__file__).resolve().parents[2] / "data" / "companion.sqlite"
cmem = CompanionMemory(db_path)

with cmem._conn() as conn:
    conn.execute("DELETE FROM companion_log WHERE session LIKE 'battery%'")
    conn.execute("DELETE FROM companion_log WHERE session IN ('deep-uc2-past-1','deep-uc2-past-2')")

ts1 = "2026-07-01T21:40:00"
ts2 = "2026-07-05T14:15:00"
summary1 = ("User has been circling a decision about leaving their job at a tech "
            "company for a smaller startup. Main friction: financial safety vs meaning. "
            "No resolution — they left saying they needed to think about the risk.")
summary2 = ("User checked back in on the job decision. Told their partner. Partner "
            "is supportive but worried about the health insurance gap. User is leaning "
            "toward taking the offer but hasn't said yes. Decided to run the numbers first.")
cmem.remember(summary1, ts1, session="deep-uc2-past-1")
cmem.remember(summary2, ts2, session="deep-uc2-past-2")

srv._companion_memory = None
if "deep-uc2-new" in srv._companions:
    del srv._companions["deep-uc2-new"]

sid2 = "deep-uc2-new"
turns_uc2 = [
    "Hey. Back again.",
    "Still stuck on the same thing honestly. The job stuff.",
    "I've been going back and forth for two weeks. I think I need to just decide.",
    "Did we talk about this before?",
    "What about my relationship with my sister — did we ever discuss that?",
]

for i, msg in enumerate(turns_uc2, 1):
    reply = turn(sid2, msg)
    print(f"\n[T{i}] USER: {msg}")
    print(f"[T{i}] COMPANION: {reply}")

print("\nDONE")
