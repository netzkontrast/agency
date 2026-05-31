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
venv is activated). The `${CLAUDE_PLUGIN_ROOT}/bin/agency` wrapper is
a convenience inside Claude Code; under Jules / no-MCP it expands to
`/bin/agency` and fails — Codex review of cedcea0.

```bash
iid=$(python -m agency.cli intent --purpose help --deliverable map --acceptance ok \
      | python3 -c 'import sys,json; print(json.load(sys.stdin)["intent_id"])')
python -m agency.cli execute --code \
  "return await call_tool('capability_plugin_help', {'intent_id': '$iid'})"
```

## Slash-command bash fallback

If neither the MCP server nor the venv-aware launcher is reachable
from your shell, the plugin's `bin/agency` wrapper resolves the
plugin venv + PYTHONPATH so the `agency` package is always
importable. Bootstrap an intent, then call the help verb with its
id (no `--db` — the Spec 020 resolver picks `./.agency/session.db`,
the same store MCP uses):

    AGENCY="${CLAUDE_PLUGIN_ROOT}/bin/agency"
    iid=$("$AGENCY" intent --purpose help --deliverable map --acceptance ok | python3 -c 'import sys,json; print(json.load(sys.stdin)["intent_id"])')
    "$AGENCY" execute --code "return await call_tool('capability_plugin_help', {'intent_id': '$iid'})"

