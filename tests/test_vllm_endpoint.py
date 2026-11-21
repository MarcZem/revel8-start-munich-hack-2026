from __future__ import annotations

import json
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from scripts.check_vllm_endpoint import (
    build_chat_payload,
    load_env_file,
    normalize_base_url,
    post_chat_completion,
    response_text,
)


class _Handler(BaseHTTPRequestHandler):
    captured_path = ""
    captured_payload = {}
    captured_auth = None

    def do_POST(self) -> None:
        type(self).captured_path = self.path
        type(self).captured_auth = self.headers.get("Authorization")
        length = int(self.headers["Content-Length"])
        type(self).captured_payload = json.loads(self.rfile.read(length).decode("utf-8"))
        body = {
            "id": "chatcmpl-test",
            "choices": [
                {
                    "message": {"role": "assistant", "content": "Hi from the test endpoint."},
                    "finish_reason": "stop",
                }
            ],
        }
        encoded = json.dumps(body).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, *_args: object) -> None:
        return


class VllmEndpointTests(unittest.TestCase):
    def test_normalize_base_url_adds_v1_when_missing(self) -> None:
        self.assertEqual(normalize_base_url("http://localhost:8000"), "http://localhost:8000/v1")
        self.assertEqual(normalize_base_url("http://localhost:8000/v1/"), "http://localhost:8000/v1")

    def test_build_chat_payload_matches_openai_chat_shape(self) -> None:
        payload = build_chat_payload("Qwen/Qwen3-14B", "hello")

        self.assertEqual(payload["model"], "Qwen/Qwen3-14B")
        self.assertEqual(payload["messages"], [{"role": "user", "content": "hello"}])
        self.assertEqual(payload["temperature"], 0)

    def test_load_env_file_does_not_override_existing_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / ".env.local"
            path.write_text("LOCAL_LLM_BASE_URL=http://example.test/v1\nWRITER_MODEL=test-model\n", encoding="utf-8")

            import os

            previous = os.environ.get("WRITER_MODEL")
            os.environ["WRITER_MODEL"] = "existing-model"
            try:
                load_env_file(path)
                self.assertEqual(os.environ["WRITER_MODEL"], "existing-model")
                self.assertEqual(os.environ["LOCAL_LLM_BASE_URL"], "http://example.test/v1")
            finally:
                if previous is None:
                    os.environ.pop("WRITER_MODEL", None)
                else:
                    os.environ["WRITER_MODEL"] = previous
                os.environ.pop("LOCAL_LLM_BASE_URL", None)

    def test_post_chat_completion_calls_v1_chat_completions(self) -> None:
        server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            base_url = f"http://127.0.0.1:{server.server_port}/v1"
            response = post_chat_completion(
                base_url=base_url,
                model="test-model",
                message="hello",
                timeout=5,
                api_key="secret-test-key",
            )
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)

        self.assertEqual(_Handler.captured_path, "/v1/chat/completions")
        self.assertEqual(_Handler.captured_payload["model"], "test-model")
        self.assertEqual(_Handler.captured_auth, "Bearer secret-test-key")
        self.assertEqual(response_text(response), "Hi from the test endpoint.")


if __name__ == "__main__":
    unittest.main()
