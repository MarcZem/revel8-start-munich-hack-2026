"""Load research findings (JSONL) into the existing KnowledgeGraph.

Star shape: a Person node in the centre, one fact node per finding, one edge each
tagged by category with confidence derived from reliability. Reuses the graph +
`paths_for` in schema.py — no new graph tech.
"""

from __future__ import annotations

import json
from pathlib import Path

from agent_core.schema import (
    RELIABILITY_CONFIDENCE,
    FindingSource,
    GraphEdge,
    GraphNode,
    KnowledgeGraph,
    NodeType,
    ResearchFinding,
)

_CAT_NODE = {
    "role": NodeType.ROLE,
    "company": NodeType.COMPANY,
    "project": NodeType.PROJECT,
}


def load_findings(path: str | Path) -> list[ResearchFinding]:
    findings: list[ResearchFinding] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        d = json.loads(line)
        d["sources"] = tuple(FindingSource(**s) for s in d.get("sources", []))
        d["contradicts"] = tuple(d.get("contradicts", []))
        findings.append(ResearchFinding(**d))
    return findings


def build_graph(target_id: str, target_name: str, findings: list[ResearchFinding]) -> KnowledgeGraph:
    person_id = f"p_{target_id}"
    nodes: dict[str, GraphNode] = {
        person_id: GraphNode(id=person_id, type=NodeType.PERSON, label=target_name)
    }
    edges: dict[str, GraphEdge] = {}
    evidence = {}
    for f in findings:
        nodes[f.id] = GraphNode(
            id=f.id,
            type=_CAT_NODE.get(f.category, NodeType.INTEREST),
            label=f.fact,
            attributes={"reliability": f.reliability, "category": f.category},
        )
        ev = f.to_evidence()
        evidence[ev.id] = ev
        edges[f"e_{f.id}"] = GraphEdge(
            id=f"e_{f.id}",
            source=person_id,
            target=f.id,
            relation=f.category,
            evidence_ids=(ev.id,),
            confidence=RELIABILITY_CONFIDENCE.get(f.reliability, 0.5),
            relevance_tags=(f.category,),
            safe_to_use=f.reliability != "unbelastbar",
        )
    return KnowledgeGraph(persona_id=target_id, nodes=nodes, edges=edges, evidence=evidence)


def graph_from_jsonl(target_id: str, target_name: str, path: str | Path) -> KnowledgeGraph:
    return build_graph(target_id, target_name, load_findings(path))
