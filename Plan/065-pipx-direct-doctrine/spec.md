---
spec_id: "065"
slug: pipx-direct-doctrine
status: draft
last_updated: 2026-06-05
owner: "@agency"
depends_on: ["055", "062"]
supersedes: ["063", "064"]   # venv-fallback + shim chain replaced
affects:
  - bin/                                          # DELETED — pipx-installed agency-mcp on PATH replaces shims
  - .mcp.json                                     # command -> bare `agency-mcp`
  - hooks/session-start                           # pipx-only install (no pip --user, no venv fallback)
  - agency/cli.py                                 # add `install` subcommand
  - agency/install.py                             # _mcp_config + _SESSION_START_HOOK_SCRIPT updated
  - pyproject.toml                                # console-script for `agency install` reachability
  - README.md
  - docs/getting-started.md
  - docs/guide/extending.md
  - skills/using-agency/SKILL.md                  # `agency install --scaffold-db` not `python -m`
  - tests/test_distribution.py                    # shim tests deleted
  - tests/test_install_session_start_hook.py      # venv-fallback tests deleted
  - tests/test_install_mcp_skill.py
  - tests/test_e2e_mcp_stdio.py                   # shim discovery deleted
estimated_jules_sessions: 0
domain: meta
wave: 5
---

# Spec 065 — Pipx-direct doctrine + CLI consolidation

## Why

PR #19 review (chatgpt-codex-connector, 2026-06-05) surfaced 4 P2
correctness issues in the SessionStart hook's 3-step fallback chain
(Spec 063). All 4 are real:

1. **Hook line 25 — shim self-detection is unreliable.**
   `command -v agency-mcp` may resolve the plugin's own `bin/agency-mcp`
   shim when nothing else is installed. The hook then treats install
   as done; MCP launches the same shim which iterates PATH (finding
   nothing else), and exits 127.

2. **Hook line 46 — `pip install --user` success ≠ on PATH.**
   `~/.local/bin` may not be on PATH. Hook marks success but
   `command -v agency-mcp` fails on next session boot.

3. **Hook line 59 — Windows venv layout.** On Windows hosts running
   the hook via Git Bash, `python3 -m venv` creates
   `.agency/.venv/Scripts/`, not `bin/`. The hard-coded `bin/pip` path
   makes the fallback unreachable in the exact cross-platform/no-pipx
   case it was designed to cover.

4. **Hook line 74 — wrong Python interpreter for scaffold-db.**
   `python3 -m agency.install` uses the system python3, NOT the one
   where `agency` was just installed. The scaffold step silently
   fails with `No module named agency` in the common fresh
   marketplace install case.

Spec 063's per-project venv was added to handle sandboxed envs
without pipx. After 7 review rounds the venv path is still subtly
broken (Windows, scaffold-db interpreter, shim-shadowing). At the
same time, the user directive (2026-06-05) shifts doctrine: **"rely
on the pipx installer; remove the shims; make `agency` the default
CLI tool."**

**The fix is to ship the canonical pipx flow only.** Remove the
shims, simplify the SessionStart hook to a single pipx path, and
consolidate the CLI so `agency` is the only invocation form (no
`python -m agency.cli`).

## Done When

- [ ] **`bin/agency` and `bin/agency-mcp` deleted.** The pipx-installed
  console-scripts on PATH replace them entirely.
- [ ] **`.mcp.json` `command`** drops the `${PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT}}/bin/`
  prefix. Becomes bare `"command": "agency-mcp"` — Claude Code
  resolves it from PATH (mirror of episodic-memory pattern).
- [ ] **`hooks/session-start`** simplified to ONE install path:
  ```bash
  if ! command -v agency-mcp >/dev/null 2>&1; then
    if command -v pipx >/dev/null 2>&1; then
      pipx install --editable "${PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT}}"
    else
      echo "agency: pipx not on PATH — install pipx (https://pipx.pypa.io) and retry" >&2
      exit 0   # don't block session; MCP shows the error on first call
    fi
  fi
  ```
  No `pip --user` fallback. No `.agency/.venv` fallback. No
  pre-existing-`agency-mcp` ambiguity because the shim no longer
  exists.
