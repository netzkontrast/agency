---
slug: vision-overview
type: vision
status: ready
summary: The model — three exported base domains (agentic, workflow, context), capability rows nested inside their one owning domain, jules as an agentic row. Names derive from (domain, row, export). Products live outside the system via drivers.
---

# Overview — three domains, nested rows

The agency plugin exposes exactly **three base domains**: `agentic`,
`workflow`, `context`. These are the only units exported as skills and as MCP
(CodeMode) surfaces. Everything the plugin can do is reached through one of the
three.

## Domains own concerns

- **agentic** — WHO / HOW. Skills, MCP tool handlers, and agent orchestration
  (including dispatching other agents).
- **workflow** — WHEN. Process: phases, ordering, handoffs, gates.
- **context** — WHAT. The ontology graph, schemas, templates — the record of
  everything that exists.

## Rows nest in their owning domain

A **row** is a named capability inside the one domain that owns its concern. A
row groups that domain's exports for a capability; it does **not** span
domains.

- `jules` (async-coding orchestration) is a WHO/HOW capability, so it is an
  **agentic row** (`agentic/jules`).
- A capability is placed by its primary concern: orchestration → agentic, a
  multi-step process → workflow, a data/schema concern → context.
- A row reaches the other domains' services through the engine (the four-verb
  contract + the graph). It never adds rows to them.

## Export & naming

The harness derives every public name from `(domain, row, export)`:

- MCP tools: `mcp__<domain>_<row>_<export>` — e.g. `mcp__agentic_jules_create`.
- Skills: `/<domain>:<row>:<export>` — e.g. `/agentic:jules:research`.

CodeMode renders one call-surface per domain; a domain's rows appear as grouped
functions within it (e.g. `agentic.jules.create(...)`).

## Per-domain row shape

Within a domain, every row follows that domain's canonical shape — so knowing a
domain teaches you all its rows:

| Domain | Row shape |
|---|---|
| agentic | `manifest.toml` + `handlers/<export>.py` + `skills/<export>/SKILL.md` |
| workflow | `manifest.toml` + `phases/<NN>-*.md` + `gates/*.yaml` |
| context | `manifest.toml` + `schemas/*.schema.json` + `templates/*.jinja` |

Adding a capability = adding **one row to one domain**. There is no
cross-domain scaffolding and no requirement that a capability appear in more
than one domain.

## Products live outside the system

The three domains describe the machine. Final artefacts (code patches, files,
documents) are the product: they live in user-owned storage via pluggable
artefact drivers and are recorded as `Artefact` nodes in the graph. No metadata
sidecar files are written to user storage.
