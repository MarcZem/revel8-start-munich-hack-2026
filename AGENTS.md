# AGENTS.md

Context for coding agents working in this repo. Start with `README.md`, `docs/revel8-official-challenge.md` (authoritative case brief and rubric), `docs/architecture.md` (the system architecture), `docs/challenge-context.md` (audio-derived supplementary context) and `docs/playbook.md` (hackathon playbook, German).

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

## LLM endpoints

Default: **AMD Token Factory** (hosted models, free, no GPU credits, no OpenAI credits). It is OpenAI-compatible, so it plugs into the existing `LOCAL_LLM_*` variables and `scripts/check_vllm_endpoint.py`. Put this in `.env.local` (git-ignored), never in Git, issues or chat:

```bash
LOCAL_LLM_BASE_URL=https://radeon-global.anruicloud.com/api/v1
LOCAL_LLM_API_KEY=rc-...            # from the Token Factory tab in the AMD Radeon Cloud dashboard
WRITER_MODEL=DeepSeek-V4-Flash
```

Model ids from `GET $LOCAL_LLM_BASE_URL/models` (Nov 2026 — the UI label can differ from the id, e.g. UI "DeepSeek-V4-Flash-0731" vs id `DeepSeek-V4-Flash`; always use the id):

- Text: `DeepSeek-V4-Flash`, `Qwen3.8-27B`, `Gemma-4-31B-IT`, `d3`, `d3-flash`
- Vision (VLM): `DeepSeek-V4.1-Flash`, `MiniCPM-V-4.7-35B-A3B`, `MiniCPM-V-4.7-1B`, `MiniCPM5-2B`
- Decision/classifier: `Clef`

`DeepSeek-V4-Flash` is verified working and writes clean German (~13 s/reply). Switch `WRITER_MODEL` to `Qwen3.8-27B` or `Gemma-4-31B-IT` if DeepSeek shows "At capacity". Verify any choice with `python scripts/check_vllm_endpoint.py --env-file .env.local`.

OpenAI credits are separate: use them only for GPT models at `api.openai.com` (`OPENAI_API_KEY`).

### Own GPU instance (only if a model is not in the Token Factory)

The AMD Developer Cloud GPU (Radeon Pro W7900D, 48 GB) burns credits while it exists, even idle; destroy it when done. Pitfalls found on the vLLM image:

- The container's ROCm/HF env vars are set only for PID 1 (Jupyter), not for SSH shells. Without them `import torch` fails with `librocm_sysdeps_elf.so.1` missing. Fix: load `/proc/1/environ` (done in `/workspace/start_vllm.sh` on the instance).
- huggingface.co is blocked there; downloads go via `HF_ENDPOINT=https://hf-mirror.com` at about 1 MB/s (7B model ≈ 4 h). Do not override `HF_HOME`/`HF_ENDPOINT`.
- Do not `pip install torch`; it replaces the AMD build. Only `/workspace` survives a delete.

## Goal prompt

For long autonomous runs, record the goal and plan in `GOAL.md` at the repo root.

Before starting a `/goal` run:

- Read the assigned GitHub Issue.
- Read `GOAL.md` and `docs/architecture.md`.
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
