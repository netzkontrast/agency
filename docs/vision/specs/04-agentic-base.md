---
slug: spec-agentic-base
type: spec
status: ready
summary: The harness — the four-verb contract, domain/capability discovery, name derivation, CodeMode, and the cold-boot budget. FastMCP is the one engine.
---

# 04 — Agentic base (the harness)

FastMCP is the only runtime. The harness lives in `agentic/_harness/` and is
booted by `agentic/_bootloader.py`.

## Four-verb contract (always on)

```python
mcp__list_tools(capability: str | None = None)    -> ToolResult
mcp__call_tool(name: str, args: dict)              -> ToolResult
mcp__list_skills(capability: str | None = None)    -> ToolResult
mcp__dispatch_skill(name: str, args: dict)         -> ToolResult     # may carry a PhaseStateEnvelope in data
```

These four are the entire cold-boot surface. Every other tool
(`mcp__agentic_*`, `mcp__workflow_*`, `mcp__context_*`) is reached through
`call_tool` and its schema is deferred until requested.

## Harness modules

| Module | Responsibility |
|---|---|
| `fastmcp_boot.py` | create the FastMCP server; register the four verbs |
| `domain_loader.py` | scan the three fixed domains; glob `<domain>/<capability>/manifest.toml`; build the registry |
| `name_deriver.py` | apply spec-01 derivation (domain-first); reject domain/capability prefixes in exports |
| `codemode.py` | render a domain's `[codemode].prefers` exports as a CodeMode call-surface |

## Discovery

The three domains (`agentic`, `workflow`, `context`) are fixed. Under each, the
loader discovers capabilities from their authored manifests and registers their
derived tools/skills. A capability appears in a domain only where it has
materialized an aspect — an authored aspect (a manifest) or lazy graph nodes.
No capability is required to author an aspect in more than its home domain.

## Cold-boot budget

System prompt + `tools/list` < 500 tokens (the four-verb schemas only; deferred
tool schemas are not counted). A CI test enforces the budget.

## Registration & validation

- The wrapper bound for each tool binds its name and function as closure
  defaults (FastMCP's `add_tool` takes a callable, no `name=` kwarg, and rejects
  `**kwargs` wrappers).
- Every tool return is validated against `tool_result.schema.json`
  ([02](02-tool-result-envelope.md)) before it leaves the server; the
  pre/post-tool hooks ([06](06-context-base.md)) wrap each call.
