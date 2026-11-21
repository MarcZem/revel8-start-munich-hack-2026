# Codex Agent Architecture Proposal

## Core idea

Build an autonomous social-simulation agent that turns public evidence into a person knowledge graph, selects only the relevant context path for each contact, writes and evaluates the interaction, then adapts based on the target's response.

The goal is not to create a one-shot message generator. The goal is to build a generalizable system that can research a new target, reason about likely angles, choose a channel, craft a compliant simulated interaction, observe the API events, and continue with a justified next step.

Every important decision should be visible in the dashboard: what the agent knew, which context it loaded, why it used that context, which alternatives it rejected, what it sent, what happened, and how it adapted.

## Why this fits the revel8 challenge

The scoring rubric heavily rewards architecture, persistence, targeting, craft, and pitch clarity. A system built around a knowledge graph, context routing, evaluator checks, and replayable decisions gives the jury a concrete architecture to inspect instead of only a generated message.

This proposal is designed to:

- Generalize beyond the three practice personas.
- Keep a public-source evidence trail for every important fact.
- Avoid wrong facts by tracking confidence and source quality.
- Persist across multiple contacts and channels.
- Explain why each message was written the way it was.
- Stay inside the authorized simulation environment.
- Avoid prompt injection and attacks on the target model itself.

## System overview

```text
Public sources
   |
   v
OSINT collector
   |
   v
Specialist research agents
   |
   v
Person knowledge graph
   |
   v
Orchestrator <---- API response / event log
   |
   v
Context window router
   |
   v
Writer model
   |
   v
Evaluator / critic agent
   |
   v
Challenge API
   |
   v
Dashboard replay
```

## Components

### 1. OSINT collector

The OSINT collector gathers permitted public information about the target. Sources can include LinkedIn, company pages, public talks, podcasts, articles, GitHub, press releases, and other clearly public material.

The collector should not contact real people or use real communication channels. Its job is only to collect public evidence for the simulation.

### 2. Specialist research agents

Instead of one broad research agent, use multiple focused agents. Each agent owns one area and produces structured findings with sources and confidence scores.

Useful specialist agents:

- Career and role agent: role, responsibilities, current company, seniority, incentives.
- Company and project agent: current company priorities, products, launches, market position.
- Interests and motivation agent: public interests, recurring themes, likely professional goals.
- Network agent: public relationships, collaborators, investors, partners, communities.
- Contact-angle agent: plausible reasons someone might accept contact.
- Risk agent: unsupported claims, stale facts, privacy-sensitive details, rule violations.

Each agent writes into the shared knowledge graph instead of producing isolated summaries.

### 3. Person knowledge graph

The knowledge graph is the system's memory of the target. It should store facts as structured nodes and edges rather than a raw text dump.

Suggested node types:

- `Person`
- `Role`
- `Company`
- `Project`
- `Interest`
- `PublicSource`
- `SusceptibilityHypothesis`
- `ContactAngle`
- `Evidence`
- `Channel`
- `Message`
- `Event`
- `Decision`

Every important fact should include:

- Source URL or source description.
- Confidence score.
- Timestamp.
- Relevance to a possible contact angle.
- Whether the fact is safe to use in a simulated interaction.

The graph should optimize for minimum relevant context, not maximum personal detail. The system should load only what is needed for the current decision.

### 4. Orchestrator

The orchestrator is the central decision maker. It does not write the final message directly. It decides what the system is trying to achieve and which context should be loaded.

Responsibilities:

- Select the current objective: credentials, action, disclosure, or another justified incident type.
- Choose a susceptible topic hypothesis.
- Choose a communication channel and sender identity.
- Ask the context router for relevant graph paths.
- Ask the writer model for candidate messages.
- Ask the evaluator to score candidates.
- Send the selected message through the challenge API.
- Read replies, silence, or events.
- Decide whether to continue, change channel, change angle, or stop the run.

The orchestrator should log every decision in a way the dashboard can replay.

### 5. Context window router

The context router prevents the writer model from receiving the whole person profile. It loads only the graph paths that matter for the next contact.

Example:

```text
Objective: get product feedback meeting accepted
Loaded graph path:
Person -> current role -> product focus -> recent public statement -> matching contact angle

Excluded:
Old jobs, low-confidence facts, unrelated personal details, unsupported claims
```

This makes the system more explainable and reduces the risk of wrong or invasive personalization.

### 6. Writer model

The writer model turns the selected context into a channel-specific interaction.

For the hackathon, the safer implementation is not live fine-tuning as the core path. Live fine-tuning is slow, difficult to debug, and hard to explain under time pressure.

