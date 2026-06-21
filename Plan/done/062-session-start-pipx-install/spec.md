---
spec_id: "062"
slug: session-start-pipx-install
status: complete   # 2026-06-04: hook script + hooks.json + install.py wiring + README + 5 tests
state: done
last_updated: 2026-06-04
owner: "@agency"
depends_on: ["055", "061"]
affects:
  - hooks/hooks.json                     # NEW — SessionStart hook registration
  - hooks/session-start.sh                # NEW — idempotent pipx install script
  - agency/install.py                    # generate the hook files
  - .claude-plugin/plugin.json           # marketplace clone surface tests this
  - README.md                            # document the auto-pipx flow
  - tests/test_install_session_start_hook.py  # NEW
estimated_jules_sessions: 0
domain: meta
wave: 4
---

# Spec 062 — SessionStart auto-pipx install

## Why

Spec 055 settled pipx as the only install path. Spec 061 closed the
`.mcp.json` drift. But there's a **missing link in the marketplace
install flow**, especially in **Claude Code Web environments**:

1. User runs `/plugin install agency@agency` (web OR local).
2. Claude Code clones the repo to `${CLAUDE_PLUGIN_ROOT}`.
3. The committed `.mcp.json` references `${CLAUDE_PLUGIN_ROOT}/bin/
   agency-mcp`.
4. `bin/agency-mcp` is a PATH router (Spec 055) that exits 127 with a
   hint if `agency-mcp` console-script isn't on PATH.
5. **In a fresh Claude Code Web env, `agency-mcp` is NOT on PATH yet
   — nothing has run pipx**. The MCP server fails to start on first
   session; the user has to manually `pipx install <plugin-root>` and
   restart.

