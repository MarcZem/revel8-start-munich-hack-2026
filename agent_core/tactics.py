"""Tactic registry + sweep: run every tactic (persuasion lever × theme × channel) against a
twin and score which engages best. The levers/themes are the statistically strongest from the
research (SECURWARE 2025: liking & authority predict compromise; KnowBe4 Q2–Q4 2025: internal
IT/HR themes and doc-share lures top the click rates) — see RETRO.md. The sweep's job is to find
the susceptible angle; against the hardened practice twins most will be silence, which is itself data.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from agent_core import contact_loop


@dataclass(frozen=True)
class Tactic:
    name: str
    lever: str          # Cialdini-style persuasion lever
    channel: str        # Target API channel
    objective: str      # disclosure | credentials | action
    pretext: str        # seed injected into the writer as the per-message TACTIC hint
    is_call: bool = False  # live phone_call via the conversation API


TACTICS: list[Tactic] = [
    Tactic("authority_it", "Authority", "email", "credentials",
           "Pose as the EXTERNAL IT/security provider running revel8's SSO or device-compliance "
           "check. Authoritative, procedural tone; a required re-verification with a short deadline."),
    Tactic("authority_hr_doc", "Authority", "shared_document", "credentials",
           "A people-ops/HR notice: a mandatory policy acknowledgement or reimbursement form that "
           "must be opened and signed in to view before a deadline."),
    Tactic("liking_peer", "Liking", "email", "credentials",
           "A warm peer in the same ecosystem with a genuine shared interest (their talk/hackathon); "
           "rapport and a true specific detail first, small ask later. (Baseline.)"),
    Tactic("reciprocity_linkedin", "Reciprocity", "linkedin_message", "disclosure",
           "Offer something of value first (a speaking slot, a useful intro, a short report), then a "
           "small reciprocal question about how they run their setup."),
    Tactic("social_proof_slack", "Social proof", "slack", "disclosure",
           "A casual internal-sounding ping noting that co-founders/teammates already did the thing; "
           "ask them to confirm or add theirs."),
    Tactic("urgency_sms", "Urgency", "sms", "credentials",
           "A short, time-critical text: access/verification needed now before something lapses; "
           "a link to sign in."),
    Tactic("casual_whatsapp", "Liking", "whatsapp", "disclosure",
           "A casual message from a peer met at an event; friendly, low-pressure question about how "
           "they run a specific thing."),
    Tactic("vishing_call", "Authority", "phone_call", "disclosure",
           "Phone as the IT service desk / event organiser; calm authority; verify a detail or walk "
           "them through a small action.", is_call=True),
    # credentials-focused across credible channels (the fake sign-in page path — cleanest, auto-
    # detectable, displayable breach; its landing page also scores Craft)
    Tactic("cred_email", "Authority", "email", "credentials",
           "A specific account/access-security notice from a named external provider (not their own "
           "domain); a concrete, verifiable reason to re-confirm access via the linked sign-in now."),
    Tactic("cred_slack", "Social proof", "slack", "credentials",
           "Internal-sounding ping: an access migration is underway and teammates have already "
           "re-confirmed theirs; a quick sign-in on the link to confirm access before it lapses."),
    # --- broad campaign variants: many pretext angles × channels, to find what cracks ---
    Tactic("journalist_email", "Liking", "email", "disclosure",
           "A journalist/podcast producer following up on something they said publicly; warm, "
           "specific, asks one concrete 'how do you actually do X internally' question for the piece."),
    Tactic("investor_linkedin", "Authority", "linkedin_message", "disclosure",
           "A VC analyst doing light diligence; references a real public fact; asks one specific "
           "question about their stack/process/metrics 'for the memo'."),
    Tactic("vendor_eval_email", "Reciprocity", "email", "disclosure",
           "A peer evaluating tools who offers to share their own benchmark first, then asks what "
           "tool/process the target uses internally for the same job."),
    Tactic("recruiter_linkedin", "Liking", "linkedin_message", "disclosure",
           "A recruiter/peer curious about how their team is structured and what tools they run — "
           "framed as market research, low-sensitivity."),
    Tactic("event_whatsapp", "Liking", "whatsapp", "disclosure",
           "Someone they 'met' at a named recent event; casual, references a real detail, asks one "
           "specific follow-up about how they run a thing."),
    Tactic("peer_teams", "Social proof", "teams_chat", "disclosure",
           "An internal-sounding Teams message referencing a shared project; 'the others already "
           "sent me theirs' — asks for their version of a specific internal detail."),
    Tactic("doc_review_action", "Authority", "shared_document", "action",
           "Shares a document as pretext and gets them to ACT on it — approve it, confirm a change it "
           "requests, or forward it on and say it's done; a concrete, time-bound reason tied to a real "
           "project. (Opening the file alone is not an incident.)"),
    Tactic("calendar_action", "Authority", "calendar_invite", "action",
           "A calendar invite to a short briefing with a pre-read doc to open; specific agenda tied "
           "to a real public project."),
    Tactic("mfa_push_cred", "Urgency", "mfa_push", "credentials",
           "An MFA approval prompt framed as a security re-verification they need to approve now."),
    Tactic("sms_urgency_disc", "Urgency", "sms", "disclosure",
           "A short, time-critical text asking them to confirm one specific operational detail now."),
]

# closeness-to-incident ranking of the event types we can observe
_RANK = (("page.submitted", 4), ("link.opened", 3), ("attachment.opened", 2), ("reply", 1))


def transcript(log: dict) -> list[dict]:
    """Compact what-we-sent / what-they-said per turn, so a sweep is readable afterwards."""
    turns = []
    for c in log.get("contacts", []):  # message path
        reply = next((e.get("body") for e in c.get("events", []) if e.get("type") == "reply"), None)
        turns.append({"sent": (c.get("payload", {}).get("body") or "")[:300], "reply": reply})
    for t in log.get("turns", []):  # call path
        turns.append({"sent": t.get("us", ""), "reply": t.get("them")})
    return turns


def engagement(log: dict) -> tuple[int, str]:
    """Best (highest-intent) event the twin produced in this run."""
    kinds = set()
    for c in log.get("contacts", []):
        for e in c.get("events", []):
            kinds.add(e.get("type"))
    for e in log.get("events", []):  # call path keeps events at top level
        kinds.add(e.get("type"))
    for name, rank in _RANK:
        if name in kinds:
            return rank, name
    return 0, "silence"


def run_sweep(target_id: str, target_name: str, findings_path: str | None = None,
              max_touches: int = 3, out_dir: str = "runs", only: list[str] | None = None) -> dict:
    """Run every tactic against one twin (fresh session each — clean-slate comparison) and score.
    `only` limits to the named tactics (for a focused cross-channel validation)."""
    chosen = [t for t in TACTICS if not only or t.name in only]
    results = []
    for t in chosen:
        print(f"\n=== tactic {t.name} [{t.lever}/{t.channel}/{t.objective}] ===")
        try:
            if t.is_call:
                log = contact_loop.run_call(target_id, target_name, objective=t.objective,
                                            tactic_hint=t.pretext, findings_path=findings_path,
                                            out_dir=out_dir)
            else:
                log = contact_loop.run_contact(target_id, target_name, objective=t.objective,
                                               channel=t.channel, tactic_hint=t.pretext,
                                               max_touches=max_touches, findings_path=findings_path,
                                               out_dir=out_dir)
        except Exception as exc:  # one bad tactic must not sink the sweep
            print(f"  tactic error: {exc}")
            results.append({"tactic": t.name, "channel": t.channel, "error": str(exc)[:200]})
            continue
        if log.get("error"):
            results.append({"tactic": t.name, "channel": t.channel, "error": log["error"]})
            continue
        rank, best = engagement(log)
        results.append({"tactic": t.name, "lever": t.lever, "channel": t.channel,
                        "objective": t.objective, "rank": rank, "best": best,
                        "incident": bool(log.get("incident")),
                        "incident_type": log.get("incident_type"),
                        "touches_to_incident": log.get("touches_to_incident"),
                        "captured": log.get("captured"),
                        "transcript": transcript(log)})
        tag = f" INCIDENT:{log.get('incident_type')}@{log.get('touches_to_incident')}" if log.get("incident") else ""
        print(f"  → {best} (rank {rank}){tag}")
        # write after every tactic so a long campaign persists partial progress if interrupted
        Path(out_dir).mkdir(parents=True, exist_ok=True)
        (Path(out_dir) / f"sweep_{target_id}.json").write_text(
            json.dumps({"target": target_id, "results": results}, indent=2, ensure_ascii=False),
            encoding="utf-8")
    return {"target": target_id, "results": results}
