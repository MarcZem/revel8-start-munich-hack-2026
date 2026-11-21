"""Eval: does the writer prompt avoid detection tells on the live model? (#17)

Runs `build_writer_system_prompt()` against the configured Token Factory /
vLLM model for a few persona briefs, scans each output for the tells in
`agent_core.writer_prompt.DETECTION_TELLS`, and writes a report. A case passes
when the output has zero tells and is non-empty.

Usage:
    python scripts/eval_writer_prompt.py --env-file .env.local

No endpoint/key configured -> exits 3 and reports "not run" (never "passed").
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "scripts"))

from agent_core.writer_prompt import build_writer_system_prompt, tells_in  # noqa: E402
from check_vllm_endpoint import (  # noqa: E402
    api_key_from_env,
    load_env_file,
    normalize_base_url,
    response_text,
)

# Synthetic briefs only — no real people (build-agent security rule). Each gives
# the writer a researched hook; a good message uses it without any tell.
CASES: tuple[dict[str, str], ...] = (
    {
        "id": "founder_sales_meetup",
        "brief": "Target: Julius, co-CEO (sales) of a logistics startup. Evidence: gave a public talk last week on dynamic freight pricing; active on LinkedIn. Channel: email. Sender: a founder who attended the talk. Objective: get a 15-minute call booked.",
    },
    {
        "id": "cto_open_source",
        "brief": "Target: Robert, CTO. Evidence: merged a public pull request on a vector-search library yesterday; speaks at a meetup next month. Channel: Slack DM. Sender: a maintainer of a related open-source project. Objective: get them to open a shared design doc.",
    },
    {
        "id": "product_hiring",
        "brief": "Target: Tom, co-CEO (product). Evidence: posted publicly that the team is hiring a first PM. Channel: LinkedIn message. Sender: a product leader offering a referral. Objective: get a reply agreeing to a short intro.",
    },
)


def complete(base_url: str, model: str, system: str, user: str, timeout: float, api_key: str | None) -> str:
    payload = json.dumps(
        {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.7,
            "max_tokens": 400,
        }
    ).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    request = Request(f"{normalize_base_url(base_url)}/chat/completions", data=payload, headers=headers, method="POST")
    with urlopen(request, timeout=timeout) as response:
        return response_text(json.loads(response.read().decode("utf-8")))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Eval the writer prompt for detection-tell avoidance.")
    parser.add_argument("--env-file", type=Path)
    parser.add_argument("--base-url", default=os.getenv("LOCAL_LLM_BASE_URL", "http://localhost:8000/v1"))
    parser.add_argument("--model", default=os.getenv("WRITER_MODEL"))
    parser.add_argument("--language", default="German")
    parser.add_argument("--timeout", type=float, default=90.0)
    parser.add_argument("--report", type=Path, default=_ROOT / "evals" / "writer_prompt_report.json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.env_file:
        load_env_file(args.env_file)
        args.base_url = os.getenv("LOCAL_LLM_BASE_URL", args.base_url)
        args.model = args.model or os.getenv("WRITER_MODEL")
    if not args.model:
        print("not run: set WRITER_MODEL or pass --model", file=sys.stderr)
        return 3

    system = build_writer_system_prompt(args.language)
    results = []
    errored = False
    for case in CASES:
        try:
            text = complete(args.base_url, args.model, system, case["brief"], args.timeout, api_key_from_env())
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            print(f"not run: endpoint request failed for {case['id']}: {exc}", file=sys.stderr)
            errored = True
            break
        hits = tells_in(text)
        passed = bool(text.strip()) and not hits
        results.append({"id": case["id"], "passed": passed, "tells": hits, "output": text.strip()})
        print(f"[{'PASS' if passed else 'FAIL'}] {case['id']}: tells={hits or 'none'}")

    if errored or not results:
        return 3

    passed = sum(r["passed"] for r in results)
    report = {"model": args.model, "language": args.language, "passed": passed, "total": len(results), "cases": results}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"\n{passed}/{len(results)} cases clean. Report: {args.report}")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
