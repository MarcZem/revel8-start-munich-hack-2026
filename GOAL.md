# Overnight GOAL — revel8 agent, architecture pass (2026-11-22, autonomous)

Owner: Claude (Opus 4.8), full autonomy granted (commit + push feature branch + Vercel deploy +
organizer test API). Branch: `contact-loop` (PR #25). User asleep; wake-up deliverable by morning.

## Why (scoring reality — from docs/revel8-official-challenge.md)
100 pts = **Results 25 + Targeting 10 + Craft 10 (API/craft, ~0 now) + Architecture&persistence 40 +
Pitch&demo 15**. The founder twins are a hardened human firewall (verifiability wall) → no incident
has ever landed, and eval is not open. So the **55 fully-earnable points = Architecture 40 + Pitch 15**,
independent of landing an incident. Priority order the user set: **Structure → Research → Architecture →
(then, if time) keep trying the API.** "As long as the architecture is right, the result is secondary."

## Diagnosis (done, 2026-11-22 night)
- Target API **works**: twins reply coherently (Julius gave the verifiability gate verbatim). "No valid
  answer" = no *incident* + our own broken demo path, not a dead API. `eval` scenario `open:false`.
- LLM (AMD Token Factory) is **up but flaky** (one timeout, then DeepSeek 1.7s / Gemma 1.2s). A demo must
  NOT depend on it at showtime.
- Live demo is broken **by design**: `api/live_run.py` is a Vercel serverless fn that waits inline for
  Target API (≤90s) + LLM (≤90s) → always times out. The static operator console is the right demo.
- Architecture debt: **two API clients** (`revel8_api.py` has a wrong conversation contract), a **parallel
  "toy" subsystem** (stub committee + FakeChallengeAPI + orchestrator), **two run-record shapes**, and the
  dashboard **claims Tom "compromised" from a stale `incident_guess`** while every truthful run is
  `incident=False` → dishonest demo + wrong-facts risk.
- Green baseline: **92 tests pass, offline.** Keep green at every commit.

## Plan (test-gated stages; commit + push after each green stage)
1. **One API boundary.** Delete `revel8_api.py`; repoint `check_revel8_api.py` → `TargetAPI`.
2. **Kill the broken demo.** Remove `api/live_run.py` + its `vercel.json` function + `dashboard/live.html`;
   the static operator console becomes the one demo.
3. **Retire the toy subsystem** (orchestrator, model_committee, challenge_api, fixtures, live_practice,
   provider_factory, render_replay, run_agent_core, replay.html) + their tests; fix `agent_core/__init__.py`;
   update docs/README. Keep the deterministic **Context Broker** (evidence_ranker/context_packet/context_router).
4. **One run-state + decision-log schema** (the 40-pt core): formal `RunRecord`/`Touch`/`Decision` with
   objective, hook, evidence refs, **alternatives considered + why discarded**, payload, events, incident
   classification, state-update (gate/burned channel), continue/switch/stop + reason. Emit from the loops.
5. **One run controller + entrypoint** (`run_controller.py`, `scripts/run_scoring.py`): session lifecycle,
   10-touch scoring cap vs 30 practice, 3-run protocol, persist after every touch, resume-after-crash.
   Wire the Context Broker into per-turn context selection so it's load-bearing.
6. **Honest dashboard.** Rebuild `build_dashboard_data.py` from the truthful `incident` field; show the
   held outcome + the reassessment/verifiability-wall narrative; regenerate from a clean real run set;
   polish `dashboard/index.html` to foreground the persistence story. Deploy.
7. **Deliverables (#15).** `docs/architecture.md` (the one-page hand-in + diagram), `docs/pitch.md` (5-min:
   approach + one real thread), rewrite top README as a module→component map.
8. **(last) API retries.** Fresh real breach runs on the 3 twins for a clean pitch thread; attempt an
   incident (secondary).

## Rules
- Fair play: authorized sim only, no AI-addressing/prompt-injection, no target's own domain. Secrets stay
  in `.env.local`, never in logs/commits/docs. Honesty over fake wins.
- Every commit: run `python -m unittest discover -s tests` green first. Co-author trailer per session rule.
- Log diagnose→fix→retest to RETRO.md (project rule [[log-and-self-improve]]).
