# Agency Plugin — Concepts You Need (self-contained)

You do **not** need to clone or read any other repository. This file is the
complete plugin model for the purpose of this task. (Canonical source:
`netzkontrast/agency`; this is a faithful summary of its `README.md` contract.)

## One engine, one graph, four concepts

The Agency plugin is **one MCP engine** backed by **one bi-temporal graph**.
Everything is expressed through **four concepts**:

1. **Intent** — what you want to accomplish (the *why*).
2. **Capability** — what the system can do (the *how*), exposed as **verbs**.
3. **Lifecycle** — the state of work in progress (the *when*).
4. **Memory** — the bi-temporal graph that records everything (the *what happened*).

## The wire contract — three primitives

Everything composes from three primitives:

- **search** — find capabilities by intent.
- **get_schema** — get the schema for a capability.
- **execute** — run a capability (code-mode: chain calls in one block).

> **The graph is the store; files are a rendered view.** Queryable/derived state
> lives in the graph. Files on disk are a *rendering* of that state — except a few
> human-authored canon documents, which are an explicit, documented exception.

## Capabilities and verbs

A **capability** groups related **verbs**. Each verb has a **role tag**:

- **`act`** — changes state and writes provenance to the graph.
- **`transform`** — a pure function: deterministic, decidable, no side effects
  (good for validators, lookups, linters, scoring).
- **`effect`** — touches the outside world (network, filesystem export, external
  service).

A domain (like *novel*) is added as a **capability extension**: it contributes
new verbs plus an **OntologyExtension** that adds nodes/edges to the graph
(strict node-merge, widen-only enums, a closed edge set). A domain should land
purely through this extension contract — **without modifying the engine core.**

## Gates and skills (multi-step flows)

- A **Lifecycle** tracks a multi-step piece of work through states.
- A **gate** is a checkpoint: it records `PASSED`, or `BLOCKED_ON` + an
  `input-required` pause that elicits a human/agent decision mid-flow. A
  `gate:"hard"` step cannot be skipped.
- A **skill** is walked with **progressive disclosure**: steps are revealed as
  you go, each step binding its inputs/outputs into the graph as provenance.

## What this means for the novel capability

When you propose how a narrative primitive should live in the plugin, decide for
each operation:

- Is it an **`act`** (mutates narrative state + records provenance), a pure
  **`transform`** (e.g. a Dramatica lookup, an NCP schema validation, a decidable
  coherence linter), or an **`effect`** (e.g. rendering chapters to disk)?
- What becomes a **graph node/edge** (queryable narrative state) vs a **rendered
  file** (a view, or a human-authored canon exception)?
- Where does a **gate** belong (e.g. a pre-drafting coherence gate)?
- Which checks are **decidable** (a `transform` linter with a deterministic
  pass/fail) vs **judgement** (need an LLM/human call)?

Keep every claim grounded in the source material you were pointed at — cite paths.
