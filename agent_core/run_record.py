"""The run record: one typed, documented contract for everything a scored run persists.

This is the system's memory and the jury's replay surface. Every touch keeps not just
what was sent and what came back, but the agent's *reasoning*: which hook was chosen over
which alternatives, why this touch was sent, how the state changed, and whether to continue,
switch, or stop. That evidence trail is what the "architecture and persistence" criterion
(40 pts) is scored on — the jury reads the architecture page and replays runs turn by turn.

`RunRecord.from_log` normalises the loop output (breach / contact / call dict shapes) into
this contract, so the loops stay simple and every consumer (controller, dashboard, pitch)
reads one stable, typed shape. Local metrics are indicators only; revel8's API is the
authoritative score.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from statistics import median
from typing import Any

# What a successful contact is expected to produce, per objective — the "expected observable"
# the planner commits to before each touch (makes the reassessment legible).
EXPECTED_OBSERVABLE = {
    "credentials": "link.opened then page.submitted with a secret",
    "disclosure": "a reply containing an internal, non-public fact",
    "action": "attachment.opened (the file is opened)",
    "breach": "a secret submitted or an internal fact disclosed",
}

_SECRET_MARKER = "(entered, not shown)"


@dataclass(frozen=True)
class Decision:
    """The agent's reassessment after (or the rationale before) a touch."""

    action: str  # continue | switch | escalate | stop
    reason: str = ""
    alternatives: tuple[str, ...] = ()  # options weighed and not taken, with the why


@dataclass(frozen=True)
class Touch:
    """One contact: what was sent, what came back, and the reasoning around it."""

    index: int
    channel: str
    objective: str
    hook_topic: str
    evidence_ids: tuple[str, ...]
    sender: dict[str, str]
    subject: str | None
    body: str
    expected_observable: str
    events: tuple[dict[str, Any], ...]
    reply: str | None
    incident: dict[str, Any] | None  # {"type","captured"} or None
    critique: dict[str, Any] | None  # lever-critic self-check scores, if any
    decision: Decision | None  # the continue/switch/stop reassessment after this touch
    state_after: dict[str, Any]  # {silent_streak, touches_used, gate_seen}
    sent_because: str = ""  # why this touch was sent (cold open / react-to-gate / re-engage)

    @property
    def silent(self) -> bool:
        return not self.events


@dataclass(frozen=True)
class RunRecord:
    """One session against one target: the whole adaptive thread, persisted."""

    run_id: str
    session_id: str
    scenario: str
    target_id: str
    target_name: str
    objective: str
    chosen_hook: dict[str, Any]
    hooks_considered: tuple[dict[str, Any], ...]  # the ranked alternatives the targeter weighed
    touches: tuple[Touch, ...]
    incident: bool
    incident_type: str | None
    captured: dict[str, Any] | None
    touches_to_incident: int | None  # Speed metric: contacts to the first incident
    stop_reason: str
    landing_page: dict[str, Any] | None = None

    @property
    def contacts_used(self) -> int:
        return len(self.touches)

    @property
    def reached_reply(self) -> bool:
        return any(t.reply for t in self.touches)

    def to_dict(self) -> dict[str, Any]:
        return _to_jsonable(asdict(self))

    @classmethod
    def from_log(cls, log: dict[str, Any]) -> "RunRecord":
        """Normalise a breach / contact / call loop log into the typed contract."""
        target_id = log.get("target", "")
        objective = log.get("objective", "disclosure")
        is_call = "turns" in log and "contacts" not in log
        raw_touches = _call_touches(log) if is_call else log.get("contacts", [])
        touches: list[Touch] = []
        for i, c in enumerate(raw_touches, 1):
            if c.get("skipped"):
                # a blocked/empty contact that never reached the target
                touches.append(_skipped_touch(i, c, objective))
                continue
            payload = c.get("payload", {})
            events = tuple(c.get("events", []))
            reply = _first_reply(events)
            inc = c.get("incident")
            touches.append(
                Touch(
                    index=i,
                    channel=payload.get("channel", log.get("channel", "")),
                    objective=objective,
                    hook_topic=log.get("hook", {}).get("topic", ""),
                    evidence_ids=tuple(log.get("hook", {}).get("evidence_ids", ())),
                    sender=payload.get("from", {}),
                    subject=payload.get("subject"),
                    body=payload.get("body", ""),
                    expected_observable=EXPECTED_OBSERVABLE.get(objective, "a reply or event"),
                    events=events,
                    reply=reply,
                    incident=inc,
                    critique=c.get("critique"),
                    decision=_decision_from(c, bool(inc), i, raw_touches),
                    state_after=c.get("state_after")
                    or {"touches_used": c.get("touches_used"), "silent": not events},
                    sent_because=c.get("sent_because", ""),
                )
            )
        return cls(
            run_id=log.get("run_id") or f"run_{target_id}_{log.get('session_id', '')[:8]}",
            session_id=log.get("session_id", ""),
            scenario=log.get("scenario", "practice"),
            target_id=target_id,
            target_name=log.get("target_name") or _NAMES.get(target_id, target_id),
            objective=objective,
            chosen_hook=log.get("hook", {}),
            hooks_considered=tuple(log.get("hooks_considered", ())),
            touches=tuple(touches),
            incident=bool(log.get("incident")),
            incident_type=log.get("incident_type"),
            captured=log.get("captured"),
            touches_to_incident=log.get("touches_to_incident"),
            stop_reason=log.get("stop_reason") or _infer_stop_reason(log, touches),
            landing_page=log.get("landing_page"),
        )