- [ ] **`hooks/session-start` scaffold step uses the pipx-installed
  binary.** Replace `python3 -m agency.install --scaffold-db ...`
  with `agency install --scaffold-db ...` — that runs in the pipx
  venv where `agency` is importable (closes PR #19 review #4).
- [ ] **`agency` CLI gains an `install` subcommand** (consolidation):
  ```bash
  agency install                          # regenerate plugin install
  agency install --scaffold-db <target>   # scaffold .agency/ in target
  agency install --dry-run                # PRE-emit lint, touch nothing
  ```
  Internally calls `agency.install.main(argv)` so existing logic
  stays. `python -m agency.install` continues to work as a fallback
  for local dev (where the venv may not have run pipx yet), but is
  no longer documented as canonical.
- [ ] **All docs/tests/scripts migrate to `agency install`.** The
  `python -m agency.install` form is grandfathered (don't break it)
  but not documented anywhere downstream.
- [ ] **Spec 063 status flipped to `superseded` with `superseded_by:
  "065"` in its frontmatter.**
- [ ] **Tests aligned:**
  - `tests/test_distribution.py::test_shim_*` — the 6 shim tests
    (Spec 055/063 PATH iteration + venv-first) deleted. The shims
    don't exist anymore.
  - `tests/test_e2e_mcp_stdio.py::agency_mcp_binary` simplified to
    PATH-only (`shutil.which('agency-mcp')`).
  - `tests/test_install_session_start_hook.py` venv-fallback tests
    deleted; replaced with `test_session_start_uses_pipx_only`.
  - `tests/test_install_mcp_skill.py` asserts `.mcp.json` command is
    bare `agency-mcp`.
- [ ] **README + getting-started + extending docs** drop:
  - `bin/agency` / `bin/agency-mcp` references
  - `.agency/.venv` mentions
  - `pip --user` fallback mentions
  - `python -m agency.install` → `agency install`
  - `python -m agency.cli` → `agency` (when appropriate)
- [ ] `agency install` round-trip works on a clean pipx install
  (smoke-tested via the test).
- [ ] `python -m pytest -q -n auto -m "not e2e"` stays green.

## Design

### Why pipx-only (not pipx + pip --user fallback)

PR #19 review #2 surfaced the load-bearing issue: `pip install --user`
puts binaries in `~/.local/bin`, which **isn't on PATH by default**
on most Linuxes (it's PEP 668 user-scheme, often opt-in). Marking the
hook successful after pip succeeds gives false confidence; the MCP
boot still fails.

We could fix this by probing `command -v agency-mcp` after pip --user
and falling through to venv if absent. But:

- The venv fallback itself has cross-platform issues (PR #19 review #3).
- The shim has self-detection issues (PR #19 review #1).
- Both add ~50 lines of bash that mostly tries-and-fails before pipx.

**Pipx is the canonical install path per Spec 055.** Make the hook
require it. Users without pipx get a clear message + a link to pipx
installation docs. They can retry after fixing their env.

### Why remove the shims

The `bin/agency` + `bin/agency-mcp` shims existed because the
marketplace flow puts the plugin tree at `${CLAUDE_PLUGIN_ROOT}` and
`.mcp.json` reaches into that tree via a relative-ish path. Pipx
console-scripts land on PATH directly — the shim is unnecessary
machinery once `.mcp.json` uses bare `"command": "agency-mcp"`.
Episodic-memory ships this way; superpowers ships node entry-points
that work the same way. The shim was a defensive holdover from the
pre-Spec-055 `.venv` bootstrap era.

Removing the shims also resolves:
- The Spec 055 PR-review iteration on PATH-vs-self resolution
  (3+ rounds of `type -ap` / `realpath` complications).
- The Spec 063 venv-vs-PATH ordering question.
- PR #19 review #1 entirely.

### CLI consolidation

Today: `python -m agency.cli` is the "bash-only / Jules / no-MCP"
invocation. `agency` (the pipx console-script) IS the same module
(`agency.cli:main`), reachable via PATH after pipx install.

The directive: make `agency` the documented form. Add an `install`
subcommand so `python -m agency.install` is no longer needed in
common flows.

```python
# agency/cli.py
def main():
    p = argparse.ArgumentParser(prog="agency", ...)
    sub = p.add_subparsers(dest="cmd", required=True)
    # existing subcommands: intent, search, get-schema, execute
    install = sub.add_parser("install",
                             help="regenerate the plugin install files")
    install.add_argument("root", nargs="?")
    install.add_argument("--scaffold-db", action="store_true")
    install.add_argument("--dry-run", action="store_true")
    # …existing subcommands…
    ns = p.parse_args()
    if ns.cmd == "install":
        from . import install as install_mod
        argv = []
        if ns.root: argv.append(ns.root)
        if ns.scaffold_db: argv.append("--scaffold-db")
        if ns.dry_run: argv.append("--dry-run")
        return install_mod.main(argv)
    # …existing dispatch…
```

`agency install` → `agency.install.main([...])`. The `python -m
agency.install` form still works (`install.main` is the same callable);
just don't document it as primary.

## Files

- **Delete:** `bin/agency`, `bin/agency-mcp`.
- **Modify:**
  - `.mcp.json` (regenerated)
  - `agency/install.py` — `_mcp_config()` drops the `bin/` prefix;
    `_SESSION_START_HOOK_SCRIPT` collapses to single pipx path
    with `agency install --scaffold-db`.
  - `agency/cli.py` — add `install` subcommand.
  - `hooks/session-start` (regenerated)
  - `README.md`, `docs/getting-started.md`, `docs/guide/extending.md`,
    `skills/using-agency/SKILL.md`.
  - Plan/063 frontmatter — `status: superseded`, `superseded_by: "065"`.
- **Tests touched:** 4 test files (distribution, session-start-hook,
  mcp-skill, e2e); ~10 tests deleted; ~3 added.

## Open Questions

1. **Should the hook surface a more helpful error when pipx isn't
   on PATH?** v1: print pipx install URL. v2 could detect common
   "you have pip, you don't have pipx" and suggest
   `python3 -m pip install --user pipx` + remind to add `~/.local/bin`
   to PATH. Recommend v1 for ship cleanliness.

2. **Should `agency install` accept the existing positional `root`
   argument?** Yes — install.main() already handles it. The wrapper
   passes through unchanged.

3. **Do we need a deprecation period for `bin/agency*` shims?**
   Probably not — they're not user-facing scripts (pipx-installed
   binaries are). Marketplace consumers picked up the new
   `.mcp.json` shape on the next session anyway.

## Evidence (cites)

- PR #19 review comments 3360826483 / 86 / 88 / 90 (the 4 P2
  findings) — `https://github.com/netzkontrast/agency/pull/19`.
- Spec 055 §"Done When" — pipx-canonical foundation.
- Spec 062 §"Why" — auto-install rationale (preserved).
- Spec 063 §"Why" — per-project venv fallback (this spec supersedes).
- `~/.claude/plugins/cache/superpowers-marketplace/episodic-memory/
  1.4.2/.mcp.json` — bare `"command": "node"` precedent for the
  no-shim pattern.
- User directive 2026-06-05 — "make agency the default CLI tool, no
  agency.cli; remove the shims; rely on pipx."

## Followup — Shipped (2026-06-05)

**Verdict:** Shipped.

### Done
- **`bin/agency` and `bin/agency-mcp` deleted.** No shims; pipx
  console-scripts on PATH replace them.
- **`.mcp.json` `command`** → bare `"agency-mcp"` (PATH resolution,
  episodic-memory pattern).
- **`hooks/session-start`** collapsed to single pipx path: try pipx
  install, fail-soft with install hint if pipx isn't on PATH. No
  pip --user, no `.agency/.venv`.
- **Scaffold step** uses `agency install --scaffold-db` — the pipx-
  installed binary, NOT system python3 (PR #19 review #2).
- **`agency install` subcommand** ships on the CLI; dispatches to
  `install.main([...])`. Replaces `python -m agency.install` as the
  documented form (module form still works for local dev).
- **`agency welcome` / `agency doctor` / `agency provenance` ship as
  subcommands** wrapping the corresponding substrate tools so the
  bash surface reaches the full code-mode + onboarding interface
  without inline `execute --code` blocks.
- **Spec 063 frontmatter** → `status: superseded`, `superseded_by:
  "065"`.
- **Tests aligned**: 6 shim tests (Spec 055/063) + 2 venv-fallback
  tests deleted; 4 new substrate-CLI tests added; `.mcp.json` /
  `.agency/.venv` / `python -m agency.install` assertions updated.
- **Docs swept**: README, docs/getting-started, docs/guide/extending,
  AGENTS.md, skills/using-agency — all references to `python -m
  agency.cli`/`python -m agency.install` rewritten to `agency` /
  `agency install`; all `bin/agency*` references removed; Spec 063
  fallback chain language replaced with the pipx-only flow.

### Tests
- `test_session_start_script_uses_pipx_only` — new positive
  assertion.
- `test_mcp_json_command_is_bare_agency_mcp` — new positive
  assertion replacing the PLUGIN_ROOT-fallback test.
- `test_agency_install_cli_subcommand_dry_run` + `_scaffold_db` —
  4 new CLI subcommand smoke tests including welcome/doctor/provenance.
- 6 shim tests deleted from `test_distribution.py`.
- 2 venv-fallback tests deleted from `test_install_session_start_hook.py`.

### Live measurements
- `pytest tests/test_install_*.py tests/test_distribution.py` —
  35/35 + 1 skip green.

### PR #19 review closure
All 4 P2 findings resolved:
- #1 (shim self-detection): shim removed.
- #2 (wrong python interpreter for scaffold): `agency install` uses
  the pipx-installed binary.
- #3 (Windows venv layout): no venv fallback.
- #4 (pip --user not on PATH): no pip --user fallback.

### Cluster-coherence (Spec 047)
- C13 (Plugin/MCP Authoring) — collapses the install surface to the
  Spec 055 pipx-canonical doctrine. Removes the iterations of Spec
  055/062/063/064 that layered defensive complexity atop the simple
  case; restores doctrinal clarity.

## Follow-up — round-2 review fixes (2026-06-05 PM)

PR #19 round-2 review (still-open threads after the initial Spec 065
push) surfaced two more issues both rooted in the **same** flaw the
Spec was trying to close: `agency install --scaffold-db` against the
project root still ran `write(target)` before `scaffold_db`, which
**overwrites the user's `.mcp.json` / `hooks/` / `skills/` /
`commands/`** in their project repo (P1). The early-exit on
`command -v agency-mcp` also prevented `.agency/` scaffolding in
fresh project repos when a user already had agency-mcp on PATH from a
prior install (P2).

### What landed
- **New `--scaffold-only` flag on `agency install`.** Does the
  `.agency/` scaffold + `.gitattributes` binary marker, NOTHING ELSE.
  Never calls `write(target)`. This is the canonical hook entry
  point.
- **SessionStart hook restructured.** Scaffold step now runs BEFORE
  the install-check early-exit (so already-installed users still get
  `.agency/` in fresh projects), and uses `--scaffold-only` for both
  the pre-exit and post-install scaffold calls.
- **Two new tests**:
  - `test_session_start_scaffolds_before_install_early_exit` —
    asserts the scaffold block index < idempotency-guard index in
    the generated hook script.
  - `test_agency_install_scaffold_only_does_not_write_plugin_files`
    — calls `cli_main(["install", str(tmp_path), "--scaffold-only"])`
    and asserts `.agency/` + `.gitattributes` exist while `.mcp.json`
    / `.claude-plugin/` / `hooks/` / `skills/` / `commands/` do NOT.

### PR #19 round-2 closure
- PRRT_kwDOSj5Qos6HSLSR (P2 — Scaffold even when server is already
  installed): scaffold now runs unconditionally before the
  early-exit.
- PRRT_kwDOSj5Qos6HSLSV (P1 — Avoid writing plugin files into the
  target repo): `--scaffold-only` bypasses `write()` entirely.

## Follow-up — round-3 review fixes (2026-06-05 PM)

PR #19 round-3 review (after round-2 push) surfaced two more P2
findings, both about the install/launch boundary surviving real
edge cases:

### What landed
- **`hooks/hooks.json` substitution simplified.** Replaced bash
  parameter-expansion `${PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT}}` with
  the canonical `${CLAUDE_PLUGIN_ROOT}` token. Claude Code's command
  substitution layer does not honor bash `${VAR:-default}` syntax;
  the unset-var fallback was therefore providing no real coverage
  while risking a literal/malformed command in environments that
  pass the field through the launcher unmodified.
- **Hook validates pipx PATH after install.** After `pipx install`
  succeeds, the hook now:
  1. Probes `pipx environment --value PIPX_BIN_DIR` to find where
     pipx put the console scripts (default `~/.local/bin`).
  2. Prepends that dir to `PATH` for THIS process so the immediate
     `agency install --scaffold-only` call resolves.
  3. Runs `pipx ensurepath` so future shells inherit it.
  4. Hard-validates `command -v agency-mcp` and surfaces an
     actionable HINT (with the resolved dir) if it's still missing
     instead of silently falling through.

### PR #19 round-3 closure
- PRRT_kwDOSj5Qos6HSqkH (P2 — hook-root substitution): switched to
  canonical `${CLAUDE_PLUGIN_ROOT}`.
- PRRT_kwDOSj5Qos6HSqkN (P2 — pipx app dir not on PATH): probe +
  prepend + ensurepath + hard validation.

### Tests
- `test_hooks_json_uses_run_hook_cmd_polyglot_wrapper` updated to
  assert canonical token form.
- `test_session_start_probes_pipx_bin_dir_and_validates_path` —
  new test asserting the 4-step probe/validate flow.
