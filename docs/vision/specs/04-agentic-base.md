---
slug: spec-agentic-base
type: spec
status: ready
summary: The harness — the four-verb contract, domain/row discovery, name derivation, CodeMode, and the cold-boot budget. FastMCP is the one engine.
---

# 04 — Agentic base (the harness)

FastMCP is the only runtime. The harness lives in `agentic/_harness/` and is
booted by `agentic/_bootloader.py`.

## Four-verb contract (always on)

```python
mcp__list_tools(row: str | None = None)        -> ToolResult
mcp__call_tool(name: str, args: dict)          -> ToolResult
mcp__list_skills(row: str | None = None)       -> ToolResult
mcp__dispatch_skill(name: str, args: dict)     -> ToolResult        # may carry a PhaseStateEnvelope in data
```

These four are the entire cold-boot surface. Every other tool
(`mcp__agentic_*`, `mcp__workflow_*`, `mcp__context_*`) is reached through
`call_tool` and its schema is deferred until requested.

## Harness modules

| Module | Responsibility |
|---|---|
| `fastmcp_boot.py` | create the FastMCP server; register the four verbs |
| `domain_loader.py` | scan the three fixed domains; glob `<domain>/<row>/manifest.toml`; build the registry |
| `name_deriver.py` | apply spec-01 derivation (domain-first); reject domain/row prefixes in exports |
| `codemode.py` | render a domain's `[codemode].prefers` exports as a CodeMode call-surface |

## Discovery

The three domains (`agentic`, `workflow`, `context`) are fixed. Under each, the
loader discovers rows from their manifests and registers their derived
tools/skills. No row is required to exist in more than one domain.

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
