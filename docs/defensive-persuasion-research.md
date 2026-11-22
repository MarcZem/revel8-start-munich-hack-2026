# Defensive Persuasion Research

This note captures two public research projects that can help evaluate defenses against persuasive language and agent-to-agent influence. It describes offline, defensive use only. It does not add a message-generation or contact path to the Revel8 agent.

## Projects

### LLM Persuasion Benchmark

Repository: [lechmazur/persuasion](https://github.com/lechmazur/persuasion)

This project runs multi-turn conversations with one language model as persuader and another as target. It records the target's stance before and after the conversation and compares persuasion strength with target resistance. Its unit of evaluation is a proposition-centered dialogue, not an email campaign or a pretrained email-writing model.

Use it as a separate robustness harness:

1. Choose benign, non-sensitive propositions and fixed target starting stances.
2. Compare a baseline target with a target that has the proposed defense prompt or policy enabled.
3. Measure stance movement, refusal/abstention, consistency, and whether the defense accepts well-supported corrections while rejecting misleading claims.
4. Keep model versions, prompts, topic sets, and evaluation seeds fixed so defense changes can be compared reproducibly.

Do not use the benchmark's persuasion score as a deployment objective. A defense should reduce movement caused by unsupported or manipulative arguments without making the target resistant to valid evidence.

### Persuasion SLM

Repository: [lbustio/persuasion-slm](https://github.com/lbustio/persuasion-slm)

This repository describes a defensive analysis system for detecting persuasion principles in text, including emails and SMS. Its README describes a multi-label classifier paired with a fine-tuned small language model that explains detected signals and highlights evidence. Treat it as a candidate detector to evaluate, not as a trusted verdict or an automatically deployable component.

A safe integration boundary is an offline adapter that accepts a stored, authorized message and returns structured signals, for example:

```json
{
  "labels": [{"name": "urgency", "score": 0.82}],
  "evidence_spans": [{"start": 14, "end": 53, "label": "urgency"}],
  "abstain": false
}
```

The downstream policy should combine these signals with deterministic checks and calibrated thresholds. High-risk messages can be held for review or shown with a warning; low model confidence should lead to abstention. Avoid letting generated explanations make the decision by themselves.

## Suggested defensive evaluation flow

```text
authorized, labeled message corpus
  → normalize and redact personal data
  → Persuasion SLM detector
  → deterministic policy and abstention rules
  → warn, hold for review, or allow
  → offline metrics and error review
```

Use separate train, validation, and held-out test splits grouped by source or campaign to reduce leakage. Report precision and recall by persuasion category, false-positive rate on ordinary messages, calibration, abstention rate, and performance under benign paraphrases. Include both misleading pressure and legitimate urgent/security notices so the detector does not learn that urgency alone means maliciousness.

The Persuasion Benchmark can test whether a defense remains robust across multiple turns. Measure both resistance to misleading influence and responsiveness to correct, evidence-backed information. Keep its dialogue experiments separate from email-detector metrics; the tasks and labels differ.

## Implementation notes for this repository

- Keep this evaluation path offline and isolated from `agent_core/live_practice.py`, `agent_core/target_api.py`, and the contact loop.
- Store only authorized test messages and the minimum annotations needed for evaluation. Redact addresses, names, and other personal data before running models.
- Pin repository revisions, model checkpoints, dependencies, and licenses before adoption. The links above are project references, not a security or quality audit.
- Add a detector only after a held-out evaluation shows useful performance at an acceptable false-positive rate. Keep the current deterministic evaluation as a reproducible baseline.

## References

- [LLM Persuasion Benchmark repository](https://github.com/lechmazur/persuasion)
- [Persuasion SLM repository](https://github.com/lbustio/persuasion-slm)
