from __future__ import annotations

import unittest

from scripts.run_context_broker_evals import run_evaluations


class ContextBrokerEvalTests(unittest.TestCase):
    def test_synthetic_offline_context_broker_eval_suite_passes(self) -> None:
        report = run_evaluations()

        self.assertTrue(report["passed"], report["checks"])
        self.assertEqual(report["mode"], "offline_synthetic_only")
        self.assertGreaterEqual(report["summary"]["total"], 40)
        self.assertEqual(report["summary"]["failed"], 0)
        self.assertEqual([run["token_budget"] for run in report["budget_runs"]], [500, 900, 4096])

    def test_eval_suite_never_selects_sensitive_or_conflicted_facts(self) -> None:
        report = run_evaluations()

        for budget_run in report["budget_runs"]:
            self.assertNotIn("eval_sensitive_private", budget_run["selected_evidence_ids"])
            self.assertNotIn("eval_conflict_a", budget_run["selected_evidence_ids"])
            self.assertNotIn("eval_conflict_b", budget_run["selected_evidence_ids"])


if __name__ == "__main__":
    unittest.main()
