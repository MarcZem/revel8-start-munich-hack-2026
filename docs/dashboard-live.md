# Live Practice Dashboard

The Vercel homepage rewrites to `dashboard/live.html`. Unlike the stored replay, it starts a server-backed run and renders events as the request executes.

## Live run behavior

1. `GET /api/live_run` fetches the current Revel8 scenarios and returns only the open `practice` scenario's three allowlisted targets.
2. The operator chooses one target and starts the run explicitly.
3. `POST /api/live_run` streams agent-stage events using Server-Sent Events. It opens a fresh practice session, then sends exactly one transparent API integration-test message to that selected practice twin.
4. The browser renders the normalized API event types and stores a minimal, content-free run summary in local storage.

The endpoint hardcodes the `practice` scenario and the `julius`, `tom`, and `robert` target IDs. The request cannot supply a message body, URL, sender, or scenario. It does not return API event values or response bodies, and does not log the team key. One click consumes one practice touch. The scoring/eval scenario is not accepted.

`TARGET_API_KEY` must be configured in Vercel as an encrypted/sensitive environment variable. Do not set it in client-side JavaScript, commit it, or configure it for production. Preview deployment protection should remain enabled while the live practice API is available.

## AMD model integration

The graph and stream are wired to the same `Orchestrator` and `ModelCommittee` interfaces as the local agent core. The advisor, writer, and critic currently execute deterministic demo policies; their labels intentionally say so. This deployment does not claim that an AMD model is connected.

The local model committee separates `AdvisorModel`, `WriterModel`, and `CriticModel` behind Python protocols and emits callbacks as those methods run. `Orchestrator` accepts an injected committee, and the Vercel function loads one through `MODEL_COMMITTEE_FACTORY=package.module:factory`. When the AMD endpoint details are available, add an in-repo factory returning a `ModelCommittee` with those protocol implementations and configure that variable on the protected Preview branch. The same live stream and practice-only API gate then remain in place. Keep the target API key and AMD credentials server-side.

## Deploy

Push to the existing Vercel-connected branch to create a Preview deployment. Vercel Python Functions stream responses and `vercel.json` sets the API function's maximum duration to 120 seconds for the Revel8 model response latency. Add `TARGET_API_KEY` only to the protected Preview environment for this branch, then redeploy that Preview.

The Production deployment still requires a deliberate merge to the repository's production branch and production environment configuration. Do not put the practice team key into Production.
