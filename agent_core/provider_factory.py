"""Load an injected model committee, falling back to safe deterministic stubs."""

from __future__ import annotations

import importlib
import os

from agent_core.model_committee import ModelCommittee, default_stub_committee


def provider_label() -> str:
    return "configured model committee" if os.environ.get("MODEL_COMMITTEE_FACTORY", "").strip() else "deterministic demo stubs"


def committee_from_environment() -> tuple[ModelCommittee, str]:
    """Return the configured committee and a display-safe provider label.

    AMD connection details are not assumed here. Once the hosted model's API
    contract is known, its adapter can be implemented in-repo and selected with
    ``MODEL_COMMITTEE_FACTORY=package.module:factory``.
    """
    factory_path = os.environ.get("MODEL_COMMITTEE_FACTORY", "").strip()
    if not factory_path:
        return default_stub_committee(), "deterministic demo stubs"
    module_name, separator, factory_name = factory_path.partition(":")
    if not separator or not module_name or not factory_name:
        raise ValueError("MODEL_COMMITTEE_FACTORY must use package.module:factory format.")
    try:
        factory = getattr(importlib.import_module(module_name), factory_name)
        committee = factory()
    except Exception:
        # Never include provider exceptions because they may contain endpoint
        # details or credential material.
        raise ValueError("The configured model committee could not be loaded.") from None
    if not _is_committee(committee):
        raise ValueError("The configured factory must return Advisor, Writer, and Critic protocol implementations.")
    return committee, "configured model committee"


def _is_committee(value: object) -> bool:
    return all(
        callable(getattr(getattr(value, role, None), method, None))
        for role, method in (
            ("advisor", "propose_angles"),
            ("writer", "draft_candidates"),
            ("critic", "score"),
            ("gate", "evaluate"),
        )
    )
