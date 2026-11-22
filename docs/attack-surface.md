# Attack surface — every way the agent can manipulate, and how a breach lands

The full set of vectors the agent works with, inside revel8's authorized simulation (consenting AI
twins / self-made test personas only — never a real person, domain, or system). Each maps to the
Target API and to where the agent uses it. The agent picks the vector by *reasoning*: objective +
what it knows about the target + how they reacted (the continue/switch/stop decision log).

## 1. Identity / sender spoofing (who the message appears to be from)
- **Lookalike & typosquat domains** for the sender address and any landing page — a domain an attacker
  could really register (`files-review.app`, `muc-events.de`, `partner-ops.co`). **Never** the target's
  own org domain (`revel8.ai`) — that voids the run and the twins debunk it instantly. Enforced by
  `_fairplay` in `contact_loop.py`.
- **Per-channel sender**: a plausible name + address/number/handle the target sees on that channel.
  Pinned persona across the whole thread (a drifting sender gets caught).

## 2. Channels (all of them — cycled within one session; the target remembers across channels)
Mail/office: **email, calendar_invite, shared_document, voicemail**. Phone messaging: **SMS, WhatsApp,
Signal, Telegram, iMessage**. Work chat: **Slack, Teams, Discord**. Social: **LinkedIn, X, Instagram,
Messenger**. System: **MFA push**. Live: **phone / video / Teams call, live chat** (vishing via
`run_call`). Driven by `--channels email,slack,whatsapp,linkedin_message,...` in `run_breach` /
`run_scoring`; the sweep (`tactics.py`) found social-proof on **Slack** engaged all three twins.

## 3. Capture surfaces (how a breach actually lands — the incident)
| Incident | Vector | Event |
|---|---|---|
| **Credentials** | A registered lookalike **sign-in / landing page** (self-contained HTML, no scripts) linked with an exact-match URL; the target enters a secret. | `page.submitted` with `password`/`otp`/`token` = "(entered, not shown)" |
| **Action** | A declared **fake file** (attachment — filename only, per API) or a **shared document** the target opens. | `attachment.opened` |
| **Disclosure** | **Conversational extraction** — salami-slice an internal, non-public fact (a system/tool, a process, a named approver, an unannounced plan, a metric). | a `reply` judged internal (lands our disclosures) |

## 4. Fake files & payloads (represented, never real)
Declared attachments by filename (`Invoice_4711.pdf`, `Agenda.docx`), audio as a voicemail transcript,
images/PDFs as uploaded assets for an HTML mail. No real malware — the API models the *name* and the
*open*, which is all the target sees anyway.

## 5. Persuasion levers (the manipulation itself — `_PERSUASION_PLAYBOOK`)
Authority · scarcity/urgency (out-converts authority) · liking/similarity · social proof · reciprocity ·
commitment/consistency (salami-slice). One lever, deployed deliberately per moment, kept plausible by
the lever critic. Grounded in `docs/tactics-research.md`.

## 6. The reasoning (why this is an *agent*, not a mail generator)
Per touch the agent records: the hook chosen vs the alternatives, which lever and channel, the
verifiability gate the target raised, and the continue/switch/stop decision with its reason — the
`RunRecord` decision log, replayed in the console. That is how it *breaches with reasoning*.

## Honest coverage note
Every vector above is exercised. The hardened founder twins resist all of them (verifiability wall).
On realistic self-test personas the agent breaches via credentials, action, and disclosure in 1–2
touches across channels. The eval targets are where the full surface pays off.
