"""Run the full tactic sweep (all levers × channels) against one twin.

    python scripts/run_sweep.py --target julius --name "Julius Muth" --findings research/julius.jsonl

Writes runs/sweep_<target>.json. Run it per twin (in parallel is fine — separate sessions),
then aggregate with scripts/score_sweep.py.
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


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except (AttributeError, ValueError):
        pass
    p = argparse.ArgumentParser(description="Run the tactic sweep against one twin.")
    p.add_argument("--target", required=True)
    p.add_argument("--name", required=True)
    p.add_argument("--findings", default=None)
    p.add_argument("--max-touches", type=int, default=3)
    p.add_argument("--tactics", default=None, help="comma-separated tactic names to run (default: all)")
    args = p.parse_args()
    only = [s.strip() for s in args.tactics.split(",")] if args.tactics else None

    load_env_file(str(ROOT / ".env.local"))
    findings = args.findings
    if findings is None:
        guess = ROOT / "research" / f"{args.target}.jsonl"
        findings = str(guess) if guess.exists() else None

    summary = tactics.run_sweep(args.target, args.name, findings_path=findings,
                                max_touches=args.max_touches, only=only)
    print(f"\n=== sweep {args.target}: best per tactic ===")
    for r in sorted(summary["results"], key=lambda x: x.get("rank", -1), reverse=True):
        if r.get("error"):
            print(f"  {r['tactic']:<22} [{r.get('channel','')}] ERROR {r['error']}")
        else:
            inc = " INCIDENT" if r["incident"] else ""
            print(f"  {r['tactic']:<22} [{r['lever']}/{r['channel']}] → {r['best']} (rank {r['rank']}){inc}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
