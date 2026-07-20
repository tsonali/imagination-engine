"""Utility — the at-home secretary (Family B).

The everyday knowledge-work tool: draft and reply to messages, summarize long
text, rewrite for tone/clarity/length, pull action items out of a mess, turn a
brain-dump into an organized list or plan. All local, all private — the user's
words never leave the machine.

Design (consistent with the thesis):
- INSTRUMENT, not companion. It does the task and returns the result. No chat
  persona, no "happy to help!", no commentary — just the work, ready to use.
- WORKS ON THE USER'S OWN WORDS. A small local model is good at *transforming
  text you give it* (summarize, rewrite, extract, restructure) — that's exactly
  what a secretary does. We lean into that strength rather than asking the model
  to supply outside knowledge it doesn't reliably have.
- ADAPTS TO YOUR VOICE (optionally). Pass a `style_sample` of the user's own past
  writing and the draft/reply tasks will match their voice — the "respond like me"
  ask — without that sample ever being uploaded or retained.
- HONEST OUTPUT. It returns only the artifact (the email, the summary, the list).
  No preamble, no "Here is the...", no sign-off it wasn't asked for.

Each task is a small declarative spec (system + user-prompt builder), so adding a
task is one entry — the same extensibility the eventual framework wants.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Callable, Iterator

from imagination_engine.inference import Engine

log = logging.getLogger(__name__)

# Shared spine for every task: the model is a transformer of the user's text, it
# returns ONLY the finished artifact, and it never invents facts not present in
# the input. This is what keeps a small local model reliable at this job.
_BASE = (
    "You are a precise writing assistant — a secretary working on this person's own "
    "text, on their own computer. Produce ONLY the finished result they asked for: "
    "no preamble, no 'Here is', no commentary, no sign-off unless the task calls for "
    "one. Never invent facts, names, dates, or details that are not in what they gave "
    "you — if something needed is missing, leave a clearly marked [bracketed blank] "
    "for them to fill in rather than making it up.\n"
    "NEVER open with filler pleasantries — no 'I hope this email finds you well', "
    "'I hope you're doing well', 'I wanted to reach out'. Start with the substance. "
    "Match the requested tone exactly; if the tone is firm or direct, do not soften it "
    "with hopeful padding or apologies.\n"
    "KNOW WHAT KIND OF THING YOU'RE WRITING:\n"
    "- If it will be SPOKEN (a eulogy, a toast, a speech, vows), write it to be said "
    "aloud — no letter frame, no 'Dear...', no sign-off block.\n"
    "- In condolence or grief writing: never center the writer ('I can't find the "
    "words', 'this has been hard for me'), never measure or minimize the loss "
    "('at least...', 'we were lucky to have him even briefly'). Short, specific, "
    "about them and the person. BANNED GRIEF PLATITUDES (automatic fail): "
    "'in a better place', 'he's in a better place', 'she's in a better place', "
    "'his love remains forever', 'his love remains with', 'time heals', "
    "'they would have wanted', 'everything happens for a reason', 'looking down on us', "
    "'always be with you in your heart', 'your memories will', 'precious gift'.\n"
    "- A subject line names the topic, never the tactic ('Billing question' — not "
    "'Threat of Service Switch')."
)

# Tone modifiers offered to draft/reply/rewrite. Empty string = leave tone alone.
TONES = {
    "": "",
    "plain": "Use plain, clear, neutral language.",
    "warm": "Use a warm, friendly, human tone — without gushing.",
    "formal": "Use a formal, professional tone.",
    "concise": ("Compress: remove every unnecessary word and cut redundant phrases. "
                "The output must be shorter than the input — fewer words, same core meaning."),
    "firm": ("Be firm and direct. State the expectation plainly and put it up front. "
             "No pleasantries, no hedging, no 'I hope', no apologizing for asking."),
}


@dataclass
class UtilityTask:
    key: str
    label: str
    blurb: str            # one-line description for the UI
    input_label: str      # what the big text box is asking for
    wants_instruction: bool   # show the "extra instruction" field?
    wants_tone: bool          # show the tone selector?
    build: Callable[[str, str, str, str], tuple[str, str]]  # (text,instruction,tone,style)->(system,user)


def _style_clause(style_sample: str) -> str:
    s = (style_sample or "").strip()
    if not s:
        return ""
    return ("\n\nMatch the VOICE of this person's own past writing (mirror their "
            "sentence length, warmth, formality, and quirks — not its content):\n"
            f"\"\"\"\n{s[:1200]}\n\"\"\"")


def _tone_clause(tone: str) -> str:
    t = TONES.get((tone or "").strip().lower(), "")
    return f"\n\n{t}" if t else ""


# ----------------------------------------------------------------- task builders
def _b_draft(text, instruction, tone, style):
    system = _BASE + _tone_clause(tone) + _style_clause(style)
    dates = _extract_dates(text)
    mandatory_clause = (
        f"\nMANDATORY DATES (each must appear verbatim in your output): {', '.join(dates)}\n"
        if dates else ""
    )
    user = (
        "Write a message (email/letter/note) based on this brief. Output only the "
        "message itself, ready to send. If it's an email or letter, give it a normal "
        "frame — a brief greeting line, and a sign-off ending with the sender's name (use "
        "[bracketed blanks] for any names not in the brief, including [Your name] at the "
        "end). Tone shapes the words, not whether the frame exists: "
        "a firm email still opens and signs like an email.\n"
        "Say only what the brief supports. If it doesn't give a reason, a date, or a "
        "detail you need, put a [bracketed blank] — NEVER invent one (no fabricated "
        "'work commitments', no assumed dates, no invented day names like 'Tuesday' "
        "when the brief only said 'next week').\n"
        + mandatory_clause
        + f"\nBRIEF (what it's about / who it's to / what to say):\n{text}"
        + (f"\n\nADDITIONAL INSTRUCTION: {instruction}" if instruction.strip() else "")
    )
    return system, user


def _b_reply(text, instruction, tone, style):
    system = _BASE + _tone_clause(tone) + _style_clause(style)
    user = (
        "Draft a reply to the message below. Output only the reply, ready to send. "
        "Answer what was actually asked; keep it appropriately short. If it's an "
        "email, keep a normal frame — greeting if appropriate, and a sign-off ending "
        "with [Your name].\n\n"
        f"MESSAGE I RECEIVED:\n{text}"
        + (f"\n\nHOW I WANT TO REPLY (gist / my intent): {instruction}"
           if instruction.strip() else "")
    )
    return system, user


def _extract_numbers(text: str) -> list[str]:
    """Pull every concrete number token from source text for explicit lossless enforcement."""
    import re
    found = []
    # Dollar amounts: $2.4M, $380K, $28K, $45K, $400K
    found += re.findall(r'\$[\d,]+(?:\.\d+)?(?:K|M|B)?', text)
    # Percentages: 3.2%, 68%, 18%, 14%
    found += re.findall(r'\d+(?:\.\d+)?\s*%', text)
    # Time/count: 11 months, 4,200, 54 (NPS)
    found += re.findall(r'\b\d[\d,]*\s+(?:months?|years?|weeks?|days?|hours?)\b', text, re.I)
    # Deduplicate while preserving order
    seen = set()
    unique = []
    for n in found:
        norm = n.strip()
        if norm not in seen:
            seen.add(norm)
            unique.append(norm)
    return unique


_MONTH_ABBR = r'(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)'

# Person-verb pattern: "[Name] will/owns/flagged/..." to extract named individuals
# who have stated responsibilities or actions in source text.
_PERSON_VERB_RE = re.compile(
    r'\b([A-Z][a-z]{2,})\s+'
    r'(?:will|shall|can|should|owns?|leads?|manages?|handles?|heads?|'
    r'flagged|said|noted|mentioned|reported|confirmed|approved|denied|'
    r'told|wrote|requested|allocated|assigned|coordinates?|oversees?|'
    r'creates?|sent|shared|raised|brought|discussed|proposed|reviewed)\b',
)
_NAME_STOPWORDS = frozenset({
    'january', 'february', 'march', 'april', 'june', 'july', 'august',
    'september', 'october', 'november', 'december',
    'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday',
    'team', 'legal', 'budget', 'document', 'slack', 'meeting', 'notes', 'thread',
    'bottom', 'line', 'focus', 'text', 'note', 'the', 'recommendation',
})


def _extract_names(text: str) -> list[str]:
    """Extract probable person names from source text via person-verb patterns.

    Finds "[Name] will/owns/flagged/..." patterns — named individuals with stated
    responsibilities. Used to build MANDATORY NAMES clause so named people survive
    summarization (root cause: model drops 'Sarah will own timeline' as non-decision).
    """
    candidates = _PERSON_VERB_RE.findall(text)
    seen: set[str] = set()
    unique = []
    for c in candidates:
        if c.lower() not in _NAME_STOPWORDS:
            key = c.lower()
            if key not in seen:
                seen.add(key)
                unique.append(c)
    return unique


def _extract_dates(text: str) -> list[str]:
    """Pull specific calendar dates from source text (Month Day forms only).

    Returns the matched token as it appears in the source — used to build a
    MANDATORY FACTS clause in draft prompts so dates survive verbatim.
    """
    found = re.findall(
        rf'\b{_MONTH_ABBR}\s+\d{{1,2}}(?:st|nd|rd|th)?\b',
        text, re.I,
    )
    # Deduplicate preserving order
    seen: set[str] = set()
    unique = []
    for d in found:
        key = d.strip().lower()
        if key not in seen:
            seen.add(key)
            unique.append(d.strip())
    return unique


def _b_summarize(text, instruction, tone, style):
    system = _BASE
    nums = _extract_numbers(text)
    num_list = ", ".join(nums) if nums else ""
    names = _extract_names(text)
    name_list = ", ".join(names) if names else ""
    lossless_rule = (
        "LOSSLESS NUMBER RULE: Every concrete number from the source MUST appear "
        "verbatim in your output — no paraphrasing. "
        "COST-CONTEXT numbers (a dollar amount that modifies a metric, e.g. "
        "'each point of churn costs $28K ARR/month') are LOAD-BEARING — "
        "the dollar amount MUST appear alongside the metric it modifies, "
        "not silently dropped.\n"
        + (f"MANDATORY NUMBERS (all must appear): {num_list}\n" if num_list else "")
    )
    names_rule = (
        "MANDATORY NAMES RULE: Named individuals and their stated ownership or "
        "responsibility assignments are as mandatory as numbers — if the source "
        "says 'Sarah will own the timeline', both Sarah's name and her role MUST "
        "appear in your output. Do not compress named assignments.\n"
        + (f"MANDATORY NAMES (all must appear): {name_list}\n" if name_list else "")
    ) if name_list else ""
    user = (
        "Summarize the text below in EXACTLY this format:\n"
        "BOTTOM LINE: <one sentence>\n"
        "- <key point>\n"
        "- <key point>\n"
        "(as many points as needed)\n\n"
        + lossless_rule + "\n"
        + (names_rule + "\n" if names_rule else "")
        + "Every decision, every CONDITION attached to a decision ('yes, but only "
        "if...'), every deadline, every named event or commitment, and every open "
        "question MUST also survive — a condition, commitment, or named event lost "
        "is wrong. Keep relative dates AS THE SOURCE SAYS THEM — never attach a "
        "month or year the source didn't state.\n\n"
        + (f"FOCUS: {instruction}\n\n" if instruction.strip() else "")
        + f"TEXT:\n{text}"
    )
    return system, user


def _b_rewrite(text, instruction, tone, style):
    system = _BASE + _tone_clause(tone) + _style_clause(style)
    user = (
        "Rewrite the text below. Keep the meaning; improve clarity and flow. Output "
        "only the rewritten version.\n\n"
        + (f"HOW TO CHANGE IT: {instruction}\n\n" if instruction.strip() else "")
        + f"TEXT:\n{text}"
    )
    return system, user


def _b_extract(text, instruction, tone, style):
    system = _BASE
    user = (
        "Read the text below and pull out the actionable parts. Return three short "
        "sections, omitting any that are empty:\n"
        "ACTION ITEMS (who does what, as a checklist)\n"
        "DATES & DEADLINES\n"
        "OPEN QUESTIONS / DECISIONS NEEDED\n\n"
        "STRICT DATE RULE: Compute notice deadlines by counting DAYS (never months). "
        "Step through it: 60 days before August 31 → subtract 31 days to reach August 1, "
        "then subtract 29 more days = July 2. Write the FINAL date only — no alternative, "
        "no intermediate, no parenthetical variant. FORBIDDEN: impossible dates (June has "
        "30 days, not 31; April/September/November also end on 30).\n\n"
        + (f"NOTE: {instruction}\n\n" if instruction.strip() else "")
        + f"TEXT:\n{text}"
    )
    return system, user


def _b_organize(text, instruction, tone, style):
    system = _BASE
    nums = _extract_numbers(text)
    num_list = ", ".join(nums) if nums else ""
    num_rule = (
        "NUMERIC FLOOR: Every number in the source (counts, amounts, dates, codes) "
        "MUST appear verbatim in your output — do NOT drop, round, or paraphrase counts.\n"
        + (f"MANDATORY NUMBERS (all must appear): {num_list}\n" if num_list else "")
    )
    user = (
        "Turn the messy notes / brain-dump below into a clean, organized structure — "
        "group related items under clear headings, order them sensibly, and use lists. "
        "EVERY item in the notes must appear exactly once in your output — count them; "
        "losing even one defeats the whole purpose. Don't add anything that isn't "
        "there: no invented ordering ('after X is done'), no advice, no new items.\n\n"
        + num_rule + "\n"
        + (f"HOW TO ORGANIZE IT: {instruction}\n\n" if instruction.strip() else "")
        + f"NOTES:\n{text}"
    )
    return system, user


TASKS: dict[str, UtilityTask] = {
    t.key: t for t in [
        UtilityTask("draft", "Draft a message", "Write an email, letter, or note from a brief.",
                    "What it's about, who it's to, what to say", True, True, _b_draft),
        UtilityTask("reply", "Draft a reply", "Reply to a message you received.",
                    "Paste the message you received", True, True, _b_reply),
        UtilityTask("summarize", "Summarize", "Condense long text into the bottom line + key points.",
                    "Paste the long text or thread", True, False, _b_summarize),
        UtilityTask("rewrite", "Rewrite", "Improve clarity, change tone, or adjust length.",
                    "Paste the text to rewrite", True, True, _b_rewrite),
        UtilityTask("extract", "Pull action items", "Find the to-dos, dates, and open questions.",
                    "Paste notes, a thread, or a transcript", True, False, _b_extract),
        UtilityTask("organize", "Organize notes", "Turn a brain-dump into a clean structure.",
                    "Paste your messy notes", True, False, _b_organize),
    ]
}


@dataclass
class UtilityResult:
    task: str
    output: str


# Filler openers the _BASE prompt bans but register pressure keeps producing.
# Enforced mechanically: the head of the stream is buffered and checked; one
# violation = one regenerate with an explicit reminder. Prompt + gate, two ways.
_BANNED_OPENERS = re.compile(
    r"i hope (this (email|message|letter) finds you|you('?re| are) (doing )?well)|"
    r"i wanted to (reach out|touch base)|i trust this (email|message) finds you", re.I)
_HEAD_CHARS = 200  # enough to cover greeting line + first sentence


class Assistant:
    """The at-home secretary. One Engine, stateless per call (a tool, not a chat)."""

    def __init__(self, engine: Engine):
        self.engine = engine

    def stream(self, task_key: str, text: str, *, instruction: str = "",
               tone: str = "", style_sample: str = "",
               max_tokens: int = 1200, _extra_system: str = "") -> Iterator[str]:
        task = TASKS.get(task_key)
        if task is None:
            raise KeyError(f"unknown task: {task_key}")
        if not (text or "").strip():
            raise ValueError("no input text")
        system, user = task.build(text, instruction or "", tone or "", style_sample or "")

        def gen(extra_system: str = "") -> Iterator[str]:
            # Low temperature: a secretary should be faithful and predictable.
            return self.engine.stream(messages=[
                {"role": "system", "content": system + _extra_system + extra_system},
                {"role": "user", "content": user},
            ], max_tokens=max_tokens, temperature=0.4)

        # Buffer the head before yielding anything, so a banned opener can be
        # caught and regenerated without the user ever seeing it.
        stream = gen()
        head: list[str] = []
        for piece in stream:
            head.append(piece)
            if sum(len(p) for p in head) >= _HEAD_CHARS:
                break
        if _BANNED_OPENERS.search("".join(head)):
            log.warning("secretary[%s]: banned filler opener — regenerating once", task_key)
            stream = gen("\n\nIMPORTANT: do NOT open with any filler greeting — "
                         "this means 'I hope this email/letter/message finds you well', "
                         "'I hope you are/you're doing well', 'I wanted to reach out', "
                         "'I trust this email finds you', or any equivalent pleasantry. "
                         "After any greeting line (Dear X / Hi X), write the substance immediately.")
            head = []
            for piece in stream:
                head.append(piece)
                if sum(len(p) for p in head) >= _HEAD_CHARS:
                    break
            # If the regen STILL produced a banned opener (model is stubborn),
            # strip just the banned sentence (not the whole line) so that content
            # on the same line after the banned phrase is preserved.
            if _BANNED_OPENERS.search("".join(head)):
                combined = "".join(head)
                # Strip the banned phrase + any text up to the next sentence end.
                # Pattern: banned phrase + everything until period/newline (or end).
                _STRIP_SENT = re.compile(
                    r"(?i)(i hope (this (email|message|letter) finds you|"
                    r"you('?re| are) (doing )?well)|"
                    r"i wanted to (reach out|touch base)|"
                    r"i trust this (email|message) finds you)[^.\n]*[.\n]?\s*"
                )
                combined = _STRIP_SENT.sub("", combined).lstrip("\n")
                head = [combined]
                log.warning("secretary[%s]: regen still had banned opener — sentence stripped", task_key)
                # If stripping left only a salutation line (≤15 chars of real content),
                # the model generated a stub that got entirely consumed. Force a third
                # regen with explicit instruction to skip the greeting pleasantry.
                if len(combined.strip()) <= 15:
                    log.warning("secretary[%s]: strip left only salutation — forcing third regen", task_key)
                    stream = gen(
                        "\n\nCRITICAL: Write the body of the email IMMEDIATELY after the "
                        "salutation line. Do NOT write 'I hope this email finds you well' or "
                        "any other pleasantry. Begin with the substance in the very first sentence."
                    )
                    head = []
                    for piece in stream:
                        head.append(piece)
                        if sum(len(p) for p in head) >= _HEAD_CHARS:
                            break
        yield "".join(head)
        yield from stream

    def run(self, task_key: str, text: str, **kw) -> UtilityResult:
        out = "".join(self.stream(task_key, text, **kw)).strip()
        # Post-check for summarize: if mandatory numbers were dropped, regen up to 3x.
        # Common failure: $28K cost-context figure alongside 3.2% churn — drops even with
        # MANDATORY NUMBERS in the initial prompt. Each regen attempt uses explicit callout;
        # second attempt escalates with CRITICAL FAILURE framing; third uses lowest temp.
        if task_key in ("summarize", "organize"):
            nums = _extract_numbers(text)
            for attempt in range(3):
                missing = [n for n in nums if n not in out]
                if not missing:
                    break
                task_obj = TASKS[task_key]
                system, user = task_obj.build(
                    text, kw.get("instruction", ""),
                    kw.get("tone", ""), kw.get("style_sample", ""),
                )
                missing_str = ", ".join(missing)
                if attempt == 0:
                    severity = "MANDATORY NUMBERS MISSING"
                elif attempt == 1:
                    severity = "CRITICAL FAILURE"
                else:
                    severity = "ABSOLUTE CRITICAL FAILURE — THIRD ATTEMPT"
                # Build per-number guidance: include the SOURCE SENTENCE for each missing
                # number so the model knows where it came from and where to put it.
                source_lines = [ln.strip() for ln in text.replace("\n", ". ").split(". ") if ln.strip()]
                per_num = []
                for n in missing:
                    src_ctx = next((ln for ln in source_lines if n in ln), None)
                    if src_ctx:
                        per_num.append(f"{n} (from source: '{src_ctx}')")
                    elif "%" in n:
                        per_num.append(f"{n} (include the percentage RATE explicitly, "
                                       "not just its dollar cost-per-point equivalent)")
                    else:
                        per_num.append(n)
                missing_detail = "; ".join(per_num)
                extra = (
                    f"\n\n{severity}: A previous attempt dropped "
                    f"these required numbers — each MUST appear verbatim in your output: "
                    f"{missing_detail}. "
                    "Do not substitute a related figure; include EACH ONE as it appears. "
                    "For cost-context figures (e.g., 'each churn point costs $28K ARR/month'), "
                    "include BOTH the percentage rate AND the dollar amount."
                )
                temp = 0.25 if attempt >= 2 else (0.35 if attempt == 1 else 0.4)
                regen = "".join(self.engine.stream(
                    messages=[
                        {"role": "system", "content": system + extra},
                        {"role": "user", "content": user},
                    ],
                    max_tokens=kw.get("max_tokens", 1200),
                    temperature=temp,
                )).strip()
                recovered = [n for n in missing if n in regen]
                if len(recovered) >= len(missing) // 2 + 1:
                    log.info("secretary[%s]: attempt %d regen recovered %d/%d missing numbers",
                             task_key, attempt + 1, len(recovered), len(missing))
                    out = regen
        # Post-check for summarize: if named individuals were dropped, regen once.
        # Root cause: model interprets "decisions only" instruction as license to drop
        # named person + assignment ("Sarah will own the timeline" → compressed to Q3 delay).
        if task_key == "summarize":
            mandatory_names = _extract_names(text)
            missing_names = [n for n in mandatory_names if n.lower() not in out.lower()]
            if missing_names:
                task_obj = TASKS[task_key]
                n_sys, n_usr = task_obj.build(
                    text, kw.get("instruction", ""),
                    kw.get("tone", ""), kw.get("style_sample", ""),
                )
                names_str = ", ".join(missing_names)
                names_extra = (
                    f"\n\nMANDATORY NAMES MISSING: A previous attempt dropped these named "
                    f"individuals — each MUST appear in your output with their stated role or "
                    f"assignment: {names_str}. If the source says 'Sarah will own X', "
                    f"include Sarah and her ownership in the output."
                )
                regen = "".join(self.engine.stream(
                    messages=[
                        {"role": "system", "content": n_sys + names_extra},
                        {"role": "user", "content": n_usr},
                    ],
                    max_tokens=kw.get("max_tokens", 1200),
                    temperature=0.4,
                )).strip()
                recovered = [n for n in missing_names if n.lower() in regen.lower()]
                if recovered:
                    log.info("secretary[summarize]: names regen recovered %s", recovered)
                    out = regen
        # Post-check for draft: if mandatory dates from brief are missing, regen up to 2x.
        # Root cause: model drops specific dates (e.g., "March 11") to vague forms
        # ("in March") even with MANDATORY DATES in the prompt.
        if task_key == "draft":
            mandatory_dates = _extract_dates(text)
            for attempt in range(2):
                missing_dates = [
                    d for d in mandatory_dates
                    if not re.search(re.escape(d), out, re.I)
                ]
                if not missing_dates:
                    break
                task_obj = TASKS[task_key]
                s_sys, s_usr = task_obj.build(
                    text, kw.get("instruction", ""),
                    kw.get("tone", ""), kw.get("style_sample", ""),
                )
                missing_str = ", ".join(missing_dates)
                severity = "CRITICAL FAILURE" if attempt else "MANDATORY DATES MISSING"
                extra = (
                    f"\n\n{severity}: A previous attempt dropped these required dates — "
                    f"each MUST appear VERBATIM in your output: {missing_str}. "
                    "Do not paraphrase (e.g., 'in March' is NOT acceptable when the brief "
                    "says 'March 11'). Use the exact date as given in the brief."
                )
                temp = 0.3 if attempt else 0.4
                regen = "".join(self.engine.stream(
                    messages=[
                        {"role": "system", "content": s_sys + extra},
                        {"role": "user", "content": s_usr},
                    ],
                    max_tokens=kw.get("max_tokens", 1200),
                    temperature=temp,
                )).strip()
                recovered = [d for d in missing_dates
                             if re.search(re.escape(d), regen, re.I)]
                if recovered:
                    log.info("secretary[draft]: regen recovered dates %s", recovered)
                    out = regen
        # Post-check for draft: if the model invented specific day names not present
        # in the brief, replace them with [day] (regression from sec-missing-facts).
        if task_key == "draft":
            _DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday",
                     "saturday", "sunday"]
            text_lower = text.lower()
            for day in _DAYS:
                if day not in text_lower and day in out.lower():
                    out = re.sub(r'\b' + day + r'\b', '[day]', out, flags=re.IGNORECASE)
                    log.info("secretary[draft]: replaced invented day '%s' with [day]", day)
        # Post-check for draft/reply: model sometimes generates a stub — only a
        # subject line or salutation with no body. Detect by stripping lines that
        # are subject headers ("Subject: ..."), salutation/sign-off lines (end with
        # comma), and placeholder lines ("[Name]") — if nothing real remains, regen
        # up to 3 times with escalating body instruction at lower temperature.
        if task_key in ("draft", "reply"):
            def _draft_is_stub(s):
                rls = [l.strip() for l in s.splitlines() if l.strip()]
                cls = [l for l in rls
                       if not re.match(r'^subject:', l, re.I)
                       and not re.match(r'.*,$', l)
                       and not re.match(r'^\[', l)]
                return not cls

            if _draft_is_stub(out):
                task_obj = TASKS[task_key]
                s_sys, s_usr = task_obj.build(
                    text, kw.get("instruction", ""),
                    kw.get("tone", ""), kw.get("style_sample", ""),
                )
                body_extra = (
                    "\n\nCRITICAL: You MUST write the complete body of the message. "
                    "Do NOT generate only a subject line or salutation. "
                    "After any greeting line (Dear X / Hi X / Subject: Y), "
                    "write the body IMMEDIATELY — at least 2–3 full sentences of substance."
                )
                for attempt in range(3):
                    log.warning("secretary[%s]: stub output — body regen attempt %d",
                                task_key, attempt + 1)
                    temp = 0.25 if attempt >= 1 else 0.3
                    regen = "".join(self.engine.stream(
                        messages=[
                            {"role": "system", "content": s_sys + body_extra},
                            {"role": "user", "content": s_usr},
                        ],
                        max_tokens=kw.get("max_tokens", 1200),
                        temperature=temp,
                    )).strip()
                    if not _draft_is_stub(regen):
                        out = regen
                        break
                    log.warning("secretary[%s]: regen attempt %d still stub", task_key, attempt + 1)
                else:
                    out = regen  # use last attempt even if stub
        return UtilityResult(task=task_key, output=out)


def task_catalog() -> list[dict]:
    """Serializable task list for the UI to render its selector."""
    return [
        {"key": t.key, "label": t.label, "blurb": t.blurb,
         "input_label": t.input_label, "wants_instruction": t.wants_instruction,
         "wants_tone": t.wants_tone}
        for t in TASKS.values()
    ]
