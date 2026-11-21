"""Render a self-contained, local-only HTML replay from an agent-core JSON log."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="theme-color" content="#101c2d">
  <title>Run replay · @@PERSONA@@</title>
  <style>
    :root{color-scheme:light;--ink:#172438;--muted:#617086;--line:#dbe3ed;--panel:#fff;--canvas:#f2f5f8;--navy:#101c2d;--blue:#315b8c;--teal:#087e78;--amber:#c57918;--red:#b83d4a;--green:#18765f}
    *{box-sizing:border-box}body{margin:0;background:var(--canvas);color:var(--ink);font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
    button{font:inherit}.topbar{background:var(--navy);color:#fff;padding:26px max(24px,calc((100vw - 1180px)/2));display:flex;justify-content:space-between;gap:24px;align-items:center}.brand{font-size:13px;text-transform:uppercase;letter-spacing:.14em;color:#a8bad0}.topbar h1{margin:5px 0 0;font-size:27px;line-height:1.2}.topbar p{margin:7px 0 0;color:#c2cedb}.tools{display:flex;align-items:center;gap:12px;flex-wrap:wrap;justify-content:flex-end}.pitch-button{border:1px solid #8194a9;background:#fff;color:var(--navy);padding:10px 14px;border-radius:8px;font-weight:700;cursor:pointer}.pitch-count{min-width:92px;color:#d6e1ec;font-size:13px}.layout{max-width:1180px;margin:24px auto 64px;padding:0 20px}.simulation-banner{display:flex;align-items:center;gap:10px;background:#e8f3f2;border:1px solid #c5e0dd;color:#145a57;padding:11px 14px;border-radius:10px;margin-bottom:16px;font-weight:650}.dot{width:9px;height:9px;border-radius:50%;background:var(--teal);flex:none}.summary{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin-bottom:16px}.metric,.panel{background:var(--panel);border:1px solid var(--line);border-radius:12px;box-shadow:0 2px 8px #20324a08}.metric{padding:14px 16px}.metric-label{color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:.08em}.metric-value{font-size:17px;font-weight:700;margin-top:4px;overflow-wrap:anywhere}.columns{display:grid;grid-template-columns:minmax(0,1.15fr) minmax(330px,.85fr);gap:16px;align-items:start}.stack{display:grid;gap:16px}.panel{padding:20px}.panel h2{font-size:17px;margin:0 0 4px}.panel-intro{margin:0 0 16px;color:var(--muted);font-size:13px}.pitch-step{transition:opacity .2s,filter .2s}.pitch-active .pitch-step.pitch-hidden{display:none}.pitch-active .pitch-step.pitch-current{outline:3px solid #90b9e2;outline-offset:3px}
    .timeline{display:grid;grid-template-columns:repeat(6,minmax(100px,1fr));gap:7px;overflow-x:auto;padding:8px 2px 4px}.timeline-item{position:relative;padding:10px;background:#f6f8fb;border:1px solid var(--line);border-radius:9px;min-height:91px}.timeline-item:before{content:attr(data-step);display:grid;place-items:center;width:22px;height:22px;border-radius:50%;background:#dce8f5;color:var(--blue);font-weight:750;font-size:12px;margin-bottom:7px}.timeline-label{font-size:12px;font-weight:700;line-height:1.3}.timeline-detail{font-size:11px;color:var(--muted);margin-top:4px;overflow-wrap:anywhere}
    .evidence-list,.path-list,.verdict-list{display:grid;gap:10px}.evidence{padding:12px;border:1px solid var(--line);border-radius:9px}.evidence-head{display:flex;justify-content:space-between;gap:12px;align-items:center}.evidence-title{font-weight:700}.confidence{font-variant-numeric:tabular-nums;color:var(--blue);font-weight:750}.bar{height:5px;border-radius:6px;background:#e7edf3;margin:8px 0}.bar span{display:block;height:100%;background:var(--teal);border-radius:6px}.meta{color:var(--muted);font-size:12px}.evidence p{margin:6px 0 0}.path{border-left:3px solid #83aaa9;padding:2px 0 4px 11px}.path-title{font-weight:650}.chips{display:flex;gap:6px;flex-wrap:wrap;margin-top:7px}.chip{background:#edf2f7;border-radius:99px;padding:3px 8px;color:#4c5b6c;font-size:11px}.message{background:#f9fbfd;border:1px solid var(--line);border-radius:10px;overflow:hidden}.mail-head{padding:12px 15px;border-bottom:1px solid var(--line);font-size:13px;color:#526177}.mail-head strong{color:var(--ink)}.mail-subject{padding:13px 15px 0;font-weight:750}.mail-body{padding:12px 15px 16px;white-space:pre-wrap}.mail-link{padding:10px 15px;border-top:1px solid var(--line);font-size:13px;color:var(--blue);overflow-wrap:anywhere}.status{display:inline-flex;align-items:center;gap:6px;padding:4px 9px;border-radius:99px;font-size:12px;font-weight:750;text-transform:uppercase;letter-spacing:.04em}.status-send{color:#14674f;background:#e4f3ed}.status-block{color:#9a2938;background:#fbe9eb}.verdict{border:1px solid var(--line);border-radius:9px;padding:11px 12px}.verdict-top{display:flex;justify-content:space-between;gap:12px;align-items:center}.verdict-reasons{margin:8px 0 0;padding-left:18px;color:#903747;font-size:12px}.event-box{border-left:4px solid var(--teal);background:#f0f8f7;padding:14px;border-radius:0 9px 9px 0}.event-name{font-weight:750;color:#155b56}.event-reply{margin:8px 0 0}.event-meta{font-size:12px;color:var(--muted);margin-top:7px}.decision{background:#f7f9fc;border:1px solid var(--line);padding:13px;border-radius:9px}.decision-score{display:flex;gap:8px;align-items:baseline;margin-bottom:6px}.decision-score strong{font-size:24px}.footnote{color:var(--muted);font-size:12px;margin:18px 2px 0}.empty{color:var(--muted);font-style:italic}
    @media(max-width:850px){.columns{grid-template-columns:1fr}.summary{grid-template-columns:repeat(2,minmax(0,1fr))}.timeline{grid-template-columns:repeat(6,130px)}}@media(max-width:560px){.topbar{align-items:flex-start;flex-direction:column;padding:22px 20px}.tools{justify-content:flex-start}.layout{margin-top:16px}.summary{gap:8px}.metric{padding:12px}.panel{padding:16px}.topbar h1{font-size:23px}}
  </style>
</head>
<body>
  <header class="topbar">
    <div><div class="brand">revel8 · Agent Run Replay</div><h1>@@PERSONA@@</h1><p>@@RUN_ID@@ · @@OBJECTIVE@@ objective</p></div>
    <div class="tools"><span class="pitch-count" id="pitch-count" aria-live="polite"></span><button class="pitch-button" id="pitch-toggle" type="button">Start pitch replay</button></div>
  </header>
  <main class="layout">
    <div class="simulation-banner"><span class="dot"></span>Synthetic local simulation · Fake API only · Not an official Revel8 practice or scoring run</div>
    <section class="summary" aria-label="Run summary">
      <div class="metric"><div class="metric-label">Run</div><div class="metric-value">@@RUN_ID@@</div></div>
      <div class="metric"><div class="metric-label">Objective</div><div class="metric-value">@@OBJECTIVE@@</div></div>
      <div class="metric"><div class="metric-label">Simulated event</div><div class="metric-value">@@EVENT_TYPE@@</div></div>
      <div class="metric"><div class="metric-label">Strategy signal</div><div class="metric-value">@@SIGNAL@@</div></div>
    </section>
    <section class="panel" style="margin-bottom:16px" aria-labelledby="timeline-title">
      <h2 id="timeline-title">Run timeline</h2><p class="panel-intro">Each step is taken from the structured run log.</p>
      <div class="timeline">@@TIMELINE@@</div>
    </section>
    <div class="columns">
      <div class="stack">
        <section class="panel pitch-step" data-pitch-step="0"><h2>1 · Evidence and confidence</h2><p class="panel-intro">Facts available to this synthetic run, with source and confidence.</p>@@EVIDENCE@@</section>
        <section class="panel pitch-step" data-pitch-step="1"><h2>2 · Context sent to the writer</h2><p class="panel-intro">Only selected paths and evidence IDs are included in the routed context. @@EXCLUDED_COUNT@@ evidence item(s) excluded.</p>@@PATHS@@</section>
        <section class="panel pitch-step" data-pitch-step="2"><h2>3 · Selected message preview</h2><p class="panel-intro">Preview of the winning synthetic candidate. Blocked candidate bodies are never shown.</p>@@MESSAGE@@</section>
      </div>
      <div class="stack">
        <section class="panel pitch-step" data-pitch-step="3"><h2>Evaluator verdicts</h2><p class="panel-intro">Code-level gate results for committee candidates.</p><div class="verdict-list">@@VERDICTS@@</div></section>
        <section class="panel pitch-step" data-pitch-step="4"><h2>4 · Fake API response</h2><p class="panel-intro">The local adapter records simulated replies and events without network effects.</p>@@EVENT@@</section>
        <section class="panel pitch-step" data-pitch-step="5"><h2>5 · Next-step decision</h2><p class="panel-intro">Feedback saved to the run record.</p>@@DECISION@@</section>
      </div>
    </div>
    <p class="footnote">Replay source: @@SOURCE@@ · No real contacts, channels, pages, or API requests were used.</p>
  </main>
  <script>
    (()=>{const button=document.getElementById('pitch-toggle');const count=document.getElementById('pitch-count');const steps=[...document.querySelectorAll('[data-pitch-step]')];let active=false,index=-1;function paint(){document.body.classList.toggle('pitch-active',active);steps.forEach((el,i)=>{el.classList.toggle('pitch-current',active&&i===index);el.classList.toggle('pitch-hidden',active&&i!==index)});if(!active){button.textContent='Start pitch replay';count.textContent='';return}count.textContent=`Step ${index+1} of ${steps.length}`;button.textContent=index===steps.length-1?'Finish replay':'Next step'}button.addEventListener('click',()=>{if(!active){active=true;index=0}else if(index<steps.length-1){index+=1}else{active=false;index=-1}paint()})})();
  </script>
</body>
</html>
"""


