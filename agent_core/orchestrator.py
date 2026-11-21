"""End-to-end local orchestration loop."""

from __future__ import annotations

import json
from pathlib import Path

from agent_core.challenge_api import FakeChallengeAPI
from agent_core.fixtures import synthetic_graph
from agent_core.model_committee import default_stub_committee
from agent_core.schema import Objective, RunLog, StrategyUpdate, to_jsonable


class Orchestrator:
    def __init__(self, api: FakeChallengeAPI | None = None) -> None:
        self.api = api or FakeChallengeAPI()
        self.committee = default_stub_committee()

    def run(self, persona_id: str = "lena_kraus", objective: Objective = Objective.ACTION) -> RunLog:
        graph = synthetic_graph(persona_id)
        context, decision = self.committee.run(graph, objective)
        winner = _candidate_by_id(decision.winner_candidate_id, decision.candidates)
        event = self.api.send(persona_id, winner) if winner else None
        wrong_fact_penalty = _wrong_fact_penalty(decision)
        event_signal = event.signal_score if event else -1
        update = StrategyUpdate(
            angle_id=context.angle.id,
            prior_score=1,
            event_signal=event_signal,
            wrong_fact_penalty=wrong_fact_penalty,
            updated_score=1 + event_signal - wrong_fact_penalty,
            lesson=_lesson(context.angle.id, event_signal, wrong_fact_penalty),
        )
        timeline = (
            {"step": 1, "type": "graph_loaded", "summary": f"{len(graph.nodes)} nodes, {len(graph.edges)} edges"},
            {"step": 2, "type": "context_routed", "loaded_paths": [path.id for path in context.loaded_paths]},
            {"step": 3, "type": "committee_scored", "winner_candidate_id": decision.winner_candidate_id},
            {"step": 4, "type": "evaluator_gate", "verdicts": [verdict.decision for verdict in decision.gate_verdicts]},
            {"step": 5, "type": "fake_api_event", "event_type": event.event_type if event else "not_sent"},
            {"step": 6, "type": "strategy_update", "updated_score": update.updated_score},
        )
        return RunLog(
            run_id=f"run_{persona_id}_stub_001",
            persona_id=persona_id,
            graph=graph,
            routed_context=context,
            committee_decision=decision,
            api_event=event,
            strategy_update=update,
            timeline=timeline,
            preference_data=_preference_data(persona_id, context, decision, event, update),
        )

    def run_and_save(self, persona_id: str, output_path: Path) -> RunLog:
        log = self.run(persona_id)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(to_jsonable(log), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return log


def _candidate_by_id(candidate_id: str | None, candidates: tuple) -> object:
    if candidate_id is None:
        raise RuntimeError("No sendable candidate was selected.")
    for candidate in candidates:
        if candidate.id == candidate_id:
            return candidate
    raise RuntimeError(f"Winner candidate '{candidate_id}' missing from committee output.")


def _wrong_fact_penalty(decision) -> int:
    blocked = [
        reason
        for verdict in decision.gate_verdicts
        for reason in verdict.blocked_reasons
        if reason in {"wrong_or_unsupported_fact", "uses_unrouted_or_unsupported_evidence"}
    ]
    return len(blocked)


def _lesson(angle_id: str, event_signal: int, wrong_fact_penalty: int) -> str:
    if wrong_fact_penalty:
        return f"{angle_id} had unsupported-fact risk in rejected candidates; keep routing strict."
    if event_signal > 0:
        return f"{angle_id} produced a positive simulated event; keep this angle warm for follow-up."
    return f"{angle_id} did not produce a useful signal; switch angle or channel."


def _preference_data(persona_id: str, context, decision, event, update) -> dict:
    verdict_by_id = {verdict.candidate_id: verdict for verdict in decision.gate_verdicts}
    score_by_id = {score.candidate_id: score for score in decision.critic_scores}
    candidates = []
    for candidate in decision.candidates:
        verdict = verdict_by_id[candidate.id]
        candidates.append(
            {
                "candidate_id": candidate.id,
                "writer_model": candidate.writer_model,
                "advisor_model": candidate.advisor_model,
                "critic_scores": score_by_id[candidate.id].scores,
                "gate_decision": verdict.decision,
                "blocked_reasons": list(verdict.blocked_reasons),
                "sent": candidate.id == decision.winner_candidate_id,
                "api_event": event.event_type if event and candidate.id == decision.winner_candidate_id else None,
            }
        )
    return {
        "persona_id": persona_id,
        "run_id": f"run_{persona_id}_stub_001",
        "objective": context.objective.value,
        "loaded_context_paths": [path.id for path in context.loaded_paths],
        "candidates": candidates,
        "winner_candidate_id": decision.winner_candidate_id,
        "lesson": update.lesson,
    }
