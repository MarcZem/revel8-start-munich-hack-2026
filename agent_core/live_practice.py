"""Revel8 practice adapter used by the streamed demo run."""

from __future__ import annotations

from typing import Callable

from agent_core.revel8_api import Revel8API
from agent_core.schema import ApiEvent, Channel, MessageCandidate


PRACTICE_TARGETS = {"julius", "tom", "robert"}
_CHANNELS = {
    Channel.FAKE_EMAIL: "email",
    Channel.FAKE_CALENDAR: "calendar_invite",
    Channel.FAKE_DOCUMENT: "shared_document",
}


class Revel8PracticeAdapter:
    """Send one gated candidate to an allowlisted Revel8 practice twin."""

    def __init__(self, on_event: Callable[[str, str], None] | None = None) -> None:
        self.client = Revel8API(timeout=120)
        self.on_event = on_event
        self.session_id: str | None = None
        self.touches_used = 0
        self.event_types: list[str] = []

    def send(self, persona_id: str, candidate: MessageCandidate) -> ApiEvent:
        if persona_id not in PRACTICE_TARGETS:
            raise ValueError("The live demo only allows the Revel8 practice targets.")
        scenarios = self.client.list_scenarios()
        if not isinstance(scenarios, list):
            raise ValueError("Revel8 returned an unexpected scenarios response.")
        scenario = next((item for item in scenarios if item.get("id") == "practice"), None)
        if not scenario or not scenario.get("open"):
            raise ValueError("The Revel8 practice scenario is not currently open.")
        target = next((item for item in scenario.get("targets", []) if item.get("id") == persona_id), None)
        if not target:
            raise ValueError("That target is not available in the open practice scenario.")
        if candidate.channel not in _CHANNELS:
            raise ValueError("The selected channel is not supported by the practice demo.")

        session = self.client.create_session("practice")
        self.session_id = str(session["session_id"])
        self._emit("gateway", f"Practice-Session geöffnet: {self.session_id}")
        response = self.client.send_message(
            self.session_id,
            to=persona_id,
            channel=_CHANNELS[candidate.channel],
            subject=candidate.subject,
            body=candidate.body,
            idempotency_key=f"team11-live-demo-{self.session_id}",
        )
        self.touches_used = int(response.get("touches_used", 1))
        self.event_types = [
            str(event.get("type"))
            for event in response.get("events", [])
            if isinstance(event, dict) and event.get("type")
        ]
        # Keep persona text and submitted values out of the live dashboard feed.
        return ApiEvent(
            id=str(response.get("message_id", self.session_id)),
            candidate_id=candidate.id,
            event_type="live_revel8_events" if self.event_types else "no_event",
            reply=f"{len(self.event_types)} normalized event(s)",
            signal_score=1 if self.event_types else 0,
            simulated=True,
        )

    def _emit(self, node: str, label: str) -> None:
        if self.on_event:
            self.on_event(node, label)
