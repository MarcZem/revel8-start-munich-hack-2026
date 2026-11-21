"""Build the operator dashboard payload from the REAL run logs.

Reads the actual Target-API run artifacts in ``runs/`` (the same files the live
sweep writes) and emits a privacy-safe JSON payload that the static dashboard
renders. No demo data: every message, reply and outcome comes from a real
session against the consenting revel8 practice twins.

What ships: the agent's chosen hook/angle, a reproducible targeting-confidence
score derived from the research evidence reliability, the full message thread
(our phishing craft + the twin's verbatim replies), the planner's turn-by-turn
decisions, the all-channel tactic sweep, and the final incident outcome.

What never ships: the API key, and the raw per-person OSINT facts in
``research/`` (only aggregate reliability counts + the score leave that dir).

The payload is embedded straight into ``dashboard/index.html`` (between the
run-data markers) so the deployed page needs no fetch, no env var and no
server function — it renders identically in every environment.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RUNS = ROOT / "runs"
RESEARCH = ROOT / "research"
INDEX = ROOT / "dashboard" / "index.html"
DATA_JSON = ROOT / "dashboard" / "data.json"

# Mirror of agent_core.schema.RELIABILITY_CONFIDENCE (kept local so the build
# step stays dependency-free and never imports the agent / its secrets).
RELIABILITY_CONFIDENCE = {"belastbar": 0.9, "unsicher": 0.5, "unbelastbar": 0.2}

TARGETS = ("julius", "tom", "robert")

# Static display names for the three consenting practice twins.
NAMES = {"julius": "Julius Muth", "tom": "Tom Müller", "robert": "Robert Seilbeck"}

# The agent pipeline, in order — nodes + edges for the Obsidian-style graph.
PIPELINE = [
    {"id": "research", "label": "Research", "role": "OSINT retrieval + atomic fact extraction"},
    {"id": "ranker", "label": "Evidence Ranker", "role": "Deterministic reliability + freshness scoring"},
    {"id": "targeter", "label": "Targeting Reasoner", "role": "Picks the angle the twin is most open to now"},
    {"id": "writer", "label": "Writer", "role": "Crafts the message in a pinned persona"},
    {"id": "critic", "label": "Critic / Planner", "role": "Reads each reply: continue / switch / stop"},
    {"id": "twin", "label": "Target Twin", "role": "revel8 Personal Interface (the AI twin)"},
]


def _load(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _reliability_index(target: str) -> dict[str, str]:
    """id -> reliability, read locally from research/<target>.jsonl (never shipped raw)."""
    path = RESEARCH / f"{target}.jsonl"
    index: dict[str, str] = {}
    if not path.exists():
        return index
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if rec.get("id"):
            index[rec["id"]] = rec.get("reliability", "unsicher")
    return index


def _targeting_score(hook: dict, rel_index: dict[str, str]) -> dict | None:
    """Reproducible confidence for the chosen hook from its cited evidence."""
    eids = hook.get("evidence_ids") or []
    rels = [rel_index.get(eid) for eid in eids if eid in rel_index]
    rels = [r for r in rels if r]
    if not rels:
        return None
    confs = [RELIABILITY_CONFIDENCE.get(r, 0.5) for r in rels]
    breakdown: dict[str, int] = {}
    for r in rels:
        breakdown[r] = breakdown.get(r, 0) + 1
    return {
        "percent": round(100 * sum(confs) / len(confs)),
        "evidence_count": len(rels),
        "breakdown": breakdown,  # e.g. {"belastbar": 3, "unsicher": 1}
    }


def _thread(contact: dict | None) -> list[dict]:
    """Normalize a contact run into ordered touches: our message + the twin reply."""
    if not contact:
        return []
    out = []
    for c in contact.get("contacts", []):
        payload = c.get("payload", {})
        reply = next((e.get("body") for e in c.get("events", []) if e.get("type") == "reply"), None)
        out.append(
            {
                "touch": c.get("touches_used"),
                "channel": payload.get("channel", ""),
                "from_name": (payload.get("from") or {}).get("name", ""),
                "from_address": (payload.get("from") or {}).get("address", ""),
                "subject": payload.get("subject", ""),
                "body": payload.get("body", ""),
                "reply": reply,
                "plan": (c.get("plan") or {}).get("action"),
                "guidance": (c.get("plan") or {}).get("guidance", ""),
            }
        )
    return out


def _call_turns(call: dict | None) -> list[dict]:
    if not call:
        return []
    return [{"us": t.get("us", ""), "them": t.get("them", "")} for t in call.get("turns", [])]


def build() -> dict:
    targets = []
    for tid in TARGETS:
        contact = _load(RUNS / f"contact_{tid}.json")
        call = _load(RUNS / f"call_{tid}.json")
        sweep = _load(RUNS / f"sweep_{tid}.json")
        if not any([contact, call, sweep]):
            continue
        rel_index = _reliability_index(tid)
        hook = (contact or call or {}).get("hook", {})
        thread = _thread(contact)
        turns = _call_turns(call)
        contact_incident = bool(contact and contact.get("incident_guess"))
        call_incident = bool(call and call.get("incident_guess"))
        targets.append(
            {
                "id": tid,
                "name": NAMES.get(tid, tid),
                "objective": (contact or call or {}).get("objective", "disclosure"),
                "hook": {
                    "topic": hook.get("topic", ""),
                    "why_now": hook.get("why_now", ""),
                    "channel": hook.get("suggested_channel", ""),
                    "angle": hook.get("suggested_angle", ""),
                },
                "score": _targeting_score(hook, rel_index),
                "thread": thread,
                "call": turns,
                "sweep": (sweep or {}).get("results", []),
                "outcome": {
                    "compromised": contact_incident or call_incident,
                    "contact_incident": contact_incident,
                    "call_incident": call_incident,
                    "touches": thread[-1]["touch"] if thread else None,
                },
            }
        )

    compromised = [t["id"] for t in targets if t["outcome"]["compromised"]]
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "model": "DeepSeek-V4-Flash · AMD Token Factory",
        "pipeline": PIPELINE,
        "scenario": "revel8 practice — consenting AI twins (authorized simulation)",
        "summary": {
            "targets_total": len(targets),
            "compromised": len(compromised),
            "compromised_ids": compromised,
        },
        "targets": targets,
    }


def embed(payload: dict) -> bool:
    """Replace the run-data block inside index.html. Returns True on success."""
    if not INDEX.exists():
        return False
    html = INDEX.read_text(encoding="utf-8")
    start = '<script id="run-data" type="application/json">'
    end = "</script>"
    i = html.find(start)
    if i == -1:
        return False
    j = html.find(end, i)
    blob = json.dumps(payload, ensure_ascii=False, indent=0)
    new = html[: i + len(start)] + "\n" + blob + "\n" + html[j:]
    INDEX.write_text(new, encoding="utf-8")
    return True


def main() -> None:
    payload = build()
    DATA_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    embedded = embed(payload)
    print(f"targets: {payload['summary']['targets_total']} | "
          f"compromised: {payload['summary']['compromised']} "
          f"{payload['summary']['compromised_ids']}")
    print(f"wrote {DATA_JSON.relative_to(ROOT)}")
    print("embedded into dashboard/index.html" if embedded
          else "WARN: could not embed (run-data marker missing in index.html)")


if __name__ == "__main__":
    main()
