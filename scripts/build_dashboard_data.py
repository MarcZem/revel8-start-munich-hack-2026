"""Build the operator-console payload from the REAL run records.

Reads the typed RunRecord artifacts in ``runs/run_<target>.json`` (what the run
controller writes), falling back to the raw breach/contact logs normalised through
``agent_core.run_record``. Emits a privacy-safe JSON payload the static dashboard
renders with no fetch, no API key and no server function — it renders identically
in every environment.

Honesty: the outcome is the TRUTHFUL ``incident`` field (a secret submitted, a file
opened, or a judged disclosure) — never the old soft ``incident_guess`` heuristic.
What ships: the chosen hook + the alternatives weighed, a reproducible targeting score
from research-evidence reliability, the full thread (our craft + the twin's verbatim
replies), the per-touch reassessment (why sent, the gate hit, continue/switch/stop), the
all-channel tactic sweep, and the honest outcome. What never ships: the API key, and the
raw per-person OSINT in ``research/`` (only aggregate reliability + the score leave it).
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent_core.run_record import RunRecord  # pure dataclasses: no network, no secrets

RUNS = ROOT / "runs"
RESEARCH = ROOT / "research"
INDEX = ROOT / "dashboard" / "index.html"
DATA_JSON = ROOT / "dashboard" / "data.json"

RELIABILITY_CONFIDENCE = {"belastbar": 0.9, "unsicher": 0.5, "unbelastbar": 0.2}
TARGETS = ("julius", "tom", "robert")
NAMES = {"julius": "Julius Muth", "tom": "Tom Müller", "robert": "Robert Seilbeck"}

# The agent pipeline, in order — nodes + edges for the force-graph. Mirrors docs/architecture.md:
# public sources -> research -> evidence graph -> targeting -> run controller -> writer -> twin,
# with the evaluator closing the loop (read the reaction, reassess, continue/switch/stop).
PIPELINE = [
    {"id": "linkedin", "label": "LinkedIn", "role": "profile + activity (first stop)", "kind": "source"},
    {"id": "company", "label": "Company site", "role": "revel8.ai / press", "kind": "source"},
    {"id": "web", "label": "Web & podcasts", "role": "talks, investors, interviews", "kind": "source"},
    {"id": "research", "label": "Research", "role": "OSINT -> atomic facts + provenance"},
    {"id": "knowledge", "label": "Evidence graph", "role": "facts ranked by reliability"},
    {"id": "targeting", "label": "Targeting", "role": "ranked, evidence-cited hooks"},
    {"id": "controller", "label": "Run controller", "role": "session + touch budget + persistence"},
    {"id": "writer", "label": "Writer", "role": "crafts the touch in a pinned persona"},
    {"id": "twin", "label": "Target twin", "role": "revel8 AI twin (the simulated person)"},
    {"id": "evaluator", "label": "Evaluator", "role": "reads each reaction: continue / switch / stop"},
]

_KG_CATEGORIES = ("role", "company", "project", "talk")


def _source_kind(domain: str) -> str:
    d = domain.lower()
    if "linkedin" in d:
        return "linkedin"
    if "revel8" in d or "webflow" in d:
        return "company"
    if "podbean" in d or "soundcloud" in d or "podcast" in d:
        return "podcast"
    if "github" in d:
        return "github"
    if "capital" in d or "merantix" in d or "crunchbase" in d or "peak" in d:
        return "investor"
    if "careers" in d or "jobs" in d:
        return "jobs"
    return "web"


def _domain(url: str) -> str:
    net = urlsplit(url).netloc.lower()
    if net.startswith("www."):
        net = net[4:]
    if net.startswith("de.") and "linkedin" in net:
        net = net[3:]
    return net


def _load(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _load_research(target: str) -> list[dict]:
    path = RESEARCH / f"{target}.jsonl"
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def _reliability_index(records: list[dict]) -> dict[str, str]:
    return {r["id"]: r.get("reliability", "unsicher") for r in records if r.get("id")}


def _sources(records: list[dict], max_sources: int = 5) -> list[dict]:
    agg: dict[str, dict] = {}
    for r in records:
        for s in (r.get("sources") or []):
            dom = _domain(s.get("url") or "")
            if not dom:
                continue
            entry = agg.setdefault(dom, {"domain": dom, "kind": _source_kind(dom),
                                         "channel": s.get("channel", ""), "count": 0})
            entry["count"] += 1
    rows = list(agg.values())
    rows.sort(key=lambda e: (e["kind"] != "linkedin", -e["count"]))
    return rows[:max_sources]


def _knowledge(records: list[dict], hook: dict, max_nodes: int = 6) -> list[dict]:
    by_id = {r["id"]: r for r in records if r.get("id")}
    cited = [eid for eid in (hook.get("evidence_ids") or []) if eid in by_id]
    chosen: list[str] = []
    seen: set[str] = set()

    def add(rid: str) -> None:
        if rid in seen or rid not in by_id:
            return
        if by_id[rid].get("category") not in _KG_CATEGORIES:
            return
        seen.add(rid)
        chosen.append(rid)

    for rid in cited:
        add(rid)
    rest = sorted((r for r in records if r.get("category") in _KG_CATEGORIES),
                  key=lambda r: (r.get("reliability") != "belastbar", len(r.get("fact", ""))))
    for cat in _KG_CATEGORIES:
        for r in rest:
            if len(chosen) >= max_nodes:
                break
            if r.get("category") == cat:
                add(r["id"])
                break
    for r in rest:
        if len(chosen) >= max_nodes:
            break
        add(r["id"])
    nodes = []
    for rid in chosen[:max_nodes]:
        r = by_id[rid]
        fact = (r.get("fact") or "").strip()
        nodes.append({"id": rid, "label": fact if len(fact) <= 52 else fact[:51] + "…",
                      "category": r.get("category", "other"),
                      "reliability": r.get("reliability", "unsicher"),
                      "domain": _domain((r.get("sources") or [{}])[0].get("url", "")),
                      "cited": rid in cited})
    return nodes


def _targeting_score(hook: dict, rel_index: dict[str, str]) -> dict | None:
    eids = hook.get("evidence_ids") or []
    rels = [rel_index.get(eid) for eid in eids if eid in rel_index]
    rels = [r for r in rels if r]
    if not rels:
        return None
    confs = [RELIABILITY_CONFIDENCE.get(r, 0.5) for r in rels]
    breakdown: dict[str, int] = {}
    for r in rels:
        breakdown[r] = breakdown.get(r, 0) + 1
    return {"percent": round(100 * sum(confs) / len(confs)), "evidence_count": len(rels),
            "breakdown": breakdown}


def _record_for(tid: str) -> RunRecord | None:
    """Prefer the typed run record; fall back to the raw breach/contact log, normalised."""
    direct = _load(RUNS / f"run_{tid}.json")
    if direct:
        return RunRecord.from_log(direct)
    for name in (f"breach_{tid}.json", f"contact_{tid}.json"):
        raw = _load(RUNS / name)
        if raw:
            return RunRecord.from_log(raw)
    return None


def _thread_from_record(rec: RunRecord) -> list[dict]:
    out = []
    for t in rec.touches:
        dec = t.decision
        out.append({
            "touch": t.index,
            "channel": t.channel,
            "from_name": (t.sender or {}).get("name", ""),
            "from_address": (t.sender or {}).get("address", ""),
            "subject": t.subject or "",
            "body": t.body,
            "reply": t.reply,
            "sent_because": t.sent_because or _sent_because(t),
            "decision": {"action": dec.action, "reason": dec.reason} if dec else None,
            "gate": (t.state_after or {}).get("gate_seen"),
            "incident": t.incident,
            "expected": t.expected_observable,
        })
    return out


def _sent_because(touch) -> str:
    # touches carry sent_because inside the raw contact; RunRecord keeps it on state_after
    # only if the loop set it. Reconstruct a short label from position/silence otherwise.
    if touch.index == 1:
        return "first, cold contact — rapport, no link"
    return "react to their reply / re-engage"


def build() -> dict:
    targets = []
    for tid in TARGETS:
        rec = _record_for(tid)
        sweep = _load(RUNS / f"sweep_{tid}.json")
        if not rec and not sweep:
            continue
        records = _load_research(tid)
        rel_index = _reliability_index(records)
        hook = rec.chosen_hook if rec else {}
        thread = _thread_from_record(rec) if rec else []
        incident = bool(rec and rec.incident)
        targets.append({
            "id": tid,
            "name": NAMES.get(tid, tid),
            "objective": rec.objective if rec else "breach",
            "hook": {"topic": hook.get("topic", ""), "why_now": hook.get("why_now", ""),
                     "channel": hook.get("suggested_channel", "") or hook.get("channel", ""),
                     "angle": hook.get("suggested_angle", "") or hook.get("angle", "")},
            "alternatives": [{"topic": h.get("topic", ""), "why_now": h.get("why_now", "")}
                             for h in (rec.hooks_considered if rec else [])[1:4]],
            "score": _targeting_score(hook, rel_index),
            "sources_seen": _sources(records),
            "knowledge": _knowledge(records, hook),
            "research_count": len(records),
            "thread": thread,
            "sweep": (sweep or {}).get("results", []),
            "outcome": {
                "compromised": incident,
                "incident_type": rec.incident_type if rec else None,
                "touches": rec.contacts_used if rec else (thread[-1]["touch"] if thread else None),
                "touches_to_incident": rec.touches_to_incident if rec else None,
                "stop_reason": rec.stop_reason if rec else "",
            },
        })

    compromised = [t["id"] for t in targets if t["outcome"]["compromised"]]
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "model": "DeepSeek-V4-Flash · AMD Token Factory",
        "pipeline": PIPELINE,
        "scenario": "revel8 practice — consenting AI twins (authorized simulation)",
        "summary": {"targets_total": len(targets), "compromised": len(compromised),
                    "compromised_ids": compromised},
        "targets": targets,
    }


def embed(payload: dict) -> bool:
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
    INDEX.write_text(html[: i + len(start)] + "\n" + blob + "\n" + html[j:], encoding="utf-8")
    return True


def main() -> None:
    payload = build()
    DATA_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    embedded = embed(payload)
    print(f"targets: {payload['summary']['targets_total']} | "
          f"incidents: {payload['summary']['compromised']} {payload['summary']['compromised_ids']}")
    print(f"wrote {DATA_JSON.relative_to(ROOT)}")
    print("embedded into dashboard/index.html" if embedded
          else "WARN: run-data marker missing in index.html")


if __name__ == "__main__":
    main()
