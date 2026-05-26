---
slug: vision-architecture
type: vision
status: ready
summary: The runtime — one FastMCP engine with a four-verb meta-contract and a code-mode call surface; one bi-temporal append-only GraphQLite graph as the only persistent state; engine guards (quality-score, loop-detection, compaction, Slot/quota) as cross-cutting concerns, not domains. Lists the SOTA context-engineering commitments the engine honors.
---

# Architecture — one engine, one graph, four domain surfaces

## One engine (NOT a domain)

**FastMCP** is the only runtime. It hosts intent + all four domains in one
process. The engine is itself **not a domain** — it is the host. Its public
surface is the **four-verb meta-contract**:

- `list_tools` · `call_tool` · `list_skills` · `dispatch_skill`

Every domain verb (`mcp__who_*`, `mcp__how_*`, `mcp__when_*`, `mcp__where_*`,
plus the `why.*` intent verbs) is an entry in the one registry reached through
that contract. See [specs/engine.md](specs/engine.md).

### Code-mode (the token-efficiency primitive)

The engine can render the domains as a **callable code API** — `who.*`,
`how.*`, `when.*`, `where.*` as functions inside a sandbox. The agent writes
code that filters and joins **in-sandbox** and returns only **deltas**, never
raw history. Code-mode is the engine's core token-efficiency primitive: it
turns "fetch everything then read it" into "compute the answer, return the
diff."

## One substrate — where (bi-temporal, append-only)

The **`where` graph** is the only persistent state: a single GraphQLite graph
(SQLite + Cypher + node/edge primitives + graph algorithms). It is
**bi-temporal** (valid-time and transaction-time) and **append-only** — facts
are never overwritten; a corrected fact `supersede`s the old one, leaving an
audit trail. Typed nodes (`Intent`, `Session`, `Task`, `Gate`, `Artefact`,
`Dispatch`, `SharedContext`, `Slot`, `Capability`, …) and typed edges
(`SERVES_INTENT`, `DRIVES`, `PRECEDES`, `PRODUCES`, `DERIVED_FROM`,
`SUPERSEDES`, …) record everything the system knows.

Reads go through **`where.project()`**: a ranked, token-budgeted, TOON-encoded
projection of the graph that returns **deltas**, never raw history. This is how
an append-only store coexists with compaction — the history is complete on
disk; what the model sees is always a budgeted projection. See
[specs/where.md](specs/where.md).

## Engine guards (cross-cutting — NOT domains)

These are engine concerns, referenced by who / when but owned by the engine.
Named as such so they are never mistaken for domains:

- **quality-score** — a confidence/quality signal on a step's output.
- **loop-detection** — halts repeating, non-progressing cycles.
- **compaction checkpoints** — named checkpoints (e.g. `compact-2026-01-12`)
  that summarize and prune working context while the full record stays in
  `where`.
- **`Slot` / quota accounting** — tracks concurrent dispatch slots and external
  quotas; `who` reads it to gate fan-out and `reclaim_slot`.

## Discovery & progressive disclosure

At cold boot the engine exposes ONLY the four meta-verbs; domain verbs and their
schemas load on demand. Under each domain the engine discovers capabilities and
derives their verb names per the naming scheme. A capability appears in a domain
only where it has materialized an aspect (lazy graph data or an authored
folder).

## Context-engineering commitments (SOTA)

The engine is built for long-horizon agentic work and MUST honor these:

- **Code-mode deltas** — render domains as a callable API; filter/join
  in-sandbox; return diffs, not whole objects.
- **Append-only bi-temporal graph + event log** — facts are never mutated;
  provenance and continuations survive across sessions.
- **Compaction checkpoints + memory tool** — named checkpoints (e.g.
  `compact-2026-01-12`) prune working context; the full record stays in `where`
  and is reachable via `where.project()`.
- **Ephemeral-subagent isolation** — heavy work runs in subagents that return
  small (1–2k token) typed summaries; the orchestrator keeps a pristine context.
- **Append-only, stable KV-cache prefixes** — prompt prefixes are stable and
  only appended to, preserving cache hits; the pinned Intent node is referenced
  by id, never re-pasted.
- **Tool-masking, not tool-removal** — unavailable tools are masked, not
  deleted, so the tool list (and its cache prefix) stays stable.
- **Progressive disclosure** — cold boot exposes only the four meta-verbs;
  domain verbs load on demand.
- **TOON for tabular projections** — graph projections render as TOON
  (token-oriented object notation) for compact tabular delivery.
