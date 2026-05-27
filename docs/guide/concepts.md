# Concepts (plain language)

Agency is **four concepts over one substrate**. If you understand these five
things, you understand the whole system. (The authoritative version is
[../vision/CORE.md](../vision/CORE.md); this page is the human summary.)

## The substrate: one graph

There is exactly **one store** — a bi-temporal, append-only graph (SQLite +
Cypher, via `graphqlite`). Every node and edge is stamped with the logical time
it became valid, so you can ask *what did this look like earlier?* and the answer
is reconstructable. Nothing is deleted; history is the point.

## Intent — *why + what*

The human-owned root. An **Intent** is a purpose, a deliverable, and an
acceptance check. Everything else in the graph edges back to an Intent via a
`SERVES` relationship, so you can always answer *what was this for?* in one hop.

`capture · confirm · amend` (amend forks a new version; the old one stays
reconstructable).

## Capability — the craft (the open set)

A **Capability** is a bundle of invokable **verbs**, each tagged by role:

- **act** — writes a crafted artefact (e.g. author a SKILL.md);
- **transform** — pure compute, no side effects (e.g. lint, checklist);
- **effect** — touches the outside world (e.g. dispatch a remote agent, git).

You don't register capabilities by hand. Drop a file in `agency/capabilities/`
and the engine **discovers it by reflection** and wires one tool per verb. Every
invocation is recorded as an `Invocation` node that `SERVES` the intent — so the
audit trail builds itself.

## Lifecycle — state + gates

A **Lifecycle** is a task/agent state machine (states align with the A2A task
vocabulary: `working`, `input-required`, `completed`, …). Two ideas matter:

- **An agent is a Lifecycle parameterization** — "delegating to an agent" is just
  opening a child Lifecycle dispatched to it.
- **A skill is a Lifecycle template** — an ordered list of phases walked one at a
  time, each phase declaring what it must `produce` before the next can start. A
  **hard gate** halts the walk until something is explicitly confirmed.

`COMPLETED ≠ done`: a step can report "completed" while the real-world effect
never landed — so effects are always verified.

## Memory — the moat

**Memory** is that one graph, with a small verb frame: `record · link · supersede`
to write, `recall · find · validate` to read, plus `project` (budget-capped reads)
and `provenance` (the moat). **Cross-concern provenance is a single traversal**:
from an Intent you reach every action that served it, the agent that performed it,
the artefact it produced, and the gates it passed or was blocked on — in one walk.
A flat "SDK + a memory tool" stack cannot answer that in one hop; this can.

## The engine — code-mode is the contract

The engine is a FastMCP server, but it does **not** hand you a flat list of tools.
Its entire public surface is three verbs:

- **`search`** — find a tool or discipline by what you're trying to do;
- **`get_schema`** — disclose just the slice you need (a verb's signature, a
  discipline's current phase);
- **`execute`** — run a small Python block that chains tools in a sandbox and
  returns only a compact result.

Two properties fall out of this, and they're the whole pitch:

- **Code-mode** — the contract *is* code. You chain many tool calls inside one
  `execute`; only the delta crosses back into the context window.
- **Context-mode** — progressive disclosure. You only ever load the schema/phase
  you need next, and heavy reference material is fetched on demand
  (`develop.reference`), never carried in the prompt.

The same contract is exposed three **isomorphic** ways — MCP, Skills, and a bash
CLI — so a bash-only agent is a first-class participant. See
[usage.md](usage.md).
