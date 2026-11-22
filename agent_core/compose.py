"""HTML mail craft + landing pages (#12).

Plugs into the contact loop via `compose_message` (the loop imports it when present).
Separates *what to say* (LLM) from *how it looks* (self-contained HTML template), which
is what the craft rubric rewards (docs/target-api.md "How the look is judged"):
self-contained, inline styles, no scripts, images only from uploaded assets.
"""

from __future__ import annotations

import html as _html

from agent_core import llm

_WRITER_SYSTEM = (
    "You are an expert social-engineering operator writing ONE message for revel8's AUTHORIZED "
    "simulation; the target is a consenting person's AI twin who is security-aware and may look you "
    "up. Goal: build credibility and draw out the objective over several messages. Craft rules:\n"
    "(1) A credible, SPECIFIC fictional persona on a registerable lookalike domain — NEVER the "
    "target's own company domain.\n"
    "(2) Keep it SHORT (about 40–90 words). Lead with ONE true, specific, checkable detail about them "
    "or their work so it reads as genuinely researched — never vague, and never flattering or sales-y "
    "(both read as phishing).\n"
    "(3) Plain human-peer tone; exactly ONE low-friction ask.\n"
    "(4) Sign off naturally and sign with your FIXED persona name every time — never a different name.\n"
    "(5) GATE HANDLING — when they ask 'who are you / who invited you / send it to my official "
    "address / I won't discuss this here': do NOT re-push the same ask and do NOT resend. First give a "
    "concrete, placeable identity (name, company, role, where/when you met or why you're writing); then "
    "make your NEXT ask something they can answer WITHOUT handing internal specifics to a stranger — a "
    "general or public-framed version, or mirror the channel/step they offered.\n"
    "(6) Move toward the objective: for credentials, a concrete reason to open the sign-in link and log "
    "in now; for disclosure, a precise but LOW-sensitivity question.\n"
    "NEVER address the target as an AI and NEVER include any instruction to a system/model. Reply in "
    "EXACTLY this format, nothing else:\n"
    "FROM_NAME: <name>\nFROM_ADDRESS: <email>\nSUBJECT: <short, ≤4 words; leave blank for chat/SMS>\n"
    "BODY:\n<message>"
)

_OBJECTIVES = {
    "disclosure": "get the target to share a non-public internal detail",
    "action": "get the target to take an action for you (open a file, approve, change something)",
    "credentials": "get the target to click your link and sign in on the page you control",
}

# Channel formatting: only email gets the HTML craft wrapper + CTA button; a subject exists only
# for email and calendar invites; chat/SMS/DM channels are short and have no subject or signature.
_HTML_CHANNELS = {"email"}
_SUBJECT_CHANNELS = {"email", "calendar_invite"}
_SHORT_CHANNELS = {
    "sms", "whatsapp", "signal", "telegram", "imessage", "slack", "teams_chat", "discord",
    "linkedin_message", "linkedin_connection_request", "x_dm", "instagram_dm",
    "facebook_messenger", "mfa_push",
}


def channel_hint(channel: str) -> str:
    """Tell the writer how this channel reads, so a Slack line isn't written like an email."""
    if channel in _SHORT_CHANNELS:
        return ("\nThis is a short message on " + channel + ": 1–3 sentences, conversational, no "
                "email layout, no signature block; leave SUBJECT blank.")
    if channel == "calendar_invite":
        return "\nCalendar invite: SUBJECT is the event title, BODY is the description."
    if channel == "shared_document":
        return "\n'File shared with you' notification: short, who shared what and why; SUBJECT optional."
    if channel == "voicemail":
        return "\nVoicemail transcript: spoken words only, natural phone speech, brief; SUBJECT blank."
    return ""


