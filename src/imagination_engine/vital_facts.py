"""vital_facts.py — Readable, user-editable memory for the companion.

The companion remembers who your sister is and what job you do — via a plain
markdown file the user owns: data/companion/vital-facts.md.

Design contract:
- Human-first format: headed sections, one fact per line with (YYYY-MM) date.
- UPDATE-not-append: "I got the new job" REPLACES the old job line; old line
  moves to ## Outdated (auditable, prunable).
- Confabulation guard: companion knows ONLY what is in this file + current sitting.
  If a fact is not written down, the companion does not "remember" it.
- Open-threads: facts the companion should ask about next session go in
  ## Open threads. Companion asks at most ONE at session open, yields instantly
  to the user's agenda, never asks same thread twice in a row, retires deflected.
- Cap: ~100 live-fact lines; prefer merging over growing.
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Optional

_DEFAULT_PATH = Path("data/companion/vital-facts.md")

_TEMPLATE = """\
# What I know about you (edit me freely — I only know what's written here)

## People
<!-- e.g. - Sister: Priya — lives in Austin, two kids (2026-07) -->

## Work
<!-- e.g. - Product lead at Hearth; running the v1 launch (2026-07) -->

## Life right now
<!-- e.g. - Training for a half marathon in October (2026-06) -->

## Preferences
<!-- e.g. - Wants direct answers, hates being "therapized" (2026-07) -->

## Open threads (things to ask about next session)
<!-- e.g. - New job — started 2026-07, asked 2026-07-08, status: settling in [gravity: med] -->

