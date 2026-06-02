---
name: plugin-development
description: Use when building or extending a Claude Code plugin — scaffolding a manifest, authoring skills or commands, adding a marketplace entry, or wiring a new capability into the agency engine.
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - mcp__plugin_agency_agency__search
  - mcp__plugin_agency_agency__get_schema
  - mcp__plugin_agency_agency__execute
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
- You're troubleshooting plugin install, MCP-server startup, or component discovery.
- You're preparing a release (versioning, tagging, regenerating the install).

## When NOT to use this skill

Use the more specific skill instead. See [`references/related-skills.md`](references/related-skills.md) for the full decision matrix.

| Task | Better skill |
|---|---|
| Authoring a `@verb`-decorated capability file in `agency/capabilities/` | `agency:authoring-capabilities` |
| Writing or revising any SKILL.md | `agency:skill-creation` (or `superpowers:writing-skills`) |
| Building a generic Claude Code plugin (not agency-engine-based) | `superpowers-developing-for-claude-code:developing-claude-code-plugins` |
| Debugging a non-plugin failure | `agency:systematic-debugging` |
| Brainstorming the shape before coding | `agency:brainstorming` or `superpowers:brainstorming` |

## Pre-flight: run the doctor first

Before any plugin-development work in this repo, run the substrate health check:

```python
await call_tool('agency_doctor', {})
```

It surfaces missing deps, an unbootstrapped venv, a non-writable `.agency/`
directory, and `JULES_API_KEY` / `CLAUDE_PROJECT_DIR` state. Every issue
comes with a copy-pasteable fix in `next_steps[]`. Skipping this step is
how onboarding sessions get stuck for an hour.

## The chain (one prestructured document per step)

The `plugin-dev` walker walks one phase at a time (progressive disclosure),
each step emitting a strict artefact, ending at a hard confirm gate:

```
manifest → skill → command → marketplace entry → confirm
```

Drive it over the code-mode contract (works in MCP, as a Skill, or bash-only):

```bash
python -m agency.cli --db plugin.db intent \
  --purpose "build a demo plugin" \
  --deliverable "installable plugin" \
  --acceptance "manifest valid"

python -m agency.cli --db plugin.db search "plugin scaffold"

python -m agency.cli --db plugin.db execute --code '
m = await call_tool("capability_plugin_scaffold", {
    "name": "demo", "version": "0.1.0",
    "description": "A demo", "intent_id": INTENT,
})
return m
'
```

Equivalent inside Claude Code (MCP-first when the agency plugin is
installed — Rule #1 of `CLAUDE.md`):

```python
# substrate (no intent_id needed):
r = await call_tool('intent_bootstrap', {
    'purpose': '...', 'deliverable': '...', 'acceptance': '...',
})
iid = r['intent_id']

# then any capability_*_* verb with intent_id=iid
m = await call_tool('capability_plugin_scaffold', {
    'name': 'demo', 'version': '0.1.0',
    'description': 'A demo', 'intent_id': iid,
})
```

## Adding a capability (no wiring)

Drop a module in `agency/capabilities/<name>.py` (or a folder for heavy
capabilities) that defines a `CapabilityBase` subclass with role-tagged verbs
(`act` / `transform` / `effect`) and, optionally, an `OntologyExtension` (its
own node types, enums, skills, template-schemas). The engine discovers it by
reflection and auto-wires one tool per verb.

For the full discipline (scaffold-first, block-mode lint, the three kinds:
light/medium/heavy), use [`agency:authoring-capabilities`](../authoring-capabilities/SKILL.md)
and read [`references/agency-patterns.md`](references/agency-patterns.md).

## The dev loop (test → iterate → release)

A condensed adaptation of the Superpowers Phase-4-through-Phase-6 workflow,
agency-flavoured:

1. **Test locally.** `python -m pytest -q` is green. For capability work,
   `capability_plugin_lint_capability(name=…)` is `ok=True` in block mode.
2. **Smoke-test the install.** Run `python -m agency` standalone; it should
   bind to stdio and accept JSON-RPC. Run `agency_doctor` to confirm.
3. **Regenerate the install.** `python -m agency.install` rewrites
   `plugin.json`, `marketplace.json`, `.mcp.json`, and the slash-commands
   from the live engine. Commit the regen alongside the source change.
4. **Tag + release.** Semver bump, git tag, push tag. The marketplace entry
   in `.claude-plugin/marketplace.json` references the tag.

Full lifecycle in [`references/release-and-distribution.md`](references/release-and-distribution.md).

## Common mistakes

- **Bare `owner/name` as a marketplace `source`** — must be a `{source: github, repo}` object. See `references/plugin-structure.md`.
- **Skill `name` not kebab-case**, or `description` not starting with **"Use when…"** — run the CSO linter (`capability_plugin_lint_skill`).
- **Forgetting that `commands`/`agents` paths in the manifest replace the default dir while `skills` extends it.** Setting `"commands": "./custom/"` silently hides `commands/`.
- **`${CLAUDE_PLUGIN_ROOT}` vs. `${CLAUDE_PROJECT_DIR}`** — the first is the plugin install root, the second is the user's working directory. Mixing them up makes `.mcp.json` reference the wrong tree.
- **Editing a regenerated file by hand** — `plugin.json`, `marketplace.json`, `.mcp.json`, and the `commands/agency-*.md` slash-commands are all rewritten by `python -m agency.install`. Hand-edits get clobbered.
- **`pytest` instead of `python -m pytest`** — the bare command may resolve to a globally-installed pytest that misses the venv's deps. Per `CLAUDE.md`.
- **Calling a `capability_*_*` verb without `intent_id`** — the SERVES guard rejects it. Call `intent_bootstrap` first; only substrate tools (`agency_welcome`, `agency_install`, `agency_doctor`, `intent_bootstrap`) can be called without one.
- **Adding a capability but forgetting to reload the plugin** — `pip install -e .` makes the source editable, but the running MCP server holds the old import until restart.
- **`user_config.X` value updated but the MCP server didn't reload** — substitution happens at server launch, not per-call. Disable+enable the plugin to refresh.

## References

| File | When to read it |
|---|---|
| [`references/plugin-structure.md`](references/plugin-structure.md) | How agency uses the Claude Code plugin contract — the actual layout, regenerated files, `.mcp.json` pattern, manifest with `userConfig` |
| [`references/common-patterns.md`](references/common-patterns.md) | The patterns agency composes (MCP+skill, bundled resources, auto-generated commands, domain extension via `examples/`) and the one it deliberately doesn't ship |
| [`references/polyglot-hooks.md`](references/polyglot-hooks.md) | Cross-platform hook pattern (Windows/macOS/Linux). Agency ships no hooks today; this is forward-looking |
| [`references/troubleshooting.md`](references/troubleshooting.md) | Agency failure modes — venv bootstrap, MCP-server startup, SERVES-guard, ontology-merge, `${user_config}` reload, slash-command staleness |
| [`references/agency-patterns.md`](references/agency-patterns.md) | Engine-internal patterns — capability, skill-walker, boundary driver, substrate tool |
| [`references/release-and-distribution.md`](references/release-and-distribution.md) | The agency release loop, `agency.install` regen contract, distribution paths |
| [`references/related-skills.md`](references/related-skills.md) | Decision matrix: which skill to use for which task |

All references are agency-adapted. For a *generic* Claude Code plugin not
based on the agency engine, use the Superpowers
`developing-claude-code-plugins` skill — that's the upstream canon.
