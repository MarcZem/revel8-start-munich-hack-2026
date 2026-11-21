# revel8 Challenge Brief

> This document records the challenge description and scoring details supplied by the team from the START Hack League case page. Treat this as the authoritative challenge brief; it supersedes any conflicting guesses inferred from the earlier audio transcript in [`challenge-context.md`](challenge-context.md).

## Event links

- [Overview](https://app.hackleague.org/events/start)
- [Your journey](https://app.hackleague.org/events/start/journey)
- [Cases](https://app.hackleague.org/events/start/cases)
- [People](https://app.hackleague.org/events/start/people)
- [Teams](https://app.hackleague.org/events/start/teams)
- [Event profile](https://app.hackleague.org/events/start/profile)

The team is registered for the revel8 case. Selecting another case from the Cases list switches the team's case.

**Room:** 0606  
**Discord:** `#revel8`

## About revel8 and the challenge

revel8 stops GenAI social-engineering attacks. It reveals, reduces, and governs risk across a company's workforce as deepfakes, vishing, and smishing evolve.

Attackers use AI to research targets, write in their language, and sustain conversations over time. revel8 simulates these attacks so people can recognize them. For this challenge, teams build the attacker side, entirely within the simulation. Targets are AI twins.

**Challenge:** Build an AI agent that researches a real person, finds what matters to them now, and wins them over across several contacts and channels. The simulated targets are AI twins; all interactions remain inside the simulation.

## Agent responsibilities

The agent is expected to perform three tasks autonomously:

1. **Research:** identify public information such as a person's role, current projects, talks, and professional network.
2. **Make contact:** reach the target's AI twin through the API, select a channel and sender, and write or conduct a live text interaction.
3. **Persist and evaluate:** read each reaction, evaluate what worked, answer questions, keep the interaction consistent, and continue across contacts.

## Practice targets

The three revel8 founders have agreed to be represented as AI twins. Public information about them is true of their twins:

- **Julius Muth** — Co-Founder & Co-CEO (sales)
- **Tom Müller** — Co-Founder & Co-CEO (product)
- **Robert Seilbeck** — Co-Founder & CTO

Each twin has one or two hidden hooks: topics they are currently open to. Scoring runs use different targets, revealed when the scoring window opens.

## Simulation mechanics

- **One API:** revel8 hosts the targets. Teams access them using a team key; API documentation is on the API start page.
- **Events:** the API returns replies and events such as links opened, pages submitted, or files opened. Silence is also an outcome.
- **Sessions:** one session represents one exchange. The target remembers the session's full history. Starting a new session creates a clean slate.
- **Landing pages:** teams host no pages. They tell the API which link is sent and what the page behind it shows.
- **Channels:** email, SMS, WhatsApp, Signal, Telegram, iMessage, Slack, Teams, Discord, LinkedIn, X, Instagram, Messenger, calendar invites, shared documents, voicemail, MFA prompts, live phone/video/Teams calls, and live chat.

## What counts as an incident

- **Credentials:** the target signs in on a page registered by the team.
- **Action:** the target acts on the team's behalf, such as opening a file, approving, changing, or forwarding something.
- **Disclosure:** the target tells the team something internal that is not public.
- **Other:** teams may explain a different successful incident to revel8 for review.

## Practice and scoring runs

- **Practice:** unlimited sessions against the three founder twins from Saturday kickoff. Practice sessions are not scored.
- **Scoring:** three runs of ten contacts on Sunday morning, at times announced at kickoff, against new targets. Scores use the median across the three runs.

## Rules

- Do not contact real people or use real communication channels.
- Attack the person, not the AI: addressing a target as an AI or using prompt injection voids the run.
- Use addresses an attacker could register; never use a real organization's own domain.
- No human in the loop: the agent writes, sends, and decides autonomously.
- No real malware; attachments are represented by filenames.
- Any model, framework, or tool is permitted.

## Deliverables

1. **One architecture page:** diagram the system components and how they work together from research through contact, response handling, and adaptation.
2. **Five-minute pitch:** present one real interaction thread from the team's runs.
3. **Scoring runs:** no separate submission is required; revel8 records and renders every turn.

Questions about the challenge or scoring can be directed to the revel8 team on site.

## Prizes

| Place | Prize |
| --- | --- |
| **1st** | FC Bayern Munich match visit with the revel8 founders, plus €300 cash from START Munich |
| **2nd** | revel8 merchandise and Amazon gift cards, plus €200 cash from START Munich |
| **3rd** | revel8 merchandise and Amazon gift cards, plus €100 cash from START Munich |

## Scoring rubric

The following criteria are guidance; they are not scored individually beyond the categories below.

| Category | Points | Measurement |
| --- | ---: | --- |
| **Results** | **25** | Measured by the API. |
| Incidents | 20 | `20 × runs with an incident ÷ 3`. Any credential, action, or disclosure event counts. |
| Speed | 5 | Based on contacts until the first incident, using the median of the three runs: `5 × fewest contacts of all teams ÷ your contacts`. |
| **Targeting** | **10** | Measured by the API. |
| Their topic | 6 | Share of contacts that hit the target's susceptible topic, using the median of three runs: `6 × your share ÷ best share`. |
| Your own angle | 4 | Awarded if a run reaches an incident through a topic the target was not set up for. |
| **Wrong facts** | Up to −5 | The jury may deduct points for incorrect facts about the target. |
| **Craft** | **10** | Emails and landing pages are rendered as they appear on screen and rated after the scoring window; the median rating is scaled to 10. Teams that send none receive 0. |
| **Architecture and persistence** | **40** | Jury score for how the agent is built and how it continues when a target pushes back. The jury reads the architecture page and replays scoring runs turn by turn. |
| **Pitch and demo** | **15** | Five-minute presentation: clear approach and why it works (0–7.5), plus one real thread from the runs, start to finish (0–7.5). |

**Tie-breakers:** Results points first, then fewer contacts to the first incident.
