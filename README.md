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

4. Run the synthetic persona evaluation suite:

   ```sh
   python3 -m evals.run_evals
   ```

   The suite writes `evals/report.json` and a minimized `evals/feedback.jsonl`. It uses the local fake API only; it does not call Revel8 or require API credentials.
5. Read the core docs in [docs/agent-core.md](docs/agent-core.md).
6. Keep local credentials in an untracked `.env.local` file. Never commit secrets.

## Project notes

- Hackathon: START Munich 2026
- Project: revel8
- Challenge brief: [official revel8 case details](docs/revel8-official-challenge.md)
- Team and implementation details: pending; see the official challenge brief and current architecture proposal above

## Deployment setup

The Vercel project is already associated with this repository. Confirm the production branch, framework preset, build command, output directory, and required environment variables in the Vercel project settings once the application stack is selected.

For local Vercel workflows, install the Vercel CLI and use `vercel link` to associate the checkout with the existing project. Do not add credentials or `.env` files to Git.
