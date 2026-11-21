"""Read-only connectivity check for the Revel8 Target API."""

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent_core.revel8_api import Revel8API, Revel8APIError


def main() -> int:
    try:
        api = Revel8API()
        scenarios = api.list_scenarios()
        channels = api.list_channels()
    except Revel8APIError as exc:
        print(f"Revel8 API check failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({"scenarios": scenarios, "channels": channels}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
