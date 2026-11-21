"""Shared JSON contracts for the local agent core prototype."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from enum import Enum
from typing import Any


class NodeType(str, Enum):
    PERSON = "Person"
    ROLE = "Role"
    COMPANY = "Company"
    PROJECT = "Project"
    INTEREST = "Interest"
    CONTACT_ANGLE = "ContactAngle"
    CHANNEL = "Channel"
    MESSAGE = "Message"
    EVENT = "Event"
    DECISION = "Decision"


class Objective(str, Enum):
    ACTION = "action"
    DISCLOSURE = "disclosure"
    MEETING = "meeting"
    AWARENESS = "awareness"


class Channel(str, Enum):
    FAKE_EMAIL = "fake_email"
    FAKE_CALENDAR = "fake_calendar"
    FAKE_DOCUMENT = "fake_document"


@dataclass(frozen=True)
class Evidence:
    id: str
    source: str
    description: str
    confidence: float
    safe_to_use: bool = True
    observed_at: str = "2026-11-21T12:00:00Z"
    tags: tuple[str, ...] = ()
    source_reliability: float = 0.5
    contradicts: tuple[str, ...] = ()


@dataclass(frozen=True)
class RankedEvidence:
    evidence_id: str
    score: float
    relevance_score: float
    freshness_score: float
    source_reliability_score: float
    confidence_score: float
    eligible: bool
    contradicted: bool
    reason: str
    exclusion_reason: str | None = None


class Reliability(str, Enum):
    BELASTBAR = "belastbar"
    UNSICHER = "unsicher"
    UNBELASTBAR = "unbelastbar"


# Derived numeric so the graph's min_confidence filter keeps working.
RELIABILITY_CONFIDENCE = {"belastbar": 0.9, "unsicher": 0.5, "unbelastbar": 0.2}


@dataclass(frozen=True)
class FindingSource:
    url: str
    excerpt: str
    channel: str = "web"
    published_at: str = ""  # source date if known, for recency weighting


@dataclass(frozen=True)
class ResearchFinding:
    """One atomic, self-contained fact about a target. See docs/research-finding-schema.md."""

    id: str
    target_id: str
    category: str  # role|project|talk|network|company|other
    fact: str
    reliability: str  # belastbar|unsicher|unbelastbar
    observed_at: str
    sources: tuple[FindingSource, ...]
    warum: str = ""
    contradicts: tuple[str, ...] = ()

    def to_evidence(self) -> Evidence:
        return Evidence(
            id=self.id,
            source=self.sources[0].url if self.sources else "",
            description=self.fact,
            confidence=RELIABILITY_CONFIDENCE.get(self.reliability, 0.5),
            safe_to_use=self.reliability != "unbelastbar",
            observed_at=self.observed_at,
            tags=(self.category,),
        )


@dataclass(frozen=True)
class GraphNode:
    id: str
    type: NodeType
    label: str
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GraphEdge:
    id: str
    source: str
    target: str
    relation: str
    evidence_ids: tuple[str, ...]
    confidence: float
    relevance_tags: tuple[str, ...]
    safe_to_use: bool = True


@dataclass(frozen=True)
class GraphPath:
    id: str
    node_ids: tuple[str, ...]
    edge_ids: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    summary: str
    relevance_tags: tuple[str, ...]
    confidence: float


@dataclass(frozen=True)
class KnowledgeGraph:
    persona_id: str
    nodes: dict[str, GraphNode]
    edges: dict[str, GraphEdge]
    evidence: dict[str, Evidence]

    def node(self, node_id: str) -> GraphNode:
        return self.nodes[node_id]

    def paths_for(
        self,
        tags: set[str],
        *,
        min_confidence: float = 0.7,
        safe_only: bool = True,
    ) -> tuple[GraphPath, ...]:
        paths: list[GraphPath] = []
        for edge in self.edges.values():
            if safe_only and not edge.safe_to_use:
                continue
            if edge.confidence < min_confidence:
                continue
            if tags and not tags.intersection(edge.relevance_tags):
                continue
            evidence = [self.evidence[eid] for eid in edge.evidence_ids if eid in self.evidence]
            if safe_only and any(not item.safe_to_use for item in evidence):
                continue
            source = self.nodes[edge.source]
            target = self.nodes[edge.target]
            confidence = min([edge.confidence, *[item.confidence for item in evidence]] or [edge.confidence])
            paths.append(
                GraphPath(
                    id=f"path_{edge.id}",
                    node_ids=(source.id, target.id),
                    edge_ids=(edge.id,),
                    evidence_ids=tuple(item.id for item in evidence),
                    summary=f"{source.label} {edge.relation} {target.label}",
                    relevance_tags=edge.relevance_tags,
                    confidence=round(confidence, 3),
                )
            )
        return tuple(sorted(paths, key=lambda path: (-path.confidence, path.id)))


@dataclass(frozen=True)
class ContactAngle:
    id: str
    title: str
    objective: Objective
    channel: Channel
    rationale: str
    required_tags: tuple[str, ...]
    risk_notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class ContextFact:
    evidence_id: str
    description: str
    source: str
    observed_at: str
    confidence: float
    source_reliability: float
    uncertainty_note: str | None = None


@dataclass(frozen=True)
class ContextPacket:
    """Small writer-facing view containing only selected, cited evidence."""

    target_name: str
    angle: ContactAngle
    as_of: str
    token_budget: int
    token_count: int
    facts: tuple[ContextFact, ...]

    @property
    def objective(self) -> Objective:
        return self.angle.objective

    @property
    def allowed_evidence_ids(self) -> set[str]:
        return {fact.evidence_id for fact in self.facts}


@dataclass(frozen=True)
class RoutedContext:
    objective: Objective
    angle: ContactAngle
    loaded_paths: tuple[GraphPath, ...]
    excluded_evidence_ids: tuple[str, ...]
    excluded_reasons: dict[str, str]
    context_packet: ContextPacket | None = None
    ranked_evidence: tuple[RankedEvidence, ...] = ()

    @property
    def allowed_evidence_ids(self) -> set[str]:
        if self.context_packet is not None:
            return self.context_packet.allowed_evidence_ids
        allowed: set[str] = set()
        for path in self.loaded_paths:
            allowed.update(path.evidence_ids)
        return allowed


@dataclass(frozen=True)
class MessageCandidate:
    id: str
    writer_model: str
    advisor_model: str
    channel: Channel
    sender_type: str
    objective: Objective
    angle_id: str
    subject: str
    body: str
    landing_page_url: str
    landing_page_summary: str
    used_evidence_ids: tuple[str, ...]
    known_risks: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CriticScores:
    candidate_id: str
    critic_model: str
    scores: dict[str, int]
    send_recommendation: str
    reasoning_summary: str

    @property
    def utility_score(self) -> int:
        positive = (
            self.scores["rule_compliance"]
            + self.scores["evidence_fidelity"]
            + self.scores["persona_fit"]
            + self.scores["craft"]
            + self.scores["persistence"]
        )
        return positive - self.scores["disqualification_risk"]


@dataclass(frozen=True)
class GateVerdict:
    candidate_id: str
    decision: str
    blocked_reasons: tuple[str, ...]
    warnings: tuple[str, ...]
    score: int


@dataclass(frozen=True)
class CommitteeDecision:
    advisor_model: str
    writer_model: str
    critic_model: str
    angles: tuple[ContactAngle, ...]
    candidates: tuple[MessageCandidate, ...]
    critic_scores: tuple[CriticScores, ...]
    gate_verdicts: tuple[GateVerdict, ...]
    winner_candidate_id: str | None
    selection_reason: str


@dataclass(frozen=True)
class ApiEvent:
    id: str
    candidate_id: str
    event_type: str
    reply: str
    signal_score: int
    simulated: bool = True


@dataclass(frozen=True)
class StrategyUpdate:
    angle_id: str
    prior_score: int
    event_signal: int
    wrong_fact_penalty: int
    updated_score: int
    lesson: str


@dataclass(frozen=True)
class RunLog:
    run_id: str
    persona_id: str
    graph: KnowledgeGraph
    routed_context: RoutedContext
    committee_decision: CommitteeDecision
    api_event: ApiEvent | None
    strategy_update: StrategyUpdate
    timeline: tuple[dict[str, Any], ...]
    preference_data: dict[str, Any]


def to_jsonable(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return {key: to_jsonable(item) for key, item in asdict(value).items()}
    if isinstance(value, dict):
        return {str(key): to_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [to_jsonable(item) for item in value]
    return value
