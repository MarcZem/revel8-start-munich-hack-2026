"""Live revel8 Target API client.

Stdlib only (no third-party deps), to match this repo's dependency-free core.
Spec: docs/target-api.md. The fake, offline simulator lives in challenge_api.py;
this talks to the real hosted targets and spends touches.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
import uuid
from typing import Any

DEFAULT_BASE = "https://target-api.apps.01.cf.eu01.stackit.cloud/v1"
_RETRYABLE = {429, 502, 503, 504}


class TargetAPIError(RuntimeError):
    def __init__(self, status: int, body: str) -> None:
        super().__init__(f"HTTP {status}: {body[:500]}")
        self.status = status
        self.body = body


def load_env_file(path: str = ".env.local") -> None:
    """Load KEY=VALUE lines into os.environ (does not overwrite existing vars)."""
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())


class TargetAPI:
    def __init__(self, base: str | None = None, key: str | None = None, timeout: int = 120) -> None:
        self.base = (base or os.environ.get("TARGET_API_BASE") or DEFAULT_BASE).rstrip("/")
        self.key = key or os.environ.get("TARGET_API_KEY")
        if not self.key:
            raise ValueError("TARGET_API_KEY not set (export it or put it in .env.local)")
        self.timeout = timeout

    # --- transport ---------------------------------------------------------

    def _request(
        self,
        method: str,
        path: str,
        body: Any = None,
        *,
        idempotency_key: str | None = None,
        retries: int = 3,
    ) -> Any:
        url = f"{self.base}{path}"
        data = json.dumps(body).encode() if body is not None else None
        headers = {"Authorization": f"Bearer {self.key}"}
        if data is not None:
            headers["Content-Type"] = "application/json"
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        last = ""
        for attempt in range(retries):
            req = urllib.request.Request(url, data=data, method=method, headers=headers)
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    raw = resp.read().decode()
                    return json.loads(raw) if raw else {}
            except urllib.error.HTTPError as exc:
                last = exc.read().decode()
                if exc.code in _RETRYABLE and attempt < retries - 1:
                    time.sleep(2**attempt + 1)
                    continue
                raise TargetAPIError(exc.code, last) from None
        raise TargetAPIError(0, last or "retries exhausted")

    # --- scenarios & sessions ---------------------------------------------

    def scenarios(self) -> list[dict]:
        return self._request("GET", "/scenarios")

    def channels(self) -> Any:
        return self._request("GET", "/channels")

    def create_session(self, scenario_id: str = "practice") -> dict:
        return self._request("POST", "/sessions", {"scenario_id": scenario_id})

    def get_session(self, sid: str) -> dict:
        return self._request("GET", f"/sessions/{sid}")

    def list_sessions(self) -> Any:
        return self._request("GET", "/sessions")

    def session_events(self, sid: str) -> dict:
        return self._request("GET", f"/sessions/{sid}/events")

    def end_session(self, sid: str) -> Any:
        return self._request("POST", f"/sessions/{sid}/end")

    # --- contact -----------------------------------------------------------

    def send_message(self, sid: str, idempotency_key: str | None = None, **message: Any) -> dict:
        """message carries: to, channel, from, subject, body, attachments, sent_at."""
        return self._request(
            "POST",
            f"/sessions/{sid}/messages",
            message,
            idempotency_key=idempotency_key or str(uuid.uuid4()),
        )

    def register_page(self, sid: str, **page: Any) -> dict:
        """page carries: url, title, html (or text/images), fields."""
        return self._request("POST", f"/sessions/{sid}/pages", page)

    def upload_asset(self, file_path: str) -> dict:
        """Multipart upload of an image/PDF. Returns {asset_id, type, size}."""
        with open(file_path, "rb") as fh:
            payload = fh.read()
        boundary = f"----revel8{uuid.uuid4().hex}"
        name = os.path.basename(file_path)
        body = b"".join(
            [
                f"--{boundary}\r\n".encode(),
                f'Content-Disposition: form-data; name="file"; filename="{name}"\r\n'.encode(),
                b"Content-Type: application/octet-stream\r\n\r\n",
                payload,
                f"\r\n--{boundary}--\r\n".encode(),
            ]
        )
        req = urllib.request.Request(
            f"{self.base}/assets",
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {self.key}",
                "Content-Type": f"multipart/form-data; boundary={boundary}",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as exc:
            raise TargetAPIError(exc.code, exc.read().decode()) from None

    # --- conversations -----------------------------------------------------

    def start_conversation(self, sid: str, idempotency_key: str | None = None, **conv: Any) -> dict:
        """conv carries: to, channel, from, sent_at."""
        return self._request(
            "POST",
            f"/sessions/{sid}/conversations",
            conv,
            idempotency_key=idempotency_key or str(uuid.uuid4()),
        )

    def say(self, cid: str, text: str, idempotency_key: str | None = None, **extra: Any) -> dict:
        return self._request(
            "POST",
            f"/conversations/{cid}/turns",
            {"say": text, **extra},
            idempotency_key=idempotency_key or str(uuid.uuid4()),
        )

    def end_conversation(self, cid: str) -> Any:
        return self._request("POST", f"/conversations/{cid}/end")
