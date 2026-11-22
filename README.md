# revel8 — START Munich Hack 2026

Project workspace for the START Munich 2026 hackathon. The official revel8 case is documented in [the challenge brief](docs/revel8-official-challenge.md); the current leading system design is in the [Codex agent architecture proposal](docs/codex-agent-architecture-proposal.md).

## Repository

- GitHub: [MarcZem/revel8-start-munich-hack-2026](https://github.com/MarcZem/revel8-start-munich-hack-2026)
- Deployment: [revel8-start-munich-hack-2026.vercel.app](https://revel8-start-munich-hack-2026.vercel.app)
- Hosting: Vercel project `revel8-start-munich-hack-2026`, linked to this GitHub repository

Pushes to the repository's production branch are handled by the existing Vercel Git integration. Vercel also creates preview deployments for other branches and pull requests when enabled in project settings. The current project has SSO deployment protection enabled, so access may require an authenticated Vercel account.

## Getting started

The frontend/application framework has not been selected yet. The first local prototype is a dependency-free Python agent core with deterministic model stubs, so it can run before AMD Developer Cloud model hosting is ready.

1. Clone this repository.
2. Run the local agent core:

   ```sh
   python3 scripts/run_agent_core.py --persona lena_kraus --out runs/latest_agent_core_run.json
   ```

3. Run tests:

   ```sh
   python3 -m unittest discover -s tests
   ```

4. Run the offline Context Broker evaluations over synthetic fixtures:

   ```sh
   python3 scripts/run_context_broker_evals.py
   ```

   The command writes `evals/context_broker_report.json` and exits nonzero if a check fails.

5. Generate and open the local jury replay:

   ```sh
   python3 -m dashboard.render_replay --input runs/latest_agent_core_run.json --output dashboard/replay.html
   ```

   Open `dashboard/replay.html` in a browser. See [the replay guide](docs/dashboard-replay.md) for the pitch-mode walkthrough.
6. Read the core docs in [docs/agent-core.md](docs/agent-core.md).
7. For the official, opt-in Revel8 API client and read-only connection check, see
   [docs/revel8-api.md](docs/revel8-api.md).
8. For the latest organizer clarifications about form values, story timestamps,
   and touch/session limits, see [the dated Revel8 update](docs/revel8-updates-2026-11-21.md).
9. For the AMD Developer Cloud / Token Factory model endpoint, use [docs/amd-vllm-endpoint.md](docs/amd-vllm-endpoint.md) and run:

   ```sh
   python3 scripts/check_vllm_endpoint.py --env-file .env.local
   ```

10. Keep local credentials in an untracked `.env.local` file or environment variable. Never commit secrets.

## Project notes

- Hackathon: START Munich 2026
- Project: revel8
- Challenge brief: [official revel8 case details](docs/revel8-official-challenge.md)
- Team and implementation details: pending; see the official challenge brief and current architecture proposal above

## Deployment setup

The Vercel project is already associated with this repository. The live dashboard uses static HTML plus one streaming Python Function; the existing Git integration creates Preview deployments for feature branches.

For local Vercel workflows, install the Vercel CLI and use `vercel link` to associate the checkout with the existing project. Do not add credentials or `.env` files to Git.

## Live demo

The Vercel homepage serves the live practice flow in [`dashboard/live.html`](dashboard/live.html). It fetches the open Revel8 practice targets and streams each run event from `/api/live_run`. Clicking **Live-Praxislauf starten** creates a practice session and spends exactly one touch on the selected synthetic persona. The server requires `TARGET_API_KEY`; set it as a Vercel Preview environment variable and never expose it to browser code.

The advisor, writer, and critic shown in this demo are still deterministic policy stubs. `Orchestrator` accepts an injected `ModelCommittee`, whose Advisor/Writer/Critic protocol is the intended connection point for the AMD-hosted model. See [`docs/dashboard-live.md`](docs/dashboard-live.md) for the run flow and integration boundary.
