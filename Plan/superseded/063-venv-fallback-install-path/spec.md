---
spec_id: "063"
slug: venv-fallback-install-path
status: superseded   # 2026-06-05: PR #19 review surfaced 4 P2 issues in the 3-step chain; Spec 065 ships pipx-only
state: superseded
superseded_by: "065"
last_updated: 2026-06-05
owner: "@agency"
depends_on: ["055", "061", "062"]
affects:
  - hooks/session-start.sh                # extends the install fallback chain
  - bin/agency-mcp                         # shim prefers .agency/.venv before PATH
  - bin/agency                              # same
  - agency/install.py                      # generate updated shim + extended hook
  - README.md                              # document the venv fallback
  - tests/test_install_session_start_hook.py
  - tests/test_distribution.py             # shim resolution order
estimated_jules_sessions: 0
domain: meta
wave: 4
---

# Spec 063 — `.agency/.venv` fallback install path

## Why

Spec 055 made pipx the canonical install. Spec 062 added a SessionStart
hook that auto-runs `pipx install` on first session. That handles
~95% of environments — local dev, mainstream Claude Code Web, CI.

The remaining 5% are **environments where pipx is unavailable AND
`pip --user` doesn't put `~/.local/bin` on PATH** (some sandboxed Web
envs, restricted corporate setups, container-layer constraints):

- pipx not installed and no admin to install it.
- `pip --user` works but `~/.local/bin` isn't auto-added to PATH.
- `agency-mcp` never lands somewhere the `.mcp.json` shim can find it.

Spec 062's hook prints a hint and the shim exits 127. The user sees a
silent failure with breadcrumbs but no automatic recovery.

**The fallback is a per-project venv** at
`${CLAUDE_PROJECT_DIR}/.agency/.venv/`. When pipx is unavailable, the
hook creates a venv inside the target repo's `.agency/` dir (which
Spec 020 + Spec 062 already manage as a per-project root for the
graph DB). `agency` gets pip-installed into THAT venv. The
`bin/agency-mcp` shim grows a single check that prefers the
project-local venv before falling through to PATH.

Why per-project (not per-user, not global):
- The `.agency/` dir already EXISTS per-project (Spec 020 graph DB).
- Disappears cleanly when the project is deleted (no leftover state).
- Survives Claude Code Web container rotation as long as the project
  workspace is preserved.
- No PATH manipulation required.

## Done When

- [ ] **`bin/agency-mcp` shim grows a venv check.** New resolution order:
  1. `${CLAUDE_PROJECT_DIR}/.agency/.venv/bin/agency-mcp` if executable
  2. PATH (existing Spec 055 behavior; `type -ap` iteration)
  3. Exit 127 with the install hint
  Same shape for `bin/agency`.
- [ ] **`hooks/session-start.sh` extends to a 3-step fallback chain:**
  1. Early-exit if `agency-mcp` already on PATH OR in `.agency/.venv/bin/`.
  2. Try `pipx install --editable` (existing Spec 062 path).
  3. If pipx returns non-zero AND `pip --user` returns non-zero,
     **create `${CLAUDE_PROJECT_DIR}/.agency/.venv` + `pip install --editable`
     ${CLAUDE_PLUGIN_ROOT} into it** — the new fallback path.
- [ ] **Hook also runs `python -m agency.install --scaffold-db`** after
  the install succeeds (any path), pointing at `${CLAUDE_PROJECT_DIR}`.
  This guarantees `.agency/session.db` + `.agency/README.md` +
  `.gitattributes` land in the target repo on first session, with or
  without the venv fallback. (Spec 020 §scaffold-db already supports
  this CLI mode.)
- [ ] **`tests/test_distribution.py` covers the new shim resolution
  order.** Two new tests:
  - venv binary at `${CLAUDE_PROJECT_DIR}/.agency/.venv/bin/agency-mcp`
    is preferred over PATH match.
  - falls through to PATH when no venv binary exists (existing
    behavior preserved).
- [ ] **`tests/test_install_session_start_hook.py` extends:**
  - hook script contains the venv-fallback path
    (`python -m venv .agency/.venv` + `pip install -e`).
  - hook script always invokes `python -m agency.install --scaffold-db`.
