"""Context broker: select and order the evidence the writer sees for a turn.

Wraps the deterministic EvidenceRanker (relevance, confidence, source reliability and
freshness at an explicit ``as_of``) over the hook's cited facts, so the writer gets the
most reliable, on-topic facts first instead of an arbitrary slice. Fully deterministic;
falls back to the hook's cited facts if ranking yields nothing, so the loop never loses
its evidence. This is the seam that makes the evidence ranker load-bearing in the agent.
"""

from __future__ import annotations

from datetime import datetime, timezone

from agent_core.evidence_ranker import EvidenceRanker
from agent_core.schema import ResearchFinding


def select_evidence(findings: list[ResearchFinding], hook, *, limit: int = 5,
                    as_of: datetime | None = None) -> list[ResearchFinding]:
    """Rank the hook's cited facts (reliable + fresh first) and return the top ``limit``."""
    cited_ids = set(getattr(hook, "evidence_ids", ()) or ())
    cited = [f for f in findings if f.id in cited_ids] or list(findings[:3])
    if len(cited) <= 1:
        return cited[:limit]
    by_id = {f.id: f for f in cited}
    tags = {f.category for f in cited if f.category} or {"role"}
    try:
        ranker = EvidenceRanker(min_confidence=0.0, min_source_reliability=0.0)
        ranked = ranker.rank([f.to_evidence() for f in cited], relevance_tags=tags,
                             as_of=as_of or datetime.now(timezone.utc))
        ordered = [by_id[r.evidence_id] for r in ranked if r.evidence_id in by_id]
    except (ValueError, KeyError):
        ordered = cited
    return (ordered or cited)[:limit]
