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
from urllib.parse import urlsplit

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
# Recon sources feed Research, which builds the Knowledge Graph; the Orchestrator
# picks the angle and drives the Writer -> Twin loop (Critic adapts each turn).
PIPELINE = [
    {"id": "linkedin", "label": "LinkedIn", "role": "profile + activity (first stop)", "kind": "source"},
    {"id": "company", "label": "Company site", "role": "revel8.ai / webflow", "kind": "source"},
    {"id": "web", "label": "Web & press", "role": "podcasts, investors, talks", "kind": "source"},
    {"id": "research", "label": "Research", "role": "OSINT extraction -> atomic facts"},
    {"id": "knowledge", "label": "Knowledge Graph", "role": "facts ranked by reliability"},
    {"id": "orchestrator", "label": "Orchestrator", "role": "picks the angle, drives the loop"},
    {"id": "writer", "label": "Writer", "role": "crafts the message in a pinned persona"},
    {"id": "twin", "label": "Target Twin", "role": "revel8 Personal Interface (the AI twin)"},
    {"id": "critic", "label": "Critic", "role": "reads each reply: continue / switch / stop"},
]

# Classify a source domain into the kind of page the agent visited.
def _source_kind(domain: str) -> str:
    d = domain.lower()
    if "linkedin" in d:
        return "linkedin"
    if "revel8" in d or "webflow" in d:
        return "company"
    if "podbean" in d or "soundcloud" in d or "podcast" in d or "podcasts" in d:
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


# Only these categories go into the published knowledge graph: public,
# professional facts. 'network'/'other' (personal ties, noise) stay out.
_KG_CATEGORIES = ("role", "company", "project", "talk")


def _load(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _load_research(target: str) -> list[dict]:
    """All findings for a target, read locally (never shipped raw)."""
    path = RESEARCH / f"{target}.jsonl"
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def _reliability_index(records: list[dict]) -> dict[str, str]:
    return {r["id"]: r.get("reliability", "unsicher") for r in records if r.get("id")}


def _sources(records: list[dict], max_sources: int = 8) -> list[dict]:
    """Distinct source domains the agent visited — LinkedIn first, then by volume.

    Domains only (no paths/query), so no per-person URL detail ships.
    """
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
    # LinkedIn (recon entry point) first, then most-cited domains.
    rows.sort(key=lambda e: (e["kind"] != "linkedin", -e["count"]))
    return rows[:max_sources]


def _knowledge(records: list[dict], hook: dict, max_nodes: int = 9) -> list[dict]:
    """A rough knowledge graph of key, public professional facts.

    Cited-evidence facts first (what the angle was built on), then one per
    category for breadth. Only professional categories; labels truncated.
    """
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
    # breadth: fill with one fact per category, preferring belastbar then shorter facts
    rest = sorted(
        (r for r in records if r.get("category") in _KG_CATEGORIES),
        key=lambda r: (r.get("reliability") != "belastbar", len(r.get("fact", ""))),
    )
    for cat in _KG_CATEGORIES:
        for r in rest:
            if len(chosen) >= max_nodes:
                break
            if r.get("category") == cat:
                add(r["id"])
                break
    for r in rest:  # top up if still short
        if len(chosen) >= max_nodes:
            break
        add(r["id"])

    nodes = []
    for rid in chosen[:max_nodes]:
        r = by_id[rid]
        fact = (r.get("fact") or "").strip()
        nodes.append({
            "id": rid,
            "label": fact if len(fact) <= 52 else fact[:51] + "…",
            "category": r.get("category", "other"),
            "reliability": r.get("reliability", "unsicher"),
            "domain": _domain((r.get("sources") or [{}])[0].get("url", "")),
            "cited": rid in cited,
        })
    return nodes


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
        records = _load_research(tid)
        rel_index = _reliability_index(records)
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
                "sources_seen": _sources(records),
                "knowledge": _knowledge(records, hook),
                "research_count": len(records),
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
