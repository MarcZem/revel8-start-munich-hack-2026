from __future__ import annotations

import unittest

from evals.runner import run_evals


class SyntheticEvalHarnessTests(unittest.TestCase):
    def test_all_declared_cases_pass_and_feedback_is_minimized(self) -> None:
        results, feedback = run_evals()

        self.assertEqual(len(results), 12)
        self.assertTrue(all(result["status"] == "passed" for result in results))
        self.assertEqual(len(feedback), 3)
        self.assertTrue(all(row["source"] == "synthetic_local_eval" for row in feedback))
        self.assertTrue(all(row["message_text_exported"] is False for row in feedback))


if __name__ == "__main__":
    unittest.main()
