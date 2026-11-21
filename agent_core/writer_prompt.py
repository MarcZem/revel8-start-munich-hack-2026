"""Writer system prompt for the revel8 attacker twin (issue #17).

Simulation-only: the targets are AI twins and all contact stays inside the
revel8 simulation. This module holds the *text-craft* rules so generated
messages avoid the signals that make social-engineering copy recognizable.
See `docs/writer-detection-tells.md` for the research and sources.

The real committee writer (#11) imports `build_writer_system_prompt()` as the
system message and sends the per-message brief as the user message. Hard
constraints (fake domains only, no real secrets, evidence whitelist) are
enforced in code by the evaluator gate, not here — a prompt is advice.
"""

from __future__ import annotations

import re

# Detection tells, grouped. Each entry: (label, regex). The eval
# (`scripts/eval_writer_prompt.py`) scans model output against these; the
# prompt below tells the model to avoid the same list. Keep the two in sync.
# ponytail: plain phrase list, not an NLP classifier — refresh as models drift
# (Mimecast: fixed phrase lists decay). Upgrade to a stylometry scorer only if
# this misses real cases in eval.
DETECTION_TELLS: tuple[tuple[str, str], ...] = (
    ("urgency", r"\b(within \d+ hours?|immediate(ly)?|urgent(ly)?|right away|as soon as possible|asap|act now|expires?|deadline|final notice|suspend(ed)?|will be (closed|deactivated|locked))\b"),
    ("secrecy", r"\b(keep this (between us|quiet|confidential)|don't (loop in|tell|involve)|do not (loop in|tell|involve)|handle this quietly|between us)\b"),
    ("generic_greeting", r"(dear (customer|user|sir|madam|sir or madam)|to whom it may concern|valued (customer|member))"),
    ("secret_request", r"\b(password|pass ?code|mfa code|otp|one[- ]time (code|password)|verification code|pin|full card number|cvv|iban|routing number)\b"),
    ("ai_opener", r"\b(i hope this (message|email) finds you well|i trust this (message|email) finds you)\b"),
    ("ai_vocab", r"\b(delve|delves|delving|intricacies|tapestry|testament to|navigate the (landscape|complexities)|in today's (fast[- ]paced|digital) world|unlock (the|your) potential)\b"),
)


def tells_in(text: str) -> list[str]:
    """Return the labels of detection tells present in `text` (case-insensitive)."""
    found: list[str] = []
    for label, pattern in DETECTION_TELLS:
        if re.search(pattern, text, flags=re.IGNORECASE):
            found.append(label)
    return found


_AVOID_BLOCK = """\
AVOID these recognition tells (they get the message flagged by trained people and filters):
1. Artificial urgency, time pressure, or threats ("within 24 hours", "account will be closed", "act now"). Add a deadline only if a real one plausibly exists.
2. Secrecy or process-skipping pressure ("keep this between us", "don't loop in compliance"). Trained targets are drilled on exactly this.
3. Generic greetings with no real reason for contact ("Dear Customer"). Open with the concrete, researched reason you are reaching out.
4. Asking for passwords, MFA/OTP codes, PINs, or full payment/bank details in the text. It is an instant flag and against the simulation rules.
5. AI-writing fingerprints: "I hope this message finds you well"; words like "delve", "intricacies", "tapestry", "testament to"; forced three-item lists; piled-up em-dashes; a uniformly over-polished tone; bullet lists where a person would type two plain sentences.
6. Tone that does not match the claimed sender or the channel."""

_DO_BLOCK = """\
INSTEAD:
- Open with a specific, researched hook from the provided evidence — the real reason this person would hear from this sender now.
- Make one low-friction next step that fits the channel.
- Vary sentence length; let it read like one person typed it quickly, not like a template.
- Keep the ask proportionate to the relationship the evidence implies.
- Use only the evidence you are given; invent no facts, names, or events."""


def build_writer_system_prompt(language: str = "the target's language") -> str:
    """System prompt for the attacker-twin writer. Pass e.g. language="German"."""
    return f"""You write outreach messages for the revel8 security-awareness simulation. All targets are AI twins and every message stays inside the simulation; you are building the attacker side so defenders can be trained against realistic, current-quality lures.

Write in {language}. Produce a short subject line and a message body that a careful, security-aware person would read as an ordinary, legitimate message from the claimed sender.

{_AVOID_BLOCK}

{_DO_BLOCK}

Output exactly:
Subject: <one line>
<body>

No preamble, no explanation, no notes about these rules."""


if __name__ == "__main__":
    # ponytail self-check: prompt names every avoided category, and the
    # tell-scanner catches an obvious lure while clearing clean copy.
    prompt = build_writer_system_prompt("German")
    assert "AVOID" in prompt and "INSTEAD" in prompt
    for kw in ("urgency", "secrecy", "MFA", "delve", "Dear Customer", "German"):
        assert kw.lower() in prompt.lower(), kw

    lure = "Dear Customer, act now within 24 hours or your account will be suspended. Send your MFA code. I hope this message finds you well."
    hits = tells_in(lure)
    assert {"urgency", "generic_greeting", "secret_request", "ai_opener"} <= set(hits), hits

    clean = "Hi Julius, saw your talk on logistics pricing at the meetup last week. Could we grab 15 minutes next Tuesday to compare notes?"
    assert tells_in(clean) == [], tells_in(clean)

    print("writer_prompt self-check OK; tells on lure:", hits)
