"""Read-only connectivity check for the revel8 Target API.

Calls only GET /scenarios and GET /channels: it opens no session, spends no touch,
and contacts no simulated target. Loads .env.local automatically.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent_core.target_api import TargetAPI, TargetAPIError, load_env_file


def main() -> int:
    load_env_file()
    try:
        api = TargetAPI()
        scenarios = api.scenarios()
        channels = api.channels()
    except TargetAPIError as exc:
        print(f"Target API check failed: {exc}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"Config error: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({"scenarios": scenarios, "channels": channels}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
