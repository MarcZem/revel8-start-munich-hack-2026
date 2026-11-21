from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent_core.orchestrator import Orchestrator


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the local revel8 agent-core prototype.")
    parser.add_argument("--persona", default="lena_kraus", help="Synthetic persona id.")
    parser.add_argument("--out", default="runs/latest_agent_core_run.json", help="Path for the JSON run log.")
    args = parser.parse_args()

    output_path = Path(args.out)
    log = Orchestrator().run_and_save(args.persona, output_path)
    print(f"run_id={log.run_id}")
    print(f"winner_candidate_id={log.committee_decision.winner_candidate_id}")
    print(f"event_type={log.api_event.event_type if log.api_event else 'not_sent'}")
    print(f"run_log={output_path}")


if __name__ == "__main__":
    main()
