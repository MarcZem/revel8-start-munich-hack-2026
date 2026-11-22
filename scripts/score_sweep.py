"""Aggregate runs/sweep_*.json into one tactic × twin scoreboard.

    python scripts/score_sweep.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_SYMBOL = {0: ".", 1: "r", 2: "a", 3: "L", 4: "S"}  # silence / reply / attach / Link / Submit


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except (AttributeError, ValueError):
        pass
    files = sorted((ROOT / "runs").glob("sweep_*.json"))
    if not files:
        print("no runs/sweep_*.json found — run scripts/run_sweep.py first")
        return 1
    twins, grid = [], {}  # grid[tactic][twin] = (rank, best, incident)
    for f in files:
        data = json.loads(f.read_text(encoding="utf-8"))
        twin = data["target"]
        twins.append(twin)
        for r in data["results"]:
            grid.setdefault(r["tactic"], {})[twin] = r

    print("legend: . silence  r reply  a attachment  L link.opened  S page.submitted(incident)\n")
    head = f"{'tactic':<22}{'lever/channel':<22}" + "".join(f"{t:<10}" for t in twins)
    print(head)
    print("-" * len(head))
    best_overall = (0, None)
    for tactic, row in grid.items():
        any_r = next(iter(row.values()))
        meta = f"{any_r.get('lever','?')}/{any_r.get('channel','?')}"
        cells = ""
        for t in twins:
            r = row.get(t)
            if not r or r.get("error"):
                cells += f"{'ERR' if r else '-':<10}"
            else:
                mark = _SYMBOL.get(r["rank"], "?") + ("*" if r["incident"] else "")
                cells += f"{mark:<10}"
                if r["rank"] > best_overall[0]:
                    best_overall = (r["rank"], f"{tactic} vs {t} → {r['best']}")
        print(f"{tactic:<22}{meta:<22}{cells}")
    print(f"\nstrongest result: {best_overall[1] or 'all silence'}")

    # Real incidents (the only thing that scores): type + fewest-touches (Speed metric)
    incidents = []
    for tactic, row in grid.items():
        for twin, r in row.items():
            if r and r.get("incident"):
                incidents.append((twin, tactic, r.get("incident_type"),
                                  r.get("touches_to_incident"), r.get("captured")))
    print(f"\nREAL incidents: {len(incidents)}")
    for twin, tactic, itype, touches, cap in sorted(incidents, key=lambda x: (x[3] or 99)):
        print(f"  {twin:<8} {tactic:<20} {itype} in {touches} touch(es) — captured: {str(cap)[:120]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