- [ ] **README.md** documents the fallback chain — the user sees one
  paragraph "Install fallback for sandboxed environments" under the
  marketplace install section.
- [ ] `python -m agency.install` regenerates the new bin/ shim files;
  `scripts/check-drift` clean.
- [ ] `python -m pytest -q -n auto -m "not e2e"` stays green.

## Design

### `bin/agency-mcp` shim — venv-first resolution

```bash
#!/usr/bin/env bash
# agency-mcp — thin router. Spec 055/062/063 install paths:
#   1. ${CLAUDE_PROJECT_DIR}/.agency/.venv/bin/agency-mcp (venv fallback)
#   2. PATH (pipx-installed / pip --user / global)
set -euo pipefail

SELF="$(readlink -f "${BASH_SOURCE[0]}" 2>/dev/null || python3 -c '...' "${BASH_SOURCE[0]}")"

# Spec 063 — per-project venv check (FIRST so a project-pinned agency
# version wins over a stale global). CLAUDE_PROJECT_DIR is set by
# Claude Code; bail safely if unset.
if [[ -n "${CLAUDE_PROJECT_DIR:-}" ]]; then
  VENV_BIN="${CLAUDE_PROJECT_DIR}/.agency/.venv/bin/agency-mcp"
  if [[ -x "$VENV_BIN" ]]; then
    exec "$VENV_BIN" "$@"
  fi
fi

# Existing Spec 055 PATH iteration follows…
```

### Hook fallback chain

```bash
#!/usr/bin/env bash
set -e

# Idempotent: both possible install locations already populated.
if command -v agency-mcp >/dev/null 2>&1; then exit 0; fi
if [[ -x "${CLAUDE_PROJECT_DIR:-/dev/null}/.agency/.venv/bin/agency-mcp" ]]; then
  exit 0
fi

INSTALL_OK=0

# Path 1 — pipx (canonical per Spec 055/062).
if command -v pipx >/dev/null 2>&1; then
  echo "agency: installing via pipx (one-time)" >&2
  if pipx install --editable "${CLAUDE_PLUGIN_ROOT}" >&2; then
    INSTALL_OK=1
  fi
fi

# Path 2 — pip --user.
if [[ "$INSTALL_OK" -eq 0 ]] && command -v pip >/dev/null 2>&1; then
  echo "agency: pipx unavailable; trying pip --user" >&2
  if pip install --user --editable "${CLAUDE_PLUGIN_ROOT}" >&2; then
    INSTALL_OK=1
  fi
fi

# Path 3 — per-project venv (Spec 063 fallback).
if [[ "$INSTALL_OK" -eq 0 ]] && [[ -n "${CLAUDE_PROJECT_DIR:-}" ]]; then
  echo "agency: pip --user also unavailable; creating .agency/.venv" >&2
  mkdir -p "${CLAUDE_PROJECT_DIR}/.agency"
  python3 -m venv "${CLAUDE_PROJECT_DIR}/.agency/.venv"
  "${CLAUDE_PROJECT_DIR}/.agency/.venv/bin/pip" install \
    --editable "${CLAUDE_PLUGIN_ROOT}" >&2 && INSTALL_OK=1
fi

# After ANY successful install path: scaffold the target repo's .agency/.
if [[ "$INSTALL_OK" -eq 1 ]] && [[ -n "${CLAUDE_PROJECT_DIR:-}" ]]; then
  python3 -m agency.install --scaffold-db "${CLAUDE_PROJECT_DIR}" >&2 || true
fi

exit 0
```

### Resolution discipline

The order `.venv → PATH` is deliberate: a per-project venv pin should
override a stale global install. The opposite order would silently
let an old global agency answer for a project that wanted a newer
version.

### What the user sees

- pipx available → existing Spec 062 flow; one-time ~5s install.
- pipx missing, pip --user works → "pipx unavailable; trying pip --user"
  → install completes; ~/.local/bin must be on PATH or shim still
  fails (this is the gap Spec 063 ALSO closes via venv).
- Both unavailable → "creating .agency/.venv" → installs locally;
  shim's venv-first check picks it up next session.
