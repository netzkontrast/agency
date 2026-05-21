# agency — Claude Code plugin

This repo **is** the `agency` plugin: ONE engine that exposes three domains
over one FastMCP runtime and one GraphQLite graph. At this stage the repo is
the **Concept, Vision canon, and Plan**; implementation follows on this branch.
The design canon in `docs/vision/` is authoritative — **the Vision wins; code
serves it.**

## The model (detail: docs/vision/OVERVIEW.md)

- Three exported **domains**: `agentic` (actions — skills, tools, the four-verb
  harness), `workflow` (process — graph-walking state machines), `context`
  (memory — the GraphQLite graph, schemas, drivers, hooks). Only these are
  exported as skills + MCP (CodeMode).
- A **capability** is a vertical area of work (e.g. `jules`). It is authored in
  exactly one **home domain** and expresses itself across the domains as
  **aspects** (its agentic aspect, workflow aspect, context aspect — the same
  capability restated per domain, isomorphic).
- **Lazy-domaining**: a capability materializes an aspect in a non-home domain
  only when it needs one. Default = lazy graph data (workflow `Phase` /
  `Continuation`; context `Artefact` / memory nodes), no authored folder. A
  capability with fixed structure may instead AUTHOR an aspect. Authored or
  lazy, the holding domain owns the aspect. No eager triplication.
- Names derive from `(domain, capability, export)`:
  `mcp__<domain>_<capability>_<export>`, `/<plugin>:<domain>:<capability>:<export>`.
  The name alone tells you domain, capability, and export.
- One engine (FastMCP) + one graph (GraphQLite) + artefact drivers. See
  `docs/vision/ARCHITECTURE.md`.

## Canonical paths

| What | Path |
|---|---|
| agentic aspect | `agentic/<capability>/{manifest.toml, handlers/<export>.py, skills/<export>/SKILL.md}` |
| workflow aspect | `workflow/<capability>/{manifest.toml, phases/<NN>-*.md, gates/*.yaml}` (or lazy graph nodes) |
| context aspect | `context/<capability>/{manifest.toml, schemas/*.schema.json, templates/*.jinja}` (or lazy graph nodes) |
| engine | `agentic/_bootloader.py`, `agentic/_harness/`, `workflow/_runner/`, `context/{_store,_hooks,_drivers}` |

## Where to look

| Task | Open |
|---|---|
| The model | `docs/vision/OVERVIEW.md` |
| The runtime | `docs/vision/ARCHITECTURE.md` |
| The four-verb contract | `docs/vision/specs/04-agentic-base.md` |
| Add a capability | `docs/vision/OVERVIEW.md` (Export & naming) |
| A contract/schema | `docs/vision/specs/` |
| Terms | `docs/vision/VOCABULARY.md` |
| What's next | `docs/ROADMAP.md` |

## How to work

- Design before code: `superpowers:brainstorming` → `superpowers:writing-plans`
  → `superpowers:executing-plans`. New skills via `superpowers:writing-skills`.
- Analysis / design / spec review: the `sc:` (superclaude) skills.
- Claude Code plugin / MCP / hook mechanics: the
  `superpowers-developing-for-claude-code` plugin.
- Add a capability = author its **home aspect** in one domain; let the other
  aspects stay lazy until needed. No eager cross-domain scaffolding.

## Dev

- Install deps: `bin/agency-dev-install` (idempotent).
- Test: `pytest tests/`.
- Develop on the active feature branch; keep `docs/vision/` authoritative.
