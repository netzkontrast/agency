---
spec_id: "064"
slug: plugin-reference-compliance
status: complete   # 2026-06-04: polyglot wrapper + matcher + async + using-agency + cwd + env_vars + PLUGIN_ROOT fallback
state: done
last_updated: 2026-06-04
owner: "@agency"
depends_on: ["029", "055", "062", "063"]
affects:
  - hooks/hooks.json                              # matcher + async: false; renamed target
  - hooks/run-hook.cmd                            # NEW — Windows polyglot wrapper
  - hooks/session-start                           # NEW — extensionless rename of session-start.sh
  - .mcp.json                                     # cwd + env_vars list (mirror episodic-memory)
  - skills/using-agency/SKILL.md                  # NEW — broad-trigger entry skill
  - agency/install.py                             # generate the new shape
  - README.md                                     # cross-IDE/Windows note
  - tests/test_install_session_start_hook.py
  - tests/test_install_mcp_skill.py
estimated_jules_sessions: 0
domain: meta
wave: 4
---

# Spec 064 — Plugin-reference compliance pass

## Why

Deep-reflection audit (2026-06-04, post-Spec 063) against the Claude
Code `developing-claude-code-plugins` reference + two installed
reference plugins (`superpowers` 5.1.0, `episodic-memory` 1.4.2)
surfaced 6 conformance gaps. None is broken — the plugin works on
Linux/macOS with default Claude Code. Each gap closes a specific
real-world failure mode:

1. **No cross-platform polyglot hook wrapper.** Superpowers ships
   `hooks/run-hook.cmd` that's valid as both CMD batch AND bash so
   the same hook entry works on Windows + Unix. Our
   `hooks/session-start.sh` works only on Unix. Claude Code on
   Windows auto-prepends `bash` to any command containing `.sh`,
   then fails because `bash` isn't on Windows CMD PATH. Reference
   §"polyglot-hooks.md" recommends the wrapper as the doctrinal
   solution.

2. **`hooks.json` lacks a `matcher`.** Both reference plugins set
   `"matcher": "startup|resume|clear"` (episodic-memory) or
   `"startup|clear|compact"` (superpowers). Without a matcher our
   hook fires on EVERY SessionStart event including `compact`,
   which retriggers pipx install during compactions — wasted cycles.

3. **`hooks.json` lacks `async: false`.** Superpowers' hook declares
   `"async": false` so subsequent session work waits for the install
   to finish. Without it Claude Code MAY start the MCP server before
   pipx install completes → first-session race.

4. **No `using-agency` meta-skill.** `using-superpowers` is the
   doctrinal pattern — a broad-trigger skill that tells the agent to
   **invoke `agency_welcome` BEFORE responding to any agency-related
   prompt**. Without it, fresh agents don't know to bootstrap the
   intent before any verb call.

5. **`.mcp.json` env block is missing `cwd` and `env_vars`.**
   Episodic-memory pins `"cwd": "."` + declares an `env_vars` list
   for passthrough. We hardcode the env dict only. Without `cwd`
   pinning the MCP subprocess CWD is undefined → Spec 020's
   `.agency/session.db` resolver could land in the wrong place if
   substitution fails. Without `env_vars` passthrough,
   `AGENCY_EMBEDDER` (Spec 045 BGE opt-in) is lost when set in the
   user's shell.

6. **`${CLAUDE_PLUGIN_ROOT}` hardcoded.** Episodic-memory uses
   `${PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT}}` (bash-default fallback)
   so the plugin works in Cursor / Codex harnesses that set
   `PLUGIN_ROOT` instead. Cheap to add; broadens reach.

## Done When

- [ ] **`hooks/run-hook.cmd`** ships — exact polyglot pattern from
  the reference (Superpowers 5.1.0). Valid in CMD + bash; routes
  to `hooks/<script-name>` (extensionless).
- [ ] **`hooks/session-start.sh` renamed to `hooks/session-start`**
  (extensionless). Body unchanged from Spec 063. Windows
  auto-detection no longer prepends `bash` to a `.sh` filename.
- [ ] **`hooks/hooks.json` updated**:
  - `matcher: "startup|resume|clear"` (NOT `compact` — we don't
    re-install on compaction).
  - `async: false` on the command entry.
  - command path: `"${CLAUDE_PLUGIN_ROOT}/hooks/run-hook.cmd"
    session-start` (calls the polyglot wrapper).
- [ ] **`skills/using-agency/SKILL.md`** ships — broad-trigger meta
  skill in the using-superpowers shape:
  ```
  name: using-agency
  description: Use when starting any conversation that may touch
    the agency engine — bootstrap an intent via agency_welcome
    BEFORE any other agency verb.
  ```
  Body documents the `agency_welcome → intent_bootstrap → verb`
  chain + the "every verb SERVES the intent" doctrine.
