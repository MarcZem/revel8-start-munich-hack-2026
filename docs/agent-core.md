# Local Agent Core Prototype

This prototype implements Issue #2 with deterministic model stubs. It has no real channels, no real people, no real domains, no secrets, and no network effects.

## Components

- `agent_core/schema.py`: JSON-ready contracts for the knowledge graph, routed context, committee outputs, evaluator verdicts, fake API events, strategy updates, and run logs.
- `agent_core/fixtures.py`: synthetic persona graphs for `lena_kraus`, `max_rieder`, and `sara_neumann`.
- `agent_core/context_router.py`: loads only safe, relevant graph paths above the confidence threshold.
- `agent_core/evidence_ranker.py`: deterministically scores evidence by context-tag overlap, confidence, source reliability, and freshness at an explicit timezone-aware `as_of`; unsafe, irrelevant, stale, future-dated, low-quality, or contradictory evidence is ineligible by default.
- `agent_core/context_packet.py`: builds a deterministic, ranked, token-bounded writer packet with source, observation date, confidence, reliability, and uncertainty notes; excluded evidence and ranking scores stay in the orchestrator audit.
- `agent_core/model_committee.py`: advisor, writer, and critic interfaces plus deterministic stubs for `smd20/socialengineering`, `Qwen/Qwen3-14B`, and `Foundation-Sec-8B`. The Writer protocol accepts only a `ContextPacket`, never the graph.
- `agent_core/evaluator.py`: code-level gate for wrong facts, unrouted evidence, rule breaks, prompt injection, real-domain misuse, generic tone, channel fit, and disqualification risk.
- `agent_core/challenge_api.py`: fake challenge API that records would-send actions in memory and returns deterministic simulated events.
- `agent_core/orchestrator.py`: end-to-end loop from graph to route to committee to gate to fake event to strategy update.
- `dashboard/render_replay.py`: creates a standalone jury replay HTML page from a run log.

## Run

```powershell
python .\scripts\run_agent_core.py --persona lena_kraus --out runs\latest_agent_core_run.json
```

Expected output:

```text
run_id=run_lena_kraus_stub_001
winner_candidate_id=msg_001_safe
event_type=fake_link_opened
run_log=runs\latest_agent_core_run.json
```

## Test

```powershell
python -m unittest discover -s tests
```

## Safety Boundaries

- The fake API never calls a network endpoint.
- The writer receives only a token-bounded `ContextPacket`, not the graph or exclusion/ranking audit. The packet contains cited descriptions, source, observed date, confidence, reliability, and uncertainty notes.
- The replay shows the exact writer packet and separately lists ranked exclusions and reasons. The default byte-based token counter is a conservative upper bound; production model adapters should inject their tokenizer's exact counter.
- The evaluator fails closed on prompt-injection phrases, credential/secret requests, unknown channels, unrouted evidence, and non-fake domains.
- Stub messages use only `.example`, `.test`, or `.invalid` URLs.
- Low-confidence or unsafe evidence is present in the graph but excluded from routed context.
- Evidence ranking uses fixed weights (relevance 0.35, confidence 0.25, source reliability 0.20, freshness 0.20) and a 180-day freshness half-life; the one-year stale cutoff and quality thresholds are configurable. Conflicts are excluded symmetrically until resolved.
