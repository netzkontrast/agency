# Getting started with Agency

**Agency** is an installable Claude Code plugin and a small engine for building
agentic systems on one idea: **everything an agent does is a node in one
provenance graph, and code-mode is the only contract.** This guide gets a human
from zero to running the engine and authoring a plugin with it.

## What you get

- An **engine** (`agency/`) — a FastMCP server over a bi-temporal graph
  (`graphqlite`), exposing exactly `search` / `get_schema` / `execute`.
- Three **capabilities** out of the box:
  - `plugin` — develop Claude Code plugins (scaffold manifests, author skills/commands, marketplace entries, lint skills).
  - `jules` — dispatch real remote async coding agents (Google Jules).
  - `reflect` — durable, scope-tagged cross-session memory.
- Installable **plugin** files at the repo root: `.claude-plugin/plugin.json`,
  `skills/` (incl. `plugin-development` and `skill-creation`), `commands/`.

## Install

This repository **is** the plugin (`.claude-plugin/plugin.json` is at the root).
Point a Claude Code marketplace entry's `source` at this repo, or add it as a
local plugin. To regenerate the install files from the live engine:

```bash
python -m agency.install
```

## Run it locally

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
pytest -q                      # 19/19 green
```

## The four concepts (plain language)

| Concept | What it is |
|---|---|
| **Intent** | *Why* + *what* + acceptance. Everything edges back to it via `SERVES`. |
| **Capability** | The craft — an invokable action, tagged `act` (writes an artefact), `transform` (pure compute), or `effect` (touches the world). |
| **Lifecycle** | Task/agent state machine + gates. A skill is a Lifecycle template: ordered phases walked one at a time. |
| **Memory** | The moat — one append-only, bi-temporal graph holding every node + edge. Cross-concern provenance is a single traversal. |

## Code-mode is the contract

You never get a flat list of tools. You `search` for tools, `get_schema` for the
ones you'll use, and `execute` a small Python block that chains them in a sandbox
— only a small delta crosses back into context. The same contract is exposed
three isomorphic ways: **MCP, Skills, and a bash CLI** (so a bash-only agent like
Jules is a first-class participant — see `AGENTS.md`).

```bash
python -m agency.cli --db g.db intent --purpose "demo" --deliverable "x" --acceptance "y"
python -m agency.cli --db g.db search "lint skill"
python -m agency.cli --db g.db execute --code \
  'return await call_tool("capability_plugin_lint_skill", {"name": "my-skill", "description": "Use when ...", "intent_id": INTENT})'
```

## Develop with it

- To **author a plugin or skill**, use the `plugin-development` and
  `skill-creation` skills (`skills/`). They drive the engine's plugin-dev chain
  and the RED-GREEN-REFACTOR skill-creation discipline.
- To **add a capability**, drop a file in `agency/capabilities/` that defines a
  `Capability`. It self-registers (reflection) and auto-wires one tool per verb —
  no central wiring. It can carry its own `OntologyExtension` (node types, enums,
  skills), merged strictly onto the core.

See `examples/` for a runnable walkthrough, and `vision/CORE.md` +
`vision/CAPABILITY-CLUSTERS.md` for the design and roadmap.
