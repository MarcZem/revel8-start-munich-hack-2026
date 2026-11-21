"""Live smoke test against the revel8 Target API practice scenario.

Reads TARGET_API_BASE / TARGET_API_KEY from .env.local, lists scenarios, opens a
practice session, sends one email to Julius, prints the reaction, then ends the
session. Spends one practice touch. Run from the repo root:

    python scripts/smoke_target_api.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent_core.target_api import TargetAPI, load_env_file


def main() -> int:
    load_env_file(str(ROOT / ".env.local"))
    api = TargetAPI()

    scenarios = api.scenarios()
    practice = next((s for s in scenarios if s.get("id") == "practice"), None)
    print("scenarios:", [s.get("id") for s in scenarios])
    assert practice and practice.get("open"), "practice scenario is not open"

    session = api.create_session("practice")
    sid = session["session_id"]
    print("session_id:", sid, "touch_budget:", session.get("touch_budget"))

    reaction = api.send_message(
        sid,
        to="julius",
        channel="email",
        **{"from": {"name": "Lena Hofer", "address": "lena.hofer@eventcrew-muc.de"}},
        subject="Speaker slot Thursday — quick confirm",
        body=(
            "Hi Julius, I'm coordinating the speaker logistics for Thursday's panel "
            "and want to confirm your arrival window and AV needs. Could you reply with "
            "a time that works for a 5-min sync? Thanks, Lena"
        ),
    )
    print("touches_used:", reaction.get("touches_used"))
    print("events:", json.dumps(reaction.get("events", []), indent=2, ensure_ascii=False))

    api.end_session(sid)
    assert "message_id" in reaction, "no message_id returned"
    print("OK: live round-trip succeeded")
    return 0


if __name__ == "__main__":
    sys.exit(main())
