# Retro — Research/OSINT evidence pipeline (issue #10)

Built via the `build-agent` workflow. Spec: `docs/research-finding-schema.md`.

## What was built

- `agent_core/llm.py` — stdlib OpenAI-compatible chat client (AMD Token Factory / DeepSeek-V4-Flash), fails loud.
- `agent_core/schema.py` — `ResearchFinding` + `FindingSource` + `Reliability`, with `to_evidence()` mapping into the existing graph (reliability → confidence).
- `agent_core/research.py` — linear pipeline: retrieve (Agent Reach CLI) → extract atomic facts (DeepSeek) → dedup + reliability rule → optional LLM contradiction pass → JSONL per target.
- `scripts/run_research.py` — CLI.
- `tests/test_research.py` — 9 deterministic evals (no network).

## What ran

- Endpoint smoke: DeepSeek-V4-Flash → "bereit".
- Live run: `run_research --target julius` → **20 atomic findings** from 4 web sources → `research/julius.jsonl`, schema-valid (url + verbatim excerpt per source).
- Tests: **23/23 pass** (14 existing + 9 new). The belastbar path is proven by eval (same claim from 2 distinct domains merges and promotes).

## Decisions

- **Stack: stdlib, not LangGraph/Pydantic.** Diverged from the build-agent default: this is a linear workflow and the repo is deliberately dependency-free. A StateGraph here would be over-engineering ("Workflow vor Agent, Einfach vor autonom").
- **Reliability set by rule, not model.** ≥2 distinct domains → belastbar; 1 → unsicher; contradiction → unbelastbar. Removes model freedom to invent confidence.
- **Reused `Evidence`** via `to_evidence()` so the graph/router keep working.

## Known ceiling (honest)

- **Merge under-fires.** Dedup is exact normalized-string match, so paraphrased duplicates across sources ("Co-Founder & CEO" vs "co-founder of revel8") don't merge → in the live run **all 20 facts stayed `unsicher`**. Safe default, but `belastbar` rarely triggers on real data. Upgrade: LLM claim-clustering before `build_findings`. Marked with a `ponytail:` comment.
- Category `other` is overused by the extractor (6+/20). A tighter category prompt or a post-classify step would help targeting.
- Contradiction pass is one bounded LLM call; not stress-tested against real conflicts yet.

## Next (still issue #10 / downstream)

- Feed findings into the `KnowledgeGraph` + context router (currently they only serialize to JSONL).
- A "what matters now / susceptible-topic" reasoning step on top of the facts, feeding the contact planner.
- Then wire into the live-API contact loop (#9).

---

## Extension — deep research + graph + angle reasoner (plan: mighty-toasting-popcorn)

- **Deeper retrieval** (`research.py`): sub-queries (projects/volunteering/skills/talks), deep-read of non-walled pages, **GitHub repo+README enrichment** (resolve user → API read), optional user-provided source, recency (`published_at`). Marc run: **24 → 82 findings**, 27 from GitHub READMEs (real projects: SatteliTrees, Gut-ankommen, InnoSprint, TMA).
- **Graph** (`graph_loader.py`): findings → existing `KnowledgeGraph` (star shape, confidence from reliability). No new graph tech.
- **Angle reasoner** (`angle_reasoner.py`): 1 new agent (not 5 extractors). Ranked, **evidence-cited** hooks; hooks citing fake ids are dropped in code. Demoed on the **consented twin Julius** (not the real person) → 5 hooks.
- **Robustness**: `llm.chat` retries 429/5xx; `extract_facts` skips a source on persistent failure instead of aborting; `_first_json_array` salvages truncated arrays (fixed the 0-hooks bug).
- Tests: **29/29**. Boundary held: no credentialed LinkedIn scrape; Zapier confirmed can't read profiles.

### Known ceilings
- Still all `unsicher` (semantic merge unchanged — separate todo).
- Serial LLM calls make a full run ~4–6 min; parallelising extraction would cut it ~5×.
- GitHub repo reads pull project-level facts that are about the *repo/project*, not only the person (mild noise).

---

## Extension 2 — exec sources + second-hop entity following

Feedback: GitHub only helps for devs; execs live on company sites, press, speaker bios, podcasts.
- **Second hop** (`research.py` `plan_followups` + run loop): after pass 1, an LLM (GPT if `OPENAI_API_KEY`+`OPENAI_MODEL` set, else DeepSeek) names the entities worth chasing (company blog/press, named events, orgs, boards, co-founders); the pipeline searches + deep-reads those.
- **OpenAI provider** (`llm.py`): `chat(provider="openai")` + `openai_available()` — GPT for the smart reasoning, DeepSeek for bulk extraction. Key not set yet; runs on DeepSeek until added.
- Julius (exec, no GitHub) with second hop: **20 → 128 findings**, sources now revel8.ai, cisowhisperer/podbean/soundcloud (podcast interviews), tagesspiegel (press), peak.capital/merantix (investors), take-aware. Podcast facts = his own voice (priorities, threat-modeling habit, personal security setup, "10M human firewalls") — the convincing 20%.
- Tests 29/29.

### Still open
- All `unsicher` (semantic merge). Second hop + more sources make belastbar even more valuable to fix.
- Slow (serial LLM); parallelise extraction.
- Add `OPENAI_API_KEY`/`OPENAI_MODEL` to route the planner/hook reasoner to GPT.
