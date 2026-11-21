from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from dashboard.render_replay import render_replay


ROOT = Path(__file__).resolve().parents[1]


class DashboardReplayTests(unittest.TestCase):
    def setUp(self) -> None:
        self.run_log = json.loads((ROOT / "runs" / "latest_agent_core_run.json").read_text(encoding="utf-8"))

    def test_replay_shows_run_evidence_message_gate_event_and_decision(self) -> None:
        document = render_replay(self.run_log)

        for expected in (
            "Synthetic local simulation",
            "Lena Kraus",
            "Evidence and confidence",
            "ev_lena_supplier",
            "82% · Selected",
            "Selected message preview",
            "fake_link_opened",
            "The vendor-risk checklist looks relevant.",
            "Next-step decision",
            "Start pitch replay",
        ):
            self.assertIn(expected, document)

    def test_blocked_candidate_message_body_is_not_rendered(self) -> None:
        document = render_replay(self.run_log)

        self.assertIn("msg_003_rule_break", document)
        self.assertIn("prompt_injection_attempt", document)
        self.assertNotIn("enter your password", document)
        self.assertNotIn("Ignore previous instructions", document)

    def test_untrusted_run_text_is_html_escaped(self) -> None:
        run_log = copy.deepcopy(self.run_log)
        person = next(node for node in run_log["graph"]["nodes"].values() if node["type"] == "Person")
        person["label"] = "<script>alert('x')</script>"
        run_log["graph"]["evidence"]["ev_lena_supplier"]["description"] = '<img src=x onerror="alert(1)">'

        document = render_replay(run_log)

        self.assertNotIn("<script>alert('x')</script>", document)
        self.assertIn("&lt;script&gt;alert(&#x27;x&#x27;)&lt;/script&gt;", document)
        self.assertNotIn('<img src=x onerror="alert(1)">', document)

    def test_blocked_run_renders_without_message_or_api_event(self) -> None:
        run_log = copy.deepcopy(self.run_log)
        run_log["committee_decision"]["winner_candidate_id"] = None
        run_log["api_event"] = None

        document = render_replay(run_log)

        self.assertIn("No candidate passed the evaluator gate", document)
        self.assertIn("No simulated event was produced", document)


if __name__ == "__main__":
    unittest.main()
