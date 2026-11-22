"""Offline checks for the run-record contract + campaign aggregation (no network)."""

import unittest

from agent_core.run_record import CampaignResult, RunRecord


def _held_log():
    """A breach-style log that engaged then hit the verifiability gate and stopped (no incident)."""
    return {
        "session_id": "s_abc12345", "target": "julius", "target_name": "Julius Muth",
        "scenario": "practice", "objective": "breach", "channel": "email",
        "hook": {"topic": "founder panel", "evidence_ids": ["f1", "f2"]},
        "hooks_considered": [
            {"topic": "founder panel", "evidence_ids": ["f1", "f2"]},
            {"topic": "podcast threat-modeling", "evidence_ids": ["f3"]},
        ],
        "contacts": [
            {"payload": {"channel": "email", "from": {"name": "Lena"}, "subject": "Panel",
                         "body": "Hi Julius, quick one about the panel."},
             "touches_used": 1, "events": [{"type": "reply", "body": "Who invited you?"}],
             "decision": {"action": "continue", "reason": "twin asks who invited you — answer the gate"},
             "state_after": {"silent_streak": 0, "gate_seen": "asks who invited you"}},
            {"payload": {"channel": "email", "from": {"name": "Lena"}, "subject": "Panel",
                         "body": "I'm with MUC Events; here are the details."},
             "touches_used": 2, "events": [],
             "decision": {"action": "switch", "reason": "silence — change angle"},
             "state_after": {"silent_streak": 1, "gate_seen": None}},
        ],
        "incident": False, "incident_type": None, "captured": None, "touches_to_incident": None,
        "stop_reason": "reached the 8-touch budget without an incident",
    }


def _incident_log():
    return {
        "session_id": "s_def67890", "target": "tom", "objective": "breach", "channel": "email",
        "hook": {"topic": "doc review", "evidence_ids": ["g1"]}, "hooks_considered": [],
        "contacts": [
            {"payload": {"channel": "email", "from": {}, "body": "first"}, "touches_used": 1, "events": []},
            {"payload": {"channel": "email", "from": {}, "body": "sign in please"},
             "touches_used": 2,
             "events": [{"type": "page.submitted", "fields": ["email", "password"],
                         "values": {"password": "(entered, not shown)"}}],
             "incident": {"type": "credentials", "captured": {"fields": ["email", "password"]}}},
        ],
        "incident": True, "incident_type": "credentials",
        "captured": {"fields": ["email", "password"]}, "touches_to_incident": 2,
    }


class RunRecordTest(unittest.TestCase):
    def test_held_run_normalises(self):
        r = RunRecord.from_log(_held_log())
        self.assertEqual(r.target_id, "julius")
        self.assertEqual(r.target_name, "Julius Muth")
        self.assertFalse(r.incident)
        self.assertEqual(r.contacts_used, 2)
        self.assertTrue(r.reached_reply)
        self.assertEqual(len(r.hooks_considered), 2)  # alternatives preserved
        self.assertEqual(r.touches[0].decision.reason[:4], "twin")
        self.assertEqual(r.touches[0].state_after["gate_seen"], "asks who invited you")
        self.assertEqual(r.touches[1].decision.action, "switch")
        self.assertIn("budget", r.stop_reason)
        self.assertEqual(r.touches[0].expected_observable[:6], "a secr")  # breach objective mapping

    def test_incident_run_and_speed(self):
        r = RunRecord.from_log(_incident_log())
        self.assertTrue(r.incident)
        self.assertEqual(r.incident_type, "credentials")
        self.assertEqual(r.touches_to_incident, 2)
        self.assertEqual(r.touches[1].incident["type"], "credentials")
        self.assertIn("incident", r.stop_reason)

    def test_inferred_decision_when_not_logged(self):
        log = _incident_log()
        for c in log["contacts"]:
            c.pop("decision", None)
        r = RunRecord.from_log(log)
        self.assertEqual(r.touches[0].decision.action, "switch")   # silence -> switch
        self.assertEqual(r.touches[1].decision.action, "stop")     # incident -> stop

    def test_call_shape_folds_to_one_touch(self):
        call = {"session_id": "s_call1", "target": "robert", "objective": "disclosure",
                "channel": "phone_call",
                "turns": [{"us": "Hi Robert", "them": "Seilbeck."}, {"us": "Quick question", "them": ""}],
                "events": [], "incident": False, "incident_type": None}
        r = RunRecord.from_log(call)
        self.assertEqual(r.contacts_used, 1)           # a whole call is one touch
        self.assertEqual(r.touches[0].channel, "phone_call")
        self.assertIn("Seilbeck", r.touches[0].reply)

    def test_campaign_aggregate_points(self):
        recs = [RunRecord.from_log(_held_log()), RunRecord.from_log(_incident_log()),
                RunRecord.from_log(_held_log())]
        agg = CampaignResult.aggregate(recs)
        self.assertEqual(agg.runs_total, 3)
        self.assertEqual(agg.runs_with_incident, 1)
        self.assertAlmostEqual(agg.incident_points_estimate, round(20 / 3, 2))
        self.assertEqual(agg.speed_median_contacts, 2.0)
        self.assertEqual(len(agg.to_dict()["records"]), 3)


if __name__ == "__main__":
    unittest.main()
