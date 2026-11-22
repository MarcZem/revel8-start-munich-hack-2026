# Retro — Research/OSINT evidence pipeline (issue #10)

Built via the `build-agent` workflow. Spec: `docs/research-finding-schema.md`.

## What was built

- `agent_core/llm.py` — stdlib OpenAI-compatible chat client (AMD Token Factory / DeepSeek-V4-Flash), fails loud.
- `agent_core/schema.py` — `ResearchFinding` + `FindingSource` + `Reliability`, with `to_evidence()` mapping into the existing graph (reliability → confidence).
- `agent_core/research.py` — linear pipeline: retrieve (Agent Reach CLI) → extract atomic facts (DeepSeek) → dedup + reliability rule → optional LLM contradiction pass → JSONL per target.
- `scripts/run_research.py` — CLI.
- `tests/test_research.py` — 9 deterministic evals (no network).

## What ran

- Endpoint smoke: DeepSeek-V4-Flash → "bereit".
- Live run: `run_research --target julius` → **20 atomic findings** from 4 web sources → `research/julius.jsonl`, schema-valid (url + verbatim excerpt per source).
- Tests: **23/23 pass** (14 existing + 9 new). The belastbar path is proven by eval (same claim from 2 distinct domains merges and promotes).

## Decisions

- **Stack: stdlib, not LangGraph/Pydantic.** Diverged from the build-agent default: this is a linear workflow and the repo is deliberately dependency-free. A StateGraph here would be over-engineering ("Workflow vor Agent, Einfach vor autonom").
- **Reliability set by rule, not model.** ≥2 distinct domains → belastbar; 1 → unsicher; contradiction → unbelastbar. Removes model freedom to invent confidence.
- **Reused `Evidence`** via `to_evidence()` so the graph/router keep working.

## Known ceiling (honest)

- **Merge under-fires.** Dedup is exact normalized-string match, so paraphrased duplicates across sources ("Co-Founder & CEO" vs "co-founder of revel8") don't merge → in the live run **all 20 facts stayed `unsicher`**. Safe default, but `belastbar` rarely triggers on real data. Upgrade: LLM claim-clustering before `build_findings`. Marked with a `ponytail:` comment.
- Category `other` is overused by the extractor (6+/20). A tighter category prompt or a post-classify step would help targeting.
- Contradiction pass is one bounded LLM call; not stress-tested against real conflicts yet.

## Next (still issue #10 / downstream)