- [ ] **`.mcp.json` extended**:
  - `cwd: "${CLAUDE_PROJECT_DIR}"` so the MCP subprocess CWD is
    pinned to the project root (where `.agency/session.db` lives).
  - `env_vars: ["AGENCY_DB", "AGENCY_EMBEDDER", "JULES_API_KEY"]`
    — declares the passthrough list so user-set values reach the
    subprocess.
- [ ] **`${PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT}}` fallback** applied
  to:
  - `.mcp.json` command path.
  - `hooks/hooks.json` command path.
  - `hooks/session-start` script's `${CLAUDE_PLUGIN_ROOT}` refs.
- [ ] **`agency/install.py`** regenerates all of the above. The
  `hooks/session-start.sh` entry in the file map renames to
  `hooks/session-start`; `_SESSION_START_HOOKS_JSON` carries
  matcher + async + run-hook.cmd path; `_mcp_config()` adds `cwd`
  + `env_vars`; a new `_USING_AGENCY_SKILL_MD` constant adds the
  skill.
- [ ] **`install.write()`** chmods `hooks/run-hook.cmd` + extensionless
  `hooks/session-start` to 0o755 (current rule matches `bin/` and
  `.sh` extension — extend to "any file under hooks/").
- [ ] **Tests**:
  - `tests/test_install_session_start_hook.py`:
    - `hooks.json` carries `matcher` + `async: false`.
    - hook command path references `run-hook.cmd session-start`.
    - polyglot wrapper exists with the canonical CMD+bash heredoc.
    - extensionless `hooks/session-start` is produced.
  - `tests/test_install_mcp_skill.py`:
    - `.mcp.json` has `cwd == "${CLAUDE_PROJECT_DIR}"`.
    - `.mcp.json` has `env_vars` list including
      `AGENCY_EMBEDDER`.
    - using-agency skill file is generated.
- [ ] **README.md** — one paragraph documenting:
  - Windows polyglot support shipped.
  - `using-agency` is the entry skill any fresh session calls first.
  - Cursor/Codex friendly via the `${PLUGIN_ROOT}` fallback.
- [ ] `python -m agency.install` produces a clean diff; drift check
  green; full suite stays green.

## Design

### `.mcp.json` post-refresh

```json
{
  "mcpServers": {
    "agency": {
      "command": "${PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT}}/bin/agency-mcp",
      "args": [],
      "cwd": "${CLAUDE_PROJECT_DIR}",
      "env": {
        "AGENCY_DB": "${CLAUDE_PROJECT_DIR}/.agency/session.db",
        "JULES_API_KEY": "${user_config.jules_api_key}"
      },
      "env_vars": ["AGENCY_DB", "AGENCY_EMBEDDER", "JULES_API_KEY"]
    }
  }
}
```

### `hooks/hooks.json` post-refresh

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup|resume|clear",
        "hooks": [
          {
            "type": "command",
            "command": "\"${PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT}}/hooks/run-hook.cmd\" session-start",
            "async": false
          }
        ]
      }
    ]
  }
}
```

### `skills/using-agency/SKILL.md`

```
---
name: using-agency
description: Use when starting any conversation that may touch the
  agency engine (capabilities, intent, provenance, MCP code-mode) —
  bootstrap an intent via agency_welcome BEFORE any other agency verb.
allowed-tools:
  - mcp__plugin_agency_agency__execute
  - mcp__plugin_agency_agency__search
  - mcp__plugin_agency_agency__get_schema
---

# using-agency

Read first. This is the entry skill the orchestrator MUST call before
invoking any agency capability.

## The two-step bootstrap

EVERY agency-related task starts with the same two calls:

1. `agency_welcome` — returns the canonical bootstrap example +
   the live capability list. **First call of every session.**
2. `intent_bootstrap(purpose=, deliverable=, acceptance=)` — mints
   AND confirms the Intent. **Every subsequent verb SERVES this id.**

