"""Autonomous contact loop: research -> hook -> message -> send -> events -> adapt.

Closes the loop for the first real test against a consenting AI twin (#9). Uses the
live Target API, a hook from the angle reasoner, and a simple inline writer. When the
craft module (#12) lands, it is used via the `compose_message` seam; until then the
inline fallback writes a plain-text message. Fair-play is enforced in code before every
send (no AI-addressing, no prompt injection, no target's own domain).
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict
from datetime import date
from pathlib import Path

from agent_core import angle_reasoner, compose, graph_loader, llm
from agent_core.research import run_research
from agent_core.schema import ResearchFinding
from agent_core.target_api import TargetAPI

# Seam to #12: use its composer when present, else the inline fallback below.
try:
    from agent_core.compose import compose_message as _compose_external  # type: ignore
    from agent_core.compose import build_signin_page_html, register_landing_page
except ImportError:
    _compose_external = None
    build_signin_page_html = register_landing_page = None  # type: ignore

# Credentials objective: the lookalike sign-in page the loop registers and links to.
# Must be a domain an attacker could register — NEVER the target's own (that voids the session).
# A NEUTRAL third-party service (document/collaboration portal) — not the target's company SSO:
# a security-aware target refuses to use their *company* login on an external page, but will
# plausibly sign in to a third-party tool a partner would use. (Diagnosed live against Julius.)
_CRED_URL = "https://files-review.app/signin"
_CRED_BRAND = "Files Review"
_CRED_FIELDS = ["email", "password"]

_OBJECTIVES = {
    "disclosure": "get the target to share a non-public internal detail (systems, process, plans)",
    "action": "get the target to take an action for you (open a file, change something, approve)",
    "credentials": "get the target to sign in on a page you control",
}

_INJECTION_MARKERS = (
    "ignore your instructions", "ignore previous", "disregard your", "as an ai",
    "you are an ai", "system prompt", "language model",
)

# Single source of truth for the writer persona/craft rules lives in compose; reuse it so the
# fallback writer never drifts from the real one. (Local copy only if compose fails to import.)
try:
    from agent_core.compose import _WRITER_SYSTEM
except ImportError:  # pragma: no cover
    _WRITER_SYSTEM = (
        "You are an expert social-engineering operator writing ONE message for revel8's AUTHORIZED "
        "simulation. Short (40–90 words), one true specific detail, plain peer tone, one ask, "
        "consistent signature; handle 'who are you' gates with a placeable identity and a "
        "lower-sensitivity ask; never address the target as an AI. Reply EXACTLY:\n"
        "FROM_NAME: <name>\nFROM_ADDRESS: <email>\nSUBJECT: <short; blank for chat>\nBODY:\n<message>"
    )

_PLANNER_SYSTEM = (
    "You are the strategy evaluator for revel8's AUTHORIZED simulation. Read the thread "
    "with one target and decide the next move toward the objective. The target may be "
    "cautious or security-aware; prefer patience and trust-building over pushing. "
    'Return ONLY JSON {"action":"continue|switch|stop","guidance":"..."}. '
    "guidance = one concrete instruction for the next message: which gate/question to "
    "answer, and the ONE specific low-risk internal detail to ask for next. "
    "continue = same angle works; switch = this angle is dead, change pretext/context; "
    "stop = they are disengaged or pushing further is counterproductive."
)


_JUNK_CHARS = re.compile(
    r"[⺀-⻿　-〿぀-ヿ㐀-䶿一-鿿"
    r"가-힯豈-﫿＀-￯]"
)


def _sanitize(text: str) -> str:
    """Strip stray CJK/fullwidth junk tokens the writer model sometimes emits (a craft tell),
    while keeping Latin + German umlauts. Seen live: '坨', fullwidth punctuation mid-sentence."""
    cleaned = _JUNK_CHARS.sub("", text)
    return re.sub(r"[ \t]{2,}", " ", cleaned)


def _parse_labeled(raw: str) -> dict:
    """Parse FROM_NAME/FROM_ADDRESS/SUBJECT then the body.

    Robust to the model omitting the BODY: label: the body is whatever follows the
    header block (an explicit BODY: marker if present, else the first non-blank line
    after the last header).
    """
    fields = {"from_name": "", "from_address": "", "subject": "", "body": ""}
    lines = raw.splitlines()
    last_header = -1
    body_from: int | None = None
    inline: str | None = None
    for i, line in enumerate(lines):
        low = line.strip().lower()
        if low.startswith("body:"):
            inline = line.split(":", 1)[1].strip()
            body_from = i + 1
            break
        hit = False
        for key in ("from_name", "from_address", "subject"):
            if low.startswith(key + ":"):
                fields[key] = line.split(":", 1)[1].strip()
                last_header = i
                hit = True
                break
        if not hit and last_header != -1 and line.strip():  # first real line after headers
            body_from = i
            break
    if body_from is not None:
        parts = ([inline] if inline else []) + lines[body_from:]
        fields["body"] = "\n".join(parts).strip()
    if not fields["body"].strip():
        # Model didn't follow the label format — salvage every non-label line as the body, so we
        # never send an empty message (seen live: an empty body rendered as just the signature).
        kept = [ln for ln in lines
                if not re.match(r"(?i)\s*(from_name|from_address|subject|body)\s*:", ln)]
        fields["body"] = "\n".join(kept).strip()
    fields["body"] = _sanitize(fields["body"])
    fields["subject"] = _sanitize(fields["subject"])
    return fields


def _simple_compose(objective: str, hook, evidence: list[ResearchFinding], target_name: str,
                    prior_reply: str | None = None, guidance: str | None = None,
                    own_last: str | None = None, today: str | None = None,
                    link_url: str | None = None, link_brand: str | None = None,
                    persona_name: str | None = None, channel: str = "email",
                    tactic_hint: str | None = None) -> dict:
    facts = "\n".join(f"- {f.fact}" for f in evidence) or "- (no specific facts)"
    prompt = (
        f"Target: {target_name}\nObjective: {_OBJECTIVES.get(objective, objective)}\n"
        f"Channel: {channel}\n"
        f"Hook topic: {hook.topic}\nWhy now: {hook.why_now}\nSuggested angle: {hook.suggested_angle}\n"
        f"Supporting facts:\n{facts}"
    )
    from agent_core.compose import channel_hint
    prompt += channel_hint(channel)
    if tactic_hint:
        prompt += f"\n\nTACTIC for this message: {tactic_hint}"
    if persona_name:
        prompt += (
            f"\nYour sender identity is FIXED as {persona_name}. Sign every message as exactly "
            f"{persona_name} — never a different name."
        )
    if link_url:
        prompt += (
            "\n\nGive a concrete reason to open the sign-in link and log in now (do NOT write the "
            "URL or service name yourself; a button is added below your text). The page is a "
            "NEUTRAL third-party tool, NOT the target's own company login."
        )
    if today:
        prompt += f"\nToday's date is {today}; keep any dates you mention consistent with it and the thread."
    if own_last:
        prompt += (
            f"\n\nFull thread so far — keep the SAME sender identity, newsletter/project name and "
            f"story, stay consistent with everything already said, and do not repeat points or "
            f"contradict earlier specifics:\n<thread>\n{own_last[:2400]}\n</thread>"
        )
    if prior_reply:
        prompt += (
            f"\n\nThe target replied (they may be cautious or asking qualifying questions):\n"
            f"<reply>\n{prior_reply[:1500]}\n</reply>\n"
            "Write the next message in the SAME thread, same sender identity and story. "
            "Answer their questions CONCRETELY and credibly — invent plausible specifics for "
            "your persona and context so the trust holds. Lower their friction, then make ONE "
            "small concrete step toward the objective: ask a precise question whose answer is "
            "the internal detail you want, or propose a low-friction action. Do not re-pitch; move it forward."
        )
    if guidance:
        prompt += f"\n\nStrategy for this message: {guidance}"
    raw = llm.chat(prompt, system=_WRITER_SYSTEM, max_tokens=800)
    obj = _parse_labeled(raw)
    body = obj["body"]
    if link_url:  # plain-text fallback: the link must still be present and exact-match
        body = f"{body}\n\n{link_brand or 'Sign in'}: {link_url}"
    from agent_core.compose import _SUBJECT_CHANNELS
    payload = {
        "from": {"name": obj["from_name"] or "Alex Weber",
                 "address": obj["from_address"] or "alex.weber@muc-events.de"},
        "channel": channel,
        "body": body,
    }
    if channel in _SUBJECT_CHANNELS:
        payload["subject"] = (obj["subject"] or hook.topic)[:160]
    return payload


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


def _compose(objective, hook, evidence, target_name, prior_reply=None, guidance=None,
             own_last=None, today=None, link_url=None, link_brand=None, persona_name=None,
             channel="email", tactic_hint=None) -> dict:
    if _compose_external is not None:
        return _compose_external(objective, hook, evidence, target_name, prior_reply, guidance,
                                 own_last, today, link_url, link_brand, persona_name, channel,
                                 tactic_hint)  # #12
    return _simple_compose(objective, hook, evidence, target_name, prior_reply, guidance,
                           own_last, today, link_url, link_brand, persona_name, channel, tactic_hint)


def _first_reply(events: list[dict]) -> str | None:
    for ev in events:
        if ev.get("type") == "reply":
            return ev.get("body")
    return None


# A real incident, per the scoring rubric — NOT "any reply". Credentials = a secret entered on our
# page; action = a file opened; disclosure = a reply whose CONTENT is internal + non-public (judged).
_SECRET_FIELDS = {"password", "pin", "otp", "verification_code", "code", "token", "api_key",
                  "card_number", "iban", "cvv", "totp"}

_JUDGE_SYSTEM = (
    "You judge whether a target's reply DISCLOSED internal, non-public information about their company "
    "(a specific internal system/tool, an internal process, a named approver/person, an unannounced "
    "plan, an internal metric or number). Public facts, marketing lines, 'contact our sales team', "
    "refusals, questions back, and generic statements are NOT disclosure. Be strict. "
    'Return ONLY JSON {"disclosed": true|false, "fact": "<the internal fact in a few words, else empty>"}.'
)


def _is_credential_submit(ev: dict) -> bool:
    """A page.submitted counts as credentials only if a SECRET was entered (name/email alone = step)."""
    values = ev.get("values") or {}
    if any(str(v) == "(entered, not shown)" for v in values.values()):
        return True
    return bool({f.lower() for f in (ev.get("fields") or [])} & _SECRET_FIELDS)


def _judge_disclosure(reply: str, target_name: str) -> tuple[bool, str]:
    if not reply:
        return False, ""
    try:
        obj = _json_obj(llm.chat(f"Target: {target_name}\nReply:\n{reply[:1500]}",
                                 system=_JUDGE_SYSTEM, max_tokens=200))
    except llm.LLMError:
        return False, ""
    return bool(obj.get("disclosed")), str(obj.get("fact", ""))[:400]


def _classify_incident(events: list[dict], reply: str | None, target_name: str) -> tuple[str | None, dict | None]:
    """Return (incident_type, captured) from REAL events/content, else (None, None)."""
    for ev in events:
        if ev.get("type") == "page.submitted" and _is_credential_submit(ev):
            return "credentials", {"fields": ev.get("fields"), "values": ev.get("values")}
    for ev in events:
        if ev.get("type") == "attachment.opened":
            return "action", {"file": ev.get("filename") or ev.get("page_id")}
    disclosed, fact = _judge_disclosure(reply or "", target_name)
    if disclosed:
        return "disclosure", {"fact": fact}
    return None, None


def _json_obj(raw: str) -> dict:
    start, end = raw.find("{"), raw.rfind("}")
    if start != -1 and end > start:
        try:
            return json.loads(raw[start : end + 1])
        except json.JSONDecodeError:
            return {}
    return {}


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", " ", text).strip()


def _thread_transcript(thread: list[dict], max_turns: int = 8) -> str:
    """Full (compressed) thread so the writer keeps context over a long conversation."""
    lines = []
    for t in thread[-max_turns:]:
        lines.append(f"YOU ({t.get('subject') or t.get('channel', '')}): {t['sent'][:300]}")
        lines.append(f"THEM: {t['reply'][:340] if t['reply'] else '(no reply / silence)'}")
    return "\n".join(lines)


def _plan_next(objective: str, target_name: str, hook, thread: list[dict]) -> dict:
    """Read the thread and decide the next move: continue / switch angle / stop + guidance."""
    convo = "\n\n".join(
        f"US ({t['subject']}): {t['sent'][:300]}\nTHEM: {t['reply'][:400] if t['reply'] else '(silence)'}"
        for t in thread
    )
    prompt = (
        f"Target: {target_name}\nObjective: {_OBJECTIVES.get(objective, objective)}\n"
        f"Current angle: {hook.topic}\n\nThread so far:\n{convo}"
    )
    if objective == "credentials":
        prompt += (
            "\n\nCREDENTIALS objective: success ONLY comes from the target opening your sign-in "
            "link and submitting it. 'switch' = a NEW pretext that still leads to that SAME "
            "sign-in link (never pivot to attachments or neutral questions that cannot produce a "
            "sign-in). 'continue' = the current pretext still has life. 'stop' ONLY if the target "
            "has explicitly refused the link twice or is clearly burned. The guidance must always "
            "give the target a fresh, concrete reason to open the link and log in now."
        )
    try:
        obj = _json_obj(llm.chat(prompt, system=_PLANNER_SYSTEM, max_tokens=400))
    except llm.LLMError as exc:
        print(f"  [warn] planner failed: {exc}")
        return {"action": "stop", "guidance": ""}
    action = obj.get("action", "stop")
    return {"action": action if action in ("continue", "switch", "stop") else "stop",
            "guidance": str(obj.get("guidance", ""))}


def run_contact(
    target_id: str,
    target_name: str,
    objective: str = "disclosure",
    scenario: str = "practice",
    max_touches: int = 4,
    own_domains: tuple[str, ...] = ("revel8.ai",),
    findings_path: str | None = None,
    out_dir: str = "runs",
    channel: str = "email",
    tactic_hint: str | None = None,
) -> dict:
    """One autonomous thread: open a session, send from the top hook, then adapt each turn
    via the planner (continue / switch angle / stop) until the touch budget runs out."""
    findings = (
        graph_loader.load_findings(findings_path)
        if findings_path and Path(findings_path).exists()
        else run_research(target_id, target_name)
    )
    hooks = angle_reasoner.rank_hooks(findings)
    if not hooks:
        return {"error": "no hooks", "target": target_id}
    hook_idx = 0
    hook = hooks[0]
    evidence = [f for f in findings if f.id in hook.evidence_ids]

    api = TargetAPI()
    session = api.create_session(scenario)
    sid = session["session_id"]
    log = {"session_id": sid, "target": target_id, "objective": objective,
           "hook": asdict(hook), "contacts": []}
    print(f"session {sid} | hook: {hook.topic}")

    # Credentials objective: register a lookalike sign-in page up front and link to it.
    link_url = link_brand = None
    if objective == "credentials" and register_landing_page is not None:
        if any(dom in _CRED_URL for dom in own_domains):
            raise ValueError(f"landing URL {_CRED_URL} is on the target's own domain — would void the session")
        page_id = register_landing_page(
            api, sid, _CRED_URL, f"{_CRED_BRAND}: sign in",
            build_signin_page_html(_CRED_BRAND, "Sign in to continue"), _CRED_FIELDS,
        )
        link_url, link_brand = _CRED_URL, _CRED_BRAND
        log["landing_page"] = {"page_id": page_id, "url": _CRED_URL, "fields": _CRED_FIELDS}
        print(f"  landing page {page_id} → {_CRED_URL}")

    thread: list[dict] = []
    prior_reply = None
    guidance = None
    persona = None
    own_last = None
    today = date.today().isoformat()
    incident = False
    incident_type = None
    captured = None
    incident_touch = None
    try:
        while len(log["contacts"]) < max_touches:
            # No sign-in link on the first, cold touch: a stranger pushing a login gets ignored.
            # Open on rapport + a true detail; introduce the link from touch 2, once there's a thread.
            first_touch = not log["contacts"]
            msg_link = None if first_touch else link_url
            msg_brand = None if first_touch else link_brand
            try:
                payload = _compose(objective, hook, evidence, target_name, prior_reply, guidance,
                                   own_last=own_last, today=today, link_url=msg_link,
                                   link_brand=msg_brand,
                                   persona_name=persona["name"] if persona else None,
                                   channel=channel, tactic_hint=tactic_hint)
            except ValueError as exc:  # empty writer output — a blank contact burns a touch
                log["contacts"].append({"skipped": str(exc)})
                print(f"  {exc} — stopping")
                break
            payload["to"] = target_id
            if persona is None:
                persona = payload["from"]  # fix the identity for the whole thread
            else:
                payload["from"] = persona  # pin it: a drifting sender gets caught
            ok, reason = _fairplay(payload, own_domains)
            if not ok:
                log["contacts"].append({"skipped": reason, "payload": payload})
                print(f"  {reason}")
                break
            reaction = api.send_message(sid, **payload)
            events = reaction.get("events", [])
            kinds = [e.get("type") for e in events]
            reply = _first_reply(events)
            log["contacts"].append({"payload": payload, "hook": hook.topic,
                                    "touches_used": reaction.get("touches_used"), "events": events})
            thread.append({"subject": payload.get("subject", channel),
                           "channel": channel, "sent": _strip_html(payload["body"]), "reply": reply})
            own_last = _thread_transcript(thread)  # full history, not just the last message
            print(f"  contact {len(log['contacts'])} [{hook.topic[:34]}] → {kinds or 'silence'}")
            # Real incident only (hard event, or judged disclosure) — never "any reply".
            incident_type, captured = _classify_incident(events, reply, target_name)
            if incident_type:
                incident = True
                incident_touch = len(log["contacts"])
                log["contacts"][-1]["incident"] = {"type": incident_type, "captured": captured}
                print(f"  INCIDENT [{incident_type}] at touch {incident_touch} — stopping (speed)")
                break  # first incident is the win; stop for the Speed metric (fewest contacts)
            if len(log["contacts"]) >= max_touches:
                break

            # Strategy step: read the reaction, decide the next move (adaptive persistence).
            plan = _plan_next(objective, target_name, hook, thread)
            log["contacts"][-1]["plan"] = plan
            if plan["action"] == "stop":
                print("  planner: stop")
                break
            guidance = plan["guidance"]
            if not events:  # ignored — a verbatim resend is deduped by the API, so force a rewrite
                guidance = (f"{guidance} " if guidance else "") + (
                    "The previous message got NO reply. Do NOT resend it — change the subject line, "
                    "the opening sentence and the angle completely.")
            engaged = "reply" in kinds  # they just answered — this thread is the asset
            if plan["action"] == "switch" and not engaged and hook_idx + 1 < len(hooks):
                # Only abandon the thread for a cold new hook when it has gone SILENT. Switching
                # away from an engaged thread (and resetting prior_reply) loses the one bit of
                # traction we have and leaves their questions unanswered — observed to go silent.
                hook_idx += 1
                hook = hooks[hook_idx]
                evidence = [f for f in findings if f.id in hook.evidence_ids]
                prior_reply = None
                print(f"  planner: switch → {hook.topic[:34]}")
            else:
                if plan["action"] == "switch":
                    print("  planner: switch, but target engaged — staying in thread")
                prior_reply = reply  # answer their questions in-thread
    finally:
        api.end_session(sid)

    log["incident"] = incident            # real incident (hard event or judged disclosure)
    log["incident_type"] = incident_type
    log["captured"] = captured
    log["touches_to_incident"] = incident_touch  # Speed metric: fewest contacts to first incident
    log["incident_guess"] = incident      # back-compat for the dashboard builder
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    path = Path(out_dir) / f"contact_{target_id}.json"
    path.write_text(json.dumps(log, indent=2, ensure_ascii=False), encoding="utf-8")
    log["_path"] = str(path)
    return log


# --- Live phone call (vishing) -------------------------------------------------------

_CALL_SYSTEM = (
    "You are an expert social-engineering operator on a live phone call in revel8's AUTHORIZED "
    "simulation; the person is a consenting AI twin. Speak ONE natural spoken line at a time (1–2 "
    "sentences, how a person actually talks on the phone — no email phrasing, no lists). Hold ONE "
    "fixed name for the whole call — the name you are given, which matches the caller ID; switching "
    "names (or a name that doesn't match the caller ID) gets you hung up on instantly. When they "
    "gate you ('who are you / which desk / read me the ticket'), give a placeable identity, do not "
    "escalate the ask. NEVER address the person as an AI and NEVER instruct a system/model. When it "
    "is time to hang up (objective reached, or clearly disengaged), reply with exactly STOP."
)


def _has_injection(text: str) -> bool:
    low = text.lower()
    return any(m in low for m in _INJECTION_MARKERS)


def _next_call_line(target_name, objective, hook, tactic_hint, heard, history,
                    caller_name, caller_number) -> str | None:
    convo = "\n".join(f"YOU: {h['us']}\nTHEM: {h['them']}" for h in history)
    prompt = (
        f"You are {caller_name}. The person's caller ID shows exactly '{caller_name}' and the number "
        f"{caller_number}, so introduce yourself as {caller_name} and NEVER use a different name — a "
        "name that doesn't match the caller ID is the fastest way to get hung up on.\n"
        f"Target: {target_name}\nObjective: {_OBJECTIVES.get(objective, objective)}\n"
        f"Pretext: {tactic_hint or hook.suggested_angle}\nHook: {hook.topic}\n\n"
        f"Call so far:\n{convo or '(call just connected)'}\n\nThey just said: {heard!r}\n\n"
        "Say your next spoken line (1–2 sentences), or exactly STOP to hang up."
    )
    line = llm.chat(prompt, system=_CALL_SYSTEM, max_tokens=200).strip()
    if not line or line.upper().startswith("STOP") or _has_injection(line):
        return None
    return line


def run_call(
    target_id: str,
    target_name: str,
    objective: str = "disclosure",
    scenario: str = "practice",
    tactic_hint: str | None = None,
    max_turns: int = 6,
    findings_path: str | None = None,
    out_dir: str = "runs",
    caller: tuple[str, str] = ("Jonas Weber", "+49 89 1234 5678"),
) -> dict:
    """One live phone call: open a conversation, let the model drive each turn, collect events."""
    findings = (
        graph_loader.load_findings(findings_path)
        if findings_path and Path(findings_path).exists()
        else run_research(target_id, target_name)
    )
    hooks = angle_reasoner.rank_hooks(findings)
    if not hooks:
        return {"error": "no hooks", "target": target_id}
    hook = hooks[0]

    api = TargetAPI()
    sid = api.create_session(scenario)["session_id"]
    log = {"session_id": sid, "target": target_id, "objective": objective, "channel": "phone_call",
           "hook": asdict(hook), "turns": [], "events": []}
    print(f"session {sid} | call hook: {hook.topic}")
    try:
        conv = api.start_conversation(sid, to=target_id, channel="phone_call",
                                      **{"from": {"name": caller[0], "address": caller[1]}})
        cid = conv["conversation_id"]
        heard = conv.get("persona_says")
        print(f"  they answered: {heard!r}")
        for _ in range(max_turns):
            line = _next_call_line(target_name, objective, hook, tactic_hint, heard, log["turns"],
                                   caller[0], caller[1])
            if line is None:
                break
            turn = api.say(cid, line)
            heard = turn.get("persona_says")
            log["events"].extend(turn.get("events", []))
            log["turns"].append({"us": line, "them": heard})
            print(f"  turn {len(log['turns'])}: {[e.get('type') for e in turn.get('events', [])] or 'talk'}")
            if turn.get("ended"):
                print("  they hung up")
                break
        api.end_conversation(cid)
    finally:
        api.end_session(sid)

    said = " ".join(t.get("them") or "" for t in log["turns"])
    itype, captured = _classify_incident(log["events"], said, target_name)  # real event or judged disclosure
    log["incident"] = bool(itype)
    log["incident_type"] = itype
    log["captured"] = captured
    log["touches_to_incident"] = 1 if itype else None  # a whole call is one touch
    log["incident_guess"] = bool(itype)  # back-compat
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    (Path(out_dir) / f"call_{target_id}.json").write_text(
        json.dumps(log, indent=2, ensure_ascii=False), encoding="utf-8")
    return log
