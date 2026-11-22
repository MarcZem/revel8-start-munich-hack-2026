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

    def test_empty_writer_output_is_refused(self):
        # Empty body + link was sent live and read as a blank phishing ping; must never send.
        llm.chat = lambda *a, **k: "FROM_NAME: IT Desk\nFROM_ADDRESS: it@x.de\nSUBJECT: Hi\nBODY:"
        with self.assertRaises(ValueError):
            compose.compose_message("credentials", _hook(), _ev(), "Julius Muth",
                                    link_url="https://files-review.app/signin")

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


class LinkInjectionTest(unittest.TestCase):
    def setUp(self):
        self._orig = llm.chat

    def tearDown(self):
        llm.chat = self._orig

    def test_cta_href_matches_url_exactly(self):
        # The persona only reacts to a link that matches the registered page URL exactly.
        url = "https://revel8-id.com/signin"
        html = compose.render_email_html("Lena", "Please review access.", url, "revel8 ID")
        self.assertIn(f'href="{url}"', html)
        self.assertIn(">revel8 ID</a>", html)

    def test_compose_message_injects_link(self):
        llm.chat = lambda *a, **k: (
            "FROM_NAME: IT Desk\nFROM_ADDRESS: it@revel8-id.com\n"
            "SUBJECT: Verify access\nBODY:\nHi Julius, please confirm your access."
        )
        url = "https://revel8-id.com/signin"
        msg = compose.compose_message("credentials", _hook(), _ev(), "Julius Muth",
                                      link_url=url, link_brand="revel8 ID")
        self.assertIn(f'href="{url}"', msg["body"])
        self.assertNotIn("<script", msg["body"].lower())


class ChannelTest(unittest.TestCase):
    def setUp(self):
        self._orig = llm.chat
        llm.chat = lambda *a, **k: (
            "FROM_NAME: Lena\nFROM_ADDRESS: lena@x.de\nSUBJECT: Hi\nBODY:\nQuick question here."
        )

    def tearDown(self):
        llm.chat = self._orig

    def test_email_is_html_with_subject(self):
        msg = compose.compose_message("disclosure", _hook(), _ev(), "Julius", channel="email")
        self.assertEqual(msg["channel"], "email")
        self.assertIn("subject", msg)
        self.assertTrue(msg["body"].startswith("<!doctype html>"))

    def test_sms_is_plain_and_subjectless(self):
        msg = compose.compose_message("disclosure", _hook(), _ev(), "Julius", channel="sms")
        self.assertEqual(msg["channel"], "sms")
        self.assertNotIn("subject", msg)
        self.assertNotIn("<html", msg["body"].lower())

    def test_sms_link_is_plain_line(self):
        url = "https://files-review.app/signin"
        msg = compose.compose_message("credentials", _hook(), _ev(), "Julius",
                                      channel="whatsapp", link_url=url, link_brand="Files Review")
        self.assertIn(url, msg["body"])
        self.assertNotIn("href=", msg["body"])


if __name__ == "__main__":
    unittest.main()