## Outdated
<!-- Retired facts are moved here; edit or delete freely -->
"""


class VitalFacts:
    """Load, render, and upsert the user's vital-facts file."""

    def __init__(self, path: Path | None = None):
        self.path = Path(path) if path else _DEFAULT_PATH
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text(_TEMPLATE, encoding="utf-8")

    # ── Read ──────────────────────────────────────────────────────────────────

    def _raw(self) -> str:
        return self.path.read_text(encoding="utf-8")

    def live_sections(self) -> str:
        """Return the live (non-Outdated) content for context injection.

        Strips comment lines, the Outdated section, and blank filler so the
        injected block stays compact."""
        text = self._raw()
        # Drop everything from ## Outdated onward
        text = re.split(r"\n##\s+Outdated", text, flags=re.IGNORECASE)[0]
        # Drop HTML comment lines
        lines = [ln for ln in text.splitlines()
                 if not re.match(r"\s*<!--", ln)]
        # Drop pure-comment sections that now have no content
        cleaned: list[str] = []
        for ln in lines:
            cleaned.append(ln)
        # Collapse 3+ consecutive blank lines
        result = re.sub(r"\n{3,}", "\n\n", "\n".join(cleaned)).strip()
        return result or ""

    def open_threads(self) -> list[dict]:
        """Parse ## Open threads lines into dicts for the session opener logic.

        Each thread line is:
          - <topic> — <detail>, asked <date>, status: <status> [gravity: <level>]

        Returns list of {topic, detail, asked, status, gravity, raw_line}.
        Only returns non-retired threads (not in Outdated section).
        """
        text = self._raw()
        # Find just the Open threads section (up to the next ## or Outdated)
        m = re.search(r"##\s+Open threads[^\n]*\n(.*?)(?:\n##|\Z)",
                      text, flags=re.IGNORECASE | re.DOTALL)
        if not m:
            return []
        block = m.group(1)
        threads = []
        for ln in block.splitlines():
            ln = ln.strip()
            if not ln.startswith("- ") or ln.startswith("<!--"):
                continue
            content = ln[2:].strip()
            t: dict = {"raw_line": ln, "topic": "", "detail": content,
                       "asked": None, "status": "", "gravity": "med"}
            # topic — detail
            if " — " in content:
                t["topic"], rest = content.split(" — ", 1)
            else:
                t["topic"] = content
                rest = content
            # asked date
            asked_m = re.search(r"asked\s+(\d{4}-\d{2}-\d{2})", rest)
            if asked_m:
                t["asked"] = asked_m.group(1)
            # status
            status_m = re.search(r"status:\s*([^[,\n]+)", rest)
            if status_m:
                t["status"] = status_m.group(1).strip()
            # gravity
            grav_m = re.search(r"\[gravity:\s*(low|med|high)\]", rest, re.I)
            if grav_m:
                t["gravity"] = grav_m.group(1).lower()
            threads.append(t)
        return threads

    def pick_opener_thread(self, last_asked_topic: str | None = None) -> Optional[dict]:
        """Pick the best thread to ask about at session open.

        Rules (from spec):
        - gravity first: high > med > low
        - never same thread twice in a row (last_asked_topic)
        - skip if no threads
        Returns None if nothing suitable.
        """
        threads = self.open_threads()
        if not threads:
            return None
        order = {"high": 0, "med": 1, "low": 2}
        threads.sort(key=lambda t: order.get(t["gravity"], 1))
        for t in threads:
            if t["topic"] != last_asked_topic:
                return t
        # All threads were last-asked; skip (shouldn't happen with >1 thread,
        # but fall back to highest-gravity to avoid silent failure)
        return threads[0] if threads else None

    # ── Write ─────────────────────────────────────────────────────────────────

    def upsert_fact(self, section: str, key: str, new_value: str,
                    date_str: str | None = None) -> bool:
        """Upsert a fact into the given section.

        If a line starting with '- {key}' exists, replace it (moving the old
        to ## Outdated). If not, append to the section.
        Returns True if the file changed.
        """
        date_str = date_str or datetime.now().strftime("%Y-%m")
        new_line = f"- {key}: {new_value} ({date_str})"
        text = self._raw()
        # Find existing line
        pattern = re.compile(
            rf"^(\s*-\s*{re.escape(key)}[:\s][^\n]*)$", re.MULTILINE | re.IGNORECASE
        )
        old_match = pattern.search(text)
        if old_match:
            old_line = old_match.group(1)
            if old_line.strip() == new_line.strip():
                return False  # no change
            # Move old line to Outdated, replace in-place
            text = text[:old_match.start()] + new_line + text[old_match.end():]
            text = self._append_outdated(text, old_line.strip())
        else:
            # Append to the named section
            sec_pattern = re.compile(
                rf"(##\s*{re.escape(section)}[^\n]*\n)", re.IGNORECASE
            )
            sec_m = sec_pattern.search(text)
            if sec_m:
                insert_at = sec_m.end()
                text = text[:insert_at] + new_line + "\n" + text[insert_at:]
            else:
                # Section doesn't exist — add it before Outdated (or at end)
                out_m = re.search(r"\n##\s+Outdated", text, re.IGNORECASE)
                if out_m:
                    text = text[:out_m.start()] + f"\n## {section}\n{new_line}\n" + text[out_m.start():]
                else:
                    text = text.rstrip() + f"\n\n## {section}\n{new_line}\n"
        self.path.write_text(text, encoding="utf-8")
        return True

    def add_thread(self, topic: str, detail: str, gravity: str = "med",
                   date_str: str | None = None) -> None:
        """Add or refresh an open thread."""
        date_str = date_str or datetime.now().strftime("%Y-%m-%d")
        new_line = f"- {topic} — {detail}, asked never [gravity: {gravity}]"
        text = self._raw()
        # Check if topic already exists in open threads
        if re.search(rf"^- {re.escape(topic)} —", text, re.MULTILINE | re.IGNORECASE):
            return  # Already tracked; don't duplicate
        sec_m = re.search(r"(##\s*Open threads[^\n]*\n)", text, re.IGNORECASE)
        if sec_m:
            insert_at = sec_m.end()
            text = text[:insert_at] + new_line + "\n" + text[insert_at:]
        else:
            out_m = re.search(r"\n##\s+Outdated", text, re.IGNORECASE)
            if out_m:
                text = text[:out_m.start()] + "\n## Open threads\n" + new_line + "\n" + text[out_m.start():]
            else:
                text = text.rstrip() + "\n\n## Open threads\n" + new_line + "\n"
        self.path.write_text(text, encoding="utf-8")

    def retire_thread(self, topic: str) -> bool:
        """Move a thread from Open threads to Outdated. Returns True if found."""
        text = self._raw()
        pattern = re.compile(
            rf"^(- {re.escape(topic)} —[^\n]*)$", re.MULTILINE | re.IGNORECASE
        )
        m = pattern.search(text)
        if not m:
            return False
        old_line = m.group(1)
        text = text[:m.start()] + text[m.end() + 1:]  # +1 to eat the \n
        text = self._append_outdated(text, f"[thread retired] {old_line}")
        self.path.write_text(text, encoding="utf-8")
        return True

    def mark_thread_asked(self, topic: str, date_str: str | None = None) -> None:
        """Update the 'asked' date on an open thread."""
        date_str = date_str or datetime.now().strftime("%Y-%m-%d")
        text = self._raw()
        pattern = re.compile(
            rf"^(- {re.escape(topic)} —[^\n]*)$", re.MULTILINE | re.IGNORECASE
        )
        m = pattern.search(text)
        if not m:
            return
        old = m.group(1)
        # Replace "asked never" or "asked YYYY-MM-DD" with current date
        updated = re.sub(r"asked [\w-]+", f"asked {date_str}", old)
        if updated == old:
            updated = old + f", asked {date_str}"
        text = text[:m.start()] + updated + text[m.end():]
        self.path.write_text(text, encoding="utf-8")

    @staticmethod
    def _append_outdated(text: str, line: str) -> str:
        """Append line to ## Outdated section (creating it if absent)."""
        out_m = re.search(r"(##\s*Outdated[^\n]*\n)", text, re.IGNORECASE)
        if out_m:
            insert_at = out_m.end()
            return text[:insert_at] + line + "\n" + text[insert_at:]
        return text.rstrip() + f"\n\n## Outdated\n{line}\n"

    # ── Context block ─────────────────────────────────────────────────────────

    def context_block(self) -> str:
        """Ready-to-inject context string for the companion system prompt.

        Returns empty string if file has no live facts."""
        content = self.live_sections()
        if not content or content == _TEMPLATE.strip():
            return ""
        # Also treat as empty if there are no actual fact bullet lines (only headers/comments)
        if not any(ln.strip().startswith("- ") for ln in content.splitlines()):
            return ""
        return (
            "----- WHAT I KNOW ABOUT YOU (from vital-facts.md — I know ONLY what is "
            "written here; nothing more) -----\n"
            + content
            + "\n----- END VITAL FACTS -----"
        )
