---
description: Use when you want to list the agency capabilities and their verbs.
---

## Quick start — MCP (Claude Code)

The plugin installs an MCP server exposing the code-mode contract
(`search` · `get_schema` · `execute`) AND three engine-substrate
onboarding tools (Spec 029):

- `agency_welcome` — one-shot onboarding payload; returns the
  bootstrap example + the live capability list. **Start here.**
- `agency_install` — scaffold `.agency/` + a CLAUDE.md snippet in
  the current target repo. Idempotent.
- `intent_bootstrap` — mint AND confirm an Intent. The only verb
  that does not require an existing `intent_id`.
- `agency_doctor` — health check (Spec 030): python version, deps,
  DB reachability, JULES_API_KEY presence (never the value).
  Call when something silently fails.

These onboarding tools and the code-mode trio share one MCP server
(`mcp__plugin_agency_agency__execute` for the sandbox, `mcp__plugin_agency_agency__search` for discovery, `mcp__plugin_agency_agency__get_schema` before a call).

```python
# 1. Onboard (one call; no intent_id needed)
await call_tool('agency_welcome', {})

# 2. Scaffold .agency/ + CLAUDE.md in the target repo if missing
await call_tool('agency_install', {})

# 3. Mint the intent every capability verb SERVES against
r = await call_tool('intent_bootstrap', {
    'purpose': 'ship X',
    'deliverable': 'Y working',
    'acceptance': 'tests green',
})
# 4. Use it
await call_tool('capability_plugin_help', {'intent_id': r['intent_id']})
```

## Quick start — bash (Jules / no-MCP)

The CLI resolves the graph DB itself (Spec 020: `AGENCY_DB` env, else
`./.agency/session.db`) — do NOT pass `--db`, or the bash surface writes
to a different store than MCP. The canonical entrypoint is
`python -m agency.cli` (works in Jules / no-MCP / any context where the
venv is activated). Spec 065: `agency` (the pipx-installed
console-script) is the canonical CLI form — no bin/ shim.

```bash
iid=$(agency intent --purpose help --deliverable map --acceptance ok \
      | python3 -c 'import sys,json; print(json.load(sys.stdin)["intent_id"])')
agency execute --code \
  "return await call_tool('capability_plugin_help', {'intent_id': '$iid'})"
```

## Slash-command bash fallback

If the MCP server isn't reachable from your shell, use the
pipx-installed `agency` console-script (Spec 055/065 — bin/ shims
removed; rely on pipx for PATH resolution).
Bootstrap an intent, then call the help verb with its
id (no `--db` — the Spec 020 resolver picks `./.agency/session.db`,
the same store MCP uses):

    iid=$(agency intent --purpose help --deliverable map --acceptance ok | python3 -c 'import sys,json; print(json.load(sys.stdin)["intent_id"])')
    agency execute --code "return await call_tool('capability_plugin_help', {'intent_id': '$iid'})"

