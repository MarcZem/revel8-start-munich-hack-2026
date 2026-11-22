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
