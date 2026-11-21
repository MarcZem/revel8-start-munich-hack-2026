"""Run the research pipeline for one target and write research/<target>.jsonl.

    python scripts/run_research.py --target julius --name "Julius Muth revel8"
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent_core import research
from agent_core.target_api import load_env_file


def main() -> int:
    parser = argparse.ArgumentParser(description="Research a target into atomic findings.")
    parser.add_argument("--target", required=True, help="Scenario target id, e.g. julius")
    parser.add_argument("--name", required=True, help="Search name, e.g. 'Julius Muth revel8'")
    parser.add_argument("--channels", default="web", help="Comma-separated agent-reach channels")
    parser.add_argument("--limit", type=int, default=4, help="Items per channel/query")
    parser.add_argument("--github-user", default=None, help="Known GitHub username to deep-read repos")
    parser.add_argument("--user-provided-file", default=None, help="Path to text the user legitimately has")
    parser.add_argument("--no-contradictions", action="store_true", help="Skip the LLM contradiction pass")
    parser.add_argument("--no-second-hop", action="store_true", help="Skip entity follow-up (2nd hop)")
    parser.add_argument("--workers", type=int, default=6, help="Parallel extraction workers (6-8 sweet spot)")
    args = parser.parse_args()

    load_env_file(str(ROOT / ".env.local"))
    channels = tuple(c.strip() for c in args.channels.split(",") if c.strip())
    user_provided = None
    if args.user_provided_file:
        user_provided = Path(args.user_provided_file).read_text(encoding="utf-8")
    print(f"researching {args.target} ({args.name}) via {channels}")

    findings = research.run_research(
        args.target, args.name, channels=channels, limit=args.limit,
        contradictions=not args.no_contradictions,
        github_user=args.github_user, user_provided=user_provided,
        second_hop=not args.no_second_hop, max_workers=args.workers,
    )

    by_rel: dict[str, int] = {}
    for f in findings:
        by_rel[f.reliability] = by_rel.get(f.reliability, 0) + 1
    print(f"findings={len(findings)} by_reliability={by_rel}")
    print(f"written=research/{args.target}.jsonl")
    for f in findings[:8]:
        print(f"  [{f.reliability:11}] ({f.category}) {f.fact}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
