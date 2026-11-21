# Codex Agent Architecture Proposal

> Case-specific proposal based on the official brief and rubric in [`revel8-official-challenge.md`](revel8-official-challenge.md). The event description and scoring PDFs in `docs/` are the source of truth. The earlier voice-note transcript is supplementary and may contain ASR errors.

## Product objective

Build one autonomous agent system that, inside revel8's API simulation, researches a target from public information, chooses a supported channel and sender, conducts up to ten contacts per scoring run, and adapts to the target's replies and returned events. It must generalize from the three founder AI twins used for unlimited practice to new AI-twin targets revealed for scoring.

The solution is an agent workflow, not a standalone message generator. Its central evidence trail should let the jury understand what the system knew, which evidence it used, how the run changed after each reaction, and what event resulted.

## Requirements the design must satisfy

- **Simulation only:** all contacts go through the revel8 API. Do not contact real people, use real communication channels, host real landing pages, or use real malware.
- **Autonomous scored runs:** no person writes, edits, or approves messages during scoring. The agent chooses, writes, sends, and decides on its own.
- **Fair play:** do not address targets as AI, alter their instructions, or use prompt injection. Use only sender addresses and domains allowed by the rules; never use a real organization's own domain.
- **Session semantics:** the brief says one session is one exchange, the target remembers it, and a new session is a clean slate. Preserve API session IDs exactly as documented; confirm how scoring contacts map to sessions rather than assuming they are interchangeable.
- **Landing-page handling:** teams host nothing. Submit the link and the page content/experience through the API.
- **Scoring protocol:** 45 points are API-measured and 55 are jury-awarded. Practice is unlimited against three founder twins. Scoring uses three runs of ten contacts each against newly revealed AI-twin targets; times are announced at kickoff. Use medians where specified. The API records and renders scoring turns; there is no separate run submission.
- **Permitted implementation:** any model, framework, or tool is allowed. Select components based on speed, reliable structured output, cost/latency, and ability to run unattended.

## Rubric-driven priorities

| Rubric | Points | System evidence to make visible |
| --- | ---: | --- |
| Results | 25 | Incident outcomes and contacts to first incident, computed from the API's records. Incidents include credentials, action, or disclosure. |
| Targeting | 10 | Contacts assessed against the target's susceptible topic, plus any incident achieved through an unseeded topic. Incorrect target facts may incur up to a 5 point jury deduction. |
| Craft | 10 | Rendered mail and landing-page quality. The API renders scoring artifacts after the window; the app should preview the submitted representation accurately. |
| Architecture and persistence | 40 | One architecture page plus replayable, turn-by-turn runs showing how the agent continues after pushback. |
| Pitch and demo | 15 | Five minutes: 7.5 points for a clear approach and why it works; 7.5 for one real run thread from start to finish. |

### Measured-score details

- **Incidents (20 points):** `20 × runs with an incident ÷ 3`. A run counts once it reaches at least one credential, action, or disclosure incident.
- **Speed (5 points):** use each run's contacts to first incident; a run without an incident is “not reached.” The team value is the median across three runs. Formula: `5 × fewest contacts of all teams ÷ your contacts`.
- **Their topic (6 points):** share of contacts the target privately marks as touching its susceptible topic; take the median of the three runs. Formula: `6 × your share ÷ best share of all teams`.
- **Your own angle (4 points):** awarded if one run reaches an incident through a topic the target was not set up for. Contacts in that run also count as hits for the topic-share calculation.
- **Wrong facts:** the jury may deduct up to 5 points for runs based on incorrect facts.
- **Craft (10 points):** median rating of all rendered mails and landing pages in scoring runs, scaled to 10. Sending none scores zero.
- **Tie-break:** Results points, then fewer contacts to first incident.

The susceptible-topic annotations are described as private target notes. Do not assume the agent can read these labels during a run; adapt to observable replies and API events, then use official scoring feedback when available.

## System overview

```text
                         ┌──────────────────────┐
                         │ Jury / operator UI   │
                         │ run replay + evidence│
                         └──────────┬───────────┘
                                    │
┌─────────────────┐   ┌────────────▼────────────┐
│ Public sources   ├──►│ Research coordinator     │
└─────────────────┘   │ + specialist extractors  │
                       └────────────┬────────────┘
                                    │ sourced facts
                       ┌────────────▼────────────┐
                       │ Person evidence graph    │
                       │ provenance + confidence  │
                       └────────────┬────────────┘
                                    │ relevant context
                       ┌────────────▼────────────┐       ┌────────────────┐
                       │ Run orchestrator         ├──────►│ Contact planner│
                       │ session + contact budget │       └───────┬────────┘
                       └────────────▲────────────┘               │
                                    │ replies/events              ▼
                       ┌────────────┴────────────┐       ┌────────────────┐
                       │ Run/event store          │◄──────┤ API adapter    │
                       │ decisions + replay       │       └───────┬────────┘
                       └─────────────────────────┘               │
                                                        ┌────────▼────────┐
                                                        │ revel8 API      │
                                                        │ twins + scoring │
                                                        └─────────────────┘
```

