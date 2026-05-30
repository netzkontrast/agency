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

# 2. Run it (sandboxed; intermediate results stay in-sandbox).
#    `intent_id` must be a captured Intent. MCP has no intent.capture
#    verb yet, so obtain one from the bash `intent` command in the
#    fallback below and paste it here (replace the placeholder):
await mcp__plugin_agency_agency__execute(code="""
  intent_id = 'intent:...'  # from `bin/agency intent ...` (see below)
  r = await call_tool('capability_plugin_help', {'intent_id': intent_id})
  return r
""")
```

Tracking issue: add a `capability_intent_capture` verb so MCP-only
sessions can self-bootstrap without the bash hop.

## Quick start — bash (Jules / no-MCP)

The CLI resolves the graph DB itself (Spec 020: `AGENCY_DB` env, else
`./.agency/session.db`) — do NOT pass `--db`, or the bash surface writes
to a different store than MCP. The canonical entrypoint is
`python -m agency.cli` (works in Jules / no-MCP / any context where the
venv is activated). The `${CLAUDE_PLUGIN_ROOT}/bin/agency` wrapper is
a convenience inside Claude Code; under Jules / no-MCP it expands to
`/bin/agency` and fails — Codex review of cedcea0.

```bash
iid=$(python -m agency.cli intent --purpose help --deliverable map --acceptance ok \
      | python3 -c 'import sys,json; print(json.load(sys.stdin)["intent_id"])')
python -m agency.cli execute --code \
  "return await call_tool('capability_plugin_help', {'intent_id': '$iid'})"
```

Use the plugin's `bin/agency` wrapper — it resolves the plugin venv
+ PYTHONPATH so the `agency` package is always importable. Bootstrap
an intent, then call the help verb with its id (no `--db` — the Spec
020 resolver picks `./.agency/session.db`, the same store MCP uses):

    AGENCY="${CLAUDE_PLUGIN_ROOT}/bin/agency"
    iid=$("$AGENCY" intent --purpose help --deliverable map --acceptance ok | python3 -c 'import sys,json; print(json.load(sys.stdin)["intent_id"])')
    "$AGENCY" execute --code "return await call_tool('capability_plugin_help', {'intent_id': '$iid'})"

