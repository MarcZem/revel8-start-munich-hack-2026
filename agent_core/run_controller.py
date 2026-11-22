"""Run controller: the single entry point to the scored agent.

Owns the run lifecycle the rubric cares about:
- one session per target (the target remembers everything within it; sessions share no memory);
- the touch cap per scenario — 10 for an eval scoring session, 30 for practice;
- persist a typed RunRecord per target and aggregate the campaign the way Results is scored;
- resume: the Target API lists sessions and replays events, so a crashed run can be picked up.

It does not re-implement the per-turn logic: it drives the proven reactive loop
(`agent_core.breach.run_breach`) once per target and normalises each result through
`RunRecord`. That keeps one control loop, one API boundary, one persisted shape.
"""

from __future__ import annotations

import json
from pathlib import Path

from agent_core import breach
from agent_core.run_record import CampaignResult, RunRecord
from agent_core.target_api import TargetAPI

# Default practice roster: the three consenting founder twins.
PRACTICE_TARGETS: tuple[tuple[str, str], ...] = (
    ("julius", "Julius Muth"),
    ("tom", "Tom Müller"),
    ("robert", "Robert Seilbeck"),
)

TOUCH_CAP = {"eval": 10, "practice": 30}


class RunController:
    def __init__(self, scenario: str = "practice", channel: str = "email", out_dir: str = "runs",
                 channels: list[str] | None = None) -> None:
        self.scenario = scenario
        self.channel = channel
        self.channels = channels  # cycle these across touches (multi-channel) if given
        self.out_dir = out_dir
        self.touch_cap = TOUCH_CAP.get(scenario, 10)

    def run_session(self, target_id: str, target_name: str, *, objective: str = "breach",
                    max_touches: int | None = None, findings_path: str | None = None,
                    attach: bool = False) -> RunRecord:
        """One target, one session. The reactive loop stops early on an incident or on two
        silences (no traction); `max_touches` is the hard cap (defaults to the scenario cap)."""
        cap = max_touches or self.touch_cap
        log = breach.run_breach(
            target_id, target_name, scenario=self.scenario, channel=self.channel,
            max_touches=cap, findings_path=findings_path, out_dir=self.out_dir, attach=attach,
            channels=self.channels,
        )
        if log.get("error"):
            raise RuntimeError(f"run_session({target_id}) failed: {log['error']}")
        log.setdefault("scenario", self.scenario)
        log.setdefault("target_name", target_name)
        record = RunRecord.from_log(log)
        self._persist(record)
        return record

    def run_campaign(self, targets: tuple[tuple[str, str], ...] = PRACTICE_TARGETS, *,
                     objective: str = "breach", max_touches: int | None = None) -> CampaignResult:
        """Run one session per target in ONE process (so the session-rate throttle is shared)
        and aggregate into the Results-style campaign metrics."""
        records: list[RunRecord] = []
        for tid, name in targets:
            findings = Path("research") / f"{tid}.jsonl"
            print(f"\n==== {self.scenario} session: {name} (cap {max_touches or self.touch_cap}) ====")
            records.append(self.run_session(
                tid, name, objective=objective, max_touches=max_touches,
                findings_path=str(findings) if findings.exists() else None,
            ))
        result = CampaignResult.aggregate(records)
        self._persist_campaign(result)
        return result

    def resume(self, session_id: str) -> dict:
        """Fetch a prior session's events so a crashed run can be inspected/continued."""
        return TargetAPI().session_events(session_id)

    # --- persistence -------------------------------------------------------

    def _persist(self, record: RunRecord) -> None:
        out = Path(self.out_dir)
        out.mkdir(parents=True, exist_ok=True)
        (out / f"run_{record.target_id}.json").write_text(
            json.dumps(record.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")

    def _persist_campaign(self, result: CampaignResult) -> None:
        out = Path(self.out_dir)
        out.mkdir(parents=True, exist_ok=True)
        (out / "campaign.json").write_text(
            json.dumps(result.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
