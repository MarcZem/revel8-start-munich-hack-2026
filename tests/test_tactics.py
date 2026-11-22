"""Deterministic evals for the tactic registry + sweep scoring (no network)."""

from __future__ import annotations

import unittest

from agent_core import tactics


class RegistryTest(unittest.TestCase):
    def test_registry_is_well_formed(self):
        names = [t.name for t in tactics.TACTICS]
        self.assertEqual(len(names), len(set(names)), "tactic names must be unique")
        for t in tactics.TACTICS:
            self.assertIn(t.objective, ("disclosure", "credentials", "action"))
            self.assertTrue(t.channel and t.lever and t.pretext)

    def test_channels_span_more_than_email(self):
        channels = {t.channel for t in tactics.TACTICS}
        self.assertTrue({"email", "sms", "slack", "phone_call"} <= channels)

    def test_exactly_the_call_tactic_is_a_call(self):
        calls = [t for t in tactics.TACTICS if t.is_call]
        self.assertTrue(all(t.channel == "phone_call" for t in calls))


class EngagementTest(unittest.TestCase):
    def test_submit_beats_reply(self):
        log = {"contacts": [
            {"events": [{"type": "reply"}]},
            {"events": [{"type": "link.opened"}, {"type": "page.submitted"}]},
        ]}
        self.assertEqual(tactics.engagement(log), (4, "page.submitted"))

    def test_reply_only(self):
        self.assertEqual(tactics.engagement({"contacts": [{"events": [{"type": "reply"}]}]}),
                         (1, "reply"))

    def test_silence(self):
        self.assertEqual(tactics.engagement({"contacts": [{"events": []}]}), (0, "silence"))

    def test_call_path_events_at_top_level(self):
        self.assertEqual(tactics.engagement({"events": [{"type": "link.opened"}]}),
                         (3, "link.opened"))


if __name__ == "__main__":
    unittest.main()
