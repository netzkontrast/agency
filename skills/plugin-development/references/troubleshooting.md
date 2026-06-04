# Troubleshooting Plugin Development

> First stop for any agency runtime issue: run the substrate health check.
>
> ```python
> await call_tool('agency_doctor', {})
> ```
>
> It reports python version, dep imports, DB reachability, the two env vars
> that bite (`JULES_API_KEY`, `CLAUDE_PROJECT_DIR`), and a copy-pasteable
> `next_steps[]` list. Run it before anything else.

This file covers failure modes specific to working on the agency plugin —
both generic Claude Code plugin-contract failures (since this plugin obeys
that contract) and engine-specific ones (venv bootstrap, SERVES-guard,
ontology-merge, code-mode envelope).

## Section 1 — Plugin doesn't load

### Symptom
Plugin doesn't appear in `/plugin list`; tools missing.

### Debug steps

```bash
# 1. validate the manifest (it's regenerated, but check anyway)
jq . .claude-plugin/plugin.json
jq . .claude-plugin/marketplace.json
jq . .mcp.json

# 2. verify the structure
ls -la .claude-plugin/        # plugin.json + marketplace.json only
ls -la skills/                # skills at plugin root
ls -la commands/              # commands at plugin root

# 3. hunt hardcoded paths (use rg per repo AGENTS.md rule, not recursive grep)
rg -e "/Users/|/home/[a-z]+/" .claude-plugin/ .mcp.json hooks/ 2>/dev/null

# 4. restart Claude Code
```

### Likely cause if you're working on this repo
You edited a regenerated file by hand (`plugin.json`, `marketplace.json`,
`.mcp.json`, or any `commands/agency-*.md`) — the next `python -m
agency.install` will clobber your edits. The fix is to edit the source
(verb docstrings, capability metadata, `agency/install.py` templates) and
regenerate.

## Section 2 — MCP server doesn't start

### Symptom
`mcp__plugin_agency_agency__*` tools are missing; `claude --debug` shows
the server failed to spawn.

### Likely causes (ranked)

1. **`agency-mcp` not on PATH.** Spec 055 collapsed install to pipx
   only — `bin/agency-mcp` is a thin shim that exits 127 with a hint
   when the pipx-installed console-script isn't resolvable. Fix:
   `pipx install git+https://github.com/netzkontrast/agency@main` (or
   `pipx install --editable /path/to/agency` for a local checkout).
2. **System `python3` is missing or <3.11.** pipx itself uses
   `python3` to build the venv. `agency_doctor` reports
   `deps.graphqlite=missing` when the venv didn't build → fix by
   reinstalling pipx against a 3.11+ interpreter
   (`python3.11 -m pip install --user pipx`).
3. **`PYTHONPATH` shadowed by the user project.** A user-project cwd
   containing its own `agency/` package shadowed the plugin's. Mitigation:
   `bin/agency-mcp:28` PREpends, not appends. If you still see this,
   check for a `.pth` file or a `PYTHONPATH` in shell-rc.
4. **`fastmcp[code-mode]` extra missing.** Code-mode IS the contract; the
   engine raises `RuntimeError("code-mode requested but unavailable")` at
   startup. Fix: `pip install 'fastmcp[code-mode]>=3.3.0'`.

### Debug

```bash
# standalone smoke test — bypasses the MCP launcher
$CLAUDE_PLUGIN_ROOT/.venv/bin/python -m agency
# … should print "MCP server running on stdio"; Ctrl-C to exit.

# run the doctor over the bash CLI:
$CLAUDE_PLUGIN_ROOT/bin/agency execute --code 'r = await call_tool("agency_doctor", {}); return r'
```

## Section 3 — Capability discovered but no MCP tool wired

### Symptom
`agency_welcome` lists the capability name in `capabilities`, but
`search('<verb>')` returns nothing and `capability_<cap>_<verb>` isn't
callable.

### Likely causes
1. **`@verb` decorator missing** on the method. Lint catches this:
   `capability_plugin_lint_capability`.
2. **Verb is private** (name starts with `_`). The discovery filter
   excludes them.
3. **Capability has no `name` or wrong `home`.** `CapabilityBase` requires
   `name: str` (kebab-case allowed) and `home: str` (one of the known
   cluster labels — see `docs/vision/CAPABILITY-CLUSTERS.md`).