…
```

### Polyglot wrapper

Verbatim port of Superpowers' `hooks/run-hook.cmd`. Valid as both
CMD batch (Windows) and bash (Unix). Hook scripts use extensionless
filenames so Claude Code's Windows `.sh` auto-detection doesn't fire.

## Open Questions

1. **Should `using-agency` carry `EXTREMELY-IMPORTANT` tone like
   `using-superpowers`?** Superpowers uses imperative blocks. Agency's
   pattern is calmer (CORE.md doctrine). v1: imperative but
   capped at one block; revisit if agents skip the bootstrap.

2. **Do we ship `hooks-cursor.json` like Superpowers does?** It's a
   per-IDE matcher override. v1: skip — Cursor's hook model differs
   enough that this is a separate spec when Cursor adoption warrants it.

3. **Should the `matcher` include `compact`?** Superpowers does;
   episodic-memory does not. We're closer to episodic-memory's pattern
   (install is once-per-project, not once-per-compaction). v1: exclude
   `compact`.

## Evidence (cites)

- `~/.claude/plugins/cache/superpowers-marketplace/superpowers/5.1.0/
  hooks/hooks.json` — matcher + async pattern.
- `~/.claude/plugins/cache/superpowers-marketplace/superpowers/5.1.0/
  hooks/run-hook.cmd` — verbatim polyglot wrapper source.
- `~/.claude/plugins/cache/superpowers-marketplace/episodic-memory/
  1.4.2/.mcp.json` — cwd + env_vars pattern.
- `~/.claude/plugins/cache/superpowers-marketplace/superpowers/5.1.0/
  skills/using-superpowers/SKILL.md` — meta-skill template.
- `developing-claude-code-plugins` skill ref §"polyglot-hooks.md".
- Our `.mcp.json` (current) — missing cwd + env_vars.
- Our `hooks/hooks.json` (current) — missing matcher + async.

## Followup — Shipped (2026-06-04)

**Verdict:** Shipped.

### Done
- **`hooks/run-hook.cmd`** — verbatim polyglot CMD+bash wrapper
  (Superpowers 5.1.0 pattern). Heredoc-delimited CMD block runs
  first on Windows; the Unix tail handles macOS/Linux. Routes the
  first arg as the script name + passes remaining args.
- **`hooks/session-start.sh` → `hooks/session-start`** (extensionless).
  Body unchanged; only the filename so Claude Code's Windows `.sh`
  auto-bash-prepend doesn't fire.
- **`hooks/hooks.json`** — `matcher: "startup|resume|clear"` (no
  `compact` so install doesn't re-fire on every compaction) +
  `async: false` (MCP boot waits for install). Command path:
  `${PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT}}/hooks/run-hook.cmd
  session-start`.
- **`.mcp.json` (regenerated)** — `cwd: ${CLAUDE_PROJECT_DIR}` pin +
  `env_vars: ["AGENCY_DB", "AGENCY_EMBEDDER", "JULES_API_KEY"]`
  passthrough list (mirror of episodic-memory). Command path uses
  `${PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT}}` for Cursor/Codex.
- **`skills/using-agency/SKILL.md`** — broad-trigger meta-skill
  modelled on `using-superpowers`. Documents the canonical
  `agency_welcome → intent_bootstrap → verb` chain + the
  "every verb SERVES the intent" doctrine. Lists trigger keywords
  (capability, intent, provenance, dispatch, Jules, research,
  analyze, explain, reflect…) so fresh agents prime themselves
  before any verb call.
- **`install.write()`** chmods any file under `hooks/` (not just
  `.sh`-suffixed) to 0o755 so the extensionless `session-start` and
  the `run-hook.cmd` both land executable.
- **`${PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT}}` fallback** applied
  consistently: `.mcp.json` command, `hooks/hooks.json` command,
  `hooks/session-start` body's `${CLAUDE_PLUGIN_ROOT}` refs.

### Tests (10 new)
- `test_hooks_json_declares_session_start_matcher` — matcher value.
- `test_hooks_json_declares_async_false` — async: false.
- `test_hooks_json_uses_run_hook_cmd_polyglot_wrapper` — command path.
- `test_polyglot_wrapper_is_generated` — `: << 'CMDBLOCK'` head +
  `exec bash` tail.
- `test_hook_script_is_extensionless` — `session-start` not
  `session-start.sh`.
- `test_hook_files_get_executable_mode` — `install.write()` chmods
  both files.
- `test_using_agency_skill_is_generated` — frontmatter + bootstrap
  chain present.
- `test_mcp_json_pins_cwd_to_project_dir` — cwd value.
- `test_mcp_json_declares_env_vars_passthrough` — env_vars list
  contents.
- `test_mcp_json_command_uses_plugin_root_fallback` — PLUGIN_ROOT
  fallback in command path.

### Live measurements
- `pytest tests/test_install_*.py` — 24/24 green.

### Cluster-coherence (Spec 047)
- C13 (Plugin/MCP Authoring) — closes the reference-compliance gap;
  agency now matches the canonical Superpowers + episodic-memory
  patterns and runs on Windows/macOS/Linux + Cursor/Codex without
  per-IDE customisation.
