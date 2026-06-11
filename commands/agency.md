---
description: Use when you want a one-keystroke entry to the agency engine — browse capabilities, run tiered discovery on a query, or see the live onboarding payload.
---

## `/agency [query]` — the agency dispatcher

One-keystroke entry to the agency MCP surface (the `search` · `get_schema` · `execute` wire contract, Spec 029 / CORE.md).

### With a query → tiered discovery

When invoked with text, route it to the live capability graph via `mcp__agency__search` (tiered discovery, Spec 068):

```python
await call_tool('mcp__agency__search', {'query': '<your query>', 'detail': 'brief'})
```

Then drill into a found verb with `mcp__agency__get_schema` before calling it inside `mcp__agency__execute`.

### Bare → the welcome payload

When invoked with no argument, print the live capability list + the bootstrap example via `agency_welcome` (the canonical first call):

```python
await call_tool('agency_welcome', {})
```

`agency_welcome` returns the wire contract, the code-mode chaining example, the tier-0 capability map, and the resolved graph DB path — everything you need to start a session.

### Next

If no Intent is open yet, run `/agency-onboard` to capture one through a short describe → configure → confirm → capture interview.

