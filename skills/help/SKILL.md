---
name: help
description: Use when you need to discover the agency engine's capabilities (macroskills) and their verbs (the micro-skills).
allowed-tools:
  - mcp__plugin_agency_agency__search
  - mcp__plugin_agency_agency__get_schema
  - mcp__plugin_agency_agency__execute
  - Bash
---

# help

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


# agency — capabilities (macroskills) and their verbs (micro-skills)

- **branch** — assess, finish
- **delegate** — dispatch_bash_hints, dispatch_decision, fan_out, join
- **develop** — checklist, reference
- **dogfood** — collect
- **gate** — check
- **jules** — activities, alias, apply_patch, approve_awaiting, approve_plan, detect_mode, dispatch, lint_prompt, list, message, patch, patch_body, plan, quota, recover, resolve_source, review_comment, status, status_all, stop, verify, watch
- **plugin** — author_command, author_skill, help, lint_capability, lint_skill, marketplace_entry, scaffold, step_doc
- **reflect** — batch_note, note, recall, search
- **skill_generator** — generate
- **subagent** — develop
- **workspace** — baseline, isolate

## Discovery

There is no separate 'remember to use the skill' layer — discovery IS the contract:

- `search` finds a capability/verb or a discipline by symptom;
- `get_schema` discloses just what you need (a verb's signature, a discipline's current phase);
- `execute` runs it — and the run is recorded provenance (an Invocation, or a skill walk, that SERVES the intent).

Walk a discipline one phase at a time (`develop.checklist` lists its steps); a hard gate halts until
confirmed, and a phase bound to a verb EXECUTES rather than merely documents. Fetch a discipline's
heavy how-to on demand with `develop.reference` (T3 progressive disclosure) — invoking a discipline IS
the recorded walk, so there is nothing extra to remember.