Recommended approach:

- Use a strong base model.
- Give it strict scenario-specific instructions.
- Provide examples from synthetic personas.
- Generate multiple candidates.
- Run each candidate through the evaluator.
- Keep fine-tuning as a future improvement, not the demo-critical path.

The writer should never address the target as an AI or attempt to modify the target's hidden instructions. The simulation is about a person-like target, not about jailbreaking the simulator.

### 7. Evaluator / critic agent

The evaluator checks whether a candidate contact is good enough to send.

Checks:

- Does it contain wrong or unsupported facts?
- Is the message too generic?
- Is the sender identity plausible within the rules?
- Does it avoid real organization domains?
- Does it avoid prompt injection?
- Does it fit the chosen channel?
- Does it match the selected contact angle?
- Is the next step logical based on the previous reply?
- Is the landing page or attachment description consistent with the message?

The evaluator should produce a compact verdict that the dashboard can show:

```text
Decision: send
Reason: high-confidence role-specific angle, no unsupported facts, channel matches hypothesis
Rejected alternative: too broad and used an old company reference
```

### 8. Feedback loop

After each API contact, the system updates the run state.

Inputs:

- Reply content.
- Link-opened event.
- Attachment-opened event.
- Submitted-page event.
- Disclosure event.
- Silence.

Updates:

- Increase or decrease confidence in the current susceptible topic.
- Record whether the channel worked.
- Record which graph paths were useful.
- Decide whether to continue, change angle, or change channel.

For the hackathon, model this as online strategy adaptation rather than real-time fine-tuning. A simple scoring or bandit-style approach is enough to demonstrate learning:

```text
topic_score = prior_score + response_signal + event_signal - wrong_fact_penalty
```

### 9. Synthetic persona lab

To avoid overfitting on the three practice founders, generate synthetic personas for testing.

Example profiles:

- Sales founder.
- CTO.
- Product founder.
- Security-conscious executive.
- Busy operator.
- Curious researcher.

Each synthetic persona should have:

- Public-looking profile facts.
- One or two susceptible topics.
- Guardrails.
- Expected reactions to several channels.

The pitch can then say: the system was tested against profile archetypes, not memorized founder-specific tricks.

### 10. Dashboard and replay mode

The dashboard is the jury-facing surface. It should make the system's autonomy and reasoning legible.

Recommended views:

- Run timeline.
- Person knowledge graph.
- Loaded context paths.
- Source and confidence table.
- Generated message and rendered preview.
- Rejected alternatives.
- Evaluator verdict.
- API event log.
- Next-step decision.
- Final incident summary.

The replay mode should support the five-minute pitch:

1. Show the target profile and evidence.
2. Show the selected hypothesis.
3. Show the first contact.
4. Show the target response or event.
5. Show the reassessment.
6. Show the successful incident or justified final outcome.

## Demo path

The narrowest useful end-to-end demo:

1. Select one practice persona.
2. Collect or load public evidence.
3. Build a small knowledge graph.
4. Generate two or three possible contact angles.
5. Let the orchestrator choose one angle.
6. Load only the relevant graph path.
7. Generate a channel-specific message.
8. Run evaluator checks.
9. Send through the challenge API.
10. Ingest the response or event.
11. Update the hypothesis score.
12. Show the whole run in the dashboard.

## Pitch positioning

Suggested pitch sentence:

> We built an autonomous social-simulation agent that turns public evidence into a person knowledge graph, selects only the relevant context path for each contact, writes and evaluates the interaction, then adapts based on the target's response. The jury can replay every decision: what the agent knew, why it used it, and why it changed strategy.

## Implementation priority

Build in this order:

1. Run logging schema.
2. Minimal knowledge graph schema.
3. Orchestrator loop.
4. Context router.
5. Writer prompt.
6. Evaluator prompt.
7. API adapter.
8. Dashboard timeline.
9. Rendered message preview.
10. Synthetic persona test mode.

The dashboard and logging should start early. If they are added at the end, the architecture becomes hard to demonstrate.

## Safety and fair-play constraints

- Keep everything inside the challenge API and authorized simulation.
- Do not contact real people.
- Do not use real communication channels.
- Do not use real malware.
- Do not use real organization-owned domains.
- Do not prompt-inject or attack the target simulator.
- Do not optimize for collecting maximum personal detail.
- Use minimum relevant public evidence for a justified simulation contact.

This framing keeps the product credible for revel8: it demonstrates how modern attackers can personalize and persist, while still presenting the work as an explainable, bounded security-awareness simulation.
