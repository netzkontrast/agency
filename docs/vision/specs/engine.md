---
slug: spec-engine
type: spec
status: ready
summary: The engine — the four-verb meta-contract (list_tools/call_tool/list_skills/dispatch_skill), the code-mode call surface, and the engine guards (quality-score, loop-detection, compaction checkpoints, Slot/quota). The engine is the host, NOT a domain.
---

# Engine

> **Status: specced — not built.** The engine is the host process; it is NOT a
> domain. It hosts intent + the four domains.

## Concept

ONE FastMCP process hosts everything. The engine exposes a tiny stable surface
(the four-verb meta-contract), renders the domains as a callable code API
(code-mode), and enforces cross-cutting guards. Domains and capabilities are
data the engine serves; the engine itself adds no domain vocabulary.

## Interface — the four-verb meta-contract (always on)

```
list_tools(domain=None, capability=None)   -> deltas: available verbs (schemas deferred)
call_tool(name, args)                       -> result
list_skills(domain=None, capability=None)   -> deltas: available skills
dispatch_skill(name, args)                  -> result
```

These four are the **entire cold-boot surface**. Every domain verb
(`mcp__who_*`, `mcp__how_*`, `mcp__when_*`, `mcp__where_*`, and the `why.*`
intent verbs) is reached through `call_tool`; its schema is deferred until
requested (progressive disclosure).

## Code-mode (the token-efficiency primitive)

On demand, the engine renders the domains as a callable code API in a sandbox:

```
who.*    how.*    when.*    where.*    why.*
```

The agent writes code that **filters and joins in-sandbox** and returns only
**deltas** — never raw history. This is the engine's core token-efficiency
primitive; `where.project()` (see [where](where.md)) is the canonical read it
calls.

## Engine guards (cross-cutting — NOT domains)

Referenced by who / when, owned by the engine:

| Guard | Role |
|---|---|
| quality-score | confidence/quality signal on a step's output; can halt below threshold |
| loop-detection | halts repeating, non-progressing cycles |
| compaction checkpoint | named checkpoint (e.g. `compact-2026-01-12`) that prunes working context; full record stays in `where` |
| `Slot` / quota accounting | tracks concurrent dispatch slots + external quotas; `who` reads it to gate `fan_out` / `reclaim_slot` |

## Interactions

- Renders verbs derived from `(domain, capability, verb)` (see naming scheme).
- Cold boot exposes only the four meta-verbs; tool-masking (not tool-removal)
  keeps the surface — and its KV-cache prefix — stable.
- Hosts the pinned Intent reference (by id) so prompt prefixes stay append-only.
