from __future__ import annotations

import unittest
from datetime import datetime, timezone

from agent_core.evidence_ranker import EvidenceRanker
from agent_core.schema import Evidence


AS_OF = datetime(2026, 11, 21, 12, 0, tzinfo=timezone.utc)


def evidence(
    evidence_id: str,
    *,
    tags: tuple[str, ...] = ("current_project",),
    confidence: float = 0.9,
    reliability: float = 0.9,
    observed_at: str = "2026-11-20T12:00:00Z",
    safe: bool = True,
    contradicts: tuple[str, ...] = (),
) -> Evidence:
    return Evidence(
        id=evidence_id,
        source="synthetic_fixture",
        description=f"Fixture {evidence_id}",
        confidence=confidence,
        safe_to_use=safe,
        observed_at=observed_at,
        tags=tags,
        source_reliability=reliability,
        contradicts=contradicts,
    )


class EvidenceRankerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.ranker = EvidenceRanker()

    def rank(self, items: list[Evidence], tags: tuple[str, ...] = ("current_project",)):
        return self.ranker.rank(items, relevance_tags=tags, as_of=AS_OF)

    def test_relevance_confidence_reliability_and_freshness_affect_score(self) -> None:
        best = evidence("best", tags=("current_project", "leadership"), confidence=0.95, reliability=0.95)
        weaker = evidence("weaker", tags=("current_project",), confidence=0.75, reliability=0.55)

        ranked = self.rank([weaker, best], tags=("current_project", "leadership"))

        self.assertEqual([item.evidence_id for item in ranked], ["best", "weaker"])
        self.assertGreater(ranked[0].score, ranked[1].score)
        self.assertEqual(ranked[0].relevance_score, 1.0)
        self.assertEqual(ranked[1].relevance_score, 0.5)
        self.assertTrue(ranked[0].eligible)
        self.assertIn("tag match 2/2", ranked[0].reason)

    def test_confidence_source_quality_and_recency_have_independent_effects(self) -> None:
        candidates = [
            evidence("baseline"),
            evidence("lower_confidence", confidence=0.75),
            evidence("lower_reliability", reliability=0.55),
            evidence("older", observed_at="2026-05-25T12:00:00Z"),
        ]

        ranked = {item.evidence_id: item for item in self.rank(candidates)}

        self.assertGreater(ranked["baseline"].score, ranked["lower_confidence"].score)
        self.assertGreater(ranked["baseline"].score, ranked["lower_reliability"].score)
        self.assertGreater(ranked["baseline"].freshness_score, ranked["older"].freshness_score)
        self.assertGreater(ranked["baseline"].score, ranked["older"].score)

    def test_hard_gates_exclude_unsafe_irrelevant_stale_and_low_quality(self) -> None:
        items = [
            evidence("safe", tags=("current_project",)),
            evidence("unsafe", safe=False),
            evidence("irrelevant", tags=("old_job",)),
            evidence("stale", observed_at="2024-01-01T00:00:00Z"),
            evidence("low_confidence", confidence=0.4),
            evidence("low_reliability", reliability=0.2),
        ]

        ranked = {item.evidence_id: item for item in self.rank(items)}

        self.assertTrue(ranked["safe"].eligible)
        self.assertEqual(ranked["unsafe"].exclusion_reason, "unsafe_or_private")
        self.assertEqual(ranked["irrelevant"].exclusion_reason, "irrelevant_to_context")
        self.assertEqual(ranked["stale"].exclusion_reason, "stale_evidence")
        self.assertEqual(ranked["low_confidence"].exclusion_reason, "low_confidence")
        self.assertEqual(ranked["low_reliability"].exclusion_reason, "low_source_reliability")

    def test_contradiction_is_symmetric_and_excluded(self) -> None:
        first = evidence("first", contradicts=("second",))
        second = evidence("second")

        ranked = {item.evidence_id: item for item in self.rank([first, second])}

        self.assertTrue(ranked["first"].contradicted)
        self.assertTrue(ranked["second"].contradicted)
        self.assertEqual(ranked["first"].exclusion_reason, "contradicted")
        self.assertEqual(ranked["second"].exclusion_reason, "contradicted")

    def test_invalid_or_timezone_naive_observation_is_ineligible(self) -> None:
        malformed = evidence("malformed", observed_at="not-a-date")
        naive = evidence("naive", observed_at="2026-11-20T12:00:00")

        ranked = {item.evidence_id: item for item in self.rank([malformed, naive])}

        self.assertEqual(ranked["malformed"].exclusion_reason, "invalid_observed_at")
        self.assertEqual(ranked["naive"].exclusion_reason, "observed_at_missing_timezone")

    def test_future_observation_is_ineligible(self) -> None:
        future = evidence("future", observed_at="2026-11-22T00:00:00Z")

        result = self.rank([future])[0]

        self.assertFalse(result.eligible)
        self.assertEqual(result.exclusion_reason, "observed_in_future")

    def test_same_inputs_and_as_of_are_deterministic_and_ties_use_id(self) -> None:
        items = [evidence("z"), evidence("a")]

        first = self.rank(items)
        second = self.rank(reversed(items))

        self.assertEqual(first, second)
        self.assertEqual([item.evidence_id for item in first], ["a", "z"])

    def test_naive_as_of_and_duplicate_ids_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "timezone-aware"):
            self.ranker.rank([], relevance_tags=("current_project",), as_of=datetime(2026, 11, 21))
        repeated = evidence("same")
        with self.assertRaisesRegex(ValueError, "unique"):
            self.rank([repeated, repeated])

    def test_invalid_scores_and_empty_query_do_not_accidentally_select_facts(self) -> None:
        with self.assertRaisesRegex(ValueError, "between 0 and 1"):
            self.rank([evidence("bad", confidence=1.1)])

        result = self.rank([evidence("candidate")], tags=())[0]
        self.assertFalse(result.eligible)
        self.assertEqual(result.exclusion_reason, "irrelevant_to_context")


if __name__ == "__main__":
    unittest.main()