def _esc(value: Any) -> str:
    return html.escape(str(value if value is not None else ""), quote=True)


def _confidence(value: Any) -> float:
    try:
        return max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return 0.0


def _evidence_html(run: dict[str, Any], allowed: set[str]) -> str:
    evidence = run.get("graph", {}).get("evidence", {})
    rows = []
    for item in sorted(evidence.values(), key=lambda row: row.get("id", "")):
        evidence_id = item.get("id", "unknown")
        confidence = _confidence(item.get("confidence"))
        state = "Selected" if evidence_id in allowed else "Excluded"
        rows.append(
            '<article class="evidence">'
            f'<div class="evidence-head"><span class="evidence-title">{_esc(evidence_id)}</span>'
            f'<span class="confidence">{confidence:.0%} · {state}</span></div>'
            f'<div class="bar" aria-label="Confidence {confidence:.0%}"><span style="width:{confidence * 100:.1f}%"></span></div>'
            f'<div class="meta">Source: {_esc(item.get("source", "unknown"))} · Observed: {_esc(item.get("observed_at", "not recorded"))}</div>'
            f'<p>{_esc(item.get("description", ""))}</p></article>'
        )
    return '<div class="evidence-list">' + "".join(rows) + "</div>" if rows else '<p class="empty">No evidence in this run.</p>'


