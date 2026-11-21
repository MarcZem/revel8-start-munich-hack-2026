# Retro — issue #17 writer system prompt (build-agent)

## What was built
- `agent_core/writer_prompt.py`: `build_writer_system_prompt(language)` + `DETECTION_TELLS` / `tells_in()`; self-check in `__main__`.
- `scripts/eval_writer_prompt.py`: runs the prompt on the live model over 3 synthetic briefs, scores tell-avoidance, writes `evals/writer_prompt_report.json`.
- `docs/writer-detection-tells.md`: research + sources.

## Result (ran, not claimed)
- Self-check: PASS (`python agent_core/writer_prompt.py`).
- Live eval on `DeepSeek-V4-Flash` (Token Factory), German: **3/3 cases clean**, zero detection tells, natural copy with a specific hook and a low-friction ask.

## Decisions / scope
- Focused on the message *text* only. Real-model committee wiring is #11; landing pages are #12; the hard constraints (fake domains, evidence whitelist, no secrets) stay in the evaluator gate as code, not prompt.
- Tell detection is a phrase/regex list, deliberately. Mimecast notes fixed lists decay, so `DETECTION_TELLS` is the eval's cheap guardrail, upgradeable to a stylometry scorer if eval starts missing cases.

## Follow-ups
- #11 should import `build_writer_system_prompt` as the writer system message and emit structured JSON (subject/body/landing) for the gate.
- Re-run the eval per model when switching `WRITER_MODEL`; add a fail case (a brief that tempts urgency) to prove the scanner bites.
