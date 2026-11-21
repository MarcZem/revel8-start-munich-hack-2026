"""Live, one-touch Revel8 practice demo endpoint for Vercel."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler
from typing import Any
from urllib.parse import urlsplit

from agent_core.fixtures import official_practice_graph
from agent_core.live_practice import PRACTICE_TARGETS, Revel8PracticeAdapter
from agent_core.orchestrator import Orchestrator
from agent_core.provider_factory import committee_from_environment, provider_label
from agent_core.revel8_api import Revel8API, Revel8APIError


MAX_BODY_BYTES = 2048


class handler(BaseHTTPRequestHandler):
    """Expose read-only practice status and a streamed, explicit practice touch."""

    def do_OPTIONS(self) -> None:  # noqa: N802 - Vercel handler convention
        self.send_response(405)
        self.send_header("Allow", "GET, POST")
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802 - Vercel handler convention
        if self.path != "/api/live_run":
            self.send_error(404)
            return
        try:
            scenario = _practice_scenario(Revel8API().list_scenarios())
        except (Revel8APIError, ValueError) as exc:
            self._json(503, {"status": "offline", "message": str(exc)})
            return
        self._json(
            200,
            {
                "status": "ready",
                "scenario": "practice",
                "model_provider": provider_label(),
                "targets": [
                    {"id": target.get("id"), "name": target.get("name"), "role": target.get("role")}
                    for target in scenario.get("targets", [])
                    if target.get("id") in PRACTICE_TARGETS
                ],
            },
        )

    def do_POST(self) -> None:  # noqa: N802 - Vercel handler convention
        if self.path != "/api/live_run":
            self.send_error(404)
            return
        request_host = self.headers.get("x-forwarded-host") or self.headers.get("Host")
        if not _same_origin(self.headers.get("Origin"), request_host):
            self.send_error(403, "Same-origin requests only")
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > MAX_BODY_BYTES:
                raise ValueError("Request body size is invalid.")
            body = json.loads(self.rfile.read(length))
            target_id = body.get("target_id") if isinstance(body, dict) else None
            if not isinstance(target_id, str) or target_id not in PRACTICE_TARGETS:
                raise ValueError("Choose one of the three Revel8 practice targets.")
        except (ValueError, json.JSONDecodeError, UnicodeDecodeError) as exc:
            self._json(400, {"status": "error", "message": str(exc)})
            return

        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache, no-transform")
        self.send_header("X-Accel-Buffering", "no")
        self.end_headers()

        def emit(kind: str, **payload: Any) -> None:
            chunk = f"event: {kind}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"
            self.wfile.write(chunk.encode("utf-8"))
            self.wfile.flush()

        try:
            api = Revel8API(timeout=120)
            scenario = _practice_scenario(api.list_scenarios())
            target = next((item for item in scenario.get("targets", []) if item.get("id") == target_id), None)
            if not target:
                raise ValueError("That target is not available in the open practice scenario.")
            target_name = str(target.get("name") or target_id)
            adapter = Revel8PracticeAdapter(on_event=lambda node, label: emit("stage", node=node, label=label))
            committee, _ = committee_from_environment()
            orchestrator = Orchestrator(api=adapter, committee=committee)
            run = orchestrator.run_live(
                persona_id=target_id,
                target=target,
                graph=official_practice_graph(target),
                on_event=lambda node, label: emit("stage", node=node, label=label),
            )
            event_count = len(adapter.event_types)
            emit("persona", target=target_name, events=[{"type": value} for value in adapter.event_types], event_count=event_count)
            emit(
                "complete",
                session_id=adapter.session_id,
                target=target_name,
                touches_used=adapter.touches_used,
                event_count=event_count,
                run_id=run.run_id,
            )
        except (Revel8APIError, ValueError, KeyError, TypeError) as exc:
            emit("run_error", message=str(exc))
        except (BrokenPipeError, ConnectionResetError):
            # The browser left; don't write any credentials or message content to logs.
            return

    def _json(self, status: int, payload: dict[str, Any]) -> None:
        raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)


def _practice_scenario(scenarios: Any) -> dict[str, Any]:
    if not isinstance(scenarios, list):
        raise ValueError("Revel8 returned an unexpected scenarios response.")
    scenario = next((item for item in scenarios if item.get("id") == "practice"), None)
    if not scenario or not scenario.get("open"):
        raise ValueError("The Revel8 practice scenario is not currently open.")
    return scenario


def _same_origin(origin: str | None, host: str | None) -> bool:
    if not origin or not host:
        return False
    parsed = urlsplit(origin)
    return parsed.scheme in {"http", "https"} and parsed.netloc.lower() == host.lower()
