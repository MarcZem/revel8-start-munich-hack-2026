# Model Committee for the Revel8 Simulation

> Optional model architecture for the current leading proposal in [`codex-agent-architecture-proposal.md`](codex-agent-architecture-proposal.md). The official case brief, API documentation, and scoring rubric take precedence. A committee is an implementation choice, not a challenge requirement.

## Purpose

Use a small set of model roles to improve evidence handling, API-payload quality, and run continuity without making live fine-tuning a dependency. The committee must follow the same challenge boundary as the orchestrator: all scored interactions go through the Revel8 API, and the agent operates without human edits or approvals during a scoring run.

The committee should help the jury understand the architecture and the system's decisions. Avoid adding agents solely to increase the count of components.

## Recommended roles

### Evidence synthesizer

Input: sourced facts from the research graph. Output: a compact, cited context packet with confidence, freshness, contradictions, and excluded facts. It must not invent missing information or treat private target labels as observable.

### Contact planner

Input: current run/session state, contact budget, API-returned replies/events, and the approved context packet. Output: a structured next-step plan, or a stop decision. It follows the API session/contact mapping and does not rely on information the API has not returned.

### Channel composer

Input: the plan, cited evidence, and the selected API channel schema. Output: a schema-valid contact payload and, where required, the landing-page content to submit through the API. It does not call external channels or host content.

### Independent evaluators

Run evaluators automatically before API submission. Their output is a structured assessment, not a manual approval request.

- **Evidence evaluator:** checks that target-specific factual claims map to evidence IDs and flags contradictions or stale facts.
- **Schema evaluator:** validates the channel payload against the API contract.
- **Fair-play evaluator:** checks the challenge rules: no real external contact, no real organization's own domain, no real malware, and no prompt injection or attempts to change the target's instructions.
- **Continuity evaluator:** checks that the next turn is consistent with the recorded replies, events, and session state.

A deterministic code-level validator has final authority to block an invalid API call. During scored runs, the orchestrator acts autonomously: it repairs, replans, or stops without asking a person to approve a message.

## Committee flow

```text
Evidence graph
  → context synthesizer
  → run planner
  → channel composer
  → evidence / schema / fair-play / continuity evaluators
  → deterministic validator
  → Revel8 API adapter
  → normalized reply, event, silence, or error
  → persisted run state
  → next autonomous plan or stop
```

Use one writer/composer by default. Candidate generation and reranking can be added only if local evaluation shows a measurable benefit and the scoring-run decision remains autonomous.

## Structured records

The following are internal records. The API's documented field names remain authoritative.

### Evaluator result

```json
{
  "contact_id": "...",
  "checks": {
    "evidence_supported": true,
    "channel_schema_valid": true,
    "fair_play_valid": true,
    "session_consistent": true
  },
  "flags": [],
  "decision": "submit|repair|stop",
  "summary": "Short, user-visible reason"
}
```

### Run feedback record

```json
{
  "run_id": "...",
  "target_id": "...",
  "session_id": "...",
  "contact_index": 1,
  "context_fact_ids": ["..."],
  "composer_model": "...",
  "evaluator_results": [],
  "api_outcome": "reply|event|silence|error",
  "normalized_events": [],
  "next_decision": "continue|replan|stop"
}
```

Keep secrets out of these records. Store only information needed to replay the simulation and diagnose failures; the Revel8 API is authoritative for recorded and rendered scoring turns.

## Run modes and exact challenge fit

- **Practice:** unlimited sessions against the three founder AI twins. Use practice to check API behavior, session semantics, supported payloads, persistence, and evaluator reliability.
- **Scoring:** three independent runs of ten contacts each against new AI-twin targets. The exact times are announced at kickoff. The agent chooses, writes, sends, and continues/stops without human intervention.
- **Session mapping:** the brief says a session is one exchange and a new session is a clean slate. Read the API docs before deciding whether a contact creates a session or continues one. Persist session IDs exactly.
- **Feedback:** adapt only to replies and events returned during the run. The target's susceptible-topic annotations are private; do not assume the committee can inspect them. Use official scoring feedback after the run where available.
- **Landing pages:** submit link and page content through the API; do not host a page.
- **Channel rendering:** use the API's supported channel schemas and rendered output. Do not add live integrations with external channels.

## How this maps to the rubric

| Rubric | Committee contribution |
| --- | --- |
| Results (25) | Reliable API payloads, event normalization, and accurate incident/contact logging. |
| Targeting (10) | Evidence-backed context selection and a record of which facts were used; private topic labels remain an API scoring signal, not a prompt input. |
| Craft (10) | Schema-correct payloads and a preview based on the API representation; the API's scoring render is authoritative. |
| Architecture & Persistence (40) | Clear responsibilities, durable run state, autonomous re-planning, evaluator outputs, and replayable decisions. |
| Pitch & Demo (15) | Show the committee as part of one real run thread; explain what each role contributes without spending the pitch listing models. |

Wrong facts can cost up to five points. The evidence evaluator should therefore reject or flag unsupported target facts before submission. The official formula for each measured score is in [`revel8-official-challenge.md`](revel8-official-challenge.md).

## Model selection and training

The case allows any model, framework, or tool. Select models only after checking availability on the team's chosen runtime, structured-output quality, latency, licensing, and cost. Local inference on AMD hardware may be tested if the team has access, but it is not an official requirement.

Do not fine-tune during the scoring window. First establish a deterministic baseline, API adapter, run persistence, and evals. Use authorized practice-run records and fictional fixtures for offline evaluation. Treat the official scoring run as an evaluation set; do not alter prompts or model weights manually during it.

## Evaluation plan

Use local fixtures and practice sessions to check:

- Evidence records preserve source, date, confidence, and contradictions.
- Context synthesis excludes irrelevant or low-confidence facts.
- Session IDs and memory follow API documentation; independent runs do not leak state into each other.
- The API adapter handles replies, events, silence, rate limits, and errors.
- The run controller never exceeds ten contacts in a scoring run.
- Evaluators flag unsupported facts, invalid channel payloads, rule violations, and discontinuity.
- The scored mode has no manual message approval or edit step.
- Logs distinguish observed API responses from private official scoring labels.

Keep development measurements separate from official scoring. The official rubric uses 45 API-measured points and 55 jury points, with medians across three runs where specified.

## Hackathon priority

Build in this order:

1. One API/mock adapter contract and persistent run record.
2. Session/contact semantics and the ten-contact run controller.
3. Evidence synthesizer plus deterministic schema and fair-play validators.
4. One composer and a reliable event-driven feedback loop.
5. Replay UI and the one-page architecture hand-in.
6. Optional model committee/reranking only after the end-to-end path is stable.

The committee is successful if it makes one real scoring thread more reliable and easier to explain. It is not successful merely because it contains several models.
