---
slug: vision-architecture
type: vision
status: ready
summary: The runtime (v4) — one FastMCP Engine with the four-verb contract + one execute(code) code-mode tool; one bi-temporal append-only GraphQLite graph as the only persistent state; engine guards (quality-score, loop-detection, compaction, Slot/quota) as middleware, NOT concepts. Lists the SOTA context-engineering commitments. Seed-proven where noted.
---

# Architecture — one Engine, one graph, four concepts

> Authoritative model: [CORE.md](CORE.md). This describes the runtime substrate.

## One Engine (the substrate, NOT a concept)

**FastMCP** is the only runtime. It hosts the four concepts (Intent, Capability,
Lifecycle, Memory) in one process. The Engine is **not a concept** — it is the
host. Its public surface is the **four-verb contract** plus **one code-mode
tool**:

- `list_tools` · `call_tool` · `list_skills` · `dispatch_skill`
- `execute(code)` — code-mode

Every concept verb (`<concept>_<capability>_<verb>`) is an entry in the one
registry reached through that contract. **Seed-proven:** the seed builds a real
FastMCP server exposing MCP-conformant tool names and the four-verb surface
(`agency_list_skills` / `agency_dispatch_skill` + `memory_graph_provenance` +
the capability verbs). See [specs/engine.md](specs/engine.md).

### Code-mode (the token-efficiency primitive — seed-proven)

On demand the Engine hides the raw tools behind **`search` / `get_schema` /
`execute`**. The agent writes code that chains tools and filters/joins
**in-sandbox**; intermediate results stay in the sandbox; large payloads return
as `elided_ref` handles; only filtered **deltas** reach context (Anthropic "Code
execution with MCP", 2025-11-04 — up to −98% tokens). The code *is* an executable
dataflow graph, and because every `call_tool` records an Invocation, that graph
mirrors itself into the durable provenance graph. **Seed-proven:** an `execute`
block chains a `transform` into an agent capability; 4 in-sandbox calls return
one small delta, and the chain appears as a connected provenance subgraph.

## One substrate — Memory (bi-temporal, append-only)

The **Memory graph** is the only persistent state: a single GraphQLite graph
(SQLite + Cypher + node/edge primitives + graph algorithms). It is
**bi-temporal** (valid-time and transaction-time) and **append-only** — facts are
never overwritten; a corrected fact `supersede`s the old one, leaving an audit
trail. Typed nodes (`Intent`, `Invocation`, `Lifecycle`, `Agent`, `Artefact`,
`Gate`, …) and typed edges (`SERVES`, `PRODUCES`, `PERFORMED_BY`,
`DISPATCHED_TO`, `PRECEDES`, `SUPERSEDED_BY`, `PASSED`, …) record everything the
system knows.

Reads go through **`project(query, budget)`**: a ranked, token-budgeted,
supersession-aware (`as_of`) projection that returns **deltas**, never raw
history. This is how an append-only store coexists with compaction — the history
is complete on disk; what the model sees is always a budgeted projection.
**Seed-proven:** bi-temporal `supersede` (the *what* changes while the *why*
holds, reconstructable `as_of`), `project`, and the one-traversal `provenance`.
See [specs/memory.md](specs/memory.md).

## Engine guards (cross-cutting middleware — NOT concepts)

CORE.md is explicit: these are engine middleware, never concepts. Named as such
so they are never mistaken for one of the four:

- **quality-score** — a confidence/quality signal on a step's output.
- **loop-detection** — halts repeating, non-progressing cycles.
- **compaction checkpoints** — named checkpoints that summarize and prune working
  context while the full record stays in Memory.
- **`Slot` / quota accounting** — tracks concurrent dispatch slots + external
  quotas; Lifecycle reads it to gate fan-out and `reclaim_slot`.

## Discovery & progressive disclosure

At cold boot the Engine exposes only the four-verb contract (+ code-mode);
capability verbs and their schemas load on demand. A skill discloses only the
*next* step's instruction, so tokens are paid per atomic step, not for the whole
skill. See [specs/skills-and-gates.md](specs/skills-and-gates.md).

## Context-engineering commitments (SOTA)

The Engine is built for long-horizon agentic work and MUST honor these:

- **Code-mode deltas** — chain tools in-sandbox; return diffs, not whole objects
  (seed-proven).
- **Append-only bi-temporal graph** — facts are never mutated; provenance
  survives across sessions (seed-proven).
- **Compaction checkpoints + memory tool** — prune working context; the full
  record stays in Memory and is reachable via `project`.
- **Ephemeral-subagent isolation** — heavy work runs in subagents that return
  small (1–2k token) typed summaries.
- **Append-only, stable KV-cache prefixes** — prompt prefixes are stable and only
  appended to; the Intent is referenced by id, never re-pasted.
- **Tool-masking, not tool-removal** — unavailable tools are masked so the tool
  list (and its cache prefix) stays stable.
- **Progressive disclosure** — cold boot exposes only the contract; verbs and
  per-step instructions load on demand.
- **TOON for tabular projections** — graph projections render as TOON when
  tabular-eligible, else JSON.