@dataclass(frozen=True)
class CampaignResult:
    """Aggregate of the runs in one campaign, scored the way the rubric describes.

    Local indicators only: the official Results/Targeting score comes from revel8's API.
    """

    records: tuple[RunRecord, ...]
    runs_total: int
    runs_with_incident: int
    incident_points_estimate: float  # 20 * runs_with_incident / 3 (eval shape)
    speed_median_contacts: float | None  # median contacts-to-incident across runs that reached one

    @classmethod
    def aggregate(cls, records: list[RunRecord]) -> "CampaignResult":
        with_inc = [r for r in records if r.incident]
        speeds = [r.touches_to_incident for r in records if r.touches_to_incident]
        return cls(
            records=tuple(records),
            runs_total=len(records),
            runs_with_incident=len(with_inc),
            incident_points_estimate=round(20 * len(with_inc) / 3, 2),
            speed_median_contacts=float(median(speeds)) if speeds else None,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "runs_total": self.runs_total,
            "runs_with_incident": self.runs_with_incident,
            "incident_points_estimate": self.incident_points_estimate,
            "speed_median_contacts": self.speed_median_contacts,
            "records": [r.to_dict() for r in self.records],
        }


# --- helpers ---------------------------------------------------------------

_NAMES = {"julius": "Julius Muth", "tom": "Tom Müller", "robert": "Robert Seilbeck"}


def _first_reply(events: tuple[dict, ...]) -> str | None:
    for ev in events:
        if ev.get("type") == "reply":
            return ev.get("body")
    return None


def _call_touches(log: dict) -> list[dict]:
    """A call is one touch; fold its turns into a single contact-shaped record for the record."""
    turns = log.get("turns", [])
    body = "\n".join(f"{t.get('us','')}" for t in turns)
    reply = "\n".join(t.get("them", "") for t in turns if t.get("them"))
    return [{
        "payload": {"channel": log.get("channel", "phone_call"), "body": body, "from": {}},
        "events": log.get("events", []) + ([{"type": "reply", "body": reply}] if reply else []),
        "touches_used": 1,
        "incident": {"type": log.get("incident_type"), "captured": log.get("captured")}
        if log.get("incident") else None,
    }]


def _skipped_touch(i: int, c: dict, objective: str) -> Touch:
    return Touch(
        index=i, channel="", objective=objective, hook_topic="", evidence_ids=(),
        sender={}, subject=None, body="", expected_observable="",
        events=(), reply=None, incident=None, critique=None,
        decision=Decision(action="stop", reason=c.get("skipped", "skipped")),
        state_after={"skipped": True}, sent_because="",
    )


def _decision_from(contact: dict, is_incident: bool, idx: int, all_touches: list) -> Decision:
    """Recover the reassessment for a touch: explicit `decision`/`plan` if the loop logged one,
    else inferred from the observable outcome (incident / silence / reply)."""
    explicit = contact.get("decision") or contact.get("plan")
    if explicit:
        return Decision(
            action=explicit.get("action", "continue"),
            reason=explicit.get("reason") or explicit.get("guidance", ""),
            alternatives=tuple(explicit.get("alternatives", ())),
        )
    if is_incident:
        return Decision(action="stop", reason="incident reached — stop for the Speed metric")
    events = contact.get("events", [])
    if not events:
        return Decision(action="switch", reason="silence — vary the angle, do not resend verbatim")
    return Decision(action="continue", reason="engaged — stay in-thread and advance one step")


def _infer_stop_reason(log: dict, touches: list[Touch]) -> str:
    if log.get("incident"):
        return f"incident ({log.get('incident_type')}) at touch {log.get('touches_to_incident')}"
    if touches and touches[-1].state_after.get("skipped"):
        return touches[-1].decision.reason if touches[-1].decision else "contact skipped"
    tail_silent = [t for t in touches[-2:] if t.silent]
    if len(tail_silent) >= 2:
        return "two silences in a row — no traction, stopped"
    return "touch budget reached without an incident"


def _to_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_jsonable(v) for v in value]
    return value
