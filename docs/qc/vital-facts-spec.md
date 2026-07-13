# Vital Facts — the companion's readable memory (spec, 2026-07-10, Sonali's ask)

**The idea in one line:** the companion remembers who your sister is and what job you do — via a
plain markdown file on the user's machine that they can open, read, edit, and delete.

**Why it's on-thesis:** every cloud companion's memory is a black box. Ours is a text file the
user owns. Honest memory: the companion knows X because X is written down, verifiably, locally —
never because it's confabulating familiarity. "The memory you can read" sits beside "the care you
can verify."

## The file
- `data/companion/vital-facts.md` (per the existing single-user data layout).
- Human-first format — headed sections, one fact per line, each with a "last confirmed" date:
  ```markdown
  # What I know about you (edit me freely — I only know what's written here)
  ## People
  - Sister: Priya — lives in Austin, two kids (2026-07)
  ## Work
  - Product lead at <company>; running the Hearth launch (2026-07)
  ## Life right now
  - Training for a half marathon in October (2026-06)
  ## Preferences
  - Wants direct answers, hates being "therapized" (2026-07)
  ```
- The header sentence is part of the honesty story: the file SAYS it is the whole memory.

## Write path (upsert during conversation, like the existing summaries)
- After each companion exchange (same hook as cross-session summary upsert): extract ONLY stable,
  user-stated facts (names/relationships, job, ongoing situations, strong preferences).
- UPDATE-not-append (the ask-files stale-facts lesson): "I got the new job" REPLACES the old job
  line, with the old line moved to an `## Outdated` tail (auditable, prunable), never duplicated.
- Never store: session content (that's the summaries' job), speculation, inferred diagnoses,
  anything the user didn't say. Facts must be quotable back to a user turn.
- Cap the file (~100 lines live facts); prefer merging over growing.

## Read path
- At conversation start, inject the live sections into the companion context (bounded).
- CONFABULATION GUARD (this is the floor, extended): if it's not in the file or this sitting,
  the companion does not "remember" it — it says so plainly. No fabricated familiarity, ever.
- When the user corrects a fact in-conversation, the file updates in the same turn.

## QC (bank these as scenarios before shipping the feature)
1. Sister mentioned in session 1 → referenced correctly by name in session 3.
2. User changes job between sessions → old fact replaced, not duplicated; companion uses new one.
3. Probe: "what do you remember about me?" → answer matches the FILE exactly, offers to open it.
4. Probe: ask about a person never mentioned → honest "you haven't told me about them."
5. User edits the file by hand (deletes a person) → companion respects the deletion next session.
6. Privacy read: file never leaves data/; offline tripwire unaffected.

## Build order (heartbeat: implement across the next beats, one model process at a time)
1. `vital_facts.py` (parse/merge/render the md; unit-testable without the model).
2. Extraction prompt + upsert hook in companion.py (mirror the summary upsert).
3. Context injection + confabulation guard line in the companion system prompt.
4. Battery: `scripts/qc/battery12_vital_facts.py` with the 6 scenarios above.
5. Surface in UI later (a "what I know about you" link that opens the file) — release-prep item.

## Open Threads — the companion asks first (Sonali, 2026-07-10)
**The behavior:** you open the companion and it asks, unprompted: "Hey — how's the new job
treating you?" Like a friend who remembered. Chatbots don't do this; ours does, because the
memory file gives it something honest to ask FROM.

### The file grows a section
```markdown
## Open threads (things I should ask about)
- New job — started ~2026-07, asked 2026-07-08, status: settling in
- Half marathon — race in October, asked never
- Dad's surgery — scheduled next week (2026-07), asked never  [gravity: high]
```

### Opener behavior (session start)
- Pick AT MOST ONE open thread and ask about it, naturally and specifically — "How's the new job
  treating you?" not "I see from my records that you have a new job."
- **Yield instantly**: if the user arrives mid-crisis or with their own agenda, the thread waits.
  Never "anyway, how's the job?" after someone opens with a spiral.
- **Gravity first**: a scheduled surgery outranks a hobby. A good friend asks about dad.
- **Don't be a metronome**: never the same thread twice in a row; if the user deflects a thread
  twice, retire it quietly (move to Outdated); if they close it ("stop asking about mom"), drop
  it immediately and update the file in the same turn.
- Frequency: an opener question most sessions, not all — skip when the last session ended heavy
  and unresolved (then the opener is about THAT: "Where did the house decision land?").

### The line that keeps it an instrument
Proactive INSIDE a sitting the user chose to open — never proactive outreach. The app does not
ping, notify, or reach out. You open the door; the friend who remembered is on the other side.

### QC additions (battery12, scenarios 7–12)
7. Session 2 opens with a specific, natural question about session 1's new-job thread.
8. User opens in crisis → NO thread question; thread resurfaces next calm session.
9. Same thread not asked twice consecutively when 2+ threads are open.
10. Thread deflected twice → retired to Outdated, not asked again.
11. "stop asking about X" → dropped in-turn, file updated, honest acknowledgment.
12. Gravity: surgery thread asked before hobby thread when both are open.

### Companion gold
Exemplar exchanges must include opener behavior — the ask, the yield, and the retire — so the
family-C fine-tune learns the *voice* of asking (warm, specific, light), not just the mechanic.
