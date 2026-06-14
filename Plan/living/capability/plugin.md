---
capability: plugin
pillar: capability
vision_goals: []        # TODO(why-author): which GOALS.md goals this serves
status: living
last_generated: 2026-06-13
sources: []             # TODO(why-author): archived Plan/_archive/NNN specs that built this
---

# plugin — Plugin ports the plugin-development craft into compute: scaffolds, skill and command authoring, marketplace entries, and the lint rules that enforce the authoring doctrine (capability pillar)

## Why
<!-- AUTHORED (the only hand-written section). The intent + trade-offs the
     code can't express. A per-pillar subagent fills this from the archived
     specs in sources:. Everything below is GENERATED — do not hand-edit. -->
_TODO: authored intent._

## Verbs (generated · 10)

| Verb | Role | Params (**required**) | Purpose |
|---|---|---|---|
| `plugin.author_command` | act | **name** · **description** · **body** | Render a slash-command markdown stub. |
| `plugin.author_skill` | act | **name** · **description** · **body** | Render a CSO-compliant SKILL.md. |
| `plugin.help` | transform |  | Map the engine's capabilities (macroskills) to their verbs — via ctx.registry. |
| `plugin.lint_capability` | transform | **name** | Lint a capability against Hint #7 structural + role-tag + render-slice rules. |
| `plugin.lint_explain` | transform | **rule** | Return the rework recipe for a lint rule kind (Spec 074) — so you learn HOW to fix it. |
| `plugin.lint_skill` | transform | **name** · **description** | Lint a skill description against the CSO + length rules. |
| `plugin.marketplace_entry` | act | **name** · **version** · **description** · **source** | Render a marketplace.json entry. |
| `plugin.publish_skill` | effect | **skills_client** · **name** · dry_run | Publish a capability's Agent Skill to the Anthropic Skills API (Spec 083). |
| `plugin.scaffold` | act | **name** · **version** · **description** | Render the plugin scaffold (plugin.json + .mcp.json). |
| `plugin.step_doc` | act | **step** · **output** · status · inputs · notes | Render a step-doc markdown block (audit trail entry). |

## Ontology (generated)

**Nodes:** `Plugin`(name, version, description) · `Command`(name, description)

## Skills (generated)

_(no walkable skills)_

<!-- doc-source: agency/capabilities/plugin -->
