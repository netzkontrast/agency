# agency — Claude Code plugin

This repo **is** the `agency` plugin: a three-domain engine for agent
workflows. The design canon in `docs/vision/` is authoritative — **the Vision
wins; code serves it.**

## The model (detail: docs/vision/OVERVIEW.md)

- Three exported base domains: `agentic` (WHO/HOW), `workflow` (WHEN),
  `context` (WHAT). Only these are exported as skills + MCP (CodeMode).
- A **row** is a capability nested in its one owning domain. `jules` is an
  agentic row.
- Names derive from `(domain, row, export)`: `mcp__<domain>_<row>_<export>`,
  `/<domain>:<row>:<export>`.
- One engine (FastMCP) + one graph (GraphQLite) + artefact drivers. See
  `docs/vision/ARCHITECTURE.md`.

## Canonical paths

| What | Path |
|---|---|
| agentic row | `agentic/<row>/{manifest.toml, handlers/<export>.py, skills/<export>/SKILL.md}` |
| workflow row | `workflow/<row>/{manifest.toml, phases/<NN>-*.md, gates/*.yaml}` |
| context row | `context/<row>/{manifest.toml, schemas/*.schema.json, templates/*.jinja}` |
| engine | `agentic/_bootloader.py`, `agentic/_harness/`, `workflow/_runner/`, `context/{_store,_hooks,_drivers}` |

## Where to look

| Task | Open |
|---|---|
| The model | `docs/vision/OVERVIEW.md` |
| The runtime | `docs/vision/ARCHITECTURE.md` |
| The four-verb contract | `docs/vision/specs/04-agentic-base.md` |
| Add a row | `docs/vision/OVERVIEW.md` (Export & naming) |
| A contract/schema | `docs/vision/specs/` |
| Terms | `docs/vision/VOCABULARY.md` |
| What's next | `docs/ROADMAP.md` |

## How to work

- Design before code: `superpowers:brainstorming` → `superpowers:writing-plans`
  → `superpowers:executing-plans`. New skills via `superpowers:writing-skills`.
- Analysis / design / spec review: the `sc:` (superclaude) skills.
- Claude Code plugin / MCP / hook mechanics: the
  `superpowers-developing-for-claude-code` plugin.
- Add a capability = add **one row to one domain**. No cross-domain
  scaffolding.

## Dev

- Install deps: `bin/agency-dev-install` (idempotent).
- Test: `pytest tests/`.
- Develop on the active feature branch; keep `docs/vision/` authoritative.
