"""Deterministic evals for the graph loader and the hook reasoner (no network)."""

from __future__ import annotations

import unittest

from agent_core import angle_reasoner, llm
from agent_core.graph_loader import build_graph
from agent_core.research import _github_users_from_urls
from agent_core.schema import FindingSource, ResearchFinding


def _finding(fid, category, fact, reliability="belastbar"):
    return ResearchFinding(
        id=fid, target_id="t", category=category, fact=fact, reliability=reliability,
        observed_at="2026-11-21", sources=(FindingSource(url="https://a.com/1", excerpt=fact),),
    )


class GraphLoaderTest(unittest.TestCase):
    def test_star_graph_shape(self):
        findings = [_finding("f1", "role", "CFO"), _finding("f2", "project", "Built X")]
        g = build_graph("t", "Target Name", findings)
        self.assertEqual(len(g.nodes), 3)  # person + 2 facts
        self.assertEqual(len(g.edges), 2)
        self.assertIn("p_t", g.nodes)

    def test_paths_filter_by_tag_and_confidence(self):
        findings = [_finding("f1", "project", "Built X"), _finding("f2", "role", "CFO", "unsicher")]
        g = build_graph("t", "Target", findings)
        proj = g.paths_for({"project"}, min_confidence=0.7)
        self.assertEqual(len(proj), 1)
        # unsicher (0.5) is filtered out at min_confidence 0.7
        self.assertEqual(len(g.paths_for({"role"}, min_confidence=0.7)), 0)

    def test_unbelastbar_edge_not_safe(self):
        g = build_graph("t", "Target", [_finding("f1", "role", "CFO", "unbelastbar")])
        self.assertEqual(len(g.paths_for({"role"}, min_confidence=0.0, safe_only=True)), 0)


class HookReasonerTest(unittest.TestCase):
    def setUp(self):
        self._orig = llm.chat

    def tearDown(self):
        llm.chat = self._orig

    def test_drops_hooks_citing_fake_evidence(self):
        llm.chat = lambda *a, **k: (
            '[{"topic":"solar","why_now":"won hackathon","evidence_ids":["f1"],'
            '"suggested_channel":"email","suggested_angle":"grid follow-up"},'
            '{"topic":"ghost","why_now":"x","evidence_ids":["does_not_exist"],'
            '"suggested_channel":"sms","suggested_angle":"y"}]'
        )
        findings = [_finding("f1", "project", "Won a solar hackathon")]
        hooks = angle_reasoner.rank_hooks(findings)
        self.assertEqual(len(hooks), 1)
        self.assertEqual(hooks[0].topic, "solar")
        self.assertEqual(hooks[0].evidence_ids, ("f1",))

    def test_empty_when_no_facts(self):
        llm.chat = lambda *a, **k: "[]"
        self.assertEqual(angle_reasoner.rank_hooks([]), [])


class GithubResolveTest(unittest.TestCase):
    def test_extracts_usernames(self):
        urls = ["https://github.com/MarcZem/SatteliTrees", "https://github.com/topics/x", "https://x.com/a"]
        self.assertEqual(_github_users_from_urls(urls), ["MarcZem"])


if __name__ == "__main__":
    unittest.main()
