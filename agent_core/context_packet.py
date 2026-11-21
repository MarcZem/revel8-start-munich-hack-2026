"""Build compact writer inputs from ranked, cited simulation evidence."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable

from agent_core.evidence_ranker import EvidenceRanker
from agent_core.schema import (
    ContactAngle,
    ContextFact,
    ContextPacket,
    KnowledgeGraph,
    NodeType,
    Objective,
    RankedEvidence,
)

TokenCounter = Callable[[str], int]


@dataclass(frozen=True)
class ContextPacketSelection:
    packet: ContextPacket
    ranked_evidence: tuple[RankedEvidence, ...]
    excluded_evidence_ids: tuple[str, ...]
    excluded_reasons: dict[str, str]


class ContextPacketBuilder:
    """Greedily pack the best eligible facts within a model-context budget.

    The default counter uses UTF-8 bytes as a conservative upper bound for
    byte-pair tokenizers. Supply the model's actual tokenizer for a less
    conservative budget. The selected packet never contains excluded facts.
    """

    def __init__(
        self,
        *,
        token_budget: int = 4096,
        token_counter: TokenCounter | None = None,
        ranker: EvidenceRanker | None = None,
    ) -> None:
        if isinstance(token_budget, bool) or not isinstance(token_budget, int) or token_budget <= 0:
            raise ValueError("token_budget must be a positive integer")
        self.token_budget = token_budget
        self.token_counter = token_counter or _conservative_token_upper_bound
        self.ranker = ranker or EvidenceRanker()

    def build(
        self,
        graph: KnowledgeGraph,
        objective: Objective,
        angle: ContactAngle,
        *,
        as_of: datetime,
    ) -> ContextPacketSelection:
        if angle.objective != objective:
            raise ValueError("angle objective must match the context objective")
        as_of_utc = _aware_utc(as_of)
        as_of_text = as_of_utc.isoformat().replace("+00:00", "Z")
        target_name = next(
            (node.label for node in graph.nodes.values() if node.type == NodeType.PERSON),
            graph.persona_id,
        )
        ranked = self.ranker.rank(
            graph.evidence.values(),
            relevance_tags=(*angle.required_tags, objective.value),
            as_of=as_of_utc,
        )
        evidence_by_id = graph.evidence
        base = ContextPacket(
            target_name=target_name,
            angle=angle,
            as_of=as_of_text,
            token_budget=self.token_budget,
            token_count=0,
            facts=(),
        )
        base_count = self._count(render_writer_context(base))
        if base_count > self.token_budget:
            raise ValueError(
                f"writer context header requires {base_count} tokens, over budget {self.token_budget}"
            )

        selected: list[ContextFact] = []
        excluded_reasons: dict[str, str] = {}
        for item in ranked:
            if not item.eligible:
                excluded_reasons[item.evidence_id] = item.exclusion_reason or "ineligible"
                continue
            evidence = evidence_by_id[item.evidence_id]
            uncertainty = _uncertainty_note(evidence.confidence, evidence.source_reliability)
            fact = ContextFact(
                evidence_id=evidence.id,
                description=evidence.description,
                source=evidence.source,
                observed_at=evidence.observed_at,
                confidence=evidence.confidence,
                source_reliability=evidence.source_reliability,
                uncertainty_note=uncertainty,
            )
            candidate = ContextPacket(
                target_name=target_name,
                angle=angle,
                as_of=as_of_text,
                token_budget=self.token_budget,
                token_count=0,
                facts=(*selected, fact),
            )
            candidate_count = self._count(render_writer_context(candidate))
            if candidate_count > self.token_budget:
                excluded_reasons[evidence.id] = "context_budget_exceeded"
                continue
            selected.append(fact)

        packet_without_count = ContextPacket(
            target_name=target_name,
            angle=angle,
            as_of=as_of_text,
            token_budget=self.token_budget,
            token_count=0,
            facts=tuple(selected),
        )
        token_count = self._count(render_writer_context(packet_without_count))
        packet = ContextPacket(
            target_name=target_name,
            angle=angle,
            as_of=as_of_text,
            token_budget=self.token_budget,
            token_count=token_count,
            facts=tuple(selected),
        )
        # Preserve source evidence order in logs while keeping deterministic IDs.
        evidence_order = {evidence_id: index for index, evidence_id in enumerate(graph.evidence)}
        excluded_ids = tuple(sorted(excluded_reasons, key=lambda evidence_id: evidence_order[evidence_id]))
        return ContextPacketSelection(packet, ranked, excluded_ids, excluded_reasons)

    def _count(self, text: str) -> int:
        count = self.token_counter(text)
        if isinstance(count, bool) or not isinstance(count, int) or count < 0:
            raise ValueError("token_counter must return a non-negative integer")
        return count


def render_writer_context(packet: ContextPacket) -> str:
    """Serialize only writer-authorized fields; audit exclusions stay separate."""
    payload = {
        "target_name": packet.target_name,
        "objective": packet.angle.objective.value,
        "angle": {
            "id": packet.angle.id,
            "title": packet.angle.title,
            "rationale": packet.angle.rationale,
            "required_tags": list(packet.angle.required_tags),
        },
        "as_of": packet.as_of,
        "facts": [
            {
                "evidence_id": fact.evidence_id,
                "description": fact.description,
                "source": fact.source,
                "observed_at": fact.observed_at,
                "confidence": fact.confidence,
                "source_reliability": fact.source_reliability,
                "uncertainty_note": fact.uncertainty_note,
            }
            for fact in packet.facts
        ],
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _uncertainty_note(confidence: float, source_reliability: float) -> str | None:
    if confidence < 0.85 or source_reliability < 0.75:
        return "Treat as uncertain; avoid stating as a confirmed current fact."
    return None


def _aware_utc(value: datetime) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("as_of must be a timezone-aware datetime")
    return value.astimezone(timezone.utc)


def _conservative_token_upper_bound(text: str) -> int:
    return len(text.encode("utf-8"))
