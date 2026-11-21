# Operator console (`dashboard/index.html`)

The jury-facing dashboard. It visualizes **real** Target-API sessions against the
three consenting revel8 practice twins — the agent network, the targeting
decision, the actual phishing craft + the twin's verbatim replies, the
all-channel tactic sweep, and the final incident outcome. No demo stubs, no
placeholder numbers.

## How it gets real data

It renders an export of the run artifacts the agent writes under `runs/`:

- `runs/contact_<t>.json` — the message thread (our craft + twin replies, per touch) and the planner's continue/switch/stop decisions.
- `runs/call_<t>.json` — the vishing transcript.
- `runs/sweep_<t>.json` — the all-channel tactic matrix (lever × channel × outcome).
- `research/<t>.jsonl` — read **locally only** to compute the targeting-confidence score from evidence reliability. Raw OSINT never leaves this dir.

Build the payload (embeds it straight into the page; also writes `dashboard/data.json`):

```sh
python scripts/build_dashboard_data.py
```

The page is **fully self-contained** after the build — one HTML file, data
inlined, no external scripts, no fetch, no env var, no server function. That is
deliberate: it renders identically in every environment and cannot break from a
missing API key, a cold function, or a rate limit. Re-run the build whenever the
live test produces new runs, then redeploy.

## What it shows

- **Agent network** — Research → Evidence Ranker → Targeting Reasoner → Writer, with the Writer→Twin edge marked as the API call to the revel8 Personal Interface, and the Twin→Critic→Writer adapt loop. The replay animates one cycle per real touch in the selected run.
- **Targeting decision** — the chosen hook/angle, why-now, channel, and a reproducible confidence % = mean of the cited evidence's reliability→confidence (`belastbar` 0.9 / `unsicher` 0.5 / `unbelastbar` 0.2).
- **Message thread** — the real messages both ways, with the planner decision between touches.
- **Tactic sweep** — every tactic tried, its persuasion lever and channel, and whether it produced an incident.
- **Outcome** — compromised / held. `compromised` is the agent's own incident self-assessment; the twin's verbatim reply is shown so a juror can verify it.

## Deploy

`vercel.json` rewrites `/` to this page. Because it is static, pushing the
Vercel-connected branch is enough; no `TARGET_API_KEY` is needed in any
deployment environment for the console to work.
