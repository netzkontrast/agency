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


# agency — capabilities (macroskills) and their verbs (micro-skills)

- **analyze** — architecture, cleanup, graph, improve, paths, performance, quality, run, security
- **branch** — assess, commit_smart, finish
- **delegate** — dispatch_bash_hints, dispatch_decision, fan_out, join
- **develop** — checklist, estimate, record_authoring_outcome, reference, scaffold_capability, skill_walk, validate_skill
- **document** — explain, index_repo, render
- **dogfood** — collect, export, import, note, render
- **gate** — check
- **intent** — assumptions, decompose, first_principles, inversion, premortem, second_order, steelman, suggests, tradeoffs
- **jules** — activities, alias, apply_patch, approve_awaiting, approve_plan, detect_mode, dispatch, lint_prompt, list, message, patch, patch_body, plan, quota, recover, resolve_source, review_comment, status, status_all, stop, verify, watch
- **music** — analyze_mix, capture_idea, catalogue_status, conceptualize, count_syllables, lyric_report, master_album, music_health, pregen_check, promo_copy, publish_asset, release_check, set_album_status, transcribe_sheet, verify_streaming
- **plugin** — author_command, author_skill, help, lint_capability, lint_explain, lint_skill, marketplace_entry, publish_skill, scaffold, step_doc
- **reflect** — batch_note, note, recall, recall_semantic, search
- **research** — lead, specialist, verify
- **shell** — define, filter, run, templates
- **skill_generator** — generate
- **skills** — find, index, lint, render
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

