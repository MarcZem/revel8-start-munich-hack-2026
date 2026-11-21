from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_core.challenge_api import FakeChallengeAPI
from agent_core.evaluator import EvaluatorGate
from agent_core.fixtures import synthetic_graph
from agent_core.model_committee import StubAdvisor, StubWriter, default_stub_committee
from agent_core.orchestrator import Orchestrator
from agent_core.schema import Channel, MessageCandidate, Objective


class AgentCoreTests(unittest.TestCase):
    def test_end_to_end_run_sends_only_to_fake_api(self) -> None:
        api = FakeChallengeAPI()
        log = Orchestrator(api=api).run("lena_kraus")

        self.assertEqual(log.committee_decision.winner_candidate_id, "msg_001_safe")
        self.assertEqual(log.api_event.event_type, "fake_link_opened")
        self.assertEqual(len(api.sent_candidates), 1)
        self.assertEqual(api.sent_candidates[0].landing_page_url, "https://review-brief.example/revel8-sim")

    def test_context_router_excludes_low_confidence_and_irrelevant_facts(self) -> None:
        graph = synthetic_graph("lena_kraus")
        angle = StubAdvisor().propose_angles(graph, Objective.ACTION)[0]
        context = __import__("agent_core.context_router", fromlist=["ContextRouter"]).ContextRouter().route(
            graph,
            Objective.ACTION,
            angle,
        )

        self.assertIn("ev_lena_old_job_low_conf", context.excluded_evidence_ids)
        self.assertNotIn("ev_lena_old_job_low_conf", context.allowed_evidence_ids)
        self.assertGreaterEqual(len(context.loaded_paths), 1)

    def test_evaluator_blocks_prompt_injection_real_domain_and_secret_request(self) -> None:
        graph = synthetic_graph("lena_kraus")
        context, decision = default_stub_committee().run(graph, Objective.ACTION)
        rule_break = next(candidate for candidate in decision.candidates if candidate.id == "msg_003_rule_break")
        score = next(score for score in decision.critic_scores if score.candidate_id == rule_break.id)

        verdict = EvaluatorGate().evaluate(rule_break, context, score)

        self.assertEqual(verdict.decision, "block")
        self.assertIn("prompt_injection_attempt", verdict.blocked_reasons)
        self.assertIn("real_domain_misuse", verdict.blocked_reasons)
        self.assertIn("secret_or_credential_request", verdict.blocked_reasons)

    def test_evaluator_blocks_unrouted_evidence(self) -> None:
        graph = synthetic_graph("lena_kraus")
        context, decision = default_stub_committee().run(graph, Objective.ACTION)
        safe = next(candidate for candidate in decision.candidates if candidate.id == "msg_001_safe")
        score = next(score for score in decision.critic_scores if score.candidate_id == safe.id)
        bad = MessageCandidate(
            id="msg_bad_evidence",
            writer_model=safe.writer_model,
            advisor_model=safe.advisor_model,
            channel=Channel.FAKE_EMAIL,
            sender_type=safe.sender_type,
            objective=safe.objective,
            angle_id=safe.angle_id,
            subject=safe.subject,
            body=safe.body,
            landing_page_url=safe.landing_page_url,
            landing_page_summary=safe.landing_page_summary,
            used_evidence_ids=("ev_lena_old_job_low_conf",),
        )

        verdict = EvaluatorGate().evaluate(bad, context, score)

        self.assertEqual(verdict.decision, "block")
        self.assertIn("uses_unrouted_or_unsupported_evidence", verdict.blocked_reasons)

    def test_run_and_save_writes_json_log(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            out = Path(tmp_dir) / "run.json"
            log = Orchestrator().run_and_save("max_rieder", out)

            self.assertTrue(out.exists())
            self.assertIn("msg_001_safe", out.read_text(encoding="utf-8"))
            self.assertEqual(log.api_event.event_type, "fake_document_opened")

    def test_writer_uses_only_routed_evidence_ids(self) -> None:
        graph = synthetic_graph("sara_neumann")
        context, decision = default_stub_committee().run(graph, Objective.ACTION)
        safe = next(candidate for candidate in decision.candidates if candidate.id == "msg_001_safe")

        self.assertTrue(set(safe.used_evidence_ids).issubset(context.allowed_evidence_ids))


if __name__ == "__main__":
    unittest.main()
