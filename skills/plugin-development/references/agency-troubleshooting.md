# Troubleshooting (Agency-Specific)

> Generic Claude Code plugin failure modes live in [`troubleshooting.md`](troubleshooting.md).
> This file covers failures specific to the agency engine.

The **first stop** for any agency runtime issue is the substrate health
check:

```python
await call_tool('agency_doctor', {})
```

It reports python version, dep imports, DB reachability, the two env vars
users hit problems with (`JULES_API_KEY`, `CLAUDE_PROJECT_DIR`), and a
copy-pasteable `next_steps[]` list of fixes. Run it before anything else.

## MCP server doesn't start

### Symptom
`mcp__plugin_agency_agency__*` tools are missing; `claude --debug` shows the server failed to spawn.

### Likely causes (ranked)

1. **`.venv` not bootstrapped.** First-run path: `bin/agency-mcp` calls `bin/agency-install`, which creates `${CLAUDE_PLUGIN_ROOT}/.venv` and `pip install -e .`. On a read-only mount or immutable image this fails silently. Fix: manually create the venv outside the plugin tree, or wait for Spec-031 (pipx install path).
2. **System `python3` is missing or <3.11.** `bin/agency-install` exits early; the wrapper falls back to `python3` on PATH, which won't have `fastmcp` / `graphqlite`. Run `agency_doctor` → reports `deps.graphqlite=missing` → fix per the next_steps.
3. **`PYTHONPATH` shadowed by the user project.** A user project whose cwd contains its own `agency/` package shadowed the plugin's. Mitigation already in place: `bin/agency-mcp:28` PREpends, not appends. If you still see this, check for a `.pth` file or a `PYTHONPATH` set in shell-rc.
4. **`fastmcp[code-mode]` extra missing.** Code-mode IS the contract; the engine raises `RuntimeError("code-mode requested but unavailable")` at startup. Fix: `pip install 'fastmcp[code-mode]>=3.3.0'`.

### Debug
```bash
# Standalone smoke test — bypasses the MCP launcher
$CLAUDE_PLUGIN_ROOT/.venv/bin/python -m agency
# … should print "MCP server running on stdio"; Ctrl-C to exit.

# Run the doctor over the bash CLI:
$CLAUDE_PLUGIN_ROOT/bin/agency execute --code 'r = await call_tool("agency_doctor", {}); return r'
```

## SERVES-guard error

### Symptom
```
ToolError: capability_<x>_<verb>: every act/effect verb must be served by an
intent — pass intent_id from intent_bootstrap (or python -m agency.cli intent).
```

### Cause
Every capability verb checks `intent_id` against the graph. You called the
verb without first minting an Intent. Substrate tools (`agency_welcome`,
`agency_install`, `intent_bootstrap`) DON'T need this — but capability verbs do.

### Fix
```python
r = await call_tool('intent_bootstrap', {
    'purpose': '...', 'deliverable': '...', 'acceptance': '...',
})
iid = r['intent_id']
# now call capability_<x>_<verb> with intent_id=iid
```

## Capability discovered but no MCP tool wired

### Symptom
`agency_welcome` lists the capability name in `capabilities`, but
`search('<verb>')` returns nothing and `capability_<cap>_<verb>` isn't callable.

### Likely causes
1. **`@verb` decorator missing** on the method (only methods decorated with
   `@verb(role=…)` become tools). Lint catches this: `capability_plugin_lint_capability`.
2. **Verb is private** (name starts with `_`). The discovery filter excludes them.
3. **Capability has no `name` or wrong `home`.** `CapabilityBase` requires
   `name: str` (kebab-case allowed) and `home: str` (one of the known cluster
   labels — see `docs/vision/CAPABILITY-CLUSTERS.md`).
4. **Verb signature uses an annotation FastMCP can't serialize** (e.g. a non-
   JSON-Schema-able custom class). Fix: use `dict`, `list`, `str`, `int`, `bool`, etc.

