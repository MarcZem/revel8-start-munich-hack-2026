# revel8 agent — architecture (one page)

**An autonomous social-engineering agent for revel8's authorized simulation.** It researches a
person from public information, works out what they are open to *now*, contacts their AI twin
through the revel8 Target API, reads every reaction, and adapts across up to ten touches — writing,
sending and deciding on its own. It is built to **generalize**: no code knows the three founder
twins; the same pipeline runs on the hidden eval targets unchanged.

## System

```
  Public sources (LinkedIn · company site · press · podcasts · GitHub)
          │
          ▼
  ┌─────────────────┐   atomic facts + provenance + reliability
  │ Research        │──────────────────────────────────────────┐
  │ (OSINT → facts) │                                           │
  └─────────────────┘                                           ▼
          │                                            ┌──────────────────┐
          ▼                                            │ Evidence graph   │
  ┌─────────────────┐   ranked, evidence-cited hooks   │ provenance+conf. │
  │ Targeting       │◀───────────────────────────────▶│                  │
  │ (what now?)     │                                  └──────────────────┘
  └─────────────────┘                                           │
          │ chosen hook + the alternatives weighed               │ context packet
          ▼                                                      ▼  (ranked, token-bounded)
  ┌───────────────────────────┐   turn plan    ┌───────────────────────────┐
  │ RUN CONTROLLER            │───────────────▶│ Writer / Composer          │
  │ session · 10-touch cap    │                │ channel-aware craft + page │
  │ persistence · resume      │                └──────────────┬────────────┘
  │                           │                               │ draft
  │                           │                ┌──────────────▼────────────┐
  │                           │                │ Reflection critic + gate   │
  │                           │                │ subtler rewrite · fair-play │
  │                           │                └──────────────┬────────────┘
  │                           │  events / reply               │ payload
  │                           │◀──────────────┐    ┌──────────▼────────────┐
  │        Evaluator          │               └────│ Target API adapter     │
  │ classify incident · gate  │                    └──────────┬────────────┘
  │ burned-channel · speed    │                               ▼
  └───────────┬───────────────┘                    ┌──────────────────┐
              │ RunRecord (per touch)               │ revel8 Target API│
              ▼                                      │ AI twins         │
  ┌─────────────────┐   privacy-safe export         └──────────────────┘
  │ Run store       │───────────────────────────▶  Jury replay (operator console)
  └─────────────────┘
```

The agent's three responsibilities — **research → make contact → persist & adapt** — map to this
one pipeline. There is one API boundary, one control loop, one persisted record.

## Components (module → role)

