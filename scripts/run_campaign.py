"""Run the full tactic campaign against all three twins in ONE sequential process.

One process so the session-creation throttle (≤58 new sessions/hour, the team cap) is shared.
Writes runs/sweep_<twin>.json incrementally; aggregate with scripts/score_sweep.py.

    python scripts/run_campaign.py [--max-touches 3]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent_core import tactics
from agent_core.target_api import load_env_file

TWINS = [("julius", "Julius Muth"), ("tom", "Tom Müller"), ("robert", "Robert Seilbeck")]


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except (AttributeError, ValueError):
        pass
    p = argparse.ArgumentParser(description="Full tactic campaign across all twins, session-paced.")
    p.add_argument("--max-touches", type=int, default=3)
    args = p.parse_args()
    load_env_file(str(ROOT / ".env.local"))

    for tid, name in TWINS:
        findings = ROOT / "research" / f"{tid}.jsonl"
        print(f"\n########## CAMPAIGN: {name} ##########")
        summary = tactics.run_sweep(tid, name, findings_path=str(findings) if findings.exists() else None,
                                    max_touches=args.max_touches)
        inc = [r for r in summary["results"] if r.get("incident")]
        print(f"## {tid}: {len(inc)} real incident(s) of {len(summary['results'])} tactics")
    print("\nCAMPAIGN DONE — run: python scripts/score_sweep.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
