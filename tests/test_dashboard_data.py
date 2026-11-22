"""Deterministic checks for the dashboard export (no network, no runs/ needed)."""

import unittest

from agent_core.run_record import RunRecord
from scripts.build_dashboard_data import _targeting_score, _thread_from_record


class TargetingScore(unittest.TestCase):
    def test_mean_confidence_from_reliability(self):
        rel = {"a": "belastbar", "b": "unsicher"}  # 0.9, 0.5 -> 70%
        hook = {"evidence_ids": ["a", "b", "missing"]}
        score = _targeting_score(hook, rel)
        self.assertEqual(score["percent"], 70)
        self.assertEqual(score["evidence_count"], 2)
        self.assertEqual(score["breakdown"], {"belastbar": 1, "unsicher": 1})

    def test_none_without_scored_evidence(self):
        self.assertIsNone(_targeting_score({"evidence_ids": ["x"]}, {}))


class Thread(unittest.TestCase):
    def test_thread_surfaces_reply_decision_and_gate(self):
        rec = RunRecord.from_log({
            "target": "julius", "objective": "breach", "channel": "email",
            "hook": {"topic": "panel", "evidence_ids": []}, "hooks_considered": [],
            "contacts": [
                {"payload": {"channel": "email", "from": {"name": "Alex", "address": "a@x.de"},
                             "subject": "hi", "body": "hello"},
                 "touches_used": 1, "sent_because": "first, cold contact — rapport, no link",
                 "events": [{"type": "reply", "body": "who are you?"}],
                 "decision": {"action": "continue", "reason": "answer the gate"},
                 "state_after": {"gate_seen": "asks who you are"}},
                {"payload": {"channel": "email", "body": "second"}, "touches_used": 2, "events": []},
            ],
            "incident": False,
        })
        thread = _thread_from_record(rec)
        self.assertEqual(len(thread), 2)
        self.assertEqual(thread[0]["reply"], "who are you?")
        self.assertEqual(thread[0]["decision"]["action"], "continue")
        self.assertEqual(thread[0]["gate"], "asks who you are")
        self.assertTrue(thread[0]["sent_because"].startswith("first"))
        self.assertIsNone(thread[1]["reply"])  # silence


if __name__ == "__main__":
    unittest.main()