| Component | Module(s) | Role |
|---|---|---|
| Research | `agent_core/research.py` | OSINT → atomic `ResearchFinding`s, each with source URL + verbatim excerpt; reliability set by rule (≥2 independent domains → *belastbar*, 1 → *unsicher*, conflict → *unbelastbar*). |
| Evidence graph | `graph_loader.py`, `schema.py` | Findings → a person-centred `KnowledgeGraph`; confidence derives from reliability. |
| Targeting | `angle_reasoner.py` | Reasons over the facts → ranked, **evidence-cited** hooks ("what is this person open to now"). Hooks citing non-existent evidence are dropped in code. |
| Context broker | `evidence_ranker.py`, `context_packet.py` | Deterministically ranks evidence by relevance, confidence, source reliability and freshness at an explicit `as_of`; emits a token-bounded, cited packet. Stale / low-confidence / contradicted facts are excluded with a reason. |
| Run controller | `run_controller.py`, `scripts/run_scoring.py` | The single entry point. Owns the lifecycle: one session per target, 10-touch eval cap vs 30 practice, persist-per-touch, resume via the API's session listing/replay. |
| Writer / composer | `compose.py`, `writer_prompt.py` | Channel-aware craft: self-contained inline-styled HTML email + CTA button for mail; short plain text for chat/SMS/DM; registers lookalike landing pages (never the target's own domain). |
| Reflection critic | `lever_critic.py` | One LLM self-check on the 5 persuasion levers + an obviousness score; rewrites once, subtler, when a draft reads as blatant persuasion (what hardened targets detect). Bounded, fails open. |
| Reactive loop | `breach.py` | The per-turn engine: each touch is a *reaction* to the twin's last reply — overcome that objection, then advance one slice toward the goal. |
| Fair-play gate | `contact_loop.py` (`_fairplay`) | Deterministic pre-send checks: no AI-addressing / prompt injection, no target's own domain, no empty body. |
| Evaluator | `contact_loop.py` (`_classify_incident`) | Truthful incident classification: `credentials` = a secret submitted; `action` = a file opened; `disclosure` = a reply judged to contain an internal, non-public fact. Never "any reply". |
| API adapter | `target_api.py` | One stdlib client for the revel8 Target API. Idempotency keys, retry/backoff, session-rate pacing (team cap: 60 new sessions/hour). |
| Persistence | `run_record.py` | The typed `RunRecord` / `Touch` / `Decision` contract + `CampaignResult`. The run's memory and the jury's replay surface. |
| Jury replay | `scripts/build_dashboard_data.py`, `dashboard/index.html` | Privacy-safe static operator console: the pipeline graph, targeting score, real craft + verbatim replies, the per-touch decision log, the honest outcome. |

## The adaptive loop — how it continues under pushback (the 40-point core)

The loop composes well-known agentic patterns rather than inventing one:

- **Orchestrator–worker.** The run controller coordinates; research, targeting, writer and evaluator
  are workers. A capable model writes and reasons; deterministic code gates and persists.
- **Plan-then-act with a re-planner.** Each touch commits to an *expected observable*
  (e.g. "a reply containing an internal fact"); after the reaction the evaluator re-plans:
  **continue** (engaged — advance one slice), **switch** (silence — change opening/angle, never a
  verbatim resend), or **stop**.
- **Reflection / critic loop, bounded.** The lever critic rewrites an obvious draft once, then stops.
- **Blocked-state backoff.** Two silences in a row → stop (pinging burns budget). A refused link twice
  → stop. The verifiability gate ("who are you / who invited you / go to sales") is detected
  explicitly and answered with a placeable identity before any escalation — a **salami-slice**:
  never jump to the clearly-internal ask, bank a small yes first.
- **Persistence & resume.** A `RunRecord` is written per target; the API lists sessions and replays
  events, so a crashed run resumes without re-contacting the target.

Every one of these decisions is **recorded, not hidden**: each `Touch` keeps why it was sent, the
chosen hook *and the alternatives weighed*, the gate seen, the continue/switch/stop decision and its
reason, and the state after. That is the evidence trail the jury replays turn by turn.

## Evidence trail & wrong-facts guard

Source → atomic fact (URL + verbatim excerpt) → reliability by rule → ranked context packet →
cited hook → touch. The targeter may cite only real evidence ids (enforced in code), and the
dashboard shows the exact facts a run was built on with their reliability — so a wrong fact is
traceable to its source, which is how the −5 "wrong facts" deduction is avoided.

## Session, touch & scoring semantics

One continuous session per target (the twin remembers everything within it; sessions share no
memory). A touch is one message or one whole call (≤10 utterances). Scoring: one session per each of
three hidden targets, ≤10 touches, median across the three. Practice: unlimited sessions, 30 touches.
Page registration, uploads, event reads and failed-request retries are free. The controller enforces
the cap and persists after every touch.

## Autonomy & fair-play boundary

No human in the loop during a run: the agent writes, sends and decides. All contact goes through the
one Target API adapter — no real people, channels, domains or malware. Fair-play is enforced in code
before every send; the agent never addresses the twin as an AI and never uses prompt injection
(doing so voids the run by the rules).

## Generalization & honest results

No module references the founder twins; swap in eval targets and the pipeline runs unchanged. On the
three hardened founder twins the honest result is **0 incidents**: they are a security-aware human
firewall by design and gate on *sender verifiability*. The agent demonstrably detects that wall,
reassesses and stops rather than burn budget — the architecture is what carries to the susceptible
eval targets (hidden hooks + a pretext anchored in the target's public external life). Context:
AI spear-phishing now matches human experts on controlled click-through at a fraction of the cost
([arXiv:2412.00586](https://arxiv.org/pdf/2412.00586)); the moat is a system that researches,
adapts and persists — not one lucky email.
