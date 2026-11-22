"""Deterministic checks for the context broker (evidence selection; no network)."""

import unittest
from datetime import datetime, timezone

from agent_core.context_broker import select_evidence
from agent_core.schema import FindingSource, ResearchFinding

AS_OF = datetime(2026, 11, 22, tzinfo=timezone.utc)


def _f(fid, reliability, category="role", observed="2026-11-01T00:00:00+00:00"):
    return ResearchFinding(id=fid, target_id="t", category=category, fact=f"fact {fid}",
                           reliability=reliability, observed_at=observed,
                           sources=(FindingSource(url="https://a.example/x", excerpt="e"),))


class _Hook:
    evidence_ids = ("f1", "f2", "f3")


class ContextBrokerTest(unittest.TestCase):
    def test_reliable_facts_rank_first(self):
        findings = [_f("f1", "unsicher"), _f("f2", "belastbar"), _f("f3", "unsicher")]
        out = select_evidence(findings, _Hook(), as_of=AS_OF)
        self.assertEqual(out[0].id, "f2")  # belastbar outranks unsicher
        self.assertEqual({f.id for f in out}, {"f1", "f2", "f3"})

    def test_fallback_when_hook_cites_nothing(self):
        class Empty:
            evidence_ids = ()
        findings = [_f(x, "unsicher") for x in ("a", "b", "c", "d")]
        out = select_evidence(findings, Empty(), limit=3)
        self.assertEqual(len(out), 3)  # fallback to findings[:3], capped at limit

    def test_single_finding_passthrough(self):
        class One:
            evidence_ids = ("only",)
        self.assertEqual([f.id for f in select_evidence([_f("only", "unsicher")], One())], ["only"])

    def test_limit_respected(self):
        findings = [_f(str(i), "unsicher") for i in range(8)]

        class All:
            evidence_ids = tuple(str(i) for i in range(8))
        self.assertEqual(len(select_evidence(findings, All(), limit=5, as_of=AS_OF)), 5)


if __name__ == "__main__":
    unittest.main()