def _paths_html(run: dict[str, Any]) -> str:
    paths = run.get("routed_context", {}).get("loaded_paths", [])
    rows = []
    for path in paths:
        confidence = _confidence(path.get("confidence"))
        ids = ", ".join(path.get("evidence_ids", [])) or "No evidence IDs"
        tags = "".join(f'<span class="chip">{_esc(tag)}</span>' for tag in path.get("relevance_tags", []))
        rows.append(
            '<article class="path">'
            f'<div class="path-title">{_esc(path.get("summary", path.get("id", "Path")))}</div>'
            f'<div class="meta">Confidence {confidence:.0%} · Evidence: {_esc(ids)}</div>'
            f'<div class="chips">{tags}</div></article>'
        )
    return '<div class="path-list">' + "".join(rows) + "</div>" if rows else '<p class="empty">No context paths were loaded.</p>'


def _message_html(run: dict[str, Any]) -> str:
    decision = run.get("committee_decision", {})
    winner_id = decision.get("winner_candidate_id")
    candidate = next((item for item in decision.get("candidates", []) if item.get("id") == winner_id), None)
    if not candidate:
        return '<p class="empty">No candidate passed the evaluator gate.</p>'
    url = candidate.get("landing_page_url", "")
    safe_url = _esc(url)
    return (
        '<div class="message">'
        f'<div class="mail-head"><strong>Channel:</strong> {_esc(candidate.get("channel", "unknown"))}'
        f' &nbsp; <strong>Sender type:</strong> {_esc(candidate.get("sender_type", "unknown"))}</div>'
        f'<div class="mail-subject">{_esc(candidate.get("subject", "(no subject)"))}</div>'
        f'<div class="mail-body">{_esc(candidate.get("body", ""))}</div>'
        f'<div class="mail-link">Simulated destination: {safe_url}</div></div>'
    )