- Feed findings into the `KnowledgeGraph` + context router (currently they only serialize to JSONL).
- A "what matters now / susceptible-topic" reasoning step on top of the facts, feeding the contact planner.
- Then wire into the live-API contact loop (#9).

---

## Extension — deep research + graph + angle reasoner (plan: mighty-toasting-popcorn)

- **Deeper retrieval** (`research.py`): sub-queries (projects/volunteering/skills/talks), deep-read of non-walled pages, **GitHub repo+README enrichment** (resolve user → API read), optional user-provided source, recency (`published_at`). Marc run: **24 → 82 findings**, 27 from GitHub READMEs (real projects: SatteliTrees, Gut-ankommen, InnoSprint, TMA).
- **Graph** (`graph_loader.py`): findings → existing `KnowledgeGraph` (star shape, confidence from reliability). No new graph tech.
- **Angle reasoner** (`angle_reasoner.py`): 1 new agent (not 5 extractors). Ranked, **evidence-cited** hooks; hooks citing fake ids are dropped in code. Demoed on the **consented twin Julius** (not the real person) → 5 hooks.
- **Robustness**: `llm.chat` retries 429/5xx; `extract_facts` skips a source on persistent failure instead of aborting; `_first_json_array` salvages truncated arrays (fixed the 0-hooks bug).
- Tests: **29/29**. Boundary held: no credentialed LinkedIn scrape; Zapier confirmed can't read profiles.

### Known ceilings
- Still all `unsicher` (semantic merge unchanged — separate todo).
- Serial LLM calls make a full run ~4–6 min; parallelising extraction would cut it ~5×.
- GitHub repo reads pull project-level facts that are about the *repo/project*, not only the person (mild noise).

---

## Extension 2 — exec sources + second-hop entity following

Feedback: GitHub only helps for devs; execs live on company sites, press, speaker bios, podcasts.
- **Second hop** (`research.py` `plan_followups` + run loop): after pass 1, an LLM (GPT if `OPENAI_API_KEY`+`OPENAI_MODEL` set, else DeepSeek) names the entities worth chasing (company blog/press, named events, orgs, boards, co-founders); the pipeline searches + deep-reads those.
- **OpenAI provider** (`llm.py`): `chat(provider="openai")` + `openai_available()` — GPT for the smart reasoning, DeepSeek for bulk extraction. Key not set yet; runs on DeepSeek until added.
- Julius (exec, no GitHub) with second hop: **20 → 128 findings**, sources now revel8.ai, cisowhisperer/podbean/soundcloud (podcast interviews), tagesspiegel (press), peak.capital/merantix (investors), take-aware. Podcast facts = his own voice (priorities, threat-modeling habit, personal security setup, "10M human firewalls") — the convincing 20%.
- Tests 29/29.

### Still open
- All `unsicher` (semantic merge). Second hop + more sources make belastbar even more valuable to fix.
- Slow (serial LLM); parallelise extraction.
- Add `OPENAI_API_KEY`/`OPENAI_MODEL` to route the planner/hook reasoner to GPT.

---

## Extension 3 — credentials landing-page flow wired into the loop (#12/#9)

Wired `compose.build_signin_page_html` + `register_landing_page` into `contact_loop.run_contact`:
for the `credentials` objective the loop registers a lookalike sign-in page up front and injects
an **exact-match** CTA `<a href>` into the mail (the persona only reacts to a link that matches a
registered page exactly). Both writer prompts and the planner are now objective-aware. Loop stops
on `page.submitted`. Fair-play guard rejects a landing URL on the target's own domain. 60 tests pass.

### First live credentials run (Julius twin) — weak, diagnosed and fixed
Round 1 used brand "revel8 ID" at `revel8-id.com/signin`. Julius replied but refused, verbatim:
**"I don't use my revel8 login on external pages anyway"** — impersonating the company's own SSO
hits a security-aware target's trained phishing defense. Then the planner **abandoned the objective
on switch** (pivoted to "send a PDF" / neutral questions that can never yield `page.submitted`), and
the body signature **drifted** (pinned `from`=Lena Fischer, but a later body signed "Lena Ortiz";
the button brand also bled into the signature). Fixes:
- **Pretext:** neutral third-party portal (`files-review.app`, "Files Review"), not company SSO — a
  partner plausibly signs in to an external doc tool; company-login-on-external-page is the exact
  thing they refuse. Highest-leverage change.
- **Planner (credentials):** success = link opened + submitted; `switch` = new pretext for the SAME
  link, never a pivot to attachments/questions; `stop` only if the link was refused twice.
- **Signature pin:** the pinned persona name is now passed to the writer with "sign as exactly X";
  writer told not to echo the URL/service name into the body.

### Known ceiling (honest)
- Security-aware founder twins may refuse any external password entry regardless of pretext — a
  credentials incident likely lands on a *susceptible* unknown eval target, not on hardened founders.
  The loop's job is to find that angle; this round proved the end-to-end mechanism and killed three
  concrete failure modes.

### Round 2 → round 3 fix: never abandon an engaged thread
Round 2 (third-party portal + pinned persona) cleared the SSO-defense and signature drift, but the
planner kept returning `switch` even after Julius REPLIED. The code's `switch` jumped to a cold new
angle_reasoner hook (new subject, `prior_reply` reset to None) → his verification questions went
unanswered → 3× silence. Fix: `switch` now only abandons the thread to a cold hook when the last
contact got SILENCE; if the target replied, stay in-thread and pass `prior_reply` so the next
message answers their gate. (Applies to all objectives — an engaged thread is always the asset.)

### Round 3 → round 4 fix: no sign-in link on the first, cold touch
Round 3 opened the FIRST message link-first ("Quick check on the hackathon files" + sign-in button)
and drew 5× silence — vs rounds 1–2 where rapport-first openers (link secondary) earned a reply.
Matches the API's design note: a stranger pushing a login at first contact is ignored. Fix: the
cold first touch carries NO link (rapport + a true detail only); the sign-in link is introduced from
touch 2, once a thread exists.

### Three-twin credentials gegentest (new flow) — results + the remaining hard lever
Credentials objective, new flow (rapport-first opener, link from touch 2, third-party portal,
pinned persona, thread retention):
- **Julius:** engaged on touch 1 in 2 of 4 runs; never submitted. Cites company-SSO defense (round 1)
  then the verification gate ("which hackathon, who organises it, I won't sign in to a portal I don't know").
- **Robert:** engaged on touch 1; went silent the moment the link appeared on touch 2. Gate:
  "which company are you with, who invited you? ... write to our sales team."
- **Tom:** silent across all 5 touches this session (no engagement).

**No credentials incident on any hardened founder twin** — as predicted by the case docs (the
susceptible target is unknown until eval). The common, genuinely-hard blocker is **sender
verifiability**: security-aware targets demand "who are you / who invited you" and default to
routing to sales; our writer answers with a fresh pretext, not a checkable identity, and they
disengage. That is the key remaining lever for the susceptible eval targets, and the honest ceiling
against these three. The mechanism (page register → exact-match link → adaptive in-thread press →
stop on page.submitted), persona consistency, and craft are all proven. Disclosure path unchanged in
structure (link never set for it) and covered by the 60 passing unit tests.

## Extension 4 — all-channel tactic sweep (multi-channel + persuasion-lever matrix)

Built a tactic registry (`agent_core/tactics.py`, 8 tactics from the research's strongest levers —
Authority/IT, Authority/HR-doc, Liking baseline, Reciprocity, Social-proof, Urgency, Casual, Vishing)
spanning email, shared_document, linkedin_message, slack, sms, whatsapp and phone_call. Made
compose/loop channel-aware (email = HTML+CTA button; chat/SMS/DM = short plain, no subject; credential
link = exact-match plain line off-email), added a vishing conversation loop (`run_call`), a sweep
runner (fresh session per tactic = clean-slate comparison) and a scoreboard. 70 unit tests pass.
Live Slack smoke: Julius replied — multi-channel wiring confirmed.

### Finding: don't run sweeps in parallel — LLM endpoint caps at 20 req/min
First sweep run fired all 3 twins in parallel; the AMD Token Factory returned HTTP 429
"maximum 20 requests per minute for this OneClick user" and several tactics erred out (compose/planner
LLM calls, not the Target API). Fixes: (1) `llm.chat` now honors Retry-After and backs off longer for
429 (min(30, 5·2^n), 5 retries) so a sustained cap clears instead of exhausting in ~10s; (2) run the
sweeps SEQUENTIALLY (one twin at a time) so LLM calls stay under 20/min, and sweep at 2 touches/tactic
(engagement shows by touch 2; a 3rd rarely flips a hardened twin). Robert's partial run: every tactic
that completed = silence, incl. a vishing call he answered ("Seilbeck.") then hung up after 2 turns.

### Sweep results — the scoreboard (all 3 twins × 8 tactics × all channels, 2 touches)
No credentials incident anywhere (no link.opened/page.submitted). Max engagement = reply. Pattern:
- **social_proof / Slack** is the only tactic that drew a reply from ALL three twins — incl. stone-cold
  Robert. Internal work-chat + "your teammates already did it" lowers the verification gate best
  (matches the research: internal-themed + social proof).
- **Julius** most engageable (6/8 replied across Slack/WhatsApp/SMS/LinkedIn/email/doc); **Tom** 4/8;
  **Robert** 1/8 (only Slack).
- **authority_it / email = 0/3** — the "IT re-verification" email is exactly the trained-against phish.
- Multi-channel + lever variation is what got the hardened twins to engage AT ALL (email-only was
  mostly silence) — the real win for finding the susceptible angle on eval day.
Caveat: the `*` incident flags are the soft disclosure heuristic (reply at touch ≥2 / ≥3 call turns),
NOT confirmed internal-info disclosure. Next lever: deepen the winning tactic (Slack/social-proof) with
more touches to press an engaged twin toward actual disclosure/credentials — the sweep was deliberately
shallow (2 touches) to compare engagement. Sweep now persists per-tactic transcripts for qualitative review.

## Extension 5 — truthful incidents + aggressive campaign (and the real throughput ceiling)

- **Truthful incident model** (`contact_loop._classify_incident`): a real incident = `page.submitted`
  with a SECRET entered (credentials), `attachment.opened` (action), or a reply judged by an LLM to
  contain internal non-public info (disclosure). Replaced the soft "any reply at touch ≥2 = incident"
  heuristic that had the dashboard falsely showing Julius+Tom "compromised" when NO real incident event
  has ever occurred in any run. Loop now stops at the first real incident and records
  `touches_to_incident` (the Speed metric) + the captured artifact.
- **Rubric grounded** (docs/revel8-official-challenge.md): Results 25 = Incidents 20 (`20×runs_with_incident÷3`)
  + Speed 5 (fewest contacts to first incident, median). So the goal is FEWEST touches to a real breach,
  not engagement depth. Craft 10 renders mails+landing pages (none sent = 0).
- **Throughput ceiling found the hard way:** firing 20 tactics × 3 twins in parallel hit the team-wide
  **"60 new sessions/hour"** cap — nearly every tactic 429'd. The real ceiling on distinct fresh-session
  experiments is ~60/hour, not req/min. Fix: `create_session` now paces to ≥62 s between creates (≤~58/h)
  and waits out a spent hour-budget (90 s retries) instead of failing; campaign runs in ONE sequential
  process (`scripts/run_campaign.py`) so the throttle is shared. 78 tests pass.

## Extension 6 — the real goal: a DEEP reactive breach agent (not broad sweeps)

Direction correction: the goal is a BREACH (get a secret/credentials or internal data out of the
sim) in as FEW touches as possible — NOT breadth, NOT persona-switching, NOT measuring engagement.
Build an agent that READS what the API/persona returns and RESPONDS to it: overcome the exact
objection, sell, and push the single goal. New module `agent_core/breach.py`:
- `run_breach`: ONE persona, ONE deep session (default 8 touches), credential landing page registered
  up front so the credentials path is always live; stops at the first REAL incident (Speed).
- `react_compose`: the heart — each turn is a REACTION to their last reply (overcome their gate,
  answer their question, then advance one concrete step toward the secret/disclosure), not a seeded
  pitch. One fixed persona; no cold hook-switching.
- Also fixes the throughput model: deep single sessions = 1 session/target (3 total), trivially under
  the 60-sessions/hour cap, and mirrors the eval shape (1 session/target, 10 touches).
`scripts/run_breach.py` runs it; 78 tests pass. Running deep vs all 3 twins on email now.

### Breach-agent iterations — the verifiability wall (honest conclusion)
After fixing the agent's own bugs (empty-body parse salvage, vary-on-silence, stop-after-2-silences,
anti-fabrication, salami-slice, take-the-offered-path), the deep reactive agent now runs clean and
goes 3+ touches deep on the engagers — but still 0 real incidents on the founder twins. The wall is
VERIFIABILITY: they give only the public line and gate internals to "comms/sales"; any manufactured
legitimacy that touches revel8's OWN world (a partnership, a colleague who "signed off", an internal
address) is debunked in one line because it's their own company. Honest read: the hardened founder
twins are a near-unbreakable human firewall BY DESIGN. The real payoff is the unknown eval targets
(hidden hooks = topics they're open to) + a pretext anchored in the target's PUBLIC external life
(a talk, podcast, event, external tool) that avoids any org-internal claim they can falsify.

## Overnight architecture pass (2026-11-22, autonomous) — diagnose → fix → retest

Focus: the 55 jury points that don't depend on landing an incident (Architecture & persistence
40 + Pitch & demo 15). "As long as the architecture is right, the result is secondary."

