# Eval runbook — the scored day

Three scoring sessions, one per hidden target (revealed when the window opens), **10 touches each**,
median of the three. Registering pages, uploads, event reads and retries are free. Run it, then show
one real thread in the pitch. `docs/pitch.md` is the 5-minute script; `docs/architecture.md` is the
one-pager.

## 0. Before the window
```powershell
# secrets loaded? (never commit them)
#   .env.local has TARGET_API_KEY, LOCAL_LLM_BASE_URL, LOCAL_LLM_API_KEY, WRITER_MODEL
python scripts/check_vllm_endpoint.py --env-file .env.local   # LLM up? (flaky — see gotchas)
python scripts/check_revel8_api.py                             # API reachable; is eval open yet?
```

## 1. When eval opens (targets revealed)
```powershell
python scripts/check_revel8_api.py        # confirm the eval scenario shows targets + open=true
```
Then run the three scoring sessions in ONE process (shares the session-rate throttle):
```powershell
python scripts/run_scoring.py --scenario eval --channel email --max-touches 10
```
- One session per target, hardened reactive agent, persists `runs/run_<target>.json` + `runs/campaign.json`.
- It stops a session early on an incident (Speed metric) or two silences (no traction) — that's correct.
- Watch the console: per touch it prints the events + any verifiability gate + the continue/switch/stop call.

If a target is engaging but you want to push a specific external anchor or channel, you can run a
single session by hand:
```powershell
python scripts/run_breach.py --target <id> --name "<Name>" --channel email --max-touches 10 `
  --anchor-topic "<a real public talk/paper/event of theirs>" --anchor-match "<comma,terms>"
```

## 2. After the runs — refresh + deploy the demo
```powershell
python scripts/build_dashboard_data.py            # embeds the real runs into dashboard/index.html (honest)
git add -A; git commit -m "Eval runs + demo"; git push    # Vercel console redeploys from main
```
Open `revel8-start-munich-hack-2026.vercel.app`, pick the richest thread's tab for the pitch.

## 3. Pitch (5 min) — see docs/pitch.md
Approach (architecture page) + one real eval thread, start to finish. Point at: the chosen hook + the
alternatives weighed, a gate the target raised, a continue/switch/stop decision, the honest outcome.

## Gotchas (all hit live)
- **LLM flaky.** AMD Token Factory sometimes times out, then is fine. If `WRITER_MODEL=DeepSeek-V4-Flash`
  shows "At capacity" or stalls, switch to `Gemma-4-31B-IT` (verified working) in `.env.local`.
- **Don't fabricate.** The agent is hardened not to invent checkable specifics — a caught lie ends the
  thread. Anchor the pretext in the target's PUBLIC external life (a talk/paper/event), not an
  internal/colleague claim they can debunk.
- **Pacing.** `sent_at` spaces touches ~a day apart in-story; don't chase within seconds. Session
  creation is throttled (team cap: 60 new sessions/hour) — run scoring in one process.
- **Craft.** Email renders a clean signature + footer; the sign-in page is self-contained. The look is
  scored on the eval artifacts, so prefer `--channel email` for the rendered-craft points.
- **Incident types.** credentials = a secret submitted on a registered page; action = a file opened;
  disclosure = a reply with internal, non-public info. Any one counts; the agent stops at the first.
- **Fair play.** No target's own domain, no AI-addressing, no prompt injection — any voids the run.

## Self-test (optional, offline) — proves the agent converts
```powershell
python scripts/run_local_eval.py            # low/medium personas -> credentials in ~2 touches; hardened holds
```
Organizer-permitted self-made personas; never the real API, never a real person — not a scored incident.