def _verdicts_html(run: dict[str, Any]) -> str:
    decision = run.get("committee_decision", {})
    scores = {item.get("candidate_id"): item for item in decision.get("critic_scores", [])}
    rows = []
    for verdict in decision.get("gate_verdicts", []):
        status = verdict.get("decision", "unknown")
        status_class = "status-send" if status == "send" else "status-block"
        score = scores.get(verdict.get("candidate_id"), {}).get("scores", {})
        reason_html = "".join(f"<li>{_esc(reason)}</li>" for reason in verdict.get("blocked_reasons", []))
        reason_html = f'<ul class="verdict-reasons">{reason_html}</ul>' if reason_html else '<div class="meta">No blocking reasons.</div>'
        score_label = f"Critic utility {verdict.get('score', 0)}"
        rows.append(
            f'<article class="verdict"><div class="verdict-top"><strong>{_esc(verdict.get("candidate_id", "unknown"))}</strong>'
            f'<span class="status {status_class}">{_esc(status)}</span></div>'
            f'<div class="meta">{_esc(score_label)} · rule compliance { _esc(score.get("rule_compliance", "—")) }/5 · evidence fidelity {_esc(score.get("evidence_fidelity", "—"))}/5</div>'
            f'{reason_html}</article>'
        )
    return "".join(rows) if rows else '<p class="empty">No verdicts recorded.</p>'


def _event_html(run: dict[str, Any]) -> str:
    event = run.get("api_event")
    if not event:
        return '<p class="empty">No simulated event was produced; the run stopped before adapter submission.</p>'
    return (
        '<div class="event-box">'
        f'<div class="event-name">{_esc(event.get("event_type", "event"))}</div>'
        f'<div class="event-reply">{_esc(event.get("reply", "(no reply)"))}</div>'
        f'<div class="event-meta">Event ID: {_esc(event.get("id", "unknown"))} · Signal: {_esc(event.get("signal_score", "—"))} · Simulated: {"yes" if event.get("simulated", False) else "no"}</div>'
        '</div>'
    )


