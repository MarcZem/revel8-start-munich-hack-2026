# Research Finding Schema

Locked design for issue #10 (research/OSINT evidence pipeline). Every retrieved
item becomes one or more **atomic findings** in this format. Findings are stored
append-only as JSONL, one per line, per target: `research/<target_id>.jsonl`.

## Record

```json
{
  "id": "f_julius_founded_2024",
  "target_id": "julius",
  "category": "role",
  "fact": "Co-Founder of revel8 since Jun 2024 (role based in Berlin).",
  "reliability": "belastbar",
  "warum": "",
  "observed_at": "2026-11-21",
  "contradicts": [],
  "sources": [
    { "url": "https://www.revel8.ai/author-julius", "channel": "web",
      "excerpt": "Co-Founder and CEO at revel8" },
    { "url": "https://www.sans.org/profiles/julius-muth", "channel": "web",
      "excerpt": "revel8 was founded in 2024" }
  ]
}
```

## Fields

| Field | Required | Rule |
|---|---|---|
| `id` | yes | Stable. `f_<target>_<slug>` or a hash of `target_id` + normalized `fact`, so the same claim dedups to one record. |
| `target_id` | yes | Scenario target id (`julius`, …). |
| `category` | yes | One of `role \| project \| talk \| network \| company \| other`. |
| `fact` | yes | **One atomic, self-contained claim.** Qualifiers stay in the sentence (never split "X in Berlin" into two facts). As short as possible, as precise as necessary. |
| `reliability` | yes | `belastbar \| unsicher \| unbelastbar`. Set by rule, not model vibe (see below). |
| `warum` | only if `reliability != belastbar` | One short line naming the doubt / conflict. Empty when belastbar. |
| `observed_at` | yes | ISO date the fact was gathered. |
| `contradicts` | yes (may be `[]`) | Ids of findings this one conflicts with. |
| `sources` | yes, ≥1 | Each `{ url, excerpt, channel? }`. `excerpt` is the **verbatim** text that backs the claim. Same claim from a new source merges into this list. |

## Reliability rule (deterministic)

The extraction model proposes facts; a rule assigns `reliability`, so the model
cannot invent confidence:

- `belastbar` — ≥2 independent sources agree **and** `contradicts` is empty.
- `unsicher` — exactly 1 source, no conflict.
- `unbelastbar` — any entry in `contradicts` (name the conflict in `warum`).

## Contradictions

Never silently drop a conflicting fact. Keep **both**, link via `contradicts`,
drop both to `unsicher`/`unbelastbar`, and name the conflict in `warum`. The
contact planner then knows the ground is soft and does not build the attack on it.
(Seen live: "Stanford" vs "TU Darmstadt/WHU" for Julius Muth — atomic + contradicts
flags only the education claim, not the whole source.)

## Why `sources` and `warum` stay (minimal)

- `sources`+`excerpt`: non-negotiable but lean (url + excerpt only). Scoring deducts
  up to −5 for wrong facts and the 40-pt architecture rubric rewards traceable
  provenance. Without a backing excerpt, `reliability` is an empty claim.
- `warum`: conditional. Zero cost on clean facts; one useful line where it is shaky.

## Mapping to existing code

Extends `Evidence` in `agent_core/schema.py` (reuse, don't greenfield). The graph's
`min_confidence` filter keeps working via a derived numeric:
`belastbar→0.9, unsicher→0.5, unbelastbar→0.2`.

## Retrieval → findings

Sources come from Agent Reach (loginfree: `web`/Exa, `youtube`, `github`,
`linkedin`-public) plus the model's own web search. Extraction model:
`DeepSeek-V4-Flash` via the AMD Token Factory (`LOCAL_LLM_*`, see AGENTS.md).
