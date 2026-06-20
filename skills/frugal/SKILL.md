---
name: frugal
description: "Use when you want to read or switch the active frugal level, pull the ruleset"
allowed-tools:
  - mcp__plugin_agency_agency__search
  - mcp__plugin_agency_agency__get_schema
  - mcp__plugin_agency_agency__execute
  - Bash
---
<!-- agency-generated: v1 -->

# frugal capability

Frugal forces the laziest solution that actually works: the ladder YAGNI -> stdlib -> native -> installed-dep -> one line -> minimum, with a non-negotiable safety floor (validate / secure / accessibility never cut). The verbs EXPOSE the core discipline (``agency/_frugal.py``, Spec 332 — the single source for the ladder + floor); they never re-define it.

## When to use

- "be lazy" / "lazy mode" / "simplest solution" / "yagni" / "do less"
- A host with no always-on hook that must pull the discipline as a tool/prompt
- Asking what the frugal levels are or how to switch them

## Verbs

| Verb | Role | Brief | Reference |
|------|------|-------|-----------|
| `help` | transform | The frugal reference card (the ponytail-help info): the discipline + the levels table + how to switch + what is configurable. | [details](#help) |
| `instructions` | transform | Return the frugal ruleset text at a level — the ponytail-MCP port (``ponytail_instructions``). | [details](references/instructions.md) |
| `level` | transform | Report the active frugal level (env AGENCY_FRUGAL_LEVEL -> .agency/config.yaml -> full). | [details](#level) |
| `set_level` | effect | Persist the frugal level (durable across processes via the Spec 334 config). | [details](references/set_level.md) |

## Example

```bash
await call_tool('capability_frugal_help', {'intent_id': 'intent:abc'})
```

## Red flags — stop and re-read this skill

- Over-engineering / boilerplate / a new dependency for a few lines → frugal.instructions
- Hand-writing the ladder text → it lives in core _frugal (single source)

## Walk this capability

Drive this capability's verbs by WALKING a skill one phase at a time (progressive disclosure, recorded as provenance):

- **`frugal-usage`** (usage): use-transform → use-effect → confirm
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'frugal-usage', 'inputs': {}, 'intent_id': '…'})`

## help

The frugal reference card (the ponytail-help info): the discipline + the levels table + how to switch + what is configurable.

Parameters: `()`.

_(Tier B — verb docstring lacks Spec 016 Inputs:/Returns:/chain_next: markers; reference is in-skill only. Add markers to upgrade to a separate references/help.md.)_

## level

Report the active frugal level (env AGENCY_FRUGAL_LEVEL -> .agency/config.yaml -> full).

Parameters: `()`.

_(Tier B — verb docstring lacks Spec 016 Inputs:/Returns:/chain_next: markers; reference is in-skill only. Add markers to upgrade to a separate references/level.md.)_
