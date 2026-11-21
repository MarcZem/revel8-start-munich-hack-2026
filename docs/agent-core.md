# Local Agent Core Prototype

This prototype implements Issue #2 with deterministic model stubs. It has no real channels, no real people, no real domains, no secrets, and no network effects. Synthetic evaluation is isolated from the Revel8 target API and does not use its key.

## Components

- `agent_core/schema.py`: JSON-ready contracts for the knowledge graph, routed context, committee outputs, evaluator verdicts, fake API events, strategy updates, and run logs.
- `agent_core/fixtures.py`: synthetic persona graphs for `lena_kraus`, `max_rieder`, and `sara_neumann`.
- `agent_core/context_router.py`: loads only safe, relevant graph paths above the confidence threshold.
- `agent_core/model_committee.py`: advisor, writer, and critic interfaces plus deterministic stubs for `smd20/socialengineering`, `Qwen/Qwen3-14B`, and `Foundation-Sec-8B`.
- `agent_core/evaluator.py`: code-level gate for wrong facts, unrouted evidence, rule breaks, prompt injection, real-domain misuse, generic tone, channel fit, and disqualification risk.
- `agent_core/challenge_api.py`: fake challenge API that records would-send actions in memory and returns deterministic simulated events.
- `agent_core/orchestrator.py`: end-to-end loop from graph to route to committee to gate to fake event to strategy update.
- `evals/cases.jsonl`: synthetic cases for all three personas, pushback, wrong facts, rule breaks, context routing, safety, committee selection, critic override, and feedback export.
- `evals/runner.py`: deterministic evaluator; the `FakeChallengeAPI` is the only adapter used by this suite.
- `evals/report.json`: latest case-by-case report. `evals/feedback.jsonl` contains minimized preference metadata and IDs, not message text.
- `RETRO.md`: findings and remaining risks for the eval harness.

## Run

```sh
python3 scripts/run_agent_core.py --persona lena_kraus --out runs/latest_agent_core_run.json
```

Expected output:

```text
run_id=run_lena_kraus_stub_001
winner_candidate_id=msg_001_safe
event_type=fake_link_opened
run_log=runs\latest_agent_core_run.json
```

## Test

```sh
python3 -m unittest discover -s tests
```

Run the eval suite and refresh its report/export:

```sh
python3 -m evals.run_evals
```

The suite covers normal runs for each fictional persona; explicit pushback; unsupported facts; prompt injection and rule-break domains; context routing; fail-closed handling of irreversible or external effects; model committee selection; deterministic critic-gate authority; and minimized synthetic feedback export. A passing report is local regression evidence only, not a live API or scoring result.

## Safety Boundaries

- The fake API never calls a network endpoint.
- The writer receives only `RoutedContext.allowed_evidence_ids`, not the full graph.
- The evaluator fails closed on prompt-injection phrases, credential/secret requests, unknown channels, unrouted evidence, and non-fake domains.
- Candidates marked as causing irreversible actions or external effects are blocked; if every candidate is blocked, the orchestrator stops without calling even the fake adapter.
- Stub messages use only `.example`, `.test`, or `.invalid` URLs.
- Low-confidence or unsafe evidence is present in the graph but excluded from routed context.
