---
slug: roadmap
type: roadmap
status: ready
summary: The Plan for the agency plugin — establish the engine, anchor the first capability (jules), then broaden. The canon (docs/vision/) defines the model; this tracks the plan and what comes next.
---

# Roadmap — the Plan

The canon in `docs/vision/` defines the model. This file tracks the Plan. At
this stage the repo is the Concept, Vision canon, and Plan; implementation
follows on this branch in phased commits. Do not claim code is implemented that
is not.

## 1 — Establish the engine

The three domains:

- `agentic` harness — four-verb contract, domain/capability discovery, name
  derivation, CodeMode rendering, cold-boot under the token budget (the harness
  exists in the prototype).
- `workflow` runner — graph-path walking, gate evaluation, `Continuation`
  nodes; a capability's workflow aspect materializes lazily as `Phase` nodes.
- `context` store — GraphQLite store, pre/post-tool hooks, artefact-driver
  protocol + `fs` driver, runtime schemas; the only persistent state.

## 2 — First capability: `jules`

Anchored in `agentic` (its home domain): the async-coding orchestrator
(lifecycle, patches, bulk, source, trim, aliases) authored as the agentic
aspect and exposed as `mcp__agentic_jules_*` + `/agency:agentic:jules:*`. Its
**workflow aspect** (session state machine, incl. silent-fail recovery) and
**context aspect** (session / patch / lesson memory) stay **lazy** — they
materialize as graph nodes when first needed. This proves lazy-domaining end to
end: one authored aspect, the rest lazy, no eager triplication.

## 3 — Broaden

More capabilities, each placed by primary concern, plus cross-cutting engine
features surfaced in research. Each item below is addressed as an engine
feature OR a capability/aspect:

- **More capabilities** — `music` (home workflow; authors all three aspects),
  `novel`, and others.
- **Context-mode** — manifest, anchor triad, cache, watchers.
- **Centralized ontology + GraphQLite** — one graph, one schema registry.
- **Quality / loop-detection / compaction** — engine-level guards for
  long-horizon runs.
- **`agents.yaml` role manifest** — declarative agent roles.
- **Composable watcher SDK** — reusable watchers for state changes.
- **Harness-in-harness** — the L1/L2/L3 dispatch ladder.
- **Cross-capability dispatch** — first-class one capability invoking another's
  aspect via the four-verb contract, recorded as a `DISPATCHED_TO` edge (the
  edge type already exists; e.g. `meta-development` → `jules`).
- **Driver registry beyond `fs`** — `repo`, `s3`, `http`, `drive`.

## Later

- Hot-reload of skills; an alternative graph driver for larger deployments.
