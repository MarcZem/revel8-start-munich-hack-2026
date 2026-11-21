"""Deterministic evals for the craft/compose module (#12, no network)."""

from __future__ import annotations

import unittest

from agent_core import compose, llm
from agent_core.angle_reasoner import Hook
from agent_core.schema import FindingSource, ResearchFinding


def _hook():
    return Hook("renewables", "won solar hackathon", ("f1",), "email", "grid follow-up")


def _ev():
    return [ResearchFinding("f1", "t", "project", "Won a solar hackathon", "belastbar",
                            "2026-11-21", (FindingSource("https://a.com/1", "won"),))]


class ComposeMessageTest(unittest.TestCase):
    def setUp(self):
        self._orig = llm.chat

    def tearDown(self):
        llm.chat = self._orig

    def test_returns_self_contained_html(self):
        llm.chat = lambda *a, **k: (
            "FROM_NAME: Lena Fischer\nFROM_ADDRESS: lena@grid-briefing.de\n"
            "SUBJECT: Your grid talk\nBODY:\nHi Julius,\n\nLoved the solar win.\n\nBest, Lena"
        )
        msg = compose.compose_message("disclosure", _hook(), _ev(), "Julius Muth")
        self.assertEqual(msg["channel"], "email")
        self.assertEqual(msg["from"]["address"], "lena@grid-briefing.de")
        self.assertEqual(msg["subject"], "Your grid talk")
        self.assertTrue(msg["body"].startswith("<!doctype html>"))
        self.assertIn("Loved the solar win.", msg["body"])
        self.assertNotIn("<script", msg["body"].lower())  # no scripts (craft rule)

    def test_html_escapes_body(self):
        html = compose.render_email_html("Lena", "a <b> & c")
        self.assertIn("&lt;b&gt;", html)
        self.assertIn("&amp;", html)


class LandingPageTest(unittest.TestCase):
    def test_signin_page_has_password_field(self):
        html = compose.build_signin_page_html("Company Portal", "Sign in to continue")
        self.assertIn('name="password"', html)
        self.assertIn('name="email"', html)
        self.assertNotIn("<script", html.lower())


if __name__ == "__main__":
    unittest.main()
