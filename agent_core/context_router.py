"""Context routing for minimum relevant graph paths."""

from __future__ import annotations

from agent_core.schema import ContactAngle, KnowledgeGraph, Objective, RoutedContext


class ContextRouter:
    def __init__(self, *, min_confidence: float = 0.7, max_paths: int = 4) -> None:
        self.min_confidence = min_confidence
        self.max_paths = max_paths

    def route(self, graph: KnowledgeGraph, objective: Objective, angle: ContactAngle) -> RoutedContext:
        tags = set(angle.required_tags) | {objective.value}
        paths = graph.paths_for(tags, min_confidence=self.min_confidence, safe_only=True)[: self.max_paths]
        loaded_evidence = {evidence_id for path in paths for evidence_id in path.evidence_ids}
        excluded: dict[str, str] = {}
        for evidence_id, evidence in graph.evidence.items():
            if evidence_id in loaded_evidence:
                continue
            if not evidence.safe_to_use:
                excluded[evidence_id] = "unsafe_or_private"
            elif evidence.confidence < self.min_confidence:
                excluded[evidence_id] = "low_confidence"
            elif tags.isdisjoint(evidence.tags):
                excluded[evidence_id] = "irrelevant_to_objective"
            else:
                excluded[evidence_id] = "not_on_selected_path"
        return RoutedContext(
            objective=objective,
            angle=angle,
            loaded_paths=paths,
            excluded_evidence_ids=tuple(sorted(excluded)),
            excluded_reasons=excluded,
        )