- All three fail → hook exits 0 (don't block startup); shim exits 127
  with hint on first MCP boot.

## Files

- **Modify:**
  - `agency/install.py` — render `bin/agency-mcp` + `bin/agency` shims
    with the venv-first check; extend `_SESSION_START_HOOK_SCRIPT`
    with the venv fallback + post-install scaffold-db call.
  - `bin/agency-mcp`, `bin/agency` — regenerated.
  - `hooks/session-start.sh` — regenerated.
  - `README.md` — fallback paragraph.
- **Modify (tests):**
  - `tests/test_distribution.py` — venv-first shim resolution + falls
    through to PATH.
  - `tests/test_install_session_start_hook.py` — venv fallback path
    asserted; scaffold-db invocation asserted.

## Open Questions

1. **Which Python interpreter creates the venv?** The hook uses
   `python3`. If the target system has only `python` (no `python3`
   symlink), the venv step fails. Recommend `python3` as the canonical
   form per `pep-0394`; document the requirement.

2. **Should the shim's venv check ALSO honour `${VIRTUAL_ENV}`?** A
   user with their own activated venv might expect that to win. v1:
   no — Spec 063 specifically wants the per-project `.agency/.venv`
   to win. If the user wants their own venv, they `pipx install` and
   benefit from PATH resolution.

3. **Does `pip install --editable` from a marketplace clone make sense?**
   Yes — Claude Code refreshes the plugin tree atomically when the
   user runs `/plugin update`, so editable installs follow updates
   without a second pip call.

## Evidence (cites)

- Spec 055 §"Done When" — pipx as canonical install. Spec 063 ADDS a
  fallback for sandboxed envs; pipx remains the recommended path.
- Spec 062 §"Why" — the silent failure surface this spec eliminates.
- `bin/agency-mcp` (current) — the PATH-router shape Spec 063 extends
  with a venv check.
- `agency/install.py:415` — the existing `--scaffold-db` flag the hook
  now invokes automatically.

## Followup — Shipped (2026-06-04)

**Verdict:** Shipped.

### Done

- **`bin/agency-mcp` + `bin/agency` shims** grew a venv-first check:
  if `${CLAUDE_PROJECT_DIR}/.agency/.venv/bin/agency-mcp` (or `…/agency`)
  is executable, the shim execs it directly without iterating PATH.
  Falls through to the existing Spec 055 PATH-iteration logic
  otherwise.
- **`hooks/session-start.sh`** rewritten as a 3-step install chain:
  - Path 1: `pipx install --editable` (Spec 055/062 canonical).
  - Path 2: `pip install --user --editable` (sandboxed envs).
  - Path 3: `python3 -m venv ${CLAUDE_PROJECT_DIR}/.agency/.venv` +
    pip-install agency into it (Spec 063 per-project fallback).
- **Post-install `--scaffold-db`** runs after ANY successful path,
  pointed at `${CLAUDE_PROJECT_DIR}`. Idempotent — the existing
  `agency_install` substrate tool no-ops when the dir is already set
  up; the CLI form mirrors that. The graph DB, README, and
  .gitattributes land in the project root on first session.
- **Idempotency**: hook early-exits when EITHER PATH-resolved
  `agency-mcp` OR the per-project venv binary already exists. The
  install loop runs at most once per project across all sessions.
- **Tests**: 4 new tests
  - `test_shim_prefers_project_venv_over_path` — venv beats stale
    PATH binary.
  - `test_shim_falls_through_to_path_when_no_venv` — Spec 055
    behavior preserved when no venv.
  - `test_session_start_script_includes_venv_fallback` — Path 3 in
    the rendered script.
  - `test_session_start_script_runs_scaffold_db_after_install` —
    target-repo scaffold call.
  - + `test_session_start_script_documents_three_paths` — sanity
    on the comment block.
- **README**: the "Fallback chain" block expanded to mention the
  per-project venv fallback + target-repo scaffold step.

### Live measurements
- `pytest tests/test_distribution.py tests/test_install_session_start_hook.py`
  — 17/17 green.

### Cluster-coherence (Spec 047)
- C13 (Plugin/MCP Authoring) — three-step fallback chain closes the
  remaining install gap; sandboxed Web envs without pipx now
  auto-install via the project venv path.