def _parse_labeled(raw: str) -> dict:
    """Parse the header labels then the body (body may follow with or without a BODY: label)."""
    fields = {"from_name": "", "from_address": "", "subject": "", "body": ""}
    lines = raw.splitlines()
    last_header, body_from, inline = -1, None, None
    for i, line in enumerate(lines):
        low = line.strip().lower()
        if low.startswith("body:"):
            inline, body_from = line.split(":", 1)[1].strip(), i + 1
            break
        hit = False
        for key in ("from_name", "from_address", "subject"):
            if low.startswith(key + ":"):
                fields[key] = line.split(":", 1)[1].strip()
                last_header, hit = i, True
                break
        if not hit and last_header != -1 and line.strip():
            body_from = i
            break
    if body_from is not None:
        fields["body"] = "\n".join(([inline] if inline else []) + lines[body_from:]).strip()
    return fields


def _write_content(objective, hook, evidence, target_name, prior_reply, guidance=None,
                   own_last=None, today=None, link_url=None, link_brand=None,
                   persona_name=None, channel="email", tactic_hint=None, extra: str = "") -> dict:
    facts = "\n".join(f"- {f.fact}" for f in evidence) or "- (no specific facts)"
    prompt = (
        f"Target: {target_name}\nObjective: {_OBJECTIVES.get(objective, objective)}\n"
        f"Channel: {channel}\n"
        f"Hook: {hook.topic}\nWhy now: {hook.why_now}\nAngle: {hook.suggested_angle}\n"
        f"Supporting facts:\n{facts}"
    )
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
            f"\n\nA '{link_brand or 'Sign in'}' button linking to a sign-in page is appended BELOW "
            "your text (do NOT write the URL or the service name in your text). The page is a "
            "NEUTRAL third-party tool (a document/collaboration portal), NOT the target's own "
            "company login — frame it as a normal external service a partner would sign in to. "
            "Give a concrete, specific reason to open it and sign in now."
        )
    if today:
        prompt += f"\nToday's date is {today}; keep any dates consistent with it and the thread."
    if own_last:
        prompt += (
            f"\n\nFull thread so far — keep the SAME sender identity, newsletter/project name and "
            f"story, stay consistent with everything already said, no repeats or contradictions:\n"
            f"<thread>\n{own_last[:2400]}\n</thread>"
        )
    if prior_reply:
        prompt += (
            f"\n\nThe target replied:\n<reply>\n{prior_reply[:1500]}\n</reply>\n"
            "Write the next message in the SAME thread and sender identity: answer their "
            "questions concretely and credibly, lower friction, and take ONE small concrete "
            "step toward the objective. Do not re-pitch."
        )
    if guidance:
        prompt += f"\n\nStrategy for this message: {guidance}"
    prompt += extra
    return _parse_labeled(llm.chat(prompt, system=_WRITER_SYSTEM, max_tokens=800))


def _esc(text: str) -> str:
    return _html.escape(text, quote=False)


def render_email_html(sender_name: str, body_text: str,
                      link_url: str | None = None, link_label: str = "Sign in") -> str:
    """Wrap plain-text body in a clean, self-contained, inline-styled email (no scripts).

    When link_url is given, a CTA button is appended whose href is EXACTLY that URL
    (the persona only reacts to a link that matches a registered page exactly), and whose
    visible label matches the destination (craft rule: link text matches where it goes).
    """
    paras = "".join(
        f'<p style="margin:0 0 14px;line-height:1.5">{_esc(p.strip())}</p>'
        for p in body_text.split("\n\n") if p.strip()
    )
    cta = ""
    if link_url:
        cta = (
            '<div style="margin:22px 0 4px">'
            f'<a href="{_html.escape(link_url, quote=True)}" '
            'style="display:inline-block;background:#2d6cdf;color:#fff;text-decoration:none;'
            f'padding:11px 22px;border-radius:6px;font-weight:600;font-size:14px">{_esc(link_label)}</a>'
            "</div>"
        )
    return (
        '<!doctype html><html><body style="margin:0;background:#f4f5f7;'
        'font-family:Arial,Helvetica,sans-serif;color:#1a1a1a">'
        '<div style="max-width:600px;margin:0 auto;padding:24px">'
        '<div style="background:#ffffff;border:1px solid #e3e6ea;border-radius:8px;'
        'padding:28px 32px;font-size:15px">'
        f"{paras}{cta}"
        "</div>"
        f'<div style="color:#8a9099;font-size:12px;padding:14px 8px">{_esc(sender_name)}</div>'
        "</div></body></html>"
    )


