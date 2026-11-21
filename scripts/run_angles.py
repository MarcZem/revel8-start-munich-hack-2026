"""Load a target's findings, build the graph, and rank current attack hooks.

    python scripts/run_angles.py --target julius --name "Julius Muth"

Intended for the authorized simulation's consenting AI-twin targets.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent_core import angle_reasoner, graph_loader
from agent_core.target_api import load_env_file


def main() -> int:
    parser = argparse.ArgumentParser(description="Rank current hooks from a target's findings.")
    parser.add_argument("--target", required=True)
    parser.add_argument("--name", required=True)
    args = parser.parse_args()

    load_env_file(str(ROOT / ".env.local"))
    findings = graph_loader.load_findings(ROOT / "research" / f"{args.target}.jsonl")
    graph = graph_loader.build_graph(args.target, args.name, findings)
    print(f"graph: {len(graph.nodes)} nodes, {len(graph.edges)} edges, {len(findings)} findings")

    hooks = angle_reasoner.rank_hooks(findings)
    print(f"hooks: {len(hooks)}\n")
    for i, h in enumerate(hooks, 1):
        print(f"{i}. [{h.suggested_channel}] {h.topic}")
        print(f"   why now: {h.why_now}")
        print(f"   angle:   {h.suggested_angle}")
        print(f"   cites:   {', '.join(h.evidence_ids)}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
