# AGENTS.md

Context for coding agents working in this repo. Start with `README.md`, `docs/challenge-context.md` (challenge brief), `docs/playbook.md` (hackathon playbook, German), and `docs/codex-agent-architecture-proposal.md`.

## Parallel Codex workflow

This repo may be worked on by two Codex subscriptions at the same time. Coordinate through GitHub Issues before changing code.

1. Pull the latest `main`.
2. Read the open GitHub Issues and pick exactly one unassigned task.
3. Comment on the issue with `Claimed by <name/account>; starting now.` before editing files.
4. Work in a small scope and avoid touching files owned by another claimed issue.
5. Commit only your own changes.
6. Push your branch or `main` only after checking `git status` and `git log --oneline -5`.
7. Comment on the issue with what changed, how it was tested, and the commit SHA.
8. Close the issue only when the task is genuinely done and verified.

If two agents need the same file, communicate in the issue comments first and split the work by section or by follow-up issue.

## Goal prompt

For long autonomous runs, use `docs/codex-goal-prototype-prompt.md` as the shared `/goal` prompt. It is written so another teammate can run it with a separate Codex subscription and local context.

Before starting a `/goal` run:

- Read the assigned GitHub Issue.
- Read `docs/codex-goal-prototype-prompt.md`.
- Read the files listed in the prompt.
- Comment on the issue that the goal run has started.

Do not run the same `/goal` prompt against the same issue in two Codex sessions at once. Split into separate implementation issues instead.

## Agent skills

### Issue tracker

Issues live in GitHub Issues of `MarcZem/revel8-start-munich-hack-2026` (via `gh`). See `docs/agents/issue-tracker.md`.

Use these issue labels:

- `coordination`: sprint map, ownership, cross-agent notes.
- `goal-ready`: issue can be handed to a Codex `/goal` run.
- `agent-build`: implementation of the agent prototype.
- `evals`: eval cases, runners, reports, synthetic personas.
- `dashboard`: timeline, replay, rendered message views.
- `safety`: rules, guardrails, approval gates, fake-channel constraints.
- `docs`: documentation, pitch, architecture notes.

### Domain docs

Single-context: one `GLOSSARY.md` and `docs/adr/` at the repo root, created lazily. See `docs/agents/domain.md`.
