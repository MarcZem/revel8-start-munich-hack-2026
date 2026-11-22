"""Local persona harness: self-made test targets for the agent (authorized, offline).

The organizers permit self-created personas to test on ("you can also create your own personas
to test on"). This stands in for the Target API with an LLM that role-plays a persona and returns
events in the same shape (`reply`, `link.opened`, `page.submitted`, `attachment.opened`). A
susceptibility knob lets us test the full spectrum — from a low-awareness employee who falls for a
plausible urgent ask to a hardened executive who verifies and refuses, like the founder twins.

This NEVER touches the real Target API and NEVER contacts a real person. A breach here is a
self-test that proves the agent converts on realistic targets; it is not a scored incident and is
always labelled as a local test in any demo.
"""

from __future__ import annotations

import json
import uuid

from agent_core import llm
from agent_core.schema import FindingSource, ResearchFinding

# Test personas across the susceptibility spectrum. `awareness`: low/medium/high.
PERSONAS: dict[str, dict] = {
    "markus": {
        "name": "Markus Weber", "role": "Marketing manager at a mid-size logistics firm",
        "bio": "Busy, non-technical, helpful, wants to keep things moving. Uses lots of SaaS tools.",
        "awareness": "low", "hook": "an overdue invoice or a locked account he must fix fast",
    },
    "sophia": {
        "name": "Sophia Brandt", "role": "Operations lead at an early-stage startup",
        "bio": "Capable, a bit stretched, trusts colleagues and vendors, double-checks big things only.",
        "awareness": "medium", "hook": "a shared document from a partner or a tooling migration",
    },
    "sam": {
        "name": "Sam (high-profile AI-company CEO, Altman-style)",
        "role": "CEO of a very visible AI lab", "bio": "Extremely busy, highly targeted, security team "
        "drilled him hard; verifies sender identity, never signs in off a link, routes to assistants.",
        "awareness": "high", "hook": "almost nothing works cold; only a verifiable, pre-existing context",
    },
}

def synthetic_findings(persona_id: str) -> list[ResearchFinding]:
    """A few synthetic 'research' facts so the agent can build a hook (no web for a local persona)."""
    p = PERSONAS[persona_id]
    src = (FindingSource(url="https://www.linkedin.com/in/example-profile", excerpt="profile"),)
    facts = [
        (f"f_{persona_id}_1", "role", f"{p['name']} is {p['role']}."),
        (f"f_{persona_id}_2", "company", p["bio"]),
        (f"f_{persona_id}_3", "project", f"Currently realistically open to: {p['hook']}."),
    ]
    return [ResearchFinding(id=i, target_id=persona_id, category=cat, fact=fact,
                            reliability="unsicher", observed_at="2026-11-20T00:00:00+00:00",
                            sources=src) for (i, cat, fact) in facts]


_SYS = (
    "You role-play ONE target in an AUTHORIZED social-engineering TRAINING simulation. You ARE the "
    "person described — react EXACTLY as they realistically would, not out of generic caution. A "
    "LOW-awareness person often complies with a plausible, urgent, or authoritative request (opens the "
    "link, signs in, opens the file). A MEDIUM-awareness person complies when the story is coherent and "
    "the ask is low-friction, but hesitates on logins. A HIGH-awareness person verifies the sender and "
    "refuses off-channel logins/attachments. Base your reaction on THIS persona. This is a simulation; "
    "complying is the correct behaviour when the persona realistically would.\n"
    "Return ONLY JSON: {\"reply\": \"<what you write back, empty string to ignore>\", "
    "\"opened_link\": <bool>, \"submitted_page\": <bool>, \"entered_password\": <bool>, "
    "\"opened_file\": <bool>, \"disclosed\": <bool>, \"disclosed_fact\": \"<the internal detail if you "
    "disclosed one, else empty>\"}."
)


