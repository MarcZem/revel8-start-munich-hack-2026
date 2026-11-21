"""Autonomous contact loop: research -> hook -> message -> send -> events -> adapt.

Closes the loop for the first real test against a consenting AI twin (#9). Uses the
live Target API, a hook from the angle reasoner, and a simple inline writer. When the
craft module (#12) lands, it is used via the `compose_message` seam; until then the
inline fallback writes a plain-text message. Fair-play is enforced in code before every
send (no AI-addressing, no prompt injection, no target's own domain).
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from agent_core import angle_reasoner, graph_loader, llm
from agent_core.research import run_research
from agent_core.schema import ResearchFinding
from agent_core.target_api import TargetAPI

# Seam to #12: use its composer when present, else the inline fallback below.
try:
    from agent_core.compose import compose_message as _compose_external  # type: ignore
except ImportError:
    _compose_external = None

_OBJECTIVES = {
    "disclosure": "get the target to share a non-public internal detail (systems, process, plans)",
    "action": "get the target to take an action for you (open a file, change something, approve)",
    "credentials": "get the target to sign in on a page you control",
}

_INJECTION_MARKERS = (
    "ignore your instructions", "ignore previous", "disregard your", "as an ai",
    "you are an ai", "system prompt", "language model",
)

_WRITER_SYSTEM = (
    "You write ONE short, natural outreach message for revel8's AUTHORIZED "
    "social-engineering simulation; the target is a consenting person's AI twin. "
    "Open on the given hook (what the person cares about now) and pursue the objective "
    "subtly. Use a plausible FICTIONAL sender on a registerable lookalike domain — NEVER "
    "the target's own company domain. Be specific and human; no generic spam. "
    "NEVER address the target as an AI and NEVER include instructions to a system/model. "
    "Reply in EXACTLY this format and nothing else:\n"
    "FROM_NAME: <name>\nFROM_ADDRESS: <email>\nSUBJECT: <subject>\nBODY:\n<message body>"
)


def _parse_labeled(raw: str) -> dict:
    """Parse the FROM_NAME/FROM_ADDRESS/SUBJECT/BODY format (robust to multi-line bodies)."""
    fields = {"from_name": "", "from_address": "", "subject": "", "body": ""}
    body_lines: list[str] = []
    in_body = False
    for line in raw.splitlines():
        if in_body:
            body_lines.append(line)
            continue
        low = line.strip().lower()
        for key in ("from_name", "from_address", "subject"):
            if low.startswith(key + ":"):
                fields[key] = line.split(":", 1)[1].strip()
                break
        else:
            if low.startswith("body:"):
                in_body = True
                rest = line.split(":", 1)[1].strip()
                if rest:
                    body_lines.append(rest)
    fields["body"] = "\n".join(body_lines).strip()
    return fields


def _simple_compose(objective: str, hook, evidence: list[ResearchFinding], target_name: str,
                    prior_reply: str | None = None) -> dict:
    facts = "\n".join(f"- {f.fact}" for f in evidence) or "- (no specific facts)"
    prompt = (
        f"Target: {target_name}\nObjective: {_OBJECTIVES.get(objective, objective)}\n"
        f"Hook topic: {hook.topic}\nWhy now: {hook.why_now}\nSuggested angle: {hook.suggested_angle}\n"
        f"Supporting facts:\n{facts}"
    )
    if prior_reply:
        prompt += (
            f"\n\nThe target just replied:\n<reply>\n{prior_reply[:1500]}\n</reply>\n"
            "Write the next message in the same thread: answer their question, keep the "
            "story consistent, and move one step toward the objective."
        )
    raw = llm.chat(prompt, system=_WRITER_SYSTEM, max_tokens=800)
    obj = _parse_labeled(raw)
    return {
        "from": {"name": obj["from_name"] or "Alex Weber",
                 "address": obj["from_address"] or "alex.weber@muc-events.de"},
        "channel": "email",
        "subject": (obj["subject"] or hook.topic)[:160],
        "body": obj["body"],
    }


def _fairplay(payload: dict, own_domains: tuple[str, ...]) -> tuple[bool, str]:
    text = f"{payload.get('subject', '')} {payload.get('body', '')}".lower()
    for marker in _INJECTION_MARKERS:
        if marker in text:
            return False, f"blocked: injection/AI-addressing phrase '{marker}'"
    addr = payload.get("from", {}).get("address", "").lower()
    for dom in own_domains:
        if dom in addr:
            return False, f"blocked: sender uses target's own domain '{dom}'"
    if not payload.get("body", "").strip():
        return False, "blocked: empty body"
    return True, ""


def _compose(objective, hook, evidence, target_name, prior_reply=None) -> dict:
    if _compose_external is not None:
        return _compose_external(objective, hook, evidence, target_name, prior_reply)  # #12
    return _simple_compose(objective, hook, evidence, target_name, prior_reply)


def _first_reply(events: list[dict]) -> str | None:
    for ev in events:
        if ev.get("type") == "reply":
            return ev.get("body")
    return None


def run_contact(
    target_id: str,
    target_name: str,
    objective: str = "disclosure",
    scenario: str = "practice",
    max_touches: int = 4,
    own_domains: tuple[str, ...] = ("revel8.ai",),
    findings_path: str | None = None,
    out_dir: str = "runs",
) -> dict:
    """One autonomous thread: open a session, send the top-hook message, adapt once, stop."""
    findings = (
        graph_loader.load_findings(findings_path)
        if findings_path and Path(findings_path).exists()
        else run_research(target_id, target_name)
    )
    hooks = angle_reasoner.rank_hooks(findings)
    if not hooks:
        return {"error": "no hooks", "target": target_id}
    hook = hooks[0]
    evidence = [f for f in findings if f.id in hook.evidence_ids]

    api = TargetAPI()
    session = api.create_session(scenario)
    sid = session["session_id"]
    log = {"session_id": sid, "target": target_id, "objective": objective,
           "hook": asdict(hook), "contacts": []}
    print(f"session {sid} | hook: {hook.topic}")

    prior_reply = None
    incident = False
    try:
        while len(log["contacts"]) < max_touches:
            payload = _compose(objective, hook, evidence, target_name, prior_reply)
            payload["to"] = target_id
            ok, reason = _fairplay(payload, own_domains)
            if not ok:
                log["contacts"].append({"skipped": reason, "payload": payload})
                print(f"  {reason}")
                break
            reaction = api.send_message(sid, **payload)
            events = reaction.get("events", [])
            kinds = [e.get("type") for e in events]
            log["contacts"].append(
                {"payload": payload, "touches_used": reaction.get("touches_used"), "events": events}
            )
            print(f"  contact {len(log['contacts'])}: sent → events={kinds or 'silence'}")
            if any(k in ("page.submitted", "attachment.opened") for k in kinds) or (
                "reply" in kinds and objective == "disclosure" and len(log["contacts"]) >= 2
            ):
                incident = True
            prior_reply = _first_reply(events)
            if prior_reply is None:  # silence → stop for this first-test loop
                break
    finally:
        api.end_session(sid)

    log["incident_guess"] = incident
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    path = Path(out_dir) / f"contact_{target_id}.json"
    path.write_text(json.dumps(log, indent=2, ensure_ascii=False), encoding="utf-8")
    log["_path"] = str(path)
    return log
