"""Deterministic evals for the research pipeline core (no network / no LLM)."""

from __future__ import annotations

import unittest

from agent_core.research import _domain, _first_json_array, _normalize, build_findings
from agent_core.schema import FindingSource, RELIABILITY_CONFIDENCE


def _row(fact, url, category="role"):
    return {"category": category, "fact": fact, "source": FindingSource(url=url, excerpt=fact)}


class ReliabilityRuleTest(unittest.TestCase):
    def test_two_distinct_domains_is_belastbar(self):
        rows = [
            _row("Co-Founder of revel8 since Jun 2024.", "https://revel8.ai/x"),
            _row("Co-Founder of revel8 since Jun 2024.", "https://sans.org/y"),
        ]
        findings = build_findings("julius", rows)
        self.assertEqual(len(findings), 1, "same claim from 2 sources must merge to one")
        self.assertEqual(findings[0].reliability, "belastbar")
        self.assertEqual(len(findings[0].sources), 2)

    def test_single_source_is_unsicher(self):
        findings = build_findings("julius", [_row("Based in Munich.", "https://revel8.ai/x", "company")])
        self.assertEqual(findings[0].reliability, "unsicher")
        self.assertEqual(findings[0].warum, "nur eine Quelle")

    def test_same_domain_twice_stays_unsicher(self):
        rows = [
            _row("Co-Founder of revel8.", "https://revel8.ai/a"),
            _row("Co-Founder of revel8.", "https://revel8.ai/b"),
        ]
        findings = build_findings("julius", rows)
        self.assertEqual(findings[0].reliability, "unsicher", "one domain is not two sources")

    def test_to_evidence_maps_confidence(self):
        ev = build_findings("julius", [_row("x", "https://a.com/1"), _row("x", "https://b.com/1")])[0].to_evidence()
        self.assertEqual(ev.confidence, RELIABILITY_CONFIDENCE["belastbar"])
        self.assertTrue(ev.safe_to_use)


class HelperTest(unittest.TestCase):
    def test_domain_strips_www(self):
        self.assertEqual(_domain("https://www.sans.org/profiles/x"), "sans.org")

    def test_normalize_collapses(self):
        self.assertEqual(_normalize("Co-Founder,  revel8!"), "co founder revel8")

    def test_first_json_array_handles_fence(self):
        self.assertEqual(_first_json_array('```json\n[{"a":1}]\n```'), [{"a": 1}])

    def test_first_json_array_handles_prose(self):
        self.assertEqual(_first_json_array('Sure:\n[1, 2]\ndone'), [1, 2])

    def test_first_json_array_bad_input(self):
        self.assertEqual(_first_json_array("no array here"), [])


if __name__ == "__main__":
    unittest.main()
