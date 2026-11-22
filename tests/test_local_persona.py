"""Offline checks for the local persona harness (mocked LLM, no network)."""

import unittest

from agent_core import llm
from agent_core.local_persona import LocalPersonaAPI, synthetic_findings


class LocalPersonaTest(unittest.TestCase):
    def setUp(self):
        self._orig = llm.chat

    def tearDown(self):
        llm.chat = self._orig

    def test_submits_page_with_secret(self):
        llm.chat = lambda *a, **k: ('{"reply":"ok done","opened_link":true,"submitted_page":true,'
                                     '"entered_password":true,"opened_file":false,"disclosed":false,'
                                     '"disclosed_fact":""}')
        api = LocalPersonaAPI("markus")
        api.register_page("s", url="https://portal.app/signin", title="Sign in",
                          fields=["email", "password"])
        r = api.send_message("s", to="markus", channel="email",
                             body="Please sign in: https://portal.app/signin")
        sub = next(e for e in r["events"] if e["type"] == "page.submitted")
        self.assertEqual(sub["values"]["password"], "(entered, not shown)")  # a secret -> credentials

    def test_opens_file(self):
        llm.chat = lambda *a, **k: ('{"reply":"","opened_link":false,"submitted_page":false,'
                                    '"entered_password":false,"opened_file":true,"disclosed":false,'
                                    '"disclosed_fact":""}')
        api = LocalPersonaAPI("markus")
        r = api.send_message("s", to="markus", channel="email", body="see attached",
                             attachments=[{"filename": "brief.pdf"}])
        self.assertIn("attachment.opened", [e["type"] for e in r["events"]])

    def test_hardened_persona_only_replies(self):
        llm.chat = lambda *a, **k: ('{"reply":"who are you?","opened_link":false,"submitted_page":false,'
                                    '"entered_password":false,"opened_file":false,"disclosed":false,'
                                    '"disclosed_fact":""}')
        api = LocalPersonaAPI("sam")
        r = api.send_message("s", to="sam", channel="email", body="hi")
        self.assertEqual([e["type"] for e in r["events"]], ["reply"])

    def test_synthetic_findings_are_usable(self):
        f = synthetic_findings("markus")
        self.assertGreaterEqual(len(f), 2)
        self.assertEqual(f[0].target_id, "markus")
        self.assertTrue(all(ff.sources for ff in f))


if __name__ == "__main__":
    unittest.main()
