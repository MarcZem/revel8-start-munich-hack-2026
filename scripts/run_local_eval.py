"""Run the breach agent against self-made local test personas (authorized, offline).

    python scripts/run_local_eval.py                      # all personas, credentials objective
    python scripts/run_local_eval.py --persona markus      # one persona
    python scripts/run_local_eval.py --persona markus --attach   # pursue the ACTION incident

Proves the agent CONVERTS on realistic targets across the susceptibility spectrum — the three
founder twins are the hardest possible wall, not the norm. A breach here is a self-test against our
own LLM-role-played persona; it never touches the real Target API and is not a scored incident.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent_core import breach
from agent_core.local_persona import PERSONAS, LocalPersonaAPI, synthetic_findings
from agent_core.target_api import load_env_file


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except (AttributeError, ValueError):
        pass
    p = argparse.ArgumentParser(description="Breach agent vs self-made local test personas.")
    p.add_argument("--persona", default=None, choices=list(PERSONAS))
    p.add_argument("--channel", default="email")
    p.add_argument("--max-touches", type=int, default=8)
    mode = p.add_mutually_exclusive_group()
    mode.add_argument("--attach", action="store_true",
                      help="ACTION incident via a file pretext (get them to approve/forward, not just open)")
    mode.add_argument("--action-page", action="store_true",
                      help="ACTION incident via a payment-confirmation form (they submit a changed detail)")
    p.add_argument("--channels", default=None, help="comma-separated channels to cycle (multi-channel)")
    args = p.parse_args()
    load_env_file(str(ROOT / ".env.local"))

    ids = [args.persona] if args.persona else list(PERSONAS)
    results = []
    for pid in ids:
        name = PERSONAS[pid]["name"]
        print(f"\n######### LOCAL PERSONA: {name} (awareness={PERSONAS[pid]['awareness']}) #########")
        channels = [c.strip() for c in args.channels.split(",")] if args.channels else None
        log = breach.run_breach(
            pid, name, scenario="local", channel=args.channel, max_touches=args.max_touches,
            attach=args.attach, action_page=args.action_page, api=LocalPersonaAPI(pid),
            findings=synthetic_findings(pid), own_domains=(), out_dir="runs", channels=channels,
        )
        results.append((pid, log.get("incident"), log.get("incident_type"), log.get("touches_to_incident")))
        print(f"==> {name}: incident={log.get('incident')} type={log.get('incident_type')} "
              f"touches_to_incident={log.get('touches_to_incident')}")

    print("\n==== local eval summary (self-test, not a scored result) ====")
    for pid, inc, typ, t2i in results:
        print(f"  {pid:8s} incident={inc} type={typ} touches={t2i}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