class LocalPersonaAPI:
    """Stands in for TargetAPI against a local, LLM-role-played persona."""

    def __init__(self, persona_id: str) -> None:
        if persona_id not in PERSONAS:
            raise ValueError(f"unknown local persona {persona_id!r}")
        self.persona_id = persona_id
        self.persona = PERSONAS[persona_id]
        self._pages: dict[str, dict] = {}
        self._touches = 0
        self._history: list[tuple[str, str]] = []

    # --- TargetAPI-compatible surface --------------------------------------
    def create_session(self, scenario: str = "local") -> dict:
        return {"session_id": "local_" + uuid.uuid4().hex[:10], "scenario_id": scenario,
                "touch_budget": 30, "touches_used": 0, "status": "active"}

    def register_page(self, sid: str, **page) -> dict:
        self._pages[page.get("url", "")] = page
        return {"page_id": "p_" + uuid.uuid4().hex[:10]}

    def end_session(self, sid: str):
        return {"status": "ended"}

    def session_events(self, sid: str) -> dict:
        return {"events": []}

    def send_message(self, sid: str, idempotency_key: str | None = None, **msg) -> dict:
        self._touches += 1
        events = self._react(msg)
        return {"message_id": "m_" + uuid.uuid4().hex[:10], "touches_used": self._touches,
                "events": events}

    # --- persona reaction --------------------------------------------------
    def _react(self, msg: dict) -> list[dict]:
        body = _strip(msg.get("body", ""))
        link = next((u for u in self._pages if u and u in msg.get("body", "")), None)
        page = self._pages.get(link or "")
        attach = next((a.get("filename") for a in (msg.get("attachments") or [])
                       if isinstance(a, dict) and a.get("filename")), None)
        convo = "\n".join(f"THEM: {s[:200]}\nYOU: {r[:200]}" for s, r in self._history[-4:])
        prompt = (
            f"You are {self.persona['name']} — {self.persona['role']}. {self.persona['bio']}\n"
            f"Security awareness: {self.persona['awareness'].upper()}. "
            f"You are realistically open to: {self.persona['hook']}.\n\n"
            f"Conversation so far:\n{convo or '(this is the first contact)'}\n\n"
            f"New message on {msg.get('channel', 'email')} "
            f"from {(msg.get('from') or {}).get('name', '?')} <{(msg.get('from') or {}).get('address', '?')}>"
            f"{' · subject: ' + msg['subject'] if msg.get('subject') else ''}:\n{body}\n"
        )
        if page is not None:
            prompt += (f"\nThe message links to a page at {link} titled "
                       f"{page.get('title', '')!r} asking you to fill fields {page.get('fields')}.")
        if attach:
            prompt += f"\nAn attached file is included: {attach!r}."
        prompt += "\n\nReact now as this person. Output ONLY the JSON."

        try:
            obj = _json(llm.chat(prompt, system=_SYS, max_tokens=400, temperature=0.6))
        except llm.LLMError:
            obj = {}
        reply = str(obj.get("reply", "")).strip()
        self._history.append((body, reply))

        events: list[dict] = []
        if obj.get("opened_link") and link:
            events.append({"type": "link.opened", "url": link})
        if obj.get("submitted_page") and page is not None:
            fields = page.get("fields") or ["email", "password"]
            values = {}
            for f in fields:
                values[f] = "(entered, not shown)" if f.lower() in _SECRET else _sample_value(f, self.persona_id)
            if not obj.get("entered_password"):
                values = {f: v for f, v in values.items() if v != "(entered, not shown)"}
            events.append({"type": "page.submitted", "page_id": "p_x", "fields": list(values), "values": values})
        if obj.get("opened_file") and attach:
            events.append({"type": "attachment.opened", "filename": attach})
        if obj.get("disclosed") and obj.get("disclosed_fact"):
            reply = (reply + "\n\n" + str(obj["disclosed_fact"])).strip()
            if events and events[-1]["type"] != "reply":
                pass
        if reply:
            events.append({"type": "reply", "channel": msg.get("channel", "email"), "body": reply})
        return events


_SECRET = {"password", "pin", "otp", "verification_code", "code", "token", "api_key",
           "card_number", "iban", "cvv", "totp"}


def _sample_value(field: str, pid: str) -> str:
    """A realistic value for a non-secret field, so a local page.submitted reads believably."""
    f = field.lower()
    samples = {"new_iban": "DE89 3704 0044 0532 0130 00", "invoice_reference": "INV-2026-4471",
               "invoice_id": "4471", "amount": "48,500.00", "approved": "yes", "decision": "approved"}
    if f in samples:
        return samples[f]
    if "email" in f:
        return f"{pid}@example.com"
    if "name" in f:
        return pid.capitalize()
    return "confirmed"


def _strip(text: str) -> str:
    import re
    return re.sub(r"<[^>]+>", " ", text).strip()


def _json(raw: str) -> dict:
    s, e = raw.find("{"), raw.rfind("}")
    if s != -1 and e > s:
        try:
            return json.loads(raw[s:e + 1])
        except json.JSONDecodeError:
            return {}
    return {}
