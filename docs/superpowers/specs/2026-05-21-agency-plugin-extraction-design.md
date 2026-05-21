---
slug: agency-plugin-extraction-design
type: design-spec
status: ready
owner: claude
created: 2026-05-21
updated: 2026-05-21
summary: Design for extracting the `agency` Claude Code plugin (3-column matrix engine + materialized `jules` row + Vision canon) from `the-agency-system` into this fresh repo. Approach A (lean Vision engine), jules tools row-native via the four-verb contract. The Vision always wins over prototype code.
---

# Design — extract the `agency` plugin into a fresh repo

## 0. Governing principle

**The prototype code is inspiration; the Vision is authoritative.** The
working implementation in `the-agency-system` (the matrix base layer + the
`jules` row + the standalone `jules-plugin` orchestrator) is the starting
point and proof that the architecture runs. Wherever the prototype diverges
from the design canon under `docs/vision/`, **follow the Vision** and finish
the engine + jules row to match it. A half-port is not acceptable: the engine
and the `jules` row must work end-to-end and be Vision-faithful.

## 1. Goal & end state

A fresh `agency` repository that **is** a Claude Code plugin (points at itself
as plugin source), containing:

1. The **3×N matrix engine** — the three base columns (`agentic`, `workflow`,
   `context`) with the FastMCP four-verb harness, GraphQLite-backed context
   graph, pre/post-tool hooks, artifact drivers, and the workflow runner.
2. The **`jules` row** — materialized across all three columns, backed by the
   *real* working orchestrator (lifecycle / patches / bulk / source / trim /
   aliases), exposed row-native through the four-verb contract.
3. The **Vision design canon** — consolidated under `docs/vision/`, the single
   source of truth that drives implementation.
4. A **self-hosting dev environment** — `CLAUDE.md` + `.claude/settings.json`
   wiring superpowers, superclaude (`sc`), and the plugin-writing plugin
   (`superpowers-developing-for-claude-code`), with the MCP server booting at
   session start.

Out of this effort's scope (later, on explicit go-ahead): wiring `agency` as a
plugin source in `the-agency-system` and deleting the moved/cruft directories
there.

## 2. Approach (decided)

- **Approach A — lean Vision engine.** MCP entry is `agentic/_bootloader.py`
  (the four-verb contract). The heavy unified server `servers/agency-mcp`
  (entangled with music/novel) is **left behind entirely**.
- **Jules tools row-native via four-verb.** The real orchestrator's tools are
  exposed as the `jules` row's MCP tools (`mcp__jules_*`) discovered through
  `agentic/jules/manifest.toml` and routed via the harness. The standalone
  `create_mcp()` factory is retired; a small loader adapter registers a
  handler module's functions as tools.

## 3. Target repo layout

```
agency/
├── .claude-plugin/
│   ├── plugin.json            # name: "agency"
│   └── marketplace.json       # plugin source "./"
├── .mcp.json                  # agency → agentic/_bootloader; + context7; + sequential-thinking
├── .claude/
│   └── settings.json          # enable superpowers/sc/plugin-writing plugin; SessionStart hook
├── CLAUDE.md                  # token-efficient dev instructions + overall goal
├── README.md
├── pyproject.toml             # single dependency manifest
├── requirements-dev.txt
├── agentic/
│   ├── __init__.py
│   ├── _bootloader.py
│   ├── _harness/{cell_loader,fastmcp_boot,name_deriver,codemode}.py
│   └── jules/
│       ├── manifest.toml      # [skills] exports + [tools] exports
│       ├── handlers/          # folded jules tools: lifecycle, patches, bulk, source, trim, aliases, query
│       ├── lib/               # sessions_state.py, watch_jules.py, api.py
│       └── skills/<export>/SKILL.md  # research + discipline skills
├── workflow/
│   ├── __init__.py
│   ├── _runner/{pipeline,envelope,gate,manifest}.py + evaluators/
│   ├── meta/{manifest.toml, phases/, templates/}
│   └── jules/{manifest.toml, phases/, gates/}
├── context/
│   ├── __init__.py
│   ├── _store/sqlite.py
│   ├── _hooks/{pre,post}_tool_use.py
│   ├── _drivers/{protocol,fs}.py
│   ├── _shared/schemas/*.schema.json
│   └── jules/{manifest.toml, schemas/, templates/}
├── bin/{agency-dev-install, jules-bulk}
├── tools/jules-patch-extract.py
├── tests/{agentic,workflow,context,jules}/
└── docs/
    ├── vision/                # consolidated design canon
    └── superpowers/specs/     # this design + the implementation plan
```

