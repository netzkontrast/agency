---
slug: roadmap
type: roadmap
status: ready
summary: The Plan for the agency plugin (v2.1) — establish the engine + the four domains, anchor the first capability (jules in who, one authored aspect + lazy rest) as the minimal proof, then broaden. Maps research-surfaced features to their domain or engine home. The canon (docs/vision/) defines the model; this tracks the plan.
---

# Roadmap — the Plan (v2.1)

The canon in `docs/vision/` defines the **v2.1 four-domain 5W1H model**. This
file tracks the Plan. At this stage the repo is the Concept, Vision canon, and
Plan — all documentation; implementation follows on this branch in phased
commits. **Do not claim code is implemented that is not.** Everything is
**"specced — not built"** unless explicitly marked otherwise.

## 1 — Establish the engine + four domains

- **Engine** — the four-verb meta-contract (`list_tools` / `call_tool` /
  `list_skills` / `dispatch_skill`), code-mode call surface, progressive
  disclosure (cold boot exposes only the four meta-verbs), engine guards
  (quality-score, loop-detection, compaction checkpoints, `Slot`/quota).
- **intent** — `why.capture` / `why.confirm` → the pinned Intent node;
  `SERVES_INTENT` edges.
- **who / how / when / where** — the four domains over the two-axis canonical
  verb frame; `where` as the bi-temporal append-only GraphQLite graph with
  `where.project()`.

## 2 — First capability: `jules` (the minimal proof)

Anchored in **`who`** (its home domain): the async-coding orchestrator authored
as the **who aspect** (dispatch / handoff / release + poll / roster / verify +
the orchestration verbs), exposed as `mcp__who_jules_*` /
`/agency:who:jules:*` / `who.jules.*`. Its **how aspect** (`patch` / `bulk`),
**when aspect** (the task state machine, incl. silent-fail recovery —
`COMPLETED` ≠ done), and **where aspect** (sessions / patches / lessons) stay
**lazy** — they materialize as graph nodes when first needed. Plus the worked
example ([EXAMPLE.md](vision/EXAMPLE.md)).

This proves lazy-domaining end to end: **one authored aspect, the rest lazy, no
eager triplication, no eager folders for the other domains.**

## 3 — Broaden

More capabilities, each placed by primary concern, plus cross-cutting engine
features surfaced in research. Each research-surfaced feature is homed at a
specific domain OR the engine:

| Research-surfaced feature | Home |
|---|---|
| Context-mode (anchor triad, cache, watchers) | **where** |
| Ontology / GraphQLite (one graph, one schema registry) | **where** |
| `agents.yaml` role manifest | **who** |
| Composable watcher SDK | **who** |
| Quality / loop-detection | **engine guards** |
| Compaction checkpoints + memory tool | **engine guards** |
| Code-mode (callable domain API, in-sandbox deltas) | **engine** |
| Harness-in-harness (nested Dispatch + SharedContext) | **who** |
| `Slot` / quota accounting | **engine guards** (read by who) |
| Driver registry beyond `fs` (`repo`/`s3`/`http`/`drive`) | **where** |
| TOON tabular projections | **where** (`where.project`) |

- **More capabilities** — `music` (home `how`; authors craft + heavier
  aspects), `novel`, `meta-development` (home `who`; dispatches `jules`).

## Later

- Hot-reload of capabilities; an alternative graph driver for larger
  deployments.
