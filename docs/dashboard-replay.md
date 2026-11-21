# Local Run Replay

The replay renderer turns the agent core's structured JSON run log into a standalone HTML view for demo and review. It uses the existing Issue #2 run-log schema and has no external dependencies or network calls.

## Generate a run and replay

From the repository root:

```sh
python3 scripts/run_agent_core.py --persona lena_kraus --out runs/latest_agent_core_run.json
python3 -m dashboard.render_replay --input runs/latest_agent_core_run.json --output dashboard/replay.html
```

Open `dashboard/replay.html` in a browser. The committed replay is generated from a fictional Lena Kraus fixture and the local `FakeChallengeAPI`; it is not an official Revel8 practice or scoring thread.

## What the replay shows

- A six-step run timeline from evidence graph through strategy update.
- Every synthetic evidence item with source, observation time, confidence, and whether the router selected it.
- Loaded context paths and their evidence IDs.
- The winning candidate rendered as a message preview.
- Every candidate's evaluator decision and blocking reasons. Bodies of blocked candidates are omitted.
- The local fake API's reply/event, followed by the stored next-step lesson.
- A **Start pitch replay** control that advances through the six demo sections.
- An agent handoff map synchronized with the pitch replay. Moving packets follow the recorded stages from synthetic evidence through model stubs and the safety gate to the fake API/persona response. The dashed edge marks feedback saved for a possible next turn; the one-turn stub run does not execute that turn.

All run-log text is HTML-escaped before rendering. The HTML and its styling/scripts are self-contained; no hosted assets, external channels, or target API credentials are used. The moving graph is a replay of stored synthetic events, not a live stream of concurrently running agents or an official Revel8 session.

## Verification

```sh
python3 -m unittest discover -s tests
```

The dashboard tests check key run details, ensure blocked candidate bodies are hidden, and check HTML escaping for untrusted run-log text.