The web environment surfaces this as a **silent failure**: the plugin
appears installed, but the MCP server never connects, the agent has no
agency tools, and the diagnosis requires reading the .mcp.json env or
running `agency-doctor` (which itself isn't on PATH yet).

**The fix is a SessionStart hook** that idempotently runs
`pipx install` on first session. Once `agency-mcp` is on PATH, the
hook exits early on every subsequent session. The user sees one extra
~5 second pause on the FIRST session after install; thereafter the
plugin just works.

## Done When

- [ ] **`hooks/hooks.json`** registers a SessionStart hook pointing at
  `${CLAUDE_PLUGIN_ROOT}/hooks/session-start.sh`. Per Claude Code
  plugin convention (`developing-claude-code-plugins` skill ref): the
  `hooks/hooks.json` file is auto-loaded — do NOT also reference it in
  `plugin.json`'s `manifest.hooks` field (that triggers "Duplicate
  hooks file detected" errors).
- [ ] **`hooks/session-start.sh`** is the idempotent install script:
  ```bash
  #!/usr/bin/env bash
  set -e
  if command -v agency-mcp >/dev/null 2>&1; then
    exit 0   # already on PATH — nothing to do
  fi
  if command -v pipx >/dev/null 2>&1; then
    pipx install --editable "${CLAUDE_PLUGIN_ROOT}" >&2
  elif command -v pip >/dev/null 2>&1; then
    pip install --user "${CLAUDE_PLUGIN_ROOT}" >&2
  else
    echo "agency: neither pipx nor pip on PATH — install one and retry" >&2
    exit 0   # don't block session start; user will see the .mcp.json shim's exit 127
  fi
  ```
  Marked executable (mode 0755). Editable mode means future marketplace
  plugin updates flow through to the live console-scripts without a
  second pipx call.
- [ ] **`agency/install.py::generate()`** produces both hook files so
  `python -m agency.install` regenerates them. The hook script lives
  under `hooks/` (rendered from a string constant, parallel to how
  `bin/agency-mcp` is generated).
- [ ] **`tests/test_install_session_start_hook.py`** asserts:
  - `hooks/hooks.json` declares a SessionStart hook with the expected
    command shape.
  - `hooks/session-start.sh` contains the idempotency guard
    (`command -v agency-mcp` early-exit) and the pipx fallback chain.
  - `generate()` returns both files in its dict.
  - The script is marked executable (mode bit) when written via
    `install.write()`.
- [ ] **README.md** documents the auto-install flow — one short
  paragraph under "Install (Claude Code)" — and notes the one-time
  cold-start cost.
- [ ] `python -m agency.install` produces a clean diff; the new files
  appear in the install tree.
- [ ] `python -m pytest -q -n auto -m "not e2e"` stays green.

## Design

### Why SessionStart vs PreToolUse

`SessionStart` fires once per session at startup, BEFORE any tool runs.
That's the only safe moment to install something — `PreToolUse` is per-
tool-call and the MCP server boot happens before any tool is called.
The session won't have agency MCP tools available on the FIRST session
(pipx hasn't run yet), but the hook runs first; the SECOND session has
everything.

Alternative: `PostToolUse` after the first user prompt. Worse — the
user already tried to do something and saw it fail.

### Why `pipx install --editable` not `--force`

- `--editable` makes the pipx venv reference the source tree directly.
  Marketplace plugin updates (Claude Code refreshes
  `${CLAUDE_PLUGIN_ROOT}`) flow through automatically — no separate
  upgrade step.
- `--force` would reinstall on every session even when agency-mcp IS on
  PATH, which is the wrong default. The idempotency guard at the top
  of the script handles "already installed" correctly without --force.

### Fail-soft semantics

If neither pipx nor pip is on PATH, the hook prints a message but
returns 0 (don't block session start). The `.mcp.json` shim then
exits 127 with the install hint on first MCP boot. The user has a
useful trail of breadcrumbs either way.

### Polyglot (Windows) deferred

Cross-platform polyglot wrappers (Windows CMD compatibility) are a
v2 concern. Web environments are Linux; the bare bash script is enough
for v1. The hooks/run-hook.cmd polyglot wrapper from the
developing-claude-code-plugins skill ref lands in v2 when a Windows
user opens an issue.

## Files

- **Create:**
  - `hooks/hooks.json` — SessionStart registration.
  - `hooks/session-start.sh` — the install script.
  - `tests/test_install_session_start_hook.py` — assertions.
- **Modify:**
  - `agency/install.py` — `_session_start_hook_json()` +
    `_session_start_hook_script()` helpers + entries in `generate()`'s
    output dict. `install.write()` already chmods executable bits for
    files under `bin/` and `hooks/`.
  - `README.md` — one paragraph under "From the GitHub marketplace".

## Open Questions

1. **Should we `pipx upgrade` if agency-mcp IS on PATH but the version
   differs?** The committed `VERSION` in `pyproject.toml` could be
   compared with `agency-doctor --json | jq .agency_version`. v1 keeps
   it simple (early-exit if on PATH); v2 can add version-drift detection
   if marketplace upgrades become routine.

2. **Should the hook log to a file for diagnostics?** v1: write to
   stderr (visible in Claude Code's session log). v2 could persist to
   `~/.cache/agency/install.log`.

3. **What about `uv` instead of pipx?** `uv tool install` is a faster
   alternative. v1 prefers pipx (already canonical per Spec 055); the
   hook can grow a `uv tool install` branch in v2 when uv adoption
   warrants it.

## Evidence (cites)

- Spec 055 §"Done When" — established pipx as the canonical install
  path; this spec closes the marketplace-flow gap.
- Spec 061 §"Why" — already noted the `.mcp.json` drift; this spec is
  the runtime complement (script that ensures agency-mcp is on PATH
  before the shim runs).
- `developing-claude-code-plugins` skill ref §"Hooks (hooks/hooks.json)"
  — the hooks.json auto-load convention this spec follows.
- `bin/agency-mcp` exit 127 hint — the silent-failure-surface this
  spec eliminates for the marketplace flow.

## Followup — Shipped (2026-06-04)

**Verdict:** Shipped.

### Done
- `hooks/session-start.sh` ships idempotent install with
  pipx → pip --user → fail-soft fallback chain.
- `hooks/hooks.json` registers the SessionStart hook per Claude Code
  plugin convention (auto-loaded; NOT also referenced in plugin.json
  to avoid the "Duplicate hooks file detected" error).
- `agency/install.py` constants `_SESSION_START_HOOKS_JSON` +
  `_SESSION_START_HOOK_SCRIPT` rendered into `generate()`'s output
  dict so `python -m agency.install` regenerates them.
- `install.write()` extended to chmod 0o755 on `hooks/*.sh` in
  addition to `bin/` files.
- README.md gains a paragraph documenting the auto-install flow
  + fallback chain; Web environments specifically called out.

### Tests (tests/test_install_session_start_hook.py — 5 tests)
- `hooks.json` declares SessionStart with the expected command shape.
- Script carries the `command -v agency-mcp` idempotency guard +
  pipx and pip fallback paths.
- Script starts with the bash shebang.
- `install.write()` writes the script with executable mode bits.
- `plugin.json` does NOT carry a top-level `hooks` key (duplicate-hooks
  guard per Claude Code plugin doc).

### Live measurements
- `pytest tests/test_install_session_start_hook.py` — 5/5 green.
- `scripts/check-drift` — clean post-regen.

### Cluster-coherence (Spec 047)
- C13 (Plugin/MCP Authoring) — closes the install-flow gap left
  by Spec 055; marketplace consumers no longer need a manual pipx
  step.
