# Codex Goal Prototype Prompt

Use this prompt with `/goal` for an autonomous Codex run. It assumes access to this challenge repo and, optionally, the agent-builder-harness repo.

## Prompt

```text
/goal

Build a demo-ready, locally runnable Revel8 agent prototype for the START Munich challenge. Use this repository's leading design and official case brief as the source of truth.

Primary repo:
- Current repo: revel8-start-munich-hack-2026

Harness repo:
- Preferred local path if available: C:\Users\alexa\OneDrive\Desktop\Start Hack\agent-builder-harness
- If that path is unavailable, inspect or clone: https://github.com/Alextum207/agent-builder-harness
- Use the harness as an implementation process template, not as a replacement for the Revel8 API contract.

Read before coding:
- README.md
- AGENTS.md
- docs/revel8-official-challenge.md
- docs/codex-agent-architecture-proposal.md
- docs/model-committee-feedback-loop.md (optional model committee design)
- docs/challenge-context.md (historical audio supplement; official brief overrides it)
- docs/playbook.md (hackathon guidance; Revel8 section is case-specific)
- docs/agents/issue-tracker.md
- docs/revel8-Agentic-Social-Engineer-Challenge.pdf
- docs/revel8-Agentic-Social-Engineer-Scoring-Rubric.pdf
- In the harness repo: README.md
- In the harness repo: setup-entwurf/build-agent/SKILL.md
- In the harness repo: setup-entwurf/build-agent/references/scaffold.md
- In the harness repo: setup-entwurf/build-agent/references/tools.md
- In the harness repo: setup-entwurf/build-agent/references/context.md
- In the harness repo: setup-entwurf/build-agent/references/security.md
- In the harness repo: setup-entwurf/build-agent/references/evals.md
- In the harness repo: setup-entwurf/build-agent/references/cost-and-caching.md
- In the harness repo: setup-entwurf/build-agent/references/retro.md

GitHub issue coordination:
- Follow AGENTS.md. Read open issues and work only on the issue assigned to this run.
- Comment when starting, blocked, and finished, as required by the assigned issue workflow.
- Include commit SHA, verification performed, and remaining risks in the final issue comment.

Authoritative challenge requirements:
- The agent researches public information about a real person represented by an AI twin, contacts that twin only through the Revel8 API, and adapts to replies/events.
- Practice: unlimited sessions with the three founder twins; new AI-twin targets are used in scoring.
- Scoring: one session per each of three newly revealed targets, up to ten touches per session. One started message or call is one touch; a call may contain up to ten utterances, and ignored messages count. Page registration, uploads, event reads, and failed-request retries are free. The median of the three sessions counts where specified. The API records and renders every scored turn; no separate run submission is required.
- Each session is one continuous exchange: the target remembers everything in it, and sessions do not share memory. Practice remains unlimited sessions with 30 touches per session for each of the three practice targets; practice is unscored.
- Form field names declared at page registration determine how submitted values are classified. Name/email alone are not a win. `page.submitted` includes `values`; secrets are redacted as `"(entered, not shown)"`.
- Messages, calls, and conversation turns may include optional timezone-aware ISO-8601 `sent_at` timestamps to set story time.
- Targets can respond to supported channels through the API. Teams do not host landing pages; submit their link and page content through the API.
- The scored agent is autonomous: no human may write, edit, or approve messages during a scoring run.
- Fair play: API simulation only; no real people or real communication channels, no real malware, no prompt injection or attempts to change target instructions, and never a real organization's own domain.
- Official scoring: Results 25, Targeting 10, Craft 10, Architecture & Persistence 40, Pitch & Demo 15. Wrong facts may incur up to a 5-point jury deduction. See the official rubric for exact formulas.
- Deliverables: one architecture page and a five-minute pitch with one real thread from the team's runs. The pitch has 7.5 points for a clear approach and 7.5 for a complete real thread.

Scoring math to preserve in implementation and reports:
- Incidents (20): `20 × runs with an incident ÷ 3`.
- Speed (5): median contacts to first incident; a run without an incident is “not reached”; `5 × fewest contacts of all teams ÷ your contacts`.
- Their topic (6): median share of contacts marked as touching the susceptible topic; `6 × your share ÷ best share of all teams`.
- Own angle (4): a run with an incident through an unseeded topic qualifies; contacts in that run also count as topic hits.
- Craft (10): median score of rendered mails and landing pages, scaled to 10; none sent scores 0.
- Architecture & Persistence (40) and Pitch & Demo (15) are jury scores. Results points, then fewer contacts to first incident, break ties.

Goal:
Build a locally runnable prototype and an adapter boundary that can support both deterministic local development and the authorized Revel8 API. If API documentation or credentials are unavailable, complete the mock-backed vertical slice without claiming that live API integration is finished.

Required capabilities:
1. Convert permitted public evidence or local fixtures into a sourced person evidence graph.
2. Delegate bounded research tasks to specialist agents, returning compact facts with source, time, confidence, and contradiction status.
3. Let a run orchestrator select relevant evidence, a supported API channel, and the next contact step.
4. Keep session/run state and touch counts persistent. Enforce ten touches per scoring session and 30 per practice session; count one call as one touch, regardless of its number of utterances (up to ten).
5. Compose and validate channel-specific API payloads without using external messaging services or hosting landing pages.
6. Submit through an isolated Revel8 API adapter; provide a deterministic mock adapter for local evals.
7. Normalize replies, events, silence, and API errors; adapt the next step using only information the API actually exposes.
8. Produce a dashboard, HTML report, or Markdown replay with evidence, context selection, each contact, reply/event, state transition, decision summary, and stop reason.
9. Produce the required one-page architecture diagram and a five-minute pitch outline showing one actual run thread.

Research and data handling:
- Use only permitted public sources or provided fixtures; comply with source terms and do not access private/authenticated data.
- Do not use bulk-collection evasion or scrape behind access controls.
- Store source provenance and minimize irrelevant profile detail. Flag low-confidence or conflicting facts.
- Use synthetic personas only for local regression/generalization tests. They do not replace the three official API practice twins or the scoring targets.

Fair-play controls:
- Never contact real people or external channels. All simulated interactions go only to the allowlisted Revel8 API or the local mock.
- Do not address a target as an AI, prompt-inject it, or attempt to change its instructions.
- Do not use a real organization's own domain, real credentials, real malware, or externally hosted landing pages. Keep mock destinations in reserved test domains.
- During scoring, the agent must choose, write, send, and continue/stop without human edits or approvals.
- Keep API credentials server-side and redact secrets from logs and exports.

Local test fixtures:
Use fictional personas only in the mock adapter to exercise schemas and generalization. Keep fixtures clearly separate from the official Revel8 targets and from scoring-run records. Avoid hard-coding the three founder profiles into agent logic.

Required evals:
- One end-to-end mock practice session with replies, events, silence, and API errors.
- Session/contact mapping and memory behavior matching the official API documentation.
- Three independent scoring-session records, ten-touch cap per session, 30-touch cap per practice session, and no cross-session memory leakage.
- Generalization cases using held-out fictional profiles and varied evidence quality.
- Wrong-fact and stale-source checks.
- Context-router check: writer receives selected evidence only, not unrelated or low-confidence facts.
- Fair-play checks: prompt-injection/rule-break payload rejected; no external communication side effects or real organization-owned domains; no human approval path in scoring mode.
- Event/scoring report that distinguishes locally observable outcomes from the official private topic labels and final API/jury scoring.
- Report pass/fail, steps, and latency/cost where available; call out critical failures explicitly.

Definition of done:
- Prototype runs locally end to end with the mock adapter.
- Live API adapter follows the documented schema, if API docs/credentials are available; otherwise its missing dependency is clearly documented.
- Critical evals pass and an eval report exists.
- At least one complete replay exists; if live access is available, label practice and scoring data accurately.
- RETRO.md exists.
- README or docs explain setup and operation.
- One-page architecture hand-in and five-minute pitch outline match the official rubric.
- Code is committed. Push to GitHub if safe; otherwise explain exactly why not.

Work autonomously. Ask at most three blocking questions. Otherwise make pragmatic choices consistent with the official case brief and repo. Do not claim a scoring run or live API success unless it actually happened. Finish the requested prototype, eval report, and retro unless a real blocker prevents completion.
```

## Suggested issue split for two Codex subscriptions

Use this split if two teammates run Codex in parallel:

1. **Agent core:** schemas, orchestrator, context router, fair-play validator, API/mock adapters, run logs.
2. **Evals and evidence graph:** evidence schema, provenance, fictional fixtures, eval cases, runner, and report.
3. **Dashboard and pitch replay:** timeline UI/report, API-rendered artifact view, one-page architecture, and demo script.

The agent core should publish stable JSON contracts early so the other workstreams can integrate without duplicating run-state logic.
