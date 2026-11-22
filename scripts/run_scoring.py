"""The single entry point to the scored agent: run one adaptive session per target.

    python scripts/run_scoring.py                      # all three practice twins, email
    python scripts/run_scoring.py --target julius       # one target
    python scripts/run_scoring.py --scenario eval        # 10-touch scoring sessions (when open)

One process, so the team-wide session-rate cap is respected. Writes runs/run_<target>.json
(a typed RunRecord) per target and runs/campaign.json for the aggregate, then
`python scripts/build_dashboard_data.py` refreshes the jury console.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent_core.run_controller import PRACTICE_TARGETS, RunController
from agent_core.target_api import load_env_file


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except (AttributeError, ValueError):
        pass
    p = argparse.ArgumentParser(description="Run the scored reactive agent (one session per target).")
    p.add_argument("--scenario", default="practice", choices=["practice", "eval"])
    p.add_argument("--channel", default="email")
    p.add_argument("--channels", default=None,
                   help="comma-separated channels to cycle across touches, e.g. email,slack,whatsapp,linkedin_message")
    p.add_argument("--target", default=None, help="single target id (default: all practice twins)")
    p.add_argument("--name", default=None, help="display name when --target is a custom id")
    p.add_argument("--max-touches", type=int, default=None, help="override the scenario touch cap")
    p.add_argument("--attach", action="store_true", help="pursue the ACTION incident (open a file)")
    args = p.parse_args()
    load_env_file(str(ROOT / ".env.local"))

    channels = [c.strip() for c in args.channels.split(",")] if args.channels else None
    ctrl = RunController(scenario=args.scenario, channel=args.channel, channels=channels)
    names = dict(PRACTICE_TARGETS)
    if args.target:
        targets = ((args.target, args.name or names.get(args.target, args.target)),)
    else:
        targets = PRACTICE_TARGETS

    result = ctrl.run_campaign(targets, max_touches=args.max_touches)
    print("\n==== campaign ====")
    print(f"runs: {result.runs_total} | with incident: {result.runs_with_incident} "
          f"| incident-points est.: {result.incident_points_estimate}/20 "
          f"| speed (median contacts): {result.speed_median_contacts}")
    for r in result.records:
        print(f"  {r.target_id:8s} incident={r.incident} type={r.incident_type} "
              f"contacts={r.contacts_used} stop={r.stop_reason}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
