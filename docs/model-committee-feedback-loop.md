# Model Committee and Feedback Loop

## Core idea

Use local open-weight models on AMD Developer Cloud as a committee instead of relying on a single model or immediate fine-tuning.

The system should first learn through structured test runs:

1. Generate several candidate strategies and messages.
2. Score them with independent critics.
3. Send only the best rule-compliant candidate to the simulation API.
4. Store the result, event, and critic scores.
5. Turn successful and failed attempts into preference data for later training.

This gives the team a strong architecture and a clear learning story without making live fine-tuning the critical path.

## Recommended model roles

### Social-engineering advisor

Candidate model: `smd20/socialengineering`

Use this model to propose tactics, pretexts, and scenario patterns for the authorized simulation. It should not be the only writer and should not decide what gets sent.

Good outputs:

- Possible contact angles.
- Social-engineering principle behind each angle.
- Likely target objections.
- Follow-up strategy after silence or pushback.
- Risk notes for the evaluator.

### Primary writer

Candidate models:

- `Qwen/Qwen3-14B`
- `Qwen/Qwen3-32B`
- `Mistral-Small-24B-Instruct`

Use the primary writer to draft the actual channel-specific message. It receives only the context paths selected by the context router, not the whole target profile.

The writer should produce multiple candidates with structured metadata:

```json
{
  "channel": "email",
  "sender_type": "fake_vendor_research_contact",
  "objective": "action",
  "angle": "vendor onboarding review",
  "message": "...",
  "landing_page_summary": "...",
  "used_evidence_ids": ["evidence_001", "evidence_004"],
  "known_risks": ["could sound too urgent"]
}
```

### Security and realism critics

Candidate models:

- `fdtn-ai/Foundation-Sec-8B-Instruct`
- `fdtn-ai/Foundation-Sec-8B-Reasoning`
- `athena129/CyberSecQwen-4B`
- `dreamgroup/MiST-8B`
- `ibm-granite/granite-3.3-8b-instruct`

Use critics to score each candidate before anything is sent to the challenge API.

Critic rubrics:

- Rule compliance: no real channels, no real domains, no malware, no prompt injection.
- Evidence fidelity: no unsupported or wrong facts.
- Persona fit: matches role, public interests, and current context.
- Craft: plausible channel formatting and tone.
- Persistence: sets up a coherent next step.
- Risk: likely to be disqualified or seen as unsafe.

The critics should return structured scores:

```json
{
  "candidate_id": "msg_002",
  "scores": {
    "rule_compliance": 4,
    "evidence_fidelity": 3,
    "persona_fit": 4,
    "craft": 3,
    "persistence": 4,
    "disqualification_risk": 1
  },
  "send_recommendation": "send",
  "reasoning_summary": "Uses high-confidence CFO evidence and fake-domain constraints; no real-world contact path."
}
```

Use a 1-4 scale where 4 is best, except risk where 1 is lowest risk.

## Orchestrator flow

```text
Person knowledge graph
   |
   v
Context router selects relevant paths
   |
   v
Social-engineering advisor proposes angles
   |
   v
Primary writer drafts candidates
   |
   v
Critic committee scores candidates
   |
   v
Safety gate blocks disallowed candidates
   |
   v
Orchestrator sends best candidate to fake/challenge API
   |
   v
API response updates strategy scores
   |
   v
Run log becomes eval + preference data
```

## Feedback data format

Every test run should store enough data to train or tune later.

```json
{
  "persona_id": "lena_kraus",
  "run_id": "run_2026_11_21_001",
  "objective": "action",
  "loaded_context_paths": ["person.role", "company.audit_preparation", "interest.supplier_risk"],
  "candidates": [
    {
      "candidate_id": "msg_001",
      "writer_model": "Qwen3-14B",
      "advisor_model": "smd20/socialengineering",
      "critic_scores": {},
      "sent": false,
      "rejection_reason": "Used low-confidence old job fact"
    },
    {
      "candidate_id": "msg_002",
      "writer_model": "Qwen3-14B",
      "advisor_model": "smd20/socialengineering",
      "critic_scores": {},
      "sent": true,
      "api_event": "link_opened"
    }
  ],
  "winner_candidate_id": "msg_002",
  "lesson": "Vendor-risk angle worked; old-job personalization should stay excluded."
}
```

## Training strategy

Do not start with fine-tuning. Start with committee scoring and reranking.

Fine-tuning becomes useful only after the team has enough high-quality examples:

- 100-300 synthetic or authorized examples for a small LoRA experiment.
- Preference pairs from real test runs.
- Clear evals that show improvement over the committee-only baseline.
- No training data from real private people.

If training is attempted, train a well-supported base model such as Qwen rather than a GGUF-only social-engineering model. Keep the framing as authorized security-awareness simulation writing, not real-world phishing or bypassing model safeguards.

## Pitch value

This is strong for the jury because it shows:

- Multiple specialized models with clear responsibilities.
- Local AMD Developer Cloud usage with reproducible inference.
- A learning loop based on simulation outcomes.
- Explainable scoring before each contact.
- Safety enforced by code and critics, not only by model refusals.

Suggested pitch wording:

> We do not rely on one black-box model to write messages. Our agent uses a local model committee: one advisor proposes the social-simulation angle, a writer drafts candidates, independent security critics score them, and a code-level safety gate blocks anything outside the rules. Every test run becomes preference data for later tuning.

## Hackathon priority

Build this in stages:

1. Committee interfaces and JSON contracts.
2. Stubbed local model outputs for deterministic evals.
3. Real local inference for one advisor and one writer.
4. Critic scoring and reranking.
5. Feedback data export.
6. Optional LoRA only if the baseline is already stable.

The demo can win without fine-tuning if the committee, logs, evals, and replay are strong.