## 4. Component plan — port + finish to Vision

### 4.1 `agentic/` — the engine surface

Port `_bootloader.py` + `_harness/{cell_loader,fastmcp_boot,name_deriver,codemode}.py`.
**Finish to Vision:**

- `boot()` registers exactly the four verbs (`mcp__list_tools`,
  `mcp__call_tool`, `mcp__list_skills`, `mcp__dispatch_skill`) and wraps every
  derived tool with the pre/post hooks (C5 closed in the prototype — preserve
  it).
- Honor the `FastMCP 2.x add_tool` signature change noted in the retrospective
  (no `name=` kwarg; no `**kwargs` wrappers) — bind tool name/func as defaults.
- Cold-boot payload stays under the 500-token budget; port the CI test that
  enforces it.
- Name derivation follows the canonical convention: handlers at
  `<col>/<row>/handlers/<export>.py`, skills at
  `<col>/<row>/skills/<export>/SKILL.md` (the retrospective's "convention
  drift" lesson — Vision/deriver paths win over any prototype shortcut).

### 4.2 `workflow/` — path walking

Port `_runner/{pipeline,envelope,gate,manifest}.py` + `evaluators/` + `meta/`.
**Finish to Vision:**

- Pipeline walks `Phase` graph nodes; Continuation is a graph node (no
  `workflow/_state/` JSON files).
- Meta-row scaffolder emits `Cell`/`Phase`/`Row` graph nodes (W5 closed —
  preserve).
- **Phase-node seeder** (retrospective follow-up #1): add a `pipeline.boot()`
  step or `bin/agency-seed-phases` that upserts `Phase` nodes from
  `workflow/<row>/phases/*.md` so a hand-rolled row (jules) actually runs end
  to end. This is required for the jules row to be Vision-faithful, so it is
  in scope.

### 4.3 `context/` — graph + drivers

Port `_store/sqlite.py`, `_hooks/{pre,post}_tool_use.py`, `_drivers/{protocol,fs}.py`,
`_shared/schemas/*.schema.json`. **Finish to Vision:**

- GraphQLite is the substrate; keep the raw-SQLite fallback for now (dropping
  it is post-v0.1 per spec 08-v1; do not let its removal block this extraction)
  but isolate it so it is easy to delete later.
- `artefact-node.schema.json` (renamed from sidecar) carries `artifact_driver`
  + `driver_pointer`. No `.meta.json` sidecars are written to user storage.
- Canonicalize the runtime schemas from the vision drafts where the prototype
  stub disagrees (context owns graph schemas per architecture §4).

### 4.4 `jules` row — the first materialized row, backed by the real orchestrator

This is the headline deliverable ("the Jules code, the first thing we need").

- **Fold the real orchestrator** (`jules_mcp.{api,source}` +
  `jules_mcp.tools.{lifecycle,patches,bulk,aliases,trim}`) into
  `agentic/jules/handlers/` (+ shared logic in `agentic/jules/lib/`).
- `agentic/jules/manifest.toml` exports the tool set so the harness derives
  `mcp__jules_*`. A loader adapter lets `cell_loader` register a handler
  module's public functions as tools (the "glue").
- **Skills:** the existing `/agency:jules:research`, plus the three discipline
  skills (`context-safe-patch-handling`, `jules-orchestrator-discipline`,
  `silent-fail-recovery`) become jules-row skills/references.
- **Workflow cells:** `workflow/jules/{phases/01-research.md,02-synthesize.md,
  gates/research-complete.yaml}` (port; the gate is currently a placeholder —
  keep it honest: mark it as a stub in prose, do not overstate behavior).
- **Context cells:** `context/jules/{manifest.toml, schemas/research-topic +
  finding, templates/research-brief.md.jinja}`.
- **CLI clients:** `bin/jules-bulk` + `lib/watch_jules.py` stay as thin clients
  that import the same row lib (used outside Claude Code). Fix the
  `jules_create` import path (retrospective follow-up #7) so the CLI works
  without a one-shot dispatcher.

### 4.5 Retired / not ported

- `servers/agency-mcp` (music/novel unified server) and all music/novel
  handlers, tools, and tests.
- `skills/music/*` (54 skills), `artists/`, `genres/`, `audio/`, `novels/`,
  `documents/`, `overrides/`, `state/`, `migrations/`, `index.html`.
- The `jules-plugin/` wrapper directory — its **code folds into the row**; the
  wrapper (its own `.claude-plugin`, `.mcp.json`, `create_mcp()`) is retired.
- bitwize-music `.claude` setup, `IDEAS.md`, `REFACTOR_DESIGN.md`.

## 5. Vision canon consolidation

- Port `the-agency-system/vision/` → `docs/vision/` verbatim as authoritative
  canon (Overview, architecture, nextsteps, retrospective, `specs/`,
  `specs/schemas/`).
- **Mine** `the-agency-system/Plan/` for durable material that *expands* the
  Vision without contradicting it — primarily `Plan/harness/VOCABULARY.md`
  (canonical glossary) and `Plan/decisions/readme.md` (ADR index). Fold the
  durable bits into `docs/vision/` (e.g., a `docs/vision/VOCABULARY.md`); do
  **not** port `Plan/` wholesale. It is the earlier attempt being consolidated.

## 6. Self-hosting dev environment

### 6.1 `.claude-plugin/`

- `plugin.json` — `name: "agency"`, description, homepage `netzkontrast/agency`.
- `marketplace.json` — single plugin, `source: "./"` (repo-as-plugin).

### 6.2 `.mcp.json`

```json
{
  "mcpServers": {
    "agency": { "type": "stdio", "command": "python",
                "args": ["-m", "agentic._bootloader"] },
    "context7": { "type": "stdio", "command": "npx",
                  "args": ["-y", "@upstash/context7-mcp"] },
    "sequential-thinking": { "type": "stdio", "command": "npx",
                  "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"] }
  }
}
```

### 6.3 `.claude/settings.json`

- `extraKnownMarketplaces`: `superpowers-marketplace` (obra), `superclaude`
  (SuperClaude-Org), `superpowers-developing-for-claude-code` (obra),
  `agency-marketplace` (this repo).
- `enabledPlugins`: `superpowers`, `sc`, `superpowers-developing-for-claude-code`,
  `agency@agency-marketplace`.
- `enabledMcpjsonServers`: `agency`, `context7`, `sequential-thinking`.
- `hooks.SessionStart`: run `bin/agency-dev-install` (idempotent) to ensure the
  venv + `fastmcp[code-mode]` + deps exist so the MCP server boots each session.

### 6.4 `CLAUDE.md` (token-efficient)

Contents (lean; links to `docs/vision` rather than inlining):

- **Overall goal** — develop the `agency` plugin: the 3×N matrix engine + rows.
- **Governing principle** — Vision (`docs/vision/`) wins over prototype/legacy.
- **Matrix law in ~5 lines** — 3 columns (agentic/workflow/context) × N rows;
  column + row isomorphism; name-driven discovery; one engine (FastMCP) walks
  one graph (GraphQLite); artifacts live in user storage via drivers.
- **Canonical paths/naming** — handler/skill/manifest conventions.
- **Skill order** — brainstorm → writing-plans → executing-plans;
  `writing-skills` for new skills; `sc:` for analysis/design/spec-panel;
  `superpowers-developing-for-claude-code` for CC plugin/MCP/hook mechanics.
- **Dev commands** — `bin/agency-dev-install`; `pytest tests/`; the
  `claude/extract-agency-plugin-o4JRc` dev-branch convention.

## 7. Validation gate (before reporting to the user)

| # | Check |
|---|---|
| 1 | `python -m agentic._bootloader --emit-cold-boot` lists the four verbs |
| 2 | `pytest tests/{agentic,workflow,context,jules}` green |
| 3 | `discover()` finds `mcp__jules_*` tools + `/agency:jules:*` skills |
| 4 | Cold-boot payload under 500 tokens (CI test) |
| 5 | jules lifecycle smoke (mocked API) round-trips through a derived tool |
| 6 | jules workflow phase 01 reaches `_walk_phase` and returns a typed envelope |
| 7 | No music/novel imports leak into the ported tree (`grep` guard) |
| 8 | No `*.meta.json` sidecars; `workflow/_state/` does not exist |

## 8. Deferred (explicitly post-extraction)

- Cross-row dispatch (vision spec 09), drivers beyond `fs`, additional rows
  (music/novel/podcast), hot-reload, dropping the raw-SQLite fallback,
  centralizing the inline error-code catalogue (retrospective #3) unless it
  blocks the jules row.
- Wiring `agency` as a plugin source in `the-agency-system` and deleting the
  moved/cruft directories there — done only after the port is validated and the
  user gives explicit go-ahead.

## 9. Process / skill order

Brainstorming (this doc) → `superpowers:writing-plans` (sharpened with
`sc:sc-design` / `sc:sc-spec-panel`) → `superpowers:executing-plans` /
`superpowers:subagent-driven-development` → `superpowers:verification-before-completion`
before reporting. Jules fan-out and parallel subagents used where columns are
independent.