### Fix
```python
await call_tool('capability_plugin_lint_capability', {
    'name': '<cap-name>',
})
# Read the ok/errors[] payload — the lint reports exactly which rule family
# was violated (structural / role_tag / render_slice / consumer_contract /
# token_budget).
```

## Ontology-merge fails on capability load

### Symptom
At engine startup:
```
ValueError: enum ('SomeNode', 'some_field') would clobber existing values
```

### Cause
Two capabilities tried to constrain the same `(label, field)` enum with
**different** allowed-sets. Enums are **widen-only**: the merge unions
allowed-values across capabilities, but if Capability A says `{"a","b"}` and
Capability B says `{"x","y"}` for the same key, the union (`{"a","b","x","y"}`)
is what you get — that's not a clobber. A real clobber is two capabilities
**defining the same node label with different required-field sets**.

### Fix
- Don't redefine an existing node type. Add fields by widening the schema in
  the capability that owns the type.
- If two capabilities genuinely need different node schemas, one of them has
  the wrong label — rename.

## Code-mode `execute` dumps a huge traceback to stdout

### Symptom
Token-cost spike on the next agent turn; previous `execute` call returned a
multi-page Python traceback.

### Cause
`agency.cli execute` (and the engine via MCP) returns raw exceptions
unfiltered. Spec 018 identified this; not yet implemented.

### Mitigation today
- Wrap risky calls in try/except inside the `execute` code block; return only
  the error message string.
- Use `--db` with a fresh path for experimental code to avoid persisting
  half-states.

## Engine returns a raw string where you expected a dict

### Symptom
```python
r = await call_tool('capability_reflect_note', {...})
type(r)  # str, not dict
```

### Cause
`engine.py:123` unwraps `result["result"]` so code-mode deltas stay lean. If
the verb returns a scalar (a string ID), you get the scalar — not a `{key:
value}` envelope. Spec 019 documents this contract; not yet implemented as
docstring discipline.

### Workaround
Check the verb's docstring's `Returns:` slice — it tells you the unwrapped
shape. When in doubt, `await call_tool('search', {'query': '<verb>',
'detail': 'full'})`.

## `${user_config.X}` is empty in `.mcp.json`

### Symptom
`JULES_API_KEY` is empty in the running MCP process even though the user set
it in the plugin's Claude Code config.

### Cause
`${user_config.X}` substitutions are evaluated **at MCP server launch**, not
on every tool call. Editing the user_config value after the plugin loaded
won't update the running process.

### Fix
1. Set the value.
2. Reload the plugin: `/plugin disable agency && /plugin enable agency`
   (or restart Claude Code).
3. Re-run `agency_doctor` to confirm `env.JULES_API_KEY: "set"`.

## Test suite collection fails with import errors

### Symptom
```
ImportError: cannot import name 'CodeMode' from 'fastmcp.experimental.transforms.code_mode'
```
or
```
ModuleNotFoundError: No module named 'graphqlite'
```

### Cause
You ran `pytest` instead of `python -m pytest`. The system `pytest` (if
installed) doesn't see the venv's site-packages.

### Fix
Per `CLAUDE.md`: **always** activate the venv AND use `python -m pytest`.
```bash
. .venv/bin/activate
python -m pytest -q
```

## Slash-command generated by `agency.install` is stale

### Symptom
You added a new capability/verb but `/agency:<verb>` still references the
old name.

### Cause
`python -m agency.install` regenerates slash commands from the live engine.
You added the capability but didn't regen the install.

### Fix
```bash
python -m agency.install
git diff commands/ skills/ .mcp.json plugin.json
# commit the regen alongside the capability change
```

## "Tool not found: capability_X_Y" but X.Y is in the source

### Symptom
The tool exists in `agency/capabilities/<X>.py` but `search('<Y>')` says it
doesn't exist.

### Likely cause
The plugin is running an older `.venv` install. `pip install -e .` is
editable, so source edits are picked up — but if `bin/agency-mcp` launched
the server BEFORE your edit, the running process still holds the old import.

### Fix
1. Restart Claude Code (or reload the plugin) to relaunch the MCP server.
2. Then `agency_welcome` should list the new capability.
