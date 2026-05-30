---
description: Use when you want to list the agency capabilities and their verbs.
---

## Quick start — MCP (Claude Code)

The plugin installs an MCP server exposing three tools:
`mcp__plugin_agency_agency__search`, `…__get_schema`, `…__execute`.
Inside `execute`, chain capability calls via `call_tool(...)` — only
the return crosses back into your context.

```python
# 1. Discover a verb (token-cheap)
await mcp__plugin_agency_agency__search(query="reflect note", limit=3)

# 2. Run it (sandboxed; intermediate results stay in-sandbox)
await mcp__plugin_agency_agency__execute(code="""
  r = await call_tool('capability_plugin_help', {'intent_id': iid})
  return r
""")
```

`intent_id` must be a captured Intent — today only the bash CLI exposes
`intent` (see fallback below). Tracking issue: add a `capability_intent_capture`
verb so MCP-only sessions can self-bootstrap.

## Quick start — bash (Jules / no-MCP)

```bash
AGENCY="${CLAUDE_PLUGIN_ROOT}/bin/agency"
iid=$("$AGENCY" --db agency.db intent --purpose help --deliverable map --acceptance ok \
      | python3 -c 'import sys,json; print(json.load(sys.stdin)["intent_id"])')
"$AGENCY" --db agency.db execute --code \
  "return await call_tool('capability_plugin_help', {'intent_id': '$iid'})"
```

Use the plugin's `bin/agency` wrapper — it resolves the plugin venv
+ PYTHONPATH so the `agency` package is always importable. Bootstrap
an intent, then call the help verb with its id:

    AGENCY="${CLAUDE_PLUGIN_ROOT}/bin/agency"
    iid=$("$AGENCY" --db agency.db intent --purpose help --deliverable map --acceptance ok | python3 -c 'import sys,json; print(json.load(sys.stdin)["intent_id"])')
    "$AGENCY" --db agency.db execute --code "return await call_tool('capability_plugin_help', {'intent_id': '$iid'})"