4. **Verb signature uses an annotation FastMCP can't serialize** (e.g. a
   non-JSON-Schema-able custom class). Fix: `dict`, `list`, `str`, `int`,
   `bool`.

### Fix
```python
await call_tool('capability_plugin_lint_capability', {
    'name': '<cap-name>',
})
# Read the ok/errors[] payload — lint reports exactly which rule family
# was violated (structural / role_tag / render_slice /
# consumer_contract / token_budget).
```

## Section 4 — SERVES-guard error

### Symptom
```
ToolError: capability_<x>_<verb>: every act/effect verb must be served by
an intent — pass intent_id from intent_bootstrap (or python -m
agency.cli intent).
```

### Cause
Every capability verb checks `intent_id` against the graph. You called the
verb without first minting an Intent. Substrate tools (`agency_welcome`,
`agency_install`, `intent_bootstrap`) DON'T need this — but capability
verbs do.

### Fix
```python
r = await call_tool('intent_bootstrap', {
    'purpose': '...', 'deliverable': '...', 'acceptance': '...',
})
iid = r['intent_id']
# now call capability_<x>_<verb> with intent_id=iid
```

## Section 5 — Ontology-merge fails on capability load

### Symptom
At engine startup:
```
ValueError: enum ('SomeNode', 'some_field') would clobber existing values
```

### Cause
Two capabilities tried to constrain the same `(label, field)` enum with
**different** allowed-sets. Enums are **widen-only**: the merge unions
allowed-values across capabilities. A real clobber is two capabilities
**defining the same node label with different required-field sets**.

### Fix
- Don't redefine an existing node type. Add fields by widening the schema
  in the capability that owns the type.
- If two capabilities genuinely need different node schemas, one of them
  has the wrong label — rename.

## Section 6 — Engine returns a raw string where you expected a dict

### Symptom
```python
r = await call_tool('capability_reflect_note', {...})
type(r)  # str, not dict
```

### Cause
`engine.py:123` unwraps `result["result"]` so code-mode deltas stay lean.
If the verb returns a scalar (a string ID), you get the scalar — not a
`{key: value}` envelope. Spec 019 documents this contract; not yet
implemented as docstring discipline.

### Workaround
Check the verb's docstring's `Returns:` slice — it tells you the unwrapped
shape. When in doubt, `await call_tool('search', {'query': '<verb>',
'detail': 'full'})`.

## Section 7 — `execute` dumps a huge traceback to stdout

### Symptom
Token-cost spike on the next agent turn; previous `execute` call returned
a multi-page Python traceback.

### Cause
`agency.cli execute` (and the engine via MCP) returns raw exceptions
unfiltered. Spec 018 identified this; not yet implemented.

### Mitigation today
- Wrap risky calls in try/except inside the `execute` code block; return
  only the error message string.
- Use `--db` with a fresh path for experimental code to avoid persisting
  half-states.

## Section 8 — `${user_config.X}` is empty in `.mcp.json`

### Symptom
`JULES_API_KEY` is empty in the running MCP process even though the user
set it in the plugin's Claude Code config.

### Cause
`${user_config.X}` substitutions are evaluated **at MCP server launch**,
not on every tool call. Editing the user_config value after the plugin
loaded won't update the running process.

### Fix
1. Set the value.
2. Reload the plugin: `/plugin disable agency && /plugin enable agency`
   (or restart Claude Code).
3. Re-run `agency_doctor` to confirm `env.JULES_API_KEY: "set"`.

## Section 9 — Skill not triggering

### Symptom
You added a skill under `skills/<name>/SKILL.md` but Claude doesn't
invoke it.

### Debug steps

1. **YAML frontmatter:**
   ```markdown
   ---
   name: skill-name
   description: Use when [clear trigger] — [what it does]
   ---
   ```
   `---` delimiters, `name` and `description` required, **spaces not tabs**.

2. **`name` is kebab-case.** Capital letters or underscores break the
   matcher.

3. **`description` starts with "Use when…"** — the host's matcher hooks
   onto that phrase. Run the CSO lint:
   ```python
   await call_tool('capability_plugin_lint_skill', {
       'name': '<name>',
       'description': '<your description>',
   })
   ```

