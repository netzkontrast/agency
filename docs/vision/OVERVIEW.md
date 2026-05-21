---
slug: vision-overview
type: vision
status: ready
summary: The model — one engine, three domains (agentic, workflow, context). A capability is authored in one home domain and expressed across the domains as isomorphic aspects, materialized only when needed (lazy-domaining). Names derive from (domain, capability, export). Products live outside the system via drivers.
---

# Overview — one engine, three domains, capabilities as aspects

The agency plugin is ONE Claude Code plugin, ONE FastMCP engine, backed by ONE
GraphQLite graph. It exposes exactly **three domains**: `agentic`, `workflow`,
`context`. These are the only units exported as skills and as MCP (CodeMode)
surfaces. Everything the plugin can do is reached through one of the three.

## The three domains

- **agentic** — actions. Skills, MCP tool handlers, and the four-verb harness
  (`list_tools` / `call_tool` / `list_skills` / `dispatch_skill`). The engine
  that hosts everything.
- **workflow** — process. Graph-walking state machines: phases, gates,
  continuations — lazily linked as paths through the graph.
- **context** — memory. The GraphQLite node/edge graph + schemas + artefact
  drivers + hooks. The only persistent state.

## Capabilities express themselves as aspects

A **capability** is a vertical area of work — e.g. `jules`, `music`, `novel`.
It is **authored in exactly one home domain** (its primary concern). It then
expresses itself across the domains as **aspects**:

- its **agentic aspect** — its actions,
- its **workflow aspect** — its state machine,
- its **context aspect** — its memory.

The three aspects are the SAME capability faithfully restated in each domain's
language — they are **isomorphic**. A capability is placed by its primary
concern: orchestration → home in agentic, a multi-step process → home in
workflow, a data/schema concern → home in context.

## Lazy-domaining

A capability materializes an aspect in a non-home domain **only when it needs
one** — this is **lazy-domaining**.

- The default is **lazy graph data**: a workflow aspect appears as `Phase` /
  `Continuation` nodes the moment the capability first needs state; a context
  aspect appears as `Artefact` / memory nodes the moment it first produces or
  learns. No authored folder is required.
- A capability with **fixed structure** may instead **author** an aspect — a
  workflow pipeline of phase files + gates, or context schemas + templates.
- Authored or lazy, **the holding domain owns the aspect**.

There is **no eager triplication and no forced isomorphism** beyond what a
capability actually needs.

## Export & naming (self-explaining)

The harness derives every public name from `(domain, capability, export)`:

- MCP tools: `mcp__<domain>_<capability>_<export>` — e.g.
  `mcp__agentic_jules_create`, `mcp__workflow_jules_advance`,
  `mcp__context_jules_recall`.
- Skills: `/<plugin>:<domain>:<capability>:<export>` — e.g.
  `/agency:agentic:jules:research`.

The name alone tells you the domain, the capability, and the export. The
capability name is shared across domains; each domain owns its own exports for
that capability. CodeMode renders one call-surface per domain; a capability's
exports appear as grouped functions within it (e.g. `agentic.jules.create(...)`).

## Per-domain aspect shape (when authored)

When a capability authors an aspect, it follows that domain's canonical shape —
so knowing a domain teaches you all its aspects:

| Domain | Authored aspect shape |
|---|---|
| agentic | `manifest.toml` + `handlers/<export>.py` + `skills/<export>/SKILL.md` |
| workflow | `manifest.toml` + `phases/<NN>-*.md` + `gates/*.yaml` |
| context | `manifest.toml` + `schemas/*.schema.json` + `templates/*.jinja` |

Adding a capability = authoring its **home aspect** in one domain and letting
the other aspects stay lazy until needed.

## Stress test (proves the model)

- **`jules`** (home agentic): agentic aspect authored (lifecycle / patch /
  bulk); workflow aspect lazy (session state machine, incl. silent-fail
  recovery — `COMPLETED` ≠ done); context aspect lazy (sessions / patches /
  lessons). One authored aspect.
- **`music`** (home workflow): heavy in all three; authors all three
  (pre-generation + pre-release pipelines with hard gates; ~50 skills; Track /
  Album schemas + audio artefacts). The "fully-domained" extreme — proves home
  ≠ exclusive ownership.
- **`meta-development`** (self-improvement, home agentic): workflow aspect is a
  LOOP (observe → diagnose → propose → implement → verify → record); context
  aspect is the system's own graph (reflexive); dispatches `jules` →
  cross-capability dispatch.

## Cross-capability dispatch (sketch, not yet first-classed)

One capability invokes another's aspect via the four-verb contract, recorded as
a `DISPATCHED_TO` graph edge (e.g. `meta-development` → `jules`). The edge type
already exists in the graph.

## Products live outside the system

The three domains describe the machine. Final artefacts (code patches, files,
documents) are the product: they live in user-owned storage via pluggable
artefact drivers and are recorded as `Artefact` nodes in the graph. No metadata
sidecar files are written to user storage.