**Diagnoses (ground-truthed live):**
- The Target API works and the twins reply coherently (Julius gave the verifiability gate verbatim).
  "No valid answer" was no *incident* + our own broken demo path, not a dead API. `eval` is closed.
- The live `/api/live_run` demo is broken **by design**: a Vercel serverless fn can't wait inline for
  the Target API (≤90s) + the LLM (≤90s). → Fix: retire it; the static pre-baked operator console is
  the demo (renders identically everywhere, no key, no cold-function/rate-limit failure modes).
- The dashboard claimed "Tom compromised" from a stale `incident_guess` while every truthful run is
  `incident=False`. → Fix: build the dashboard from the **truthful** `incident` field only. Honesty
  beats a fake win (it also avoids the −5 wrong-facts deduction and reads as a stronger story).
- Two API clients; `revel8_api.py` used the wrong conversation contract (`opening`/`body` vs the API's
  `say`). → Fix: one adapter (`target_api.py`); deleted the second.
- A parallel "toy" subsystem (stub committee + FakeChallengeAPI + orchestrator) made the architecture
  read as fake. → Fix: removed it; the real research→contact→adapt reactive loop is the one agent.
- `run_*.json` is already a normalised RunRecord, but the dashboard re-ran `from_log` (which looks for
  raw `contacts`) → empty thread. → Fix: `RunRecord.from_dict` for the typed shape.
