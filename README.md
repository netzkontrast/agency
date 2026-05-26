# agency

A Claude Code plugin: **ONE FastMCP engine + ONE bi-temporal GraphQLite graph**
that hosts everything an agent does. Its design is **four concepts** over one
substrate — and a **running seed** that proves the moat.

The human owns the goal. The engine serves it through three machine concepts and
one substrate:

- **Intent** — the human-owned root: purpose + acceptance, with the deliverable
  as an attribute (why/what merged). `capture · confirm · amend`. **Everything
  edges back to it via `SERVES`.**
- **Capability** — the craft, the OPEN set. An invokable action whose verbs are
  capability-defined and **role-tagged**: `act` (craft write) · `transform`
  (stateless compute) · `effect` (external side-effect). Discover via
  `<capability>.help`.
- **Lifecycle** — the task/agent state-machine. Write frame `open · move ·
  close`; observe frame `read · find · check · watch`. States align with A2A
  tasks. **An agent is a Lifecycle parameterization** (a remote async agent
  inserts `verify`; `COMPLETED ≠ done`). Gates pause at `input-required`.
- **Memory** — the moat. One bi-temporal, append-only graph holding every node
  and edge. `record · link · supersede` + `recall · find · validate`;
  `project(query, budget)` returns ranked, token-budgeted deltas. **Cross-concern
  provenance is a single traversal** — the one thing a flat SDK + memory-tool
  stack cannot answer in one hop.

The **Engine** is the substrate, not a concept: one FastMCP server + one graph,
the four-verb contract (`list_tools` / `call_tool` / `list_skills` /
`dispatch_skill`) + one `execute(code)` code-mode tool. Cross-cutting guards
(quality-score, loop-detection, compaction, `Slot`/quota) are engine middleware.

**5W1H is a lens, not the architecture.** Capability cross-sections are an
optional *observation* (a faceted home + `(home, target)` projection), never a
total function.

## Skills are atomic, gated, progressively-disclosed step-graphs

A skill is **not** a monolithic file loaded wholesale. It is a **Lifecycle
template: a graph of atomic Capability steps + Gates**, walked step-by-step via
code-mode. Each step discloses only the *next* instruction, so tokens are paid
per atomic step. Gates / intent-verification / askuser are `ctx.elicit` steps —
the Lifecycle pauses at `input-required`, the answer resumes it, the outcome is
recorded as a `Gate`. See [docs/vision/specs/skills-and-gates.md](docs/vision/specs/skills-and-gates.md).

## Status — the concept, the canon, the plan, AND a running seed

This repo is the **Concept, the Vision canon (v4), the Plan — and the first
RUNNING code**: `seed/`, a proof-of-concept on the real substrate (`graphqlite`
+ `fastmcp`) that proves the moat (cross-concern provenance in one traversal),
code-mode tool-chaining, and gate/elicitation human-in-the-flow. The canon
documents the full four-concept model; the seed makes the core claims runnable
and falsifiable. Everything else is **"specced — not built."**

**Start here:** [`docs/vision/CORE.md`](docs/vision/CORE.md) for the authoritative
v4 model, then [`docs/vision/`](docs/vision/README.md) for the canon and
[`seed/`](seed/README.md) for the running proof. The canon is authoritative;
where any prototype diverges from the canon, the canon wins.

> **Supersedes v2.1.** The earlier three-domain model (agentic / workflow /
> context) and the capability/aspect/lazy-domaining framing are superseded. An
> adversarial panel cut the six-domain 5W1H model to its irreducible four-concept
> core; 5W1H is now a lens, not the structure.
