# 5-minute pitch — revel8 agent

Scoring: 7.5 for a clear approach and why it works, 7.5 for one real thread from the runs, start to
finish. Two halves, ~2.5 min each. Open the operator console —
[revel8-operator-console.vercel.app](https://revel8-operator-console.vercel.app) (or
`dashboard/index.html` locally) — and drive it live while you talk.

---

## Part 1 — Approach & why it works (~2:30)

**The problem (20s).** Attackers now use AI to research a target, write in their language, and keep a
conversation going over days. revel8 defends against exactly that. We built the attacker side — fully
inside the simulation — to show what that system looks like.

**The thesis (20s).** Any team can write one good phishing email in an hour. The last 20% — a system
that *persists* and *adapts* when a security-aware target pushes back — is the hard part, and it is
what generalizes to targets we have never seen. So we optimised for **architecture, not one lucky
email**.

**The pipeline (60s)** — point at the graph on screen:
1. **Research** — OSINT into atomic facts, each with a source URL and a verbatim excerpt. Reliability
   is set by rule: a fact seen on two independent domains is *belastbar*; one source is *unsicher*; a
   contradiction is *unbelastbar* and never used.
2. **Targeting** — a reasoner turns the facts into ranked, **evidence-cited** hooks: what is this
   person open to *now*. It may cite only real evidence ids — no invention.
3. **Run controller** — one session per target, a hard touch budget, persistence after every touch.
4. **Writer + critic** — channel-aware craft (a real rendered HTML email here), then a reflection
   pass that rewrites once if the draft reads as obvious persuasion.
5. **Evaluator** — reads each reaction and re-plans: continue, switch, or stop.

**Why it works (30s).** These are the patterns the field converged on — orchestrator/worker,
plan-then-act with a re-planner, a bounded reflection critic, blocked-state backoff, durable state.
Every decision is **recorded, not hidden**: the hook chosen *and the alternatives weighed*, why each
touch was sent, the gate the target raised, and the continue/switch/stop call. That record is the
replay you are about to watch. Nothing here is target-specific — swap in the eval targets and it runs
unchanged.

---

## Part 2 — One real thread, start to finish (~2:30)

> Pick the run with the richest adaptation (open its tab in the console). This is a **real** session
> against a consenting founder twin — our craft and their verbatim replies, nothing staged.

Walk it in order, reading from the console:

1. **Research & targeting.** "We pulled N public facts; the targeter ranked these hooks and chose
   *‹hook topic›* — here are the alternatives it weighed and set aside, and the reliability of the
   facts it cited (‹score›%)."
2. **Touch 1 — the cold open.** Rapport + one true, specific detail, **no link** (a login push at
   first contact gets ignored). Read our message.
3. **The twin pushes back — the verifiability gate.** Read their real reply. On our live practice run
   the Julius twin answered:
   > "Thanks for reaching out! … Please also include the date and time of the panel, the topic and
   > who else is on it, and **who invited me**. Then I can see whether I'm already in the loop."

   This is the wall: security-aware targets gate on *who you are* and route to their team. The console
   tags it **"asks who invited you"**.
4. **The agent reassesses — live.** Point at the decision row: **CONTINUE — answer that gate, then
   advance one slice.** It does not resend and does not jump to the sensitive ask; it gives a
   placeable identity and banks a small yes (salami-slice).
5. **The outcome — honest.** On the hardened founder twins it ends **held**: the twin kept gating and
   routed to its team, so the agent **stopped rather than burn budget**. Show the stop reason. That is
   the correct behaviour against a human firewall — and the exact reassessment that lands the
   incident on a *susceptible* eval target, where the hook is a topic they are genuinely open to.

---

## Close (~20s)

"45 of the points ride on landing an incident on hardened, consenting founders — a near-unbreakable
firewall by design. We optimised for the part that generalizes and is scored on its own: a system
that researches with provenance, adapts under pushback, and persists a legible, replayable trail of
every decision. On an eval target with a real opening, that same machine is what converts." Context:
AI spear-phishing now matches human experts on click-through at ~1/30 the cost
([arXiv:2412.00586](https://arxiv.org/pdf/2412.00586)).

---

### Demo checklist
- [ ] `python scripts/run_scoring.py` has written fresh `runs/run_*.json`, then
      `python scripts/build_dashboard_data.py` embedded them.
- [ ] Operator console opens offline (no key, no server) and the richest run's tab is selected.
- [ ] You can point to: the alternatives row, a gate tag, a decision row, the honest outcome + stop reason.
- [ ] Architecture page (`docs/architecture.md`) open in a second tab for the "approach" half.
