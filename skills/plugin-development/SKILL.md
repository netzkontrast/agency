---
name: plugin-development
description: Use when building or extending a Claude Code plugin — scaffolding a manifest, authoring skills or commands, adding a marketplace entry, or wiring a new capability into the agency engine.
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
---

# Plugin Development

## Overview

Develop a Claude Code plugin with the **agency** engine. The plugin-development
capability authors every artefact a plugin needs — manifest, skills, commands,
marketplace entry — as strict, template-backed documents, and the engine records
each as provenance. Adding a new capability to the engine is just **adding a
file** in `agency/capabilities/`: it self-registers and auto-wires.

## When to use

- You're scaffolding a new plugin (`.claude-plugin/plugin.json`).
- You're authoring a SKILL.md or a slash command.
- You're publishing to a marketplace (`marketplace.json` entry).
- You're adding a capability/verb to the agency engine.

## The chain (one prestructured document per step)

The `plugin-dev` skill walks one phase at a time (progressive disclosure), each
step emitting a strict artefact, ending at a hard confirm gate:

`manifest → skill → command → marketplace entry → confirm`

Drive it over the code-mode contract (works in MCP, as a Skill, or bash-only):

```bash
python -m agency.cli --db plugin.db intent \
  --purpose "build a demo plugin" --deliverable "installable plugin" --acceptance "manifest valid"

python -m agency.cli --db plugin.db search "plugin scaffold"
python -m agency.cli --db plugin.db execute --code '
m = await call_tool("capability_plugin_scaffold", {"name": "demo", "version": "0.1.0", "description": "A demo", "intent_id": INTENT})
return m
'
```

## Adding a capability (no wiring)

Drop a module in `agency/capabilities/` that defines a `Capability` with
role-tagged verbs (`act` / `transform` / `effect`) and, optionally, an
`OntologyExtension` (its own node types, enums, skills, template-schemas). The
engine discovers it by reflection and auto-wires one tool per verb.

## Common mistakes

- Bare `owner/name` as a marketplace `source` — must be a `{source: github, repo}` object.
- Skill `name` not kebab-case, or `description` not starting with "Use when…" — run the CSO linter (`capability_plugin_lint_skill`).
- Forgetting that `commands`/`agents` paths in the manifest **replace** the default dir while `skills` **extends** it.
