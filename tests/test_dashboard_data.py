"""Deterministic checks for the dashboard export (no network, no runs/ needed)."""

import unittest

from scripts.build_dashboard_data import _targeting_score, _thread


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
    def test_pairs_message_with_reply_and_plan(self):
        contact = {
            "contacts": [
                {
                    "payload": {"channel": "email", "from": {"name": "Alex", "address": "a@x.de"},
                                "subject": "hi", "body": "hello", "to": "t"},
                    "touches_used": 1,
                    "events": [{"type": "reply", "body": "who are you?"}],
                    "plan": {"action": "continue", "guidance": "anchor a detail"},
                },
                {"payload": {"channel": "email", "body": "second"}, "touches_used": 2, "events": []},
            ]
        }
        thread = _thread(contact)
        self.assertEqual(len(thread), 2)
        self.assertEqual(thread[0]["reply"], "who are you?")
        self.assertEqual(thread[0]["plan"], "continue")
        self.assertIsNone(thread[1]["reply"])  # silence


if __name__ == "__main__":
    unittest.main()
