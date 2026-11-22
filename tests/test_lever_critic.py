"""Deterministic evals for the lever critic + its breach-loop wiring (no network)."""

from __future__ import annotations

import os
import unittest

from agent_core import breach, lever_critic, llm
from agent_core.angle_reasoner import Hook

_CLEAN = '{"authority":0.2,"social_proof":0.1,"liking":0.5,"commitment_reciprocity":0.1,"urgency":0.1,"obviousness":0.2}'
_BLATANT = '{"authority":0.3,"social_proof":0.1,"liking":0.1,"commitment_reciprocity":0.1,"urgency":0.9,"obviousness":0.95}'


class CritiqueTest(unittest.TestCase):
    def setUp(self):
        self._orig = llm.chat

    def tearDown(self):
        llm.chat = self._orig
        os.environ.pop("LEVER_CRITIC", None)

    def test_blatant_draft_needs_rewrite(self):
        llm.chat = lambda *a, **k: _BLATANT
        c = lever_critic.critique_draft("sign in NOW or lose access")
        self.assertTrue(c.blatant)
        self.assertTrue(c.needs_rewrite)

    def test_clean_draft_ok(self):
        llm.chat = lambda *a, **k: _CLEAN
        c = lever_critic.critique_draft("Hi, loved your talk — one quick question.")
        self.assertTrue(c.ok)
        self.assertFalse(c.needs_rewrite)

    def test_missing_intended_lever_flagged(self):
        llm.chat = lambda *a, **k: _CLEAN  # authority = 0.2 < 0.40
        c = lever_critic.critique_draft("hey", intended_lever="authority")
        self.assertFalse(c.lever_present)
        self.assertTrue(c.needs_rewrite)
        self.assertIn("authority", c.note)

    def test_intended_lever_alias_present(self):
        # "Reciprocity" -> commitment_reciprocity (0.1 here) stays absent...
        llm.chat = lambda *a, **k: _CLEAN
        self.assertFalse(lever_critic.critique_draft("x", intended_lever="Reciprocity").lever_present)
        # ...and a strong commitment score counts as present
        llm.chat = lambda *a, **k: '{"authority":0,"social_proof":0,"liking":0,"commitment_reciprocity":0.8,"urgency":0,"obviousness":0.2}'
        self.assertTrue(lever_critic.critique_draft("x", intended_lever="Reciprocity").lever_present)

    def test_scores_clamped_out_of_range(self):
        llm.chat = lambda *a, **k: '{"authority":-1,"social_proof":9,"liking":0,"commitment_reciprocity":0,"urgency":0,"obviousness":5}'
        c = lever_critic.critique_draft("x")
        self.assertEqual(c.scores["authority"], 0.0)
        self.assertEqual(c.scores["social_proof"], 1.0)
        self.assertTrue(c.blatant)  # obviousness clamped 5 -> 1.0

    def test_fail_open_on_llm_error(self):
        def boom(*a, **k):
            raise llm.LLMError("endpoint down")
        llm.chat = boom
        c = lever_critic.critique_draft("x")
        self.assertTrue(c.ok)  # never blocks a send
        self.assertEqual(c.scores, {})

    def test_fail_open_on_junk(self):
        llm.chat = lambda *a, **k: "I think this message is fine, no JSON here."
        self.assertTrue(lever_critic.critique_draft("x").ok)

    def test_disabled_does_not_call_model(self):
        def boom(*a, **k):
            raise AssertionError("llm.chat must not be called when disabled")
        llm.chat = boom
        self.assertTrue(lever_critic.critique_draft("x", critique=False).ok)
        os.environ["LEVER_CRITIC"] = "0"
        self.assertTrue(lever_critic.critique_draft("x").ok)


class BreachWiringTest(unittest.TestCase):
    """react_compose self-checks the draft and rewrites once when the critic flags it."""

    def setUp(self):
        self._orig = llm.chat

    def tearDown(self):
        llm.chat = self._orig

    def test_blatant_draft_is_rewritten_once(self):
        def fake(prompt, *, system=None, **k):
            if system and "persuasion analyst" in system:   # the critic call
                return _BLATANT
            if "SELF-CHECK failed" in prompt:               # the rewrite call
                return "FROM_NAME: Lena\nFROM_ADDRESS: lena@grid-events.de\nBODY:\nSubtle human note about your talk."
            return "FROM_NAME: Lena\nFROM_ADDRESS: lena@grid-events.de\nBODY:\nURGENT!! sign in NOW or lose access!!!"
        llm.chat = fake
        hook = Hook("renewables", "won solar hackathon", ("f1",), "sms", "grid follow-up")
        payload = breach.react_compose("Julius Muth", hook, [], [], None, None, None, "sms", "2026-11-22")
        self.assertEqual(payload["body"], "Subtle human note about your talk.")
        self.assertTrue(payload["_critique"]["blatant"])
        self.assertTrue(payload["_critique"]["rewritten"])

    def test_clean_draft_sent_as_is(self):
        def fake(prompt, *, system=None, **k):
            if system and "persuasion analyst" in system:
                return _CLEAN
            return "FROM_NAME: Lena\nFROM_ADDRESS: lena@grid-events.de\nBODY:\nHi Julius, loved your solar talk — one question."
        llm.chat = fake
        hook = Hook("renewables", "won solar hackathon", ("f1",), "sms", "grid follow-up")
        payload = breach.react_compose("Julius Muth", hook, [], [], None, None, None, "sms", "2026-11-22")
        self.assertIn("loved your solar talk", payload["body"])
        self.assertFalse(payload["_critique"]["rewritten"])


if __name__ == "__main__":
    unittest.main()