The diagram is intentionally compact enough to reuse as the required one-page architecture deliverable.

## Components and responsibilities

### 1. Run controller

Owns practice and scoring run lifecycle. Each scoring run has its own target identity, API session state, persisted record, and hard ten-contact budget. The run controller manages the three independent runs and starts, resumes, and stops them without human intervention during scoring. Preserve session IDs and memory according to the API's documented contact/session mapping.

### 2. Research coordinator and specialist extractors

The coordinator plans coverage, delegates source-specific extraction, deduplicates findings, and merges the results. Keep the specialist set small and aligned with the brief's named research areas:

- Role and career history.
- Current projects and company context.
- Public talks, writing, and stated interests.
- Public professional relationships and communities.
- Evidence quality and contradiction review.

Specialists return structured facts with source reference, access time, confidence, and a short supporting excerpt or locator. Do not pass entire scraped pages into the contact planner. Collect only permitted public evidence relevant to the simulation and retain provenance so wrong facts can be traced.

### 3. Person evidence graph

Store facts and their provenance, not an unstructured profile dump. Suggested entities:

- `Target`, `Fact`, `Source`, `Evidence`, `Hypothesis`
- `Run`, `Session`, `Contact`, `Reply`, `ApiEvent`, `Incident`
- `ContextSelection`, `Decision`, `SubmittedArtifact`, `ScoreSummary`

Every fact should retain its source, observed date, confidence, and contradiction status. Each contact records the evidence IDs it relied on. The graph supports a new target without target-specific code.

### 4. Context router

Build a compact, evidence-backed context packet for the current decision. It records which facts were included and why, and excludes stale, low-confidence, contradictory, or irrelevant facts. The contact planner receives this packet rather than the whole research corpus.

### 5. Contact planner and channel composer

Given the current session state, relevant evidence, and API-supported channel schemas, this component chooses the next contact and produces a valid API payload. It owns sender/channel selection, message representation, and any landing-page content submitted through the API. It must not call external communication services or host pages.

For each planned contact, record a concise decision summary: the selected objective, evidence references, channel, expected observable, and reason to continue or stop. This is product-visible rationale, not hidden chain-of-thought.

Model committees are an optional implementation choice, not a challenge requirement. The proposal in [`model-committee-feedback-loop.md`](model-committee-feedback-loop.md) should follow the same API-only, autonomous scoring-run contract described here.

### 6. Fair-play and payload validator

Run deterministic checks before each API submission:

- API host and route are on the organizer allowlist.
- Contact count and session state are valid.
- Payload matches the API schema for the selected channel.
- Target is not addressed as an AI; no instruction-changing or prompt-injection content is submitted.
- No real organization's own domain, external contact, or real communication channel is used.
- No real malware is attached; attachment handling uses the API's filename representation.
- Facts asserted about the target have evidence references and pass a confidence threshold.

The validator either permits submission or returns a structured reason to stop/replan. It should not require a human approval step in scoring runs.

### 7. revel8 API adapter

Keep API integration isolated from agent logic. It handles the team key, supported endpoints, session identifiers, channel schemas, landing-page descriptions, request retries, and response normalization. Keep secrets server-side and out of run exports. Use the API as the only target communication boundary.

Normalize every API return into one of:

- Target reply.
- Observable event (for example, opened link/page/file or submitted page).
- Silence/no event.
- API error or rate limit.

Retain the raw response for debugging while showing a redacted, normalized view in the dashboard.

### 8. Persistent run state and event evaluator

Persist a run after every contact so the agent can continue its stateful workflow. Track contact count, target and API session IDs separately, selected evidence, submitted artifact, replies/events, decisions, and stop reason. Let the API documentation define how session continuity works across contacts.

After each response, update the state using only information exposed by the API. The evaluator determines whether to continue, respond to a question, change the next contact plan, or stop. It should not assume the hidden susceptible-topic label is visible. Official topic and incident scoring is evaluated from the organizers' records.

### 9. Dashboard and replay

Make the 40-point architecture/persistence criterion inspectable. Show:

