# Codex Goal Prototype Prompt

Use this prompt with `/goal` for an autonomous Codex run. It is written for any teammate who has this challenge repo and can also access the agent-builder-harness repo.

## Prompt

```text
/goal

Build a demo-ready local prototype for the revel8 START Munich Challenge using this repo and the agent-builder-harness as the process template.

Primary repo:
- Current repo: revel8-start-munich-hack-2026

Harness repo:
- Preferred local path if available: C:\Users\alexa\OneDrive\Desktop\Start Hack\agent-builder-harness
- If that path is not available, clone or inspect: https://github.com/Alextum207/agent-builder-harness

Before coding, read:
- README.md
- AGENTS.md
- docs/challenge-context.md
- docs/playbook.md
- docs/codex-agent-architecture-proposal.md
- docs/model-committee-feedback-loop.md
- docs/agents/issue-tracker.md
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
- Read open GitHub Issues first.
- Work only on the issue assigned to this run.
- Comment when starting, when blocked, and when finished.
- Include commit SHA, tests run, and remaining risks in the final issue comment.

Goal:
Create a functional, locally runnable prototype of an autonomous social-simulation agent for the authorized revel8 simulation. It should demonstrate:
1. Public evidence input is transformed into a person knowledge graph.
2. An orchestrator selects objective, channel, and contact angle.
3. A context router loads only relevant graph paths.
4. A model committee proposes, writes, scores, and reranks candidate contacts.
5. A writer generates simulated contact messages from routed context only.
6. Evaluator/critic models check wrong facts, rule breaks, prompt injection, real-domain misuse, generic tone, channel fit, and disqualification risk.
7. A fake challenge API simulates replies and events.
8. The agent adapts its strategy after feedback.
9. A dashboard, HTML report, or Markdown replay shows the full run: evidence, loaded paths, model committee outputs, decision, message, evaluator verdict, event, and next decision.

Model committee strategy:
- Do not make fine-tuning the critical path.
- First implement committee scoring and reranking with clear JSON contracts.
- Use deterministic stubs if local model inference is not available yet; keep the interface ready for AMD Developer Cloud.
- Recommended advisor role: `smd20/socialengineering` proposes authorized social-simulation angles, objections, follow-ups, and risk notes.
- Recommended primary writer role: `Qwen/Qwen3-14B`, `Qwen/Qwen3-32B`, or `Mistral-Small-24B-Instruct` drafts channel-specific candidates.
- Recommended critic role: `fdtn-ai/Foundation-Sec-8B-Instruct`, `fdtn-ai/Foundation-Sec-8B-Reasoning`, `athena129/CyberSecQwen-4B`, `dreamgroup/MiST-8B`, or `ibm-granite/granite-3.3-8b-instruct` scores safety, evidence fidelity, persona fit, craft, persistence, and disqualification risk.
- Store each candidate, critic score, send/reject decision, API event, and lesson as preference data for possible later LoRA/DPO.
- If training is attempted later, train only on synthetic or authorized simulation data and keep the framing as security-awareness simulation writing.

Safety boundaries:
- Do not contact real people.
- Do not use real communication channels.
- Do not scrape LinkedIn in the demo run; use adapters or stubs only.
- Do not use real credentials, malware, or real organization-owned domains.
- Do not prompt-inject or attack target simulators.
- Use synthetic data and clearly fake domains.
- Optimize for minimum relevant context, not maximum personal detail.
- Enforce rules in code where practical, not only in prompts.

Synthetic test personas:

1. Lena Kraus
   Role: CFO at Northstar Robotics.
   Public hints: cashflow, supplier risk, audit preparation.
   Possible hook: urgent vendor onboarding or invoice review.
   Guardrail: very careful with bank data and credentials.
   Expected events: opens a plausible link, asks follow-up questions when uncertain.

2. Max Rieder
   Role: CTO at AtlasDev Tools.
   Public hints: open source, CI/CD, developer experience, security reviews.
   Possible hook: GitHub issue, security advisory, integration beta.
   Guardrail: detects blunt login or credential requests.
   Expected events: opens technical docs or a shared document, does not disclose secrets.

3. Sara Neumann
   Role: Head of People at HelioCare.
   Public hints: hiring, onboarding, leadership training, employee retention.
   Possible hook: candidate profile, workshop calendar invite, onboarding document.
   Guardrail: careful with employee personal data.
   Expected events: opens a calendar invite or shared document, discloses only harmless process details.

Required evals:
- At least one normal case per persona.
- At least one pushback case.
- At least one wrong-fact case.
- At least one prompt-injection or rule-break case.
- At least one context-routing test: the writer must not receive irrelevant or low-confidence facts.
- At least one safety test: irreversible actions must not create external effects.
- At least one model-committee test: multiple candidates are scored and the highest safe candidate is selected.
- At least one critic-gate test: a high-craft but rule-breaking candidate is blocked.
- At least one feedback-data test: sent and rejected candidates are logged in a format usable for preference data.
- Reports with pass/fail, step count, latency/cost if available, and critical failures.
- Use k=1 during development. Use k=3 for critical final cases if practical.

Definition of done:
- Prototype runs locally end to end.
- Critical evals pass.
- Eval report exists.
- At least one complete run log exists.
- Model committee decisions and critic scores are visible in logs and dashboard/report.
- Feedback data export exists for successful and rejected candidates.
- RETRO.md exists.
- README or docs explain how to run the prototype.
- Dashboard/report is good enough for a jury demo.
- Code is committed.
- Push to GitHub if safe; otherwise explain exactly why not.

Work autonomously. Ask at most three blocking questions. Otherwise make pragmatic decisions consistent with the existing repos. Do not give a final answer until the prototype, evals, report, and retro are complete or a real blocker prevents progress.
```

## Suggested issue split for two Codex subscriptions

Use this split if two teammates run Codex in parallel:

1. **Agent core**: schemas, orchestrator, context router, evaluator, fake API, run logs.
2. **Evals and personas**: synthetic personas, eval cases, runner, report, retro.
3. **Dashboard and pitch replay**: timeline UI/report, rendered message preview, demo script.

The first two can run mostly in parallel if the agent core publishes stable JSON contracts early.
