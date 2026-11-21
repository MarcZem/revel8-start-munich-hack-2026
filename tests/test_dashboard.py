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

    def test_replay_shows_the_exact_writer_packet_and_exclusion_audit(self) -> None:
        run_log = copy.deepcopy(self.run_log)
        routed = run_log["routed_context"]
        evidence_id = "ev_lena_supplier"
        evidence = run_log["graph"]["evidence"][evidence_id]
        routed["context_packet"] = {
            "target_name": "Lena Kraus",
            "as_of": "2026-11-21T00:00:00Z",
            "token_budget": 400,
            "token_count": 240,
            "facts": [{
                "evidence_id": evidence_id,
                "description": evidence["description"],
                "source": evidence["source"],
                "observed_at": evidence["observed_at"],
                "confidence": evidence["confidence"],
                "source_reliability": 0.8,
                "uncertainty_note": "Treat as uncertain; avoid stating as a confirmed current fact.",
            }],
        }
        routed["ranked_evidence"] = [
            {"evidence_id": evidence_id, "score": 0.72, "eligible": True},
            {"evidence_id": "ev_lena_old_job_low_conf", "score": 0.11, "eligible": False},
        ]
        routed["excluded_reasons"]["ev_lena_old_job_low_conf"] = "unsafe_or_private"

        document = render_replay(run_log)

        self.assertIn("240 / 400 tokens", document)
        self.assertIn("Selected · Score 0.72", document)
        self.assertIn("Excluded · Score 0.11 · unsafe_or_private", document)
        self.assertIn("synthetic_public_procurement_panel", document)
        self.assertIn("Treat as uncertain", document)


if __name__ == "__main__":
    unittest.main()
