"""Run one autonomous contact thread against a (consenting) twin — the first real test.

    python scripts/run_contact.py --target julius --name "Julius Muth" \
        --objective disclosure --findings research/julius.jsonl
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent_core import contact_loop
from agent_core.target_api import load_env_file


def main() -> int:
    p = argparse.ArgumentParser(description="One autonomous contact thread via the live API.")
    p.add_argument("--target", required=True, help="Scenario target id, e.g. julius")
    p.add_argument("--name", required=True)
    p.add_argument("--objective", default="disclosure", choices=["disclosure", "action", "credentials"])
    p.add_argument("--scenario", default="practice")
    p.add_argument("--max-touches", type=int, default=4)
    p.add_argument("--findings", default=None, help="Path to research/<target>.jsonl (skips re-research)")
    args = p.parse_args()

    load_env_file(str(ROOT / ".env.local"))
    findings = args.findings
    if findings is None:
        guess = ROOT / "research" / f"{args.target}.jsonl"
        findings = str(guess) if guess.exists() else None

    log = contact_loop.run_contact(
        args.target, args.name, objective=args.objective, scenario=args.scenario,
        max_touches=args.max_touches, findings_path=findings,
    )
    if log.get("error"):
        print("error:", log["error"])
        return 1
    print(f"\ncontacts={len(log['contacts'])} incident_guess={log.get('incident_guess')}")
    print(f"run_log={log.get('_path')}")
    for i, c in enumerate(log["contacts"], 1):
        if c.get("skipped"):
            print(f"  {i}. SKIPPED: {c['skipped']}")
            continue
        kinds = [e.get("type") for e in c.get("events", [])]
        print(f"  {i}. [{c['payload']['channel']}] '{c['payload']['subject']}' → {kinds or 'silence'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
