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
| `gain` | transform | The frugal impact scoreboard — the published benchmark medians (a documented external constant sourced from ``data/benchmark.json``, the CLAUDE.md #8 exception, NOT a frozen snapshot) PLUS the LIVE per-repo marker count (a read-only scan — the only honest per-repo number; never an invented savings figure, since the unbuilt version was never written). | [details](references/gain.md) |
| `help` | transform | The frugal reference card (the ponytail-help info): the discipline + the levels table + how to switch + what is configurable. | [details](#help) |
| `instructions` | transform | Return the frugal ruleset text at a level — the ponytail-MCP port (``ponytail_instructions``). | [details](references/instructions.md) |
| `level` | transform | Report the active frugal level (env AGENCY_FRUGAL_LEVEL -> .agency/config.yaml -> full). | [details](#level) |
| `review` | effect | Review for over-engineering ONLY (delete/stdlib/native/yagni/shrink) — distinct from analyze's multi-axis pass. | [details](references/review.md) |
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

- **`frugal`** (discipline): necessity → stdlib → native → installed-dep → one-line → minimum
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'frugal', 'inputs': {}, 'intent_id': '…'})`
  1. **necessity** — Ask whether this is needed AT ALL (YAGNI).
     The first rung: does this need to exist? The cheapest code is the code you don't write. Reject the feature before optimising it.
  2. **stdlib** — Prefer the standard library.
     If it IS needed, can the stdlib do it? Reach for batteries-included before anything external.
  3. **native** — Prefer an existing native capability.
     Can an existing agency capability/verb do it? Extend the substrate before adding a dependency.
  4. **installed-dep** — Prefer an ALREADY-installed dependency.
     If a dep is unavoidable, prefer one already in the lockfile over a new one. Every new dep is a maintenance + supply-chain cost.
  5. **one-line** — Prefer the one-line solution.
     Can it be a one-liner / a few lines inline rather than a new abstraction? Don't build a framework for a function.
  6. **minimum** — Ship the minimum that meets the floor.
     Implement the smallest thing that works — but NEVER cut the floor (validation, security, a11y). Confirm this gate only when the implementation is minimal AND complete.

## help

The frugal reference card (the ponytail-help info): the discipline + the levels table + how to switch + what is configurable.

Parameters: `()`.

_(Tier B — verb docstring lacks Spec 016 Inputs:/Returns:/chain_next: markers; reference is in-skill only. Add markers to upgrade to a separate references/help.md.)_

## level

Report the active frugal level (env AGENCY_FRUGAL_LEVEL -> .agency/config.yaml -> full).

Parameters: `()`.

_(Tier B — verb docstring lacks Spec 016 Inputs:/Returns:/chain_next: markers; reference is in-skill only. Add markers to upgrade to a separate references/level.md.)_