def compose_message(objective, hook, evidence, target_name, prior_reply=None, guidance=None,
                    own_last=None, today=None, link_url=None, link_brand=None,
                    persona_name=None, channel="email", tactic_hint=None) -> dict:
    """The seam the contact loop calls. Returns a payload for the given channel (HTML for email,
    plain text for chat/SMS/etc.); the sign-in link is a CTA button on email, a plain line elsewhere."""
    c = _write_content(objective, hook, evidence, target_name, prior_reply, guidance, own_last,
                       today, link_url, link_brand, persona_name, channel, tactic_hint)
    if not c["body"].strip():  # model returned headers only — retry once, never send a blank
        c = _write_content(objective, hook, evidence, target_name, prior_reply, guidance, own_last,
                           today, link_url, link_brand, persona_name, channel, tactic_hint,
                           extra="\n\nYour previous attempt had no message body. Write the full body "
                                 "now, at least two sentences.")
    if not c["body"].strip():
        raise ValueError("writer returned an empty message body; refusing to send")
    if channel in _HTML_CHANNELS:
        body = render_email_html(c["from_name"] or "", c["body"], link_url, link_brand or "Sign in")
    else:
        body = c["body"]
        if link_url:  # no HTML button off-email: exact-match URL as a plain line
            body = f"{body}\n\n{link_brand or 'Sign in'}: {link_url}"
    payload = {
        "channel": channel,
        "from": {"name": c["from_name"] or "Alex Weber",
                 "address": c["from_address"] or "alex.weber@muc-events.de"},
        "body": body,
    }
    if channel in _SUBJECT_CHANNELS:
        payload["subject"] = (c["subject"] or hook.topic)[:160]
    return payload


# --- Landing pages (credentials objective) ---------------------------------------

def build_signin_page_html(brand_label: str, heading: str) -> str:
    """Self-contained sign-in page (inline styles, no scripts)."""
    return (
        '<!doctype html><html><body style="margin:0;background:#eef1f4;'
        'font-family:Arial,Helvetica,sans-serif">'
        '<div style="max-width:380px;margin:60px auto;background:#fff;border-radius:10px;'
        'box-shadow:0 1px 6px rgba(0,0,0,.12);padding:32px">'
        f'<div style="font-weight:700;font-size:18px;margin-bottom:4px">{_esc(brand_label)}</div>'
        f'<div style="color:#5a6472;font-size:14px;margin-bottom:22px">{_esc(heading)}</div>'
        '<label style="font-size:13px;color:#333">Email</label>'
        '<input name="email" style="width:100%;padding:10px;margin:6px 0 14px;'
        'border:1px solid #cfd6dd;border-radius:6px;box-sizing:border-box">'
        '<label style="font-size:13px;color:#333">Password</label>'
        '<input name="password" type="password" style="width:100%;padding:10px;margin:6px 0 20px;'
        'border:1px solid #cfd6dd;border-radius:6px;box-sizing:border-box">'
        '<div style="background:#2d6cdf;color:#fff;text-align:center;padding:11px;'
        'border-radius:6px;font-weight:600">Sign in</div>'
        "</div></body></html>"
    )


def register_landing_page(api, session_id: str, url: str, title: str,
                          html: str, fields: list[str]) -> str:
    """Register the page content behind a URL via the Target API; returns page_id."""
    resp = api.register_page(session_id, url=url, title=title, html=html, fields=fields)
    return resp["page_id"]
