"""The ACTION landing page end-to-end: run_breach(action_page=True) must register the payment-
confirmation form (not the sign-in page) and classify a submit of it as an ACTION incident — the
form path through which 'the target changed a payment detail for us' fires in a live run."""

from __future__ import annotations

import tempfile
import types
import unittest

from agent_core import angle_reasoner, breach, compose, context_broker, lever_critic, llm
from agent_core.angle_reasoner import Hook

_WRITER = ("FROM_NAME: Lena Fischer\nFROM_ADDRESS: lena@supplier-ops.de\n"
           "SUBJECT: Invoice correction\nBODY:\nQuick correction on the pending invoice — please "
           "confirm the updated details.\nBest, Lena")


class _FakeAPI:
    """Stands in for the Target API: the target submits the payment form on the 2nd touch."""

    def __init__(self) -> None:
        self.registered: list[dict] = []
        self.calls = 0

    def create_session(self, scenario: str = "x") -> dict:
        return {"session_id": "s1"}

    def register_page(self, sid: str, **page) -> dict:
        self.registered.append(page)
        return {"page_id": "p1"}

    def send_message(self, sid: str, **msg) -> dict:
        self.calls += 1
        if self.calls == 1:  # cold first touch: a reply, no link yet
            return {"touches_used": 1, "events": [{"type": "reply", "body": "Which invoice?"}]}
        return {"touches_used": self.calls, "events": [{  # 2nd touch: they submit the changed IBAN
            "type": "page.submitted", "page_id": "p1", "fields": ["invoice_reference", "new_iban"],
            "values": {"invoice_reference": "INV-2026-4471", "new_iban": "DE89 3704 0044 0532 0130 00"},
        }]}

    def end_session(self, sid: str) -> dict:
        return {"status": "ended"}


class BreachActionPageTest(unittest.TestCase):
    def setUp(self) -> None:
        self._orig = (angle_reasoner.rank_hooks, context_broker.select_evidence,
                      lever_critic.critique_draft, llm.chat)
        angle_reasoner.rank_hooks = lambda findings, max_hooks=5: [
            Hook("invoice correction", "pending invoice", ("f1",), "email",
                 "confirm the updated payment details")]
        context_broker.select_evidence = lambda findings, hook, **k: []
        lever_critic.critique_draft = lambda text, *a, **k: types.SimpleNamespace(
            needs_rewrite=False, note="", scores={}, blatant=False, lever_present=True)
        llm.chat = lambda *a, **k: _WRITER  # writer + (touch-1) judge both get a non-JSON reply

    def tearDown(self) -> None:
        (angle_reasoner.rank_hooks, context_broker.select_evidence,
         lever_critic.critique_draft, llm.chat) = self._orig

    def test_action_page_registered_and_submit_is_action(self) -> None:
        api = _FakeAPI()
        with tempfile.TemporaryDirectory() as d:
            log = breach.run_breach("acme", "Acme AP", channel="email", max_touches=3,
                                    action_page=True, api=api, findings=[], own_domains=(),
                                    out_dir=d, critique=False)
        # the ACTION form was registered, not the sign-in page
        self.assertEqual(api.registered[0]["fields"], ["invoice_reference", "new_iban"])
        self.assertEqual(api.registered[0]["url"], "https://supplier-portal.app/confirm")
        self.assertNotIn("password", api.registered[0]["fields"])
        # submitting the changed payment detail is classified as an ACTION incident
        self.assertTrue(log["incident"])
        self.assertEqual(log["incident_type"], "action")
        self.assertEqual(log["touches_to_incident"], 2)

    def test_default_still_registers_signin(self) -> None:
        api = _FakeAPI()
        with tempfile.TemporaryDirectory() as d:
            breach.run_breach("acme", "Acme AP", channel="email", max_touches=1,
                              api=api, findings=[], own_domains=(), out_dir=d, critique=False)
        self.assertEqual(api.registered[0]["fields"], ["email", "password"])


class ActionPageHtmlTest(unittest.TestCase):
    def test_has_action_fields_and_no_password(self) -> None:
        html = compose.build_action_page_html("Supplier Payments", "Confirm the updated payment details")
        self.assertIn('name="new_iban"', html)
        self.assertIn('name="invoice_reference"', html)
        self.assertNotIn('type="password"', html)


if __name__ == "__main__":
    unittest.main()
