"""Run the deep reactive breach agent against one twin (one session, up to N touches).

    python scripts/run_breach.py --target julius --name "Julius Muth" --channel email --max-touches 8
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent_core import breach
from agent_core.target_api import load_env_file


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except (AttributeError, ValueError):
        pass
    p = argparse.ArgumentParser(description="Deep reactive breach agent against one twin.")
    p.add_argument("--target", required=True)
    p.add_argument("--name", required=True)
    p.add_argument("--channel", default="email")
    p.add_argument("--max-touches", type=int, default=8)
    p.add_argument("--findings", default=None)
    p.add_argument("--attach", action="store_true", help="pursue ACTION incident (get them to open a file)")
    p.add_argument("--anchor-topic", default=None, help="force an external-anchored pretext (public talk/paper/event)")
    p.add_argument("--anchor-angle", default=None, help="one-line pretext for the anchor")
    p.add_argument("--anchor-why", default=None, help="why-now for the anchor")
    p.add_argument("--anchor-match", default="", help="comma-separated terms to cite matching real facts")
    p.add_argument("--channels", default=None, help="comma-separated channels to cycle, e.g. email,slack,whatsapp")
    args = p.parse_args()

    load_env_file(str(ROOT / ".env.local"))
    findings = args.findings
    if findings is None:
        guess = ROOT / "research" / f"{args.target}.jsonl"
        findings = str(guess) if guess.exists() else None

    anchor = None
    if args.anchor_topic:
        anchor = {"topic": args.anchor_topic, "angle": args.anchor_angle or args.anchor_topic,
                  "why_now": args.anchor_why or "", "match": args.anchor_match}
    channels = [c.strip() for c in args.channels.split(",")] if args.channels else None
    log = breach.run_breach(args.target, args.name, channel=args.channel,
                            max_touches=args.max_touches, findings_path=findings, attach=args.attach,
                            anchor=anchor, channels=channels)
    if log.get("error"):
        print("error:", log["error"])
        return 1
    print(f"\n=== breach {args.target}: incident={log['incident']} "
          f"type={log['incident_type']} touches={log['touches_to_incident']} ===")
    for i, c in enumerate(log["contacts"], 1):
        if c.get("skipped"):
            print(f"  {i}. SKIPPED {c['skipped']}")
            continue
        body = re.sub(r"<[^>]+>", " ", c["payload"].get("body", "")).strip()
        reply = next((e.get("body") for e in c.get("events", []) if e.get("type") == "reply"), None)
        print(f"\n  [{i}] US: {body[:400]}")
        print(f"      THEM: {(reply or '(silence)')[:400]}")
    if log.get("captured"):
        print(f"\n  CAPTURED: {log['captured']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