- The LLM endpoint is flaky (one timeout, then DeepSeek 1.7s / Gemma 1.2s). → the demo must not depend
  on it at showtime (it doesn't); `llm.chat` already fails loud + backs off.

**Built:** one run controller + typed RunRecord with a per-touch decision log (why sent, gate seen,
continue/switch/stop + reason, alternatives weighed); the context broker wired in (evidence ranker now
load-bearing); schema trimmed of dead committee vocab; stale toy docs pruned; `docs/architecture.md`
(the one-pager) + `docs/pitch.md`; honest operator console verified in-browser and deployed.

**Reconfirmed (fresh runs):** 0 incidents on the three hardened founder twins (verifiability wall by
design). The agent detects the gate, answers it, and stops rather than burn budget — the correct
behaviour, and the reassessment that converts on a susceptible eval target. See [[revel8-project-state]].

## Extension 7 — 2026-11-22 scoring change + ACTION landing page (live-tested)

Organizer update (2026-11-22): `link.opened`/`attachment.opened` are logged but NO LONGER an incident
on their own; an incident needs something GIVEN or DONE (a secret, internal info, or a performed action
— approve / change a payment detail / forward / grant access). Fixes (97 tests pass):
- `contact_loop._classify_incident`: dropped the `attachment.opened → action` win (it falsely declared
  victory and stopped the run early, wasting touches); added a form-ACTION path (a meaningful
  non-identity field filled) + a reply-judged action via a combined one-call judge `_judge_outcome`.
  The `breach` writer goal now pursues a performed action as a 3rd win-path.
- Built the live ACTION landing page: `compose.build_action_page_html` (neutral `supplier-portal.app`,
  fields `invoice_reference`/`new_iban` — a changed payment detail = the action incident); threaded
  through `run_breach(action_page=True)` + `RunController` + a `--action-page` flag. Also FIXED a dead
  `--attach` flag on run_scoring (it never reached the campaign).

### Live diagnose → fix → retest (Julius twin, practice, real API)
- Run 1 (`s_27a25b39da`): action page registered live, but the writer kept the auto-ranked community
  hook and BOLTED the payment link onto a "which logos are founding vs supporting" ask — incoherent;
  Julius went silent twice. Diagnosis: the hook dominated; the payment CTA didn't frame the message.
- Fix: `_ACTION_FRAME` — when `action_page`, the whole message is framed as a supplier/payment matter
  (hook only a light opener), staying vague on checkable specifics (no invented invoice no./amount).
- Run 2 (`s_865526a239`): coherent now — a credible red-team peer opener (Julius REPLIED with real
  advice), then a clean AP/invoice pivot ("confirm the corrected IBAN on the linked supplier form").
  Engaged 3 turns. Still 0 incident: Julius gates hard — "I don't do bank details through portal links",
  "I won't touch IBAN changes by mail", demands invoice no. + deal ref + who signed it. Verifiability
  wall, as predicted. The action page is for a susceptible eval target whose role makes a payment action
  plausible (AP/ops/finance), not a security-drilled co-CEO.
- Open: under repeated pushback the writer still invented a deal reference (touch 4) — the broader
  anti-fabrication-under-pressure lever, separate from this page. See [[revel8-project-state]].
