from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_BASE_URL = "http://localhost:8000/v1"
DEFAULT_MESSAGE = "Say hi in one sentence."


def load_env_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"env file not found: {path}")
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("\"'")
        if key and key not in os.environ:
            os.environ[key] = value


def normalize_base_url(base_url: str) -> str:
    base = base_url.strip().rstrip("/")
    if not base:
        raise ValueError("base URL must not be empty")
    if base.endswith("/v1"):
        return base
    return f"{base}/v1"


def model_from_env() -> str | None:
    return os.getenv("WRITER_MODEL") or os.getenv("CRITIC_MODEL")


def api_key_from_env() -> str | None:
    return os.getenv("LOCAL_LLM_API_KEY") or os.getenv("OPENAI_API_KEY")


def build_chat_payload(model: str, message: str) -> dict[str, Any]:
    return {
        "model": model,
        "messages": [{"role": "user", "content": message}],
        "temperature": 0,
        "max_tokens": 64,
    }


def post_chat_completion(
    *,
    base_url: str,
    model: str,
    message: str,
    timeout: float,
    api_key: str | None,
) -> dict[str, Any]:
    payload = json.dumps(build_chat_payload(model, message)).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    request = Request(
        f"{normalize_base_url(base_url)}/chat/completions",
        data=payload,
        headers=headers,
        method="POST",
    )
    with urlopen(request, timeout=timeout) as response:
        body = response.read().decode("utf-8")
    return json.loads(body)


def response_text(response: dict[str, Any]) -> str:
    choices = response.get("choices")
    if not isinstance(choices, list) or not choices:
        return ""
    first = choices[0]
    if not isinstance(first, dict):
        return ""
    message = first.get("message")
    if isinstance(message, dict) and isinstance(message.get("content"), str):
        return message["content"]
    text = first.get("text")
    return text if isinstance(text, str) else ""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Smoke-test an OpenAI-compatible vLLM chat completions endpoint.",
    )
    parser.add_argument("--base-url", default=os.getenv("LOCAL_LLM_BASE_URL", DEFAULT_BASE_URL))
    parser.add_argument("--model", default=model_from_env())
    parser.add_argument("--message", default=DEFAULT_MESSAGE)
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument(
        "--env-file",
        type=Path,
        help="Optional local env file to load before reading LOCAL_LLM_* and model variables.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.env_file:
        load_env_file(args.env_file)
        args.base_url = os.getenv("LOCAL_LLM_BASE_URL", args.base_url)
        args.model = args.model or model_from_env()

    if not args.model:
        print("error: set WRITER_MODEL/CRITIC_MODEL or pass --model", file=sys.stderr)
        return 2

    safe_base_url = normalize_base_url(args.base_url)
    print(f"endpoint={safe_base_url}")
    print(f"model={args.model}")

    try:
        response = post_chat_completion(
            base_url=safe_base_url,
            model=args.model,
            message=args.message,
            timeout=args.timeout,
            api_key=api_key_from_env(),
        )
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print(f"error: HTTP {exc.code} from endpoint", file=sys.stderr)
        if body:
            print(body[:1000], file=sys.stderr)
        return 1
    except (URLError, TimeoutError, OSError) as exc:
        print(f"error: endpoint request failed: {exc}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as exc:
        print(f"error: endpoint returned non-JSON response: {exc}", file=sys.stderr)
        return 1

    content = response_text(response)
    response_id = response.get("id", "unknown")
    finish_reason = ""
    if isinstance(response.get("choices"), list) and response["choices"]:
        finish_reason = str(response["choices"][0].get("finish_reason", ""))

    print(f"response_id={response_id}")
    if finish_reason:
        print(f"finish_reason={finish_reason}")
    print(f"content={content.strip()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
