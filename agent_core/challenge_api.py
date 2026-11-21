"""Fake challenge API with deterministic events and no external effects."""

from __future__ import annotations

from agent_core.schema import ApiEvent, MessageCandidate


class FakeChallengeAPI:
    """In-memory simulation adapter.

    This class is deliberately not a real network client. It records the would-send
    action and returns deterministic synthetic events for replay and evals.
    """

    def __init__(self) -> None:
        self.sent_candidates: list[MessageCandidate] = []

    def send(self, persona_id: str, candidate: MessageCandidate) -> ApiEvent:
        self.sent_candidates.append(candidate)
        if persona_id == "max_rieder":
            return ApiEvent(
                id="event_max_docs_opened",
                candidate_id=candidate.id,
                event_type="fake_document_opened",
                reply="Looks relevant. Please share the checklist assumptions before any next step.",
                signal_score=2,
            )
        if persona_id == "sara_neumann":
            return ApiEvent(
                id="event_sara_calendar_opened",
                candidate_id=candidate.id,
                event_type="fake_calendar_opened",
                reply="The workshop angle is plausible. Keep it limited to synthetic manager training.",
                signal_score=2,
            )
        return ApiEvent(
            id="event_lena_link_opened",
            candidate_id=candidate.id,
            event_type="fake_link_opened",
            reply="The vendor-risk checklist looks relevant. I would want a concise follow-up summary.",
            signal_score=2,
        )
