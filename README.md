# revel8 — START Munich Hack 2026

An **autonomous social-engineering agent** for revel8's authorized simulation: it researches a person
from public information, finds what they are open to now, contacts their AI twin through the revel8
Target API, and adapts across several touches — writing, sending and deciding on its own. Built to
generalize to new targets, not to memorize the three practice founders.

- **Architecture (the one-pager):** [`docs/architecture.md`](docs/architecture.md)
- **5-minute pitch script:** [`docs/pitch.md`](docs/pitch.md)
- **Case brief & rubric:** [`docs/revel8-official-challenge.md`](docs/revel8-official-challenge.md)
- **Live jury console:** [revel8-operator-console.vercel.app](https://revel8-operator-console.vercel.app) — self-contained, honest replay of the real runs (also `dashboard/index.html` locally)

## How it is built

The agent's three responsibilities — **research → make contact → persist & adapt** — are one
pipeline with one API boundary, one control loop, and one persisted record. Component map:

| Stage | Modules |
|---|---|
| Research (OSINT → facts + provenance) | `agent_core/research.py`, `graph_loader.py` |
| Targeting (ranked, evidence-cited hooks) | `agent_core/angle_reasoner.py` |
| Context broker (rank + bound the evidence) | `agent_core/evidence_ranker.py`, `context_packet.py` |
| Run controller (session · touch cap · persistence · resume) | `agent_core/run_controller.py` → `scripts/run_scoring.py` |
| Writer + reflection critic | `agent_core/compose.py`, `writer_prompt.py`, `lever_critic.py` |
| Reactive per-turn loop | `agent_core/breach.py` |
| Fair-play gate + evaluator (truthful incidents) | `agent_core/contact_loop.py` |
| Target API adapter (one client) | `agent_core/target_api.py` |
| Persistence contract (RunRecord + decision log) | `agent_core/run_record.py` |
| LLM client (AMD Token Factory, fail-loud) | `agent_core/llm.py` |
| Offline multi-channel tactic sweep (recon tool) | `agent_core/tactics.py`, `scripts/run_sweep.py` |
| Jury replay (static operator console) | `scripts/build_dashboard_data.py`, `dashboard/index.html` |

## Quickstart

```sh
# 1. credentials (never committed): copy and fill in your team key + model endpoint
cp .env.example .env.local        # set TARGET_API_KEY, LOCAL_LLM_BASE_URL, LOCAL_LLM_API_KEY, WRITER_MODEL

# 2. read-only API check (no session, no touch)
python scripts/check_revel8_api.py

# 3. run the scored agent — one adaptive session per practice twin
python scripts/run_scoring.py                  # all three; --target julius for one; --scenario eval when open

# 4. refresh the jury console from the real runs, then open it
python scripts/build_dashboard_data.py
#    open dashboard/index.html in a browser (no key, no server needed)

# tests (offline, deterministic)
python -m unittest discover -s tests
```

Research dossiers (`research/`) and run logs (`runs/`) are git-ignored local artifacts; the curated,
privacy-safe view ships embedded in `dashboard/`. See [`docs/target-api.md`](docs/target-api.md) for
the API contract and [AGENTS.md](AGENTS.md) for the model endpoint.

## Safety & fair play

Authorized simulation only. All contact goes through the revel8 Target API — no real people,
channels, domains or malware. The agent never addresses a twin as an AI and never uses prompt
injection (both void the run). Fair-play is enforced in code before every send; secrets live only in
`.env.local`.

## Deployment

The Vercel homepage serves the static operator console (`vercel.json` rewrites `/` →
`dashboard/index.html`). It is fully self-contained — real run data is embedded at build time by
`scripts/build_dashboard_data.py`, so it needs no API key and no server function and renders
identically everywhere. (There is deliberately **no** live-API call from the browser: a twin reply
can take 90 s and a serverless function would time out — the console replays persisted real runs.)
