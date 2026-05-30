---
slug: vision-overview
type: vision
status: ready
summary: The v4 model — one Engine, one bi-temporal graph, four concepts (Intent, Capability, Lifecycle, Memory). Intent is the human-owned root (why/what merged); Capability is the open craft (verbs role-tagged act/transform/effect); Lifecycle is the task/agent state-machine (an agent is a parameterization); Memory is the moat (provenance in one traversal). 5W1H is a lens. Names follow structure.
---

# Overview — Intent + Capability + Lifecycle + Memory

The agency plugin is ONE Claude Code plugin: **ONE FastMCP engine** backed by
**ONE bi-temporal GraphQLite graph**. Its design is **four concepts** over one
substrate. The authoritative spec is [CORE.md](CORE.md); this is the narrative.

> **5W1H is a lens, not the architecture** — a journalistic checklist, not an
> execution theorem.

## The substrate — the Engine

ONE FastMCP server + ONE graph. **Code-mode IS the contract**: the public surface
is exactly `search` / `get_schema` / `execute` (no four-verb surface). Tools are
discovered via `search` and called from inside `execute`; results stay in-sandbox,
only deltas reach context. Capabilities self-register by reflection (add a file).
Cross-cutting guards (quality-score,
loop-detection, compaction, `Slot`/quota) are engine **middleware, not
concepts**. The Engine is the host; it adds no concept vocabulary. See
[specs/engine.md](specs/engine.md).

## 1. Intent — the human-owned root (why/what merged)

A supersedable node carrying **purpose + acceptance**, with the **deliverable as
an attribute**. why and what are NOT two domains: a deliverable change with the
purpose held is just an attribute change on one Intent.

- `capture → confirm`, revised via `amend` (a bi-temporal `supersede`, so the
  prior version keeps its valid window for `as_of` reconstruction).
- **Everything edges back to it via `SERVES`.** See [specs/intent.md](specs/intent.md).

## 2. Capability — the craft (the open set)

An invokable action. Verbs are capability-defined and **role-tagged**:

- `act` — a craft write (e.g. write lyrics, apply a patch),
- `transform` — stateless compute, no side-effect (e.g. count syllables),
- `effect` — an external side-effect (e.g. master audio, upload, web search).

Discover via `<capability>.help` (progressive disclosure). Invoking a capability
records an **Invocation** in Memory, edged `SERVES → intent` (and
`PERFORMED_BY → agent` / `PRODUCES → artefact` when relevant). See
[specs/capability.md](specs/capability.md).

## 3. Lifecycle — the task/agent state-machine (+ gates)

The state-machine for a unit of work. Verb frame:

- write: **`open · move · close`**
- observe: **`read · find · check · watch`** (`check` validates against rules;
  `watch` is a continuous monitor).

States align with A2A tasks (`submitted · working · input-required · completed ·
failed · canceled`). **An agent (the old "who") is a Lifecycle parameterization**
— an agent-session is a Lifecycle whose transitions/observers differ: a remote
async agent inserts `verify` because `COMPLETED ≠ done`. **Gates =
`input-required` → Intent re-entry.** See [specs/lifecycle.md](specs/lifecycle.md).

## 4. Memory — the moat

One bi-temporal, append-only graph holding **every** node — Intent, Capability
invocations, Lifecycle states, agents, artefacts, gates — and their edges
(`SERVES`, `PRODUCES`, `PERFORMED_BY`, `DISPATCHED_TO`, `PRECEDES`,
`SUPERSEDED_BY`, `PASSED`).

- write: `record · link · supersede`
- read: `recall · find · validate`
- `project(query, budget)` → ranked, token-budgeted, supersession-aware (`as_of`)
  deltas.

**The one thing a flat SDK + memory-tool rival cannot match:** cross-concern
provenance is a *single traversal* — "every action that `SERVES` intent Q1, the
agent that ran it, the artefact it produced, the gate it passed." Proven in
the `agency/` package. See [specs/memory.md](specs/memory.md).

## Skills are atomic, gated, progressively-disclosed step-graphs

A skill is **not** a monolithic file loaded wholesale. A skill is a **Lifecycle
template: a graph of atomic Capability steps + Gates**, walked step-by-step via
code-mode. Each step discloses only the *next* instruction
(`search → get_schema → execute`), so tokens are paid per atomic step. The chain
*is* an executable dataflow graph, and because every `call_tool` records an
Invocation, it mirrors itself into the provenance graph.

**Gates / intent-verification / human-in-the-loop are `elicit` steps.** A step
can `ctx.elicit(prompt)` (ask the agent or human a one-line question and get a
typed answer), `ctx.sample(...)`, or `ctx.report_progress(...)`. A gate that
needs a human is just an `elicit` → the Lifecycle pauses at `input-required`, the
answer resumes it, the outcome is recorded as a `Gate`. "askuser" is therefore
not a special case — it is one node in the chain. See
[specs/skills-and-gates.md](specs/skills-and-gates.md).

## 5W1H is a lens, not the structure

A Capability may be *observed* through a faceted home concept plus an optional
`(home, target)` cross-section. That cross-section is an **observation**, NOT a
total function — total decomposition always leaks (Cyc / RDF / Ranganathan). When
a capability is genuinely cross-cutting (`verify`/QC, observability), an **AOP
escape hatch** models it across concepts rather than forcing a home. There is no
generating function and no eager triplication.

## Naming (structure-first, self-describing)

Concepts: `intent`, `capability`, `lifecycle`, `memory`. Tool names
`<concept>_<capability>_<verb>` — underscores, ≤64 chars, no dots; the client
injects the `mcp__` prefix. The serializer detail (skill/code-mode forms) is not
a top-level concern.

## What v0.1 proves

The installable plugin proves the moat and falsifies the risks: it
records an Intent, opens an agent Lifecycle, runs two genuinely different
capabilities (a `transform` and an agent), passes a gate via `elicit`, chains
tools in code-mode (one delta out), and answers the cross-concern provenance
query end-to-end. 56 passing on `graphqlite` + `fastmcp`. See the `agency/`
package and `tests/`.

## Scope

The canon DOCUMENTS the full four-concept model. **v0.1** (the `agency/` package,
56 passing) ships the engine, ten core capabilities (`plugin` · `skill_generator` ·
`develop` · `delegate` · `subagent` · `gate` · `workspace` · `branch` · `jules` ·
`reflect`), the reflection-based self-registration, the extensible ontology, and the
self-hosted install; domain capabilities load as example extensions (`examples/`).
Further capabilities are specced — see
[CAPABILITY-CLUSTERS.md](CAPABILITY-CLUSTERS.md).
