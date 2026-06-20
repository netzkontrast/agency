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

Frugal forces the laziest solution that actually works: the ladder YAGNI -> stdlib -> native -> installed-dep -> one line -> minimum, with a non-negotiable safety floor (validate / secure / accessibility never cut). The verbs EXPOSE the core discipline (``agency/_frugal.py``, Spec 332 — the single source for the ladder + floor); they never re-define it. ``debt`` harvests the deliberate ``frugal:`` shortcut markers into queryable provenance.

## When to use

- "be lazy" / "lazy mode" / "simplest solution" / "yagni" / "do less"
- A host with no always-on hook that must pull the discipline as a tool/prompt
- "what did we defer" / "list the shortcuts" / "ponytail debt"

## Verbs

| Verb | Role | Brief | Reference |
|------|------|-------|-----------|
| `debt` | effect | Harvest deliberate ``frugal:``/``ponytail:`` shortcut markers into a debt ledger — each a ``DebtMarker`` node SERVING the intent, so "what did we defer" is a query, not a re-grep (the substrate's edge over the JS original). | [details](references/debt.md) |
| `gain` | transform | The frugal impact scoreboard — the published benchmark medians (a documented external constant sourced from ``data/benchmark.json``, the CLAUDE.md #8 exception, NOT a frozen snapshot) plus a pointer to the only real per-repo number (``frugal.debt``). | [details](#gain) |
| `help` | transform | The frugal reference card (the ponytail-help info): the discipline + the levels table + how to switch + what is configurable. | [details](#help) |
| `instructions` | transform | Return the frugal ruleset text at a level — the ponytail-MCP port (``ponytail_instructions``). | [details](references/instructions.md) |
| `level` | transform | Report the active frugal level (env AGENCY_FRUGAL_LEVEL -> .agency/config.yaml -> full). | [details](#level) |
| `set_level` | effect | Persist the frugal level (durable across processes via the Spec 334 config). | [details](references/set_level.md) |

## Example

```bash
await call_tool('capability_frugal_debt', {'intent_id': 'intent:abc'})
```

## Red flags — stop and re-read this skill

- Over-engineering / boilerplate / a new dependency for a few lines → frugal.instructions
- Hand-writing the ladder text → it lives in core _frugal (single source)
- A frugal: shortcut with no named upgrade path → frugal.debt flags it

## Walk this capability

Drive this capability's verbs by WALKING a skill one phase at a time (progressive disclosure, recorded as provenance):

- **`frugal-usage`** (usage): use-transform → use-effect → confirm
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'frugal-usage', 'inputs': {}, 'intent_id': '…'})`

## gain

The frugal impact scoreboard — the published benchmark medians (a documented external constant sourced from ``data/benchmark.json``, the CLAUDE.md #8 exception, NOT a frozen snapshot) plus a pointer to the only real per-repo number (``frugal.debt``).

Parameters: `()`.

_(Tier B — verb docstring lacks Spec 016 Inputs:/Returns:/chain_next: markers; reference is in-skill only. Add markers to upgrade to a separate references/gain.md.)_

## help

The frugal reference card (the ponytail-help info): the discipline + the levels table + how to switch + what is configurable.

Parameters: `()`.

_(Tier B — verb docstring lacks Spec 016 Inputs:/Returns:/chain_next: markers; reference is in-skill only. Add markers to upgrade to a separate references/help.md.)_

## level

Report the active frugal level (env AGENCY_FRUGAL_LEVEL -> .agency/config.yaml -> full).

Parameters: `()`.

_(Tier B — verb docstring lacks Spec 016 Inputs:/Returns:/chain_next: markers; reference is in-skill only. Add markers to upgrade to a separate references/level.md.)_
