"""Run deterministic, offline Context Broker evaluations over synthetic fixtures."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent_core.context_packet import ContextPacketBuilder, render_writer_context
from agent_core.evidence_ranker import EvidenceRanker
from agent_core.schema import (
    Channel,
    ContactAngle,
    Evidence,
    GraphNode,
    KnowledgeGraph,
    NodeType,
    Objective,
)


CASE_PATH = ROOT / "evals" / "context_broker_cases.json"
DEFAULT_REPORT_PATH = ROOT / "evals" / "context_broker_report.json"


def _load_case(path: Path = CASE_PATH) -> tuple[dict[str, Any], KnowledgeGraph, Objective, ContactAngle, datetime]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("version") != 1:
        raise ValueError("unsupported context broker eval fixture version")
    as_of = datetime.fromisoformat(data["as_of"].replace("Z", "+00:00"))
    objective = Objective(data["objective"])
    angle_data = data["angle"]
    angle = ContactAngle(
        id=angle_data["id"],
        title=angle_data["title"],
        objective=objective,
        channel=Channel.FAKE_EMAIL,
        rationale=angle_data["rationale"],
        required_tags=tuple(angle_data["required_tags"]),
    )
    evidence = [
        Evidence(
            id=item["id"],
            source=item["source"],
            description=item["description"],
            confidence=item["confidence"],
            safe_to_use=item.get("safe_to_use", True),
            observed_at=item["observed_at"],
            tags=tuple(item["tags"]),
            source_reliability=item["source_reliability"],
            contradicts=tuple(item.get("contradicts", ())),
        )
        for item in data["evidence"]
    ]
    person = GraphNode("person_synthetic_eval", NodeType.PERSON, "Alex Example", {"persona": "synthetic_eval"})
    graph = KnowledgeGraph(
        persona_id="synthetic_context_broker_eval",
        nodes={person.id: person},
        edges={},
        evidence={item.id: item for item in evidence},
    )
    return data, graph, objective, angle, as_of


def run_evaluations(path: Path = CASE_PATH) -> dict[str, Any]:
    data, graph, objective, angle, as_of = _load_case(path)
    ranked = EvidenceRanker().rank(
        graph.evidence.values(),
        relevance_tags=(*angle.required_tags, objective.value),
        as_of=as_of,
    )
    rank_ids = [item.evidence_id for item in ranked]
    expected_top = data["expected_top_evidence_id"]
    checks: list[dict[str, Any]] = []

    def record(name: str, passed: bool, details: str) -> None:
        checks.append({"name": name, "passed": bool(passed), "details": details})

    first_eligible = next((item for item in ranked if item.eligible), None)
    record(
        "relevant_current_fact_ranks_first",
        first_eligible is not None and first_eligible.evidence_id == expected_top,
        f"expected {expected_top}; got {first_eligible.evidence_id if first_eligible else 'no eligible facts'}",
    )
    eligible_scores = [item.score for item in ranked if item.eligible]
    eligibility_boundary = next((index for index, item in enumerate(ranked) if not item.eligible), len(ranked))
    record(
        "eligible_facts_precede_excluded_facts",
        all(item.eligible for item in ranked[:eligibility_boundary])
        and all(not item.eligible for item in ranked[eligibility_boundary:]),
        f"eligibility boundary at ranked index {eligibility_boundary}",
    )
    record(
        "eligible_scores_descend",
        eligible_scores == sorted(eligible_scores, reverse=True),
        f"eligible scores: {eligible_scores}",
    )
    expected_exclusions = data["expected_exclusions"]
    ranking_reasons = {item.evidence_id: item.exclusion_reason for item in ranked}
    for evidence_id, expected_reason in expected_exclusions.items():
        record(
            f"rank_excludes_{evidence_id}",
            ranking_reasons.get(evidence_id) == expected_reason,
            f"expected {expected_reason}; got {ranking_reasons.get(evidence_id)}",
        )

    budgets = []
    for budget in data["budgets"]:
        builder = ContextPacketBuilder(token_budget=budget)
        selection = builder.build(graph, objective, angle, as_of=as_of)
        repeated = builder.build(graph, objective, angle, as_of=as_of)
        serialized = render_writer_context(selection.packet)
        actual_count = builder.token_counter(serialized)
        eligible_ids = {item.evidence_id for item in ranked if item.eligible}
        selected_ids = {fact.evidence_id for fact in selection.packet.facts}
        expected_audit = {
            item.evidence_id: (
                item.exclusion_reason if not item.eligible else "context_budget_exceeded"
            )
            for item in ranked
            if item.evidence_id not in selected_ids
        }
        record(
            f"budget_{budget}_not_exceeded",
            selection.packet.token_count <= budget and actual_count <= budget,
            f"recorded {selection.packet.token_count}, measured {actual_count}, limit {budget}",
        )
        record(
            f"budget_{budget}_cites_only_eligible_facts",
            selected_ids <= eligible_ids,
            f"selected {sorted(selected_ids - eligible_ids)} ineligible IDs",
        )
        record(
            f"budget_{budget}_provenance_complete",
            all(
                fact.evidence_id in graph.evidence
                and fact.source == graph.evidence[fact.evidence_id].source
                and fact.confidence == graph.evidence[fact.evidence_id].confidence
                for fact in selection.packet.facts
            ),
            f"{len(selection.packet.facts)} packet fact(s) checked against source evidence",
        )
        record(
            f"budget_{budget}_all_exclusions_explained",
            selection.excluded_reasons == expected_audit
            and set(selection.excluded_evidence_ids) == set(expected_audit),
            f"expected {expected_audit}; got {selection.excluded_reasons}",
        )
        record(
            f"budget_{budget}_repeatable",
            selection == repeated,
            "identical fixture and as_of produced identical packet, scores, and exclusions",
        )
        for evidence_id, expected_reason in expected_exclusions.items():
            record(
                f"budget_{budget}_audits_{evidence_id}",
                selection.excluded_reasons.get(evidence_id) == expected_reason,
                f"expected {expected_reason}; got {selection.excluded_reasons.get(evidence_id)}",
            )
        budgets.append(
            {
                "token_budget": budget,
                "token_count": selection.packet.token_count,
                "selected_evidence_ids": [fact.evidence_id for fact in selection.packet.facts],
                "excluded_evidence_ids": list(selection.excluded_evidence_ids),
                "excluded_reasons": selection.excluded_reasons,
            }
        )

    # Budget growth must not remove a higher-ranked fact already selected below.
    for lower, higher in zip(budgets, budgets[1:]):
        lower_ids = set(lower["selected_evidence_ids"])
        higher_ids = set(higher["selected_evidence_ids"])
        record(
            f"budget_{higher['token_budget']}_preserves_lower_budget_selection",
            lower_ids <= higher_ids,
            f"lower-only IDs: {sorted(lower_ids - higher_ids)}",
        )

    failures = [check for check in checks if not check["passed"]]
    return {
        "fixture": path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else path.name,
        "fixture_version": data["version"],
        "as_of": data["as_of"],
        "mode": "offline_synthetic_only",
        "ranked_evidence": [
            {
                "evidence_id": item.evidence_id,
                "score": item.score,
                "eligible": item.eligible,
                "exclusion_reason": item.exclusion_reason,
            }
            for item in ranked
        ],
        "budget_runs": budgets,
        "checks": checks,
        "passed": len(failures) == 0,
        "summary": {"passed": len(checks) - len(failures), "failed": len(failures), "total": len(checks)},
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", type=Path, default=CASE_PATH, help="synthetic JSON eval fixture")
    parser.add_argument("--output", type=Path, default=DEFAULT_REPORT_PATH, help="JSON report path")
    args = parser.parse_args(argv)
    report = run_evaluations(args.case)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary = report["summary"]
    print(f"context_broker_evals={summary['passed']}/{summary['total']} passed")
    print(f"report={args.output}")
    for check in report["checks"]:
        if not check["passed"]:
            print(f"FAIL {check['name']}: {check['details']}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
