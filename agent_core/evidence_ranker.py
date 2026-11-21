"""Deterministic, provenance-aware ranking for simulation evidence."""

from __future__ import annotations

from datetime import datetime, timezone
from math import exp, log
from typing import Iterable

from agent_core.schema import Evidence, RankedEvidence


class EvidenceRanker:
    """Rank evidence for a turn without consulting private target metadata.

    ``as_of`` is required so a saved input set always produces the same scores.
    Contradictions are treated symmetrically: if either finding names the other,
    both are ineligible until an upstream review resolves the conflict.
    """

    _WEIGHTS = {
        "relevance": 0.35,
        "confidence": 0.25,
        "source_reliability": 0.20,
        "freshness": 0.20,
    }

    def __init__(
        self,
        *,
        min_confidence: float = 0.7,
        min_source_reliability: float = 0.5,
        stale_after_days: float = 365.0,
        freshness_half_life_days: float = 180.0,
    ) -> None:
        self._validate_unit_interval("min_confidence", min_confidence)
        self._validate_unit_interval("min_source_reliability", min_source_reliability)
        if stale_after_days <= 0:
            raise ValueError("stale_after_days must be greater than zero")
        if freshness_half_life_days <= 0:
            raise ValueError("freshness_half_life_days must be greater than zero")
        self.min_confidence = min_confidence
        self.min_source_reliability = min_source_reliability
        self.stale_after_days = stale_after_days
        self.freshness_half_life_days = freshness_half_life_days

    def rank(
        self,
        evidence: Iterable[Evidence],
        *,
        relevance_tags: Iterable[str],
        as_of: datetime,
    ) -> tuple[RankedEvidence, ...]:
        """Return all candidates, eligible items first, with auditable scores."""
        as_of_utc = self._require_aware("as_of", as_of).astimezone(timezone.utc)
        items = tuple(evidence)
        ids = [item.id for item in items]
        if len(ids) != len(set(ids)):
            raise ValueError("evidence IDs must be unique within a ranking request")

        query_tags = self._normalize_tags(relevance_tags)
        contradicted_ids = {
            item.id for item in items if item.contradicts
        } | {
            related_id
            for item in items
            for related_id in item.contradicts
        }

        ranked = [
            self._rank_one(item, query_tags=query_tags, as_of=as_of_utc, contradicted_ids=contradicted_ids)
            for item in items
        ]
        return tuple(sorted(ranked, key=lambda item: (not item.eligible, -item.score, item.evidence_id)))

    def _rank_one(
        self,
        item: Evidence,
        *,
        query_tags: frozenset[str],
        as_of: datetime,
        contradicted_ids: set[str],
    ) -> RankedEvidence:
        self._validate_unit_interval(f"{item.id}.confidence", item.confidence)
        self._validate_unit_interval(f"{item.id}.source_reliability", item.source_reliability)

        item_tags = self._normalize_tags(item.tags)
        relevance = len(query_tags & item_tags) / len(query_tags) if query_tags else 0.0
        observed_at, date_error = self._parse_observed_at(item.observed_at)
        if observed_at is None:
            freshness = 0.0
            age_days = None
        else:
            age_days = (as_of - observed_at.astimezone(timezone.utc)).total_seconds() / 86400
            freshness = exp(-log(2) * max(age_days, 0.0) / self.freshness_half_life_days)

        score = round(
            self._WEIGHTS["relevance"] * relevance
            + self._WEIGHTS["confidence"] * item.confidence
            + self._WEIGHTS["source_reliability"] * item.source_reliability
            + self._WEIGHTS["freshness"] * freshness,
            6,
        )

        reason_parts = [
            f"tag match {len(query_tags & item_tags)}/{len(query_tags)}" if query_tags else "no query tags",
            f"confidence {item.confidence:.2f}",
            f"source reliability {item.source_reliability:.2f}",
            f"freshness {freshness:.2f}",
        ]
        exclusion_reason = self._exclusion_reason(
            item,
            relevance=relevance,
            age_days=age_days,
            date_error=date_error,
            contradicted=item.id in contradicted_ids,
        )
        return RankedEvidence(
            evidence_id=item.id,
            score=score,
            relevance_score=round(relevance, 6),
            freshness_score=round(freshness, 6),
            source_reliability_score=item.source_reliability,
            confidence_score=item.confidence,
            eligible=exclusion_reason is None,
            contradicted=item.id in contradicted_ids,
            reason="; ".join(reason_parts),
            exclusion_reason=exclusion_reason,
        )

    def _exclusion_reason(
        self,
        item: Evidence,
        *,
        relevance: float,
        age_days: float | None,
        date_error: str | None,
        contradicted: bool,
    ) -> str | None:
        # Apply hard safety and evidence-quality gates before considering score.
        if not item.safe_to_use:
            return "unsafe_or_private"
        if not self._normalize_tags(item.tags):
            return "missing_relevance_tags"
        if not relevance:
            return "irrelevant_to_context"
        if date_error:
            return date_error
        if age_days is not None and age_days < 0:
            return "observed_in_future"
        if age_days is not None and age_days > self.stale_after_days:
            return "stale_evidence"
        if item.confidence < self.min_confidence:
            return "low_confidence"
        if item.source_reliability < self.min_source_reliability:
            return "low_source_reliability"
        if contradicted:
            return "contradicted"
        return None

    @staticmethod
    def _parse_observed_at(value: str) -> tuple[datetime | None, str | None]:
        try:
            parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
        except (AttributeError, TypeError, ValueError):
            return None, "invalid_observed_at"
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            return None, "observed_at_missing_timezone"
        return parsed, None

    @staticmethod
    def _require_aware(name: str, value: datetime) -> datetime:
        if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{name} must be a timezone-aware datetime")
        return value

    @staticmethod
    def _normalize_tags(tags: Iterable[str]) -> frozenset[str]:
        return frozenset(tag.strip().casefold() for tag in tags if isinstance(tag, str) and tag.strip())

    @staticmethod
    def _validate_unit_interval(name: str, value: float) -> None:
        if not isinstance(value, (int, float)) or isinstance(value, bool) or not 0.0 <= value <= 1.0:
            raise ValueError(f"{name} must be a number between 0 and 1")
