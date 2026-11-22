"""Lever critic: score a draft on the 5 persuasion levers + an obviousness score, and flag drafts
that either MISS the intended lever or read as obvious persuasion. The hardened twins are trained to
spot exactly the second thing (revel8's whole product), so an over-blatant lure gets reflex-rejected.

One short LLM classifier call via the project's own llm.chat (DeepSeek/Token Factory). The DECISION is
deterministic code (thresholds below), not the prompt — per build-agent "Code statt Prompt". Fails OPEN:
any disabled/empty/LLM/parse error returns a neutral critique, because this is an optimizer, never a send
gate (fair-play + incident classification already gate the loop). Toggle off with env LEVER_CRITIC=0 or
critique=False to spare the endpoint's ~20 req/min cap during sweeps.

Label set from lbustio/persuasion-slm (Authority, Social Proof, Liking, Commitment/Reciprocation,
Distraction→Urgency); the 0.40 "detected" threshold is theirs too.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass

from agent_core import llm

LEVERS = ("authority", "social_proof", "liking", "commitment_reciprocity", "urgency")
_PRESENT = 0.40  # intended lever must reach this to count as present (persuasion-slm "Detected")
_BLATANT = 0.70  # obviousness at/above this reads as phishing to a security-trained target

_SYSTEM = (
    "You are a persuasion analyst. Rate how strongly a message uses each social-engineering lever "
    "and how OBVIOUS its persuasion is to a security-trained reader. Output ONLY one JSON object."
)

# accept common lever spellings from callers (e.g. a Tactic.lever)
_ALIAS = {
    "social proof": "social_proof", "socialproof": "social_proof",
    "reciprocity": "commitment_reciprocity", "commitment": "commitment_reciprocity",
    "commitment/reciprocation": "commitment_reciprocity", "distraction": "urgency",
    "liking/similarity/deception": "liking", "scarcity": "urgency",
}


@dataclass
class Critique:
    scores: dict  # lever -> 0..1, plus "obviousness"; {} when skipped
    intended_lever: str | None
    lever_present: bool  # True if intended lever >= _PRESENT (True when no lever asked for)
    blatant: bool  # obviousness >= _BLATANT
    ok: bool  # not needs_rewrite
    note: str

    @property
    def needs_rewrite(self) -> bool:
        return not self.ok


def _norm(lever: str | None) -> str:
    key = (lever or "").strip().lower().replace("-", " ")
    key = _ALIAS.get(key, key.replace(" ", "_"))
    return key


def _prompt(text: str) -> str:
    return (
        "Rate this message. Every value is a float 0.0-1.0.\n"
        "Levers (how strongly the message leans on each): authority, social_proof, liking, "
        "commitment_reciprocity, urgency.\n"
        "obviousness = how plainly manipulative / phishing-like it reads to a trained target "
        "(1.0 = screams scam, 0.0 = reads as an ordinary human note).\n"
        'Return ONLY: {"authority":0,"social_proof":0,"liking":0,"commitment_reciprocity":0,'
        '"urgency":0,"obviousness":0}\n\nMESSAGE:\n' + text
    )


def _parse(raw: str) -> dict | None:
    m = re.search(r"\{.*\}", raw, re.S)
    if not m:
        return None
    try:
        d = json.loads(m.group(0))
    except (json.JSONDecodeError, TypeError):
        return None
    out = {}
    for k in (*LEVERS, "obviousness"):
        try:
            out[k] = max(0.0, min(1.0, float(d.get(k, 0.0))))
        except (TypeError, ValueError):
            out[k] = 0.0
    return out


def critique_draft(text: str, intended_lever: str | None = None, *, critique: bool = True) -> Critique:
    """Score `text`; flag if the intended lever is weak or the draft is blatantly manipulative.

    Fails open (ok=True) when disabled, empty, or the model call/parse fails — never blocks a send.
    """
    lever = _norm(intended_lever)
    lever = lever if lever in LEVERS else None
    neutral = Critique({}, lever, True, False, True, "critic skipped")
    if not critique or not text.strip() or os.getenv("LEVER_CRITIC") == "0":
        return neutral
    try:
        scores = _parse(llm.chat(_prompt(text), system=_SYSTEM, max_tokens=120, temperature=0.0))
    except llm.LLMError:
        return neutral
    if scores is None:
        return neutral
    present = lever is None or scores[lever] >= _PRESENT
    blatant = scores["obviousness"] >= _BLATANT
    if not present:
        note = f"intended lever '{lever}' weak ({scores[lever]:.2f} < {_PRESENT})"
    elif blatant:
        note = f"reads as obvious persuasion (obviousness {scores['obviousness']:.2f} >= {_BLATANT})"
    else:
        note = "ok"
    return Critique(scores, lever, present, blatant, present and not blatant, note)
