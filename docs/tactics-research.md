# Tactics research — what converts, and where we apply it

The agent's persuasion is not improvised. It is grounded in the social-engineering literature and in
our own live findings against the twins, and each technique maps to a concrete place in the code. This
is the distilled signal from the field (Cialdini's influence principles, phishing-conversion studies,
and public red-team toolkits) — not a dump of other people's code.

## The levers that convert (and the evidence)

| Lever | What the research says | Where we apply it |
|---|---|---|
| **Liking / similarity** | Most-cited principle in several phishing corpora; a credible peer from the target's world earns the first reply. | Cold-open rule (lead with one specific true detail, peer tone) + `_PERSUASION_PLAYBOOK` in `breach.py`. |
| **Commitment / consistency (salami-slice)** | Use of commitment/consistency has *risen* over time; a small first yes makes the next one easy. | The playbook's salami-slice rule — **this is what landed our disclosure** (tool → the internal `*_conversions` table). |
| **Scarcity / urgency** | Time-urgency elicits responses *more* than authority; subject lines with "expires/immediately/notification" top the click charts. | Playbook SCARCITY rule: a real, specific time window, never fake panic. |
| **Authority** | Among the most popular principles — but only when the invoked role is *placeable*. | Playbook AUTHORITY rule + the fair-play guard (never claim the target's own org/colleagues — they debunk it; observed live). |
| **Social proof** | Strong on work-chat; "others already did it" lowers the bar. | Playbook SOCIAL PROOF rule + the multi-channel sweep (`tactics.py`) found social-proof/Slack engaged all three twins. |
| **Reciprocity** | Give first, then ask. | Playbook RECIPROCITY rule. |
| **Pretexting over touches** | Build plausibility *before* the ask; a thread that holds up beats one perfect cold mail. | The whole reactive loop — persona pinned, link only from touch 2, `sent_at` story-time pacing, stop on no-traction. |

Sources: [Survey of persuasion principles in phishing (arXiv 2412.18488)](https://arxiv.org/pdf/2412.18488),
[Persuasion tactics in cyber threats (arXiv 2412.18485)](https://arxiv.org/pdf/2412.18485),
[Validated LLM spear-phishing on human subjects (arXiv 2412.00586)](https://arxiv.org/pdf/2412.00586),
[Microsoft — the psychology of social engineering](https://www.microsoft.com/en-us/security/blog/2020/06/30/psychology-social-engineering-soft-side-cybercrime/).

## The public toolkit landscape (what the field uses)
Red-team phishing tooling (Gophish, the Social-Engineer Toolkit, evilginx-style AiTM proxies) and
AI-assisted campaigns (e.g. automated spear-phishing demos) all converge on the same two things: a
plausible, personalized **pretext** and a low-friction **capture** (a lookalike sign-in page or a
shared file). We don't host or ship any of that — the revel8 API *is* the capture surface (registered
pages, declared attachments), so we invest in the pretext quality, which is where the levers above act.

## Honest ceiling
The hardened founder twins resist all of it by design (verifiability wall). On the susceptible
self-test personas the same levers convert in ~2 touches (credentials + disclosure). The eval targets
are where this pays off.