4. **Location:** `skills/<skill-name>/SKILL.md` at plugin root — NOT
   `.claude-plugin/skills/`.

5. **Test explicitly:** ask for a task that matches the trigger phrase
   verbatim.

## Section 10 — Slash-command stale

### Symptom
You added a new capability/verb but `/agency:<verb>` still references the
old name (or doesn't exist).

### Cause
`python -m agency.install` regenerates slash commands from the live
engine. You added the capability but didn't regen the install.

### Fix
```bash
python -m agency.install
git diff commands/ skills/help/ .mcp.json plugin.json
# commit the regen alongside the capability change
```

## Section 11 — "Tool not found" but the source has it

### Symptom
The tool exists in `agency/capabilities/<X>.py` but `search('<Y>')` says
it doesn't exist.

### Likely cause
The plugin is running an older `.venv` install. `pip install -e .` is
editable, so source edits ARE picked up — but if `bin/agency-mcp`
launched the server BEFORE your edit, the running process still holds
the old import.

### Fix
1. Restart Claude Code (or reload the plugin) to relaunch the MCP server.
2. Then `agency_welcome` should list the new capability.

## Section 12 — Test suite collection fails with import errors

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

## Section 13 — Marketplace install fails

### Symptom
`/plugin install agency@agency` fails or the install never finishes.

### Debug steps

1. **`.claude-plugin/marketplace.json` exists and validates:**
   ```bash
   jq . .claude-plugin/marketplace.json
   ```
2. **Marketplace added:**
   ```
   /plugin marketplace list
   ```
3. **Source shape:** the agency marketplace uses `{"source": "github",
   "repo": "netzkontrast/agency"}` — bare `"netzkontrast/agency"` is
   invalid.

## Section 14 — Plugin works locally but not after release

### Symptom
The plugin runs fine in dev (editable install) but install from the
marketplace tag yields a missing capability or stale slash-command.

### Likely cause
Pre-release checklist not followed — see
[`release-and-distribution.md`](release-and-distribution.md).
The most common skip: `python -m agency.install` not re-run before
tagging, so the slash-command for a new verb didn't get committed.

### Fix
Run the full pre-release checklist:
- [ ] `python -m pytest -q` green
- [ ] `capability_plugin_lint_capability` ok=True for every changed cap
- [ ] `python -m agency.install` regen committed
- [ ] `agency_doctor` ok=True on a fresh venv
- [ ] `tests/test_search_isomorphism.py` passes

## Common pitfalls — quick table

| Mistake | Why it fails | Fix |
|---|---|---|
| Edited a regenerated file by hand | Next `agency.install` clobbers it | Edit the source; regen |
| Skills in `.claude-plugin/skills/` | Host looks in `skills/` at root | Move to plugin root |
| Hardcoded absolute paths | Breaks on other systems | `${CLAUDE_PLUGIN_ROOT}` |
| Confused `${CLAUDE_PLUGIN_ROOT}` with `${CLAUDE_PROJECT_DIR}` | Wrong tree referenced | Plugin install root vs. user cwd |
| Forgot to restart | Changes load at startup | Restart Claude Code or reload plugin |
| `pytest` instead of `python -m pytest` | Misses venv deps | Always `python -m pytest` |
| Vague skill description | Matcher can't hook | "Use when…" + specific trigger |
| Called capability verb without intent_id | SERVES guard rejects | `intent_bootstrap` first |
| `user_config.X` edited but server not reloaded | Substitution is at launch | Reload plugin |
| Bare `owner/name` marketplace source | Invalid shape | `{source: github, repo: "..."}` |

## When all else fails

1. **`agency_doctor`** — first stop. Almost everything triages from
   `next_steps[]`.
2. **Standalone smoke test:**
   `$CLAUDE_PLUGIN_ROOT/.venv/bin/python -m agency` should bind to
   stdio. If it crashes, the stack tells you exactly what's missing.
3. **Read `claude --debug`** logs for MCP startup errors.
4. **Simplify** — disable other plugins, strip your `userConfig`,
   confirm the bare agency plugin loads. Then add complexity back.
5. **Report:** https://github.com/netzkontrast/agency/issues
   (include `agency_doctor` output, `agency_welcome` output, the exact
   error, and what you tried).
