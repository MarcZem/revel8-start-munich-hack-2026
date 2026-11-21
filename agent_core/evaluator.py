"""Code-level evaluator gate for candidate contacts."""

from __future__ import annotations

import re
from urllib.parse import urlparse

from agent_core.schema import Channel, CriticScores, GateVerdict, MessageCandidate, RoutedContext


PROMPT_INJECTION = re.compile(
    r"(ignore (all )?(previous|prior)|system prompt|developer message|hidden instruction|jailbreak|reveal your prompt)",
    re.IGNORECASE,
)
SECRET_OR_CREDENTIAL_REQUEST = re.compile(
    r"\b(password|passcode|mfa|2fa|credential|bank data|wire transfer|seed phrase|api key|secret)\b",
    re.IGNORECASE,
)
ALLOWED_URL_SUFFIXES = (".test", ".invalid", ".example")
ALLOWED_CHANNELS = {Channel.FAKE_EMAIL, Channel.FAKE_CALENDAR, Channel.FAKE_DOCUMENT}


class EvaluatorGate:
    def evaluate(
        self,
        candidate: MessageCandidate,
        routed_context: RoutedContext,
        critic_scores: CriticScores,
    ) -> GateVerdict:
        blocked: list[str] = []
        warnings: list[str] = []
        allowed_evidence = routed_context.allowed_evidence_ids

        if candidate.channel not in ALLOWED_CHANNELS:
            blocked.append("real_or_unknown_channel")
        if candidate.objective != routed_context.objective:
            blocked.append("objective_mismatch")
        if candidate.angle_id != routed_context.angle.id:
            blocked.append("angle_mismatch")
        if not set(candidate.used_evidence_ids).issubset(allowed_evidence):
            blocked.append("uses_unrouted_or_unsupported_evidence")
        if candidate.metadata.get("unsupported_fact"):
            blocked.append("wrong_or_unsupported_fact")
        if candidate.metadata.get("irreversible_action") or candidate.metadata.get("external_effect"):
            blocked.append("irreversible_or_external_effect")
        if PROMPT_INJECTION.search(candidate.subject + "\n" + candidate.body):
            blocked.append("prompt_injection_attempt")
        if SECRET_OR_CREDENTIAL_REQUEST.search(candidate.body):
            blocked.append("secret_or_credential_request")
        if not _uses_fake_domain(candidate.landing_page_url):
            blocked.append("real_domain_misuse")
        if candidate.channel == Channel.FAKE_EMAIL and not candidate.subject.strip():
            blocked.append("channel_fit_missing_subject")
        if critic_scores.scores["disqualification_risk"] > 2:
            blocked.append("high_disqualification_risk")
        if critic_scores.scores["rule_compliance"] < 3:
            blocked.append("critic_rule_compliance_too_low")
        if critic_scores.scores["evidence_fidelity"] < 3:
            blocked.append("critic_evidence_fidelity_too_low")

        body_lower = candidate.body.lower()
        if not any(path.summary.split()[0].lower() in body_lower for path in routed_context.loaded_paths):
            warnings.append("message_may_be_generic")
        if len(candidate.body.split()) < 45:
            warnings.append("message_short_or_generic")

        decision = "block" if blocked else "send"
        return GateVerdict(
            candidate_id=candidate.id,
            decision=decision,
            blocked_reasons=tuple(blocked),
            warnings=tuple(warnings),
            score=critic_scores.utility_score,
        )


def _uses_fake_domain(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in {"https", "http"}:
        return False
    host = parsed.hostname or ""
    return host.endswith(ALLOWED_URL_SUFFIXES)
