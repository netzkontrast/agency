---
name: plugin
description: "Use when building or extending a Claude Code plugin — scaffolding a manifest, authoring a skill or command, or linting a capability against the authoring doctrine."
allowed-tools:
  - mcp__plugin_agency_agency__search
  - mcp__plugin_agency_agency__get_schema
  - mcp__plugin_agency_agency__execute
  - Bash
---
<!-- agency-generated: v1 -->

# plugin capability

Plugin ports the plugin-development craft into compute: scaffolds, skill and command authoring, marketplace entries, and the lint rules that enforce the authoring doctrine.

## When to use

- A new plugin skill or command needing CSO-clean structure
- A capability that may violate the authoring doctrine
- A lint finding whose remedy is unclear

## Verbs

| Verb | Role | Brief | Reference |
|------|------|-------|-----------|
| `author_command` | act | Render a slash-command markdown stub. | [details](references/author_command.md) |
| `author_skill` | act | Render a CSO-compliant SKILL.md. | [details](references/author_skill.md) |
| `help` | transform | Map the engine's capabilities (macroskills) to their verbs — via ctx.registry. | [details](references/help.md) |
| `lint_capability` | transform | Lint a capability against Hint #7 structural + role-tag + render-slice rules. | [details](references/lint_capability.md) |
| `lint_disciplines` | transform | The graduated discipline gate (Spec 378 Slice 4): strict-lint every registered discipline, partitioned into clean / warned (the migration tail) / blocked (a self-contained discipline that regressed). | [details](references/lint_disciplines.md) |
| `lint_explain` | transform | Return the rework recipe for a lint rule kind (Spec 074) — so you learn HOW to fix it. | [details](references/lint_explain.md) |
| `lint_skill` | transform | Lint a skill description against the CSO + length rules. | [details](references/lint_skill.md) |
| `lint_skill_schema` | transform | Strict per-type + self-containment + no-stub + verb-resolves lint over a 371 Skill dict (Spec 377) — beyond the SkillDoc shape ``lint_skill`` checks. | [details](references/lint_skill_schema.md) |
| `marketplace_entry` | act | Render a marketplace.json entry. | [details](references/marketplace_entry.md) |
| `publish_skill` | effect | Publish a capability's Agent Skill to the Anthropic Skills API (Spec 083). | [details](references/publish_skill.md) |
| `scaffold` | act | Render the plugin scaffold (plugin.json + .mcp.json). | [details](references/scaffold.md) |
| `step_doc` | act | Render a step-doc markdown block (audit trail entry). | [details](references/step_doc.md) |

## Example

```bash
await call_tool('capability_plugin_author_command', {'intent_id': 'intent:abc'})
```

## Red flags — stop and re-read this skill

- Shipping a capability without linting → run capability_plugin_lint_capability
- Hand-writing a SKILL.md → render it via capability_plugin_author_skill

## Walk this capability

Drive this capability's verbs by WALKING a skill one phase at a time (progressive disclosure, recorded as provenance):

- **`plugin-dev`** (authoring): manifest → skill → command → marketplace → confirm
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'plugin-dev', 'inputs': {}, 'intent_id': '…'})`
- **`skill-creation`** (authoring): red-baseline → green-author → lint → refactor → deploy
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'skill-creation', 'inputs': {}, 'intent_id': '…'})`
