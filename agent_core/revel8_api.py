"""Client for the official Revel8 simulated Target API.

This adapter is opt-in. It never sends anything unless ``send_message`` is
explicitly called by application code. Credentials are read from the environment
and are never included in exception messages.
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from typing import Any


API_BASE_URL = "https://target-api.apps.01.cf.eu01.stackit.cloud/v1"
_SESSION_ID = re.compile(r"^[A-Za-z0-9_-]+$")


class Revel8APIError(RuntimeError):
    """Safe-to-display API error without request headers or credentials."""


class Revel8API:
    """Small stdlib-only client for the Revel8 Target API."""

    def __init__(self, api_key: str | None = None, *, timeout: float = 120) -> None:
        self._api_key = (api_key or os.environ.get("TARGET_API_KEY", "")).strip()
        if not self._api_key:
            raise Revel8APIError("TARGET_API_KEY is missing. Set it in your local environment.")
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        self.timeout = timeout

    def _request(
        self,
        method: str,
        path: str,
        *,
        payload: dict[str, Any] | None = None,
        idempotency_key: str | None = None,
    ) -> Any:
        if not path.startswith("/") or ".." in path:
            raise ValueError("API path must be an absolute path without traversal")
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Accept": "application/json",
        }
        data = None
        if payload is not None:
            headers["Content-Type"] = "application/json"
            data = json.dumps(payload).encode("utf-8")
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        request = urllib.request.Request(API_BASE_URL + path, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                raw = response.read()
        except urllib.error.HTTPError as exc:
            # Do not expose response bodies, which could include reflected input.
            raise Revel8APIError(f"Revel8 API returned HTTP {exc.code} for {method} {path}.") from None
        except (urllib.error.URLError, TimeoutError) as exc:
            reason = "request timed out" if isinstance(exc, TimeoutError) else "network connection failed"
            raise Revel8APIError(f"Revel8 API {reason} for {method} {path}.") from None
        if not raw:
            return None
        try:
            return json.loads(raw)
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise Revel8APIError(f"Revel8 API returned invalid JSON for {method} {path}.") from None

    def list_scenarios(self) -> Any:
        return self._request("GET", "/scenarios")

    def list_channels(self) -> Any:
        return self._request("GET", "/channels")

    def list_sessions(self) -> Any:
        return self._request("GET", "/sessions")

    def create_session(self, scenario_id: str = "practice") -> Any:
        return self._request("POST", "/sessions", payload={"scenario_id": scenario_id})

    def get_session(self, session_id: str) -> Any:
        return self._request("GET", self._session_path(session_id))

    def get_events(self, session_id: str) -> Any:
        return self._request("GET", self._session_path(session_id) + "/events")

    def end_session(self, session_id: str) -> Any:
        return self._request("POST", self._session_path(session_id) + "/end", payload={})

    def send_message(
        self,
        session_id: str,
        *,
        to: str,
        channel: str,
        body: str,
        from_: dict[str, str] | None = None,
        subject: str | None = None,
        attachments: list[Any] | None = None,
        idempotency_key: str,
    ) -> Any:
        """Send one message into a Revel8 simulation; this spends one touch."""
        if not idempotency_key.strip():
            raise ValueError("idempotency_key is required to prevent duplicate touches")
        payload: dict[str, Any] = {"to": to, "channel": channel, "body": body}
        if from_ is not None:
            payload["from"] = from_
        if subject is not None:
            payload["subject"] = subject
        if attachments is not None:
            payload["attachments"] = attachments
        return self._request(
            "POST", self._session_path(session_id) + "/messages",
            payload=payload, idempotency_key=idempotency_key,
        )

    def register_page(self, session_id: str, *, url: str, title: str, text: str,
                      fields: list[str] | None = None) -> Any:
        payload: dict[str, Any] = {"url": url, "title": title, "text": text}
        if fields is not None:
            payload["fields"] = fields
        return self._request("POST", self._session_path(session_id) + "/pages", payload=payload)

    def start_conversation(self, session_id: str, *, to: str, channel: str,
                           opening: str, idempotency_key: str) -> Any:
        if not idempotency_key.strip():
            raise ValueError("idempotency_key is required to prevent duplicate touches")
        return self._request(
            "POST", self._session_path(session_id) + "/conversations",
            payload={"to": to, "channel": channel, "opening": opening},
            idempotency_key=idempotency_key,
        )

    def conversation_turn(self, session_id: str, conversation_id: str, *,
                          body: str, idempotency_key: str) -> Any:
        if not _SESSION_ID.fullmatch(conversation_id):
            raise ValueError("invalid Revel8 conversation id")
        if not idempotency_key.strip():
            raise ValueError("idempotency_key is required to prevent duplicate touches")
        return self._request(
            "POST", self._session_path(session_id) + f"/conversations/{conversation_id}/turns",
            payload={"body": body}, idempotency_key=idempotency_key,
        )

    def end_conversation(self, session_id: str, conversation_id: str) -> Any:
        if not _SESSION_ID.fullmatch(conversation_id):
            raise ValueError("invalid Revel8 conversation id")
        return self._request(
            "POST", self._session_path(session_id) + f"/conversations/{conversation_id}/end",
            payload={},
        )

    @staticmethod
    def _session_path(session_id: str) -> str:
        if not _SESSION_ID.fullmatch(session_id):
            raise ValueError("invalid Revel8 session id")
        return f"/sessions/{session_id}"