def _timeline_html(run: dict[str, Any]) -> str:
    labels = {
        "graph_loaded": "Research graph",
        "context_routed": "Context routed",
        "committee_scored": "Committee",
        "evaluator_gate": "Evaluator gate",
        "fake_api_event": "Fake API event",
        "strategy_update": "Next decision",
    }
    rows = []
    for item in sorted(run.get("timeline", []), key=lambda row: row.get("step", 0)):
        event_type = item.get("type", "step")
        detail = item.get("summary") or item.get("event_type") or item.get("winner_candidate_id")
        if event_type == "evaluator_gate":
            detail = ", ".join(item.get("verdicts", []))
        if event_type == "strategy_update":
            detail = run.get("strategy_update", {}).get("lesson", "strategy updated")
        rows.append(
            f'<div class="timeline-item" data-step="{_esc(item.get("step", "·"))}">'
            f'<div class="timeline-label">{_esc(labels.get(event_type, event_type))}</div>'
            f'<div class="timeline-detail">{_esc(detail or "Recorded")}</div></div>'
        )
    return "".join(rows) if rows else '<p class="empty">No timeline steps in this run.</p>'


def render_replay(run: dict[str, Any], source: str = "local run log") -> str:
    """Build an escaped, dependency-free HTML replay from a schema-compatible run log."""
    if not isinstance(run, dict):
        raise ValueError("Run log must be a JSON object.")
    graph = run.get("graph", {})
    nodes = graph.get("nodes", {})
    person = next((node.get("label") for node in nodes.values() if node.get("type") == "Person"), "Synthetic persona")
    routed = run.get("routed_context", {})
    allowed = {
        evidence_id
        for path in routed.get("loaded_paths", [])
        for evidence_id in path.get("evidence_ids", [])
    }
    event = run.get("api_event") or {}
    strategy = run.get("strategy_update") or {}
    values = {
        "PERSONA": _esc(person),
        "RUN_ID": _esc(run.get("run_id", "unknown_run")),
        "OBJECTIVE": _esc(routed.get("objective", "unknown")),
        "EVENT_TYPE": _esc(event.get("event_type", "none")),
        "SIGNAL": _esc(strategy.get("event_signal", "—")),
        "TIMELINE": _timeline_html(run),
        "EVIDENCE": _evidence_html(run, allowed),
        "EXCLUDED_COUNT": _esc(len(routed.get("excluded_evidence_ids", []))),
        "PATHS": _paths_html(run),
        "MESSAGE": _message_html(run),
        "VERDICTS": _verdicts_html(run),
        "EVENT": _event_html(run),
        "DECISION": (
            '<div class="decision"><div class="decision-score"><strong>'
            f'{_esc(strategy.get("updated_score", "—"))}</strong><span class="meta">updated strategy score</span></div>'
            f'<div>{_esc(strategy.get("lesson", "No next-step decision recorded."))}</div>'
            f'<div class="meta">Angle: {_esc(strategy.get("angle_id", "unknown"))} · Wrong-fact penalty: {_esc(strategy.get("wrong_fact_penalty", 0))}</div></div>'
        ),
        "SOURCE": _esc(source),
    }
    output = TEMPLATE
    for key, value in values.items():
        output = output.replace(f"@@{key}@@", value)
    return output


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=ROOT / "runs" / "latest_agent_core_run.json")
    parser.add_argument("--output", type=Path, default=ROOT / "dashboard" / "replay.html")
    args = parser.parse_args(argv)
    run = json.loads(args.input.read_text(encoding="utf-8"))
    html_document = render_replay(run, source=str(args.input))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(html_document, encoding="utf-8")
    print(f"replay={args.output}")
    print(f"run_id={run.get('run_id', 'unknown_run')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