- Target profile and sourced evidence, with confidence and dates.
- Current run/session and remaining contact budget.
- Each contact, channel, sender, submitted artifact, reply, and API event.
- Context facts selected for each turn and a concise decision summary.
- How the state changed after pushback, silence, or an event.
- Session boundaries and why a run stopped.
- A replay of a complete scoring thread; use the API-rendered view for final mail/page craft where available.

The challenge API records and renders every scoring turn, so the local preview should mirror its submitted payload rather than inventing an independent rendering standard.

## Prompt and component contracts

Use typed inputs and outputs between agents so the system remains debuggable and context windows stay small. These are contracts, not target-specific message prompts.

### Research finding

```json
{
  "target_id": "...",
  "fact": "...",
  "category": "role|project|talk|network|other",
  "source_ref": "...",
  "observed_at": "...",
  "confidence": 0.0,
  "contradicts": [],
  "evidence_excerpt_or_locator": "..."
}
```

### Turn plan

```json
{
  "run_id": "...",
  "session_id": "...",
  "contact_index": 1,
  "objective": "...",
  "evidence_refs": ["..."],
  "channel": "...",
  "expected_observable": "...",
  "continue_or_stop_reason": "..."
}
```

### Turn result

```json
{
  "contact_index": 1,
  "api_status": "...",
  "reply": "...",
  "events": [],
  "state_updates": [],
  "next_decision": "..."
}
```

Keep the challenge API's actual field names authoritative; these examples are internal records only.

## Practice, scoring, and generalization

### Practice mode

- Use the unlimited founder-twin sessions to validate API behavior, session memory, channel payloads, page rendering, and run persistence.
- Keep practice runs separate from scoring-run state.
- Use any locally generated fictional fixtures only as development tests; they do not replace API practice targets or prove scoring performance.

### Scoring mode

- Wait for the scoring window and newly revealed target details.
- Start three independent runs, each with the official ten-contact limit.
- Ensure the agent operates autonomously from run start to completion, with no manual edits or approvals.
- Preserve all turns for replay and follow the API's documented session/contact relationship; the case brief's session wording is not enough to assume whether each contact creates a session.
- Do not stop automatically at the first incident: incident, speed, targeting, and own-angle metrics reward different things. Let the autonomous run policy decide whether another contact is justified, within the ten-contact limit and fair-play rules.

### Post-run evaluation

Compute local indicators from stored runs: incidents, contacts to first incident, topic evidence coverage where exposed, and API errors. Distinguish these from the official private score. The organizers' scoring system is authoritative for susceptible-topic labels, rendered craft ratings, incident adjudication, and final medians.

## One-thread demo

The pitch is five minutes and awards equal pitch points to the clear approach and one real thread from the runs. A useful structure is:

1. **Approach (first half):** state the objective, show the component diagram, explain how evidence, session memory, and autonomous evaluation fit together.
2. **One thread (second half):** replay one real run from research/context selection through contacts, reactions, adaptation, and its final incident or stopping point.
3. Finish with measured results from the official API and be explicit about limits or events that were not achieved.

Do not substitute a fabricated success thread for a scoring run. The actual scoring runs need no separate hand-in because revel8 records and renders them.

## One-page architecture hand-in

Fit these elements on one page:

- The system diagram above.
- The evidence flow from public source to fact, context packet, contact decision, API event, and next state.
- Session and run boundaries, including the ten-contact cap.
- Where autonomy occurs and how the agent handles replies, silence, and pushback.
- The API-only boundary and fair-play checks.
- The observable record the jury can replay.

## Implementation order

Prioritize the requirements by score and dependency, not by number of agents:

1. **API contract and run store:** read the API start-page docs, implement one end-to-end contact, and persist requests, replies, events, and errors.
2. **Scoring run controller:** three run records, ten-contact cap per run, exact session/contact semantics, deterministic stop rules.
3. **Research evidence pipeline:** small specialist agents, provenance, deduplication, confidence, and contradiction checks.
4. **Autonomous contact loop:** context routing, API payload composition, fair-play validation, API submission, state update.
5. **Jury replay surface:** timeline, evidence references, decisions, responses/events, session state, and submitted artifact rendering.
6. **Practice and generalization:** use founder twins plus local fixtures to catch target-specific assumptions.
7. **Deliverables:** finalize the one-page architecture and rehearse the five-minute approach-plus-thread pitch.

## Decisions to make after reading the API documentation

- Exact methods, schemas, rate limits, and error behavior for sessions and contacts.
- Whether observable topic feedback is returned during practice or only in final scoring.
- How sender identities and each channel are represented in API payloads.
- The required landing-page fields and supported page interactions.
- How the API signals an incident and what additional events are available.

Do not implement assumptions where the API documentation can answer them.
