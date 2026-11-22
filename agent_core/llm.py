"""Thin OpenAI-compatible chat client (stdlib only).

Talks to the AMD Token Factory endpoint via LOCAL_LLM_* (see AGENTS.md). Fails
loud: any transport/HTTP/parse error raises LLMError, never a masked empty answer
(build-agent learning: a hidden failure turns an eval green without a real call).
"""

from __future__ import annotations

import json
import os
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

_RETRYABLE = {429, 500, 502, 503, 504}


class LLMError(RuntimeError):
    pass


def _endpoint(provider: str) -> tuple[str, str | None, str | None]:
    """(base_url, api_key, model) for a provider. 'openai' uses GPT credits; else DeepSeek."""
    if provider == "openai":
        base = (os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1").strip().rstrip("/")
        return base, os.getenv("OPENAI_API_KEY"), os.getenv("OPENAI_MODEL")
    base = (os.getenv("LOCAL_LLM_BASE_URL") or "").strip().rstrip("/")
    if not base:
        raise LLMError("LOCAL_LLM_BASE_URL not set (see .env.local / AGENTS.md)")
    base = base if base.endswith("/v1") else f"{base}/v1"
    return base, os.getenv("LOCAL_LLM_API_KEY") or os.getenv("OPENAI_API_KEY"), os.getenv("WRITER_MODEL")


def openai_available() -> bool:
    return bool(os.getenv("OPENAI_API_KEY") and os.getenv("OPENAI_MODEL"))


def chat(
    prompt: str,
    *,
    system: str | None = None,
    model: str | None = None,
    provider: str = "local",
    temperature: float = 0.0,
    max_tokens: int = 1500,
    timeout: float = 120.0,
    retries: int = 5,
) -> str:
    base, key, default_model = _endpoint(provider)
    model = model or default_model
    if not model:
        raise LLMError(f"no model configured for provider '{provider}'")
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    payload = json.dumps(
        {"model": model, "messages": messages, "temperature": temperature, "max_tokens": max_tokens}
    ).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if key:
        headers["Authorization"] = f"Bearer {key}"
    url = f"{base}/chat/completions"
    last = ""
    body = None
    for attempt in range(retries):
        req = Request(url, data=payload, headers=headers, method="POST")
        try:
            with urlopen(req, timeout=timeout) as resp:
                body = json.loads(resp.read().decode("utf-8"))
            break
        except HTTPError as exc:
            last = f"HTTP {exc.code}: {exc.read().decode('utf-8', 'replace')[:300]}"
            if exc.code in _RETRYABLE and attempt < retries - 1:
                # 429 here is the endpoint's own per-minute cap (e.g. AMD Token Factory's
                # "20 requests per minute"): honor Retry-After, else back off longer than for 5xx
                # so a sustained rate limit actually clears instead of exhausting retries in ~10s.
                if exc.code == 429:
                    retry_after = exc.headers.get("Retry-After") if exc.headers else None
                    delay = float(retry_after) if (retry_after or "").isdigit() else min(30, 5 * 2**attempt)
                else:
                    delay = 2**attempt + 1
                time.sleep(delay)
                continue
            raise LLMError(last) from None
        except (URLError, TimeoutError, OSError) as exc:
            last = f"request failed: {exc}"
            if attempt < retries - 1:
                time.sleep(2**attempt + 1)
                continue
            raise LLMError(last) from None
        except json.JSONDecodeError as exc:
            raise LLMError(f"non-JSON response: {exc}") from None
    if body is None:
        raise LLMError(last or "retries exhausted")
    choices = body.get("choices")
    if not isinstance(choices, list) or not choices:
        raise LLMError(f"no choices in response: {str(body)[:300]}")
    content = choices[0].get("message", {}).get("content")
    if not isinstance(content, str) or not content.strip():
        raise LLMError("empty content from model")
    return content
