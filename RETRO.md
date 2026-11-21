# Eval Harness Retro

## What changed

- Added deterministic, offline eval cases for Lena Kraus, Max Rieder, and Sara Neumann, all fictional personas.
- Covered normal runs, explicit pushback, unsupported facts, prompt injection, real-domain misuse, context routing, irreversible action blocking, committee selection, critic override, and minimized feedback export.
- Made the orchestrator stop cleanly when the evaluator blocks every candidate; no mock API call is made in that path.
- Added a gate rule for candidates explicitly marked as causing irreversible or external effects.

## Findings

- The default local committee chooses its highest-scoring sendable candidate and blocks the rule-break fixture.
- The deterministic code gate remains authoritative even when an intentionally misleading critic recommends sending an unsafe fixture.
- The fake API and the fixtures are local-only. The Revel8 target key is not required for these synthetic regression cases.
- The existing pushback loop records a reply and emits a re-planning lesson, but does not yet generate a follow-up contact. Multi-contact persistence remains a core follow-up.

## Remaining risks

- The real Revel8 adapter and its documented request/response schema are outside this issue; these evals do not claim live API coverage.
- Model committee behavior uses deterministic stubs, not live inference; remote-model latency, structured output, and cost remain unmeasured.
- Feedback export intentionally omits message bodies. It is suitable for audit and preference analysis but is not a direct fine-tuning dataset.

## Verification

Run `python3 -m evals.run_evals` and `python3 -m unittest discover -s tests`. The generated case report and feedback export are committed alongside the harness.
