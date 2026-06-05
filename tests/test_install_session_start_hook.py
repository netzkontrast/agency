"""Spec 062 — SessionStart hook auto-runs pipx install on first session.

The marketplace install flow (especially Claude Code Web) clones the
plugin to ${CLAUDE_PLUGIN_ROOT} but does NOT run pipx, so `agency-mcp`
isn't on PATH and the .mcp.json shim exits 127 silently. The hook
landed in this spec closes that loop.
"""
from __future__ import annotations

import json
import os
import stat

from agency.engine import Engine
from agency.install import generate, write


def _files():
    e = Engine(":memory:")
    try:
        return generate(e)
    finally:
        e.memory.close()


# ---------------------------------------------------------------------------
# hooks.json shape.
# ---------------------------------------------------------------------------


def test_hooks_json_registers_session_start():
    files = _files()
    assert "hooks/hooks.json" in files, sorted(files)
    cfg = json.loads(files["hooks/hooks.json"])
    session_start = cfg["hooks"]["SessionStart"]
    assert isinstance(session_start, list) and len(session_start) >= 1
    entry = session_start[0]
    assert isinstance(entry, dict)
    commands = entry["hooks"]
    assert any(
        h["type"] == "command"
        and "session-start" in h["command"]
        and "CLAUDE_PLUGIN_ROOT" in h["command"]
        for h in commands
    ), f"unexpected hook shape: {commands}"


# ---------------------------------------------------------------------------
# session-start.sh idempotency + fallback shape.
# ---------------------------------------------------------------------------


def test_session_start_script_has_idempotency_guard():
    files = _files()
    assert "hooks/session-start" in files, sorted(files)
    script = files["hooks/session-start"]
    # Idempotency: bail out if agency-mcp is already on PATH.
    assert "command -v agency-mcp" in script
    # Spec 065: pipx is the canonical (and only) install path.
    assert "pipx install --editable" in script
    # Spec 065: no pip --user install action for agency itself, no
    # .agency/.venv fallback. The HINT block mentions `pip install
    # --user pipx` (user-facing fix for missing pipx — not an install
    # action by us); the comment block mentions `.agency/.venv` in
    # historical/why context. Only the CODE paths must be absent.
    code_lines = [ln for ln in script.splitlines() if not ln.lstrip().startswith("#")]
    code = "\n".join(code_lines)
    assert "pip install --user --editable" not in code
    assert "python3 -m venv" not in code
    assert ".agency/.venv" not in code
    # Fail-soft: don't block session start when pipx isn't on PATH.
    assert "exit 0" in script


# ---------------------------------------------------------------------------
# Spec 065 — single pipx install path + agency CLI for scaffold-db.
# ---------------------------------------------------------------------------


def test_session_start_script_uses_pipx_only():
    """Spec 065: the 3-step fallback chain (Spec 063) is gone. Pipx is
    THE install path. If pipx isn't reachable the hook prints a clear
    hint and exits 0 without blocking session startup."""
    script = _files()["hooks/session-start"]
    # Restrict to code lines so historical/context refs in comments
    # don't false-fire.
    code = "\n".join(
        ln for ln in script.splitlines() if not ln.lstrip().startswith("#"))
    # No project venv creation, no pip --user install of agency.
    assert "python3 -m venv" not in code
    assert "pip install --user --editable" not in code
    # Pipx is the single install path.
    assert "command -v pipx" in code
    # Helpful hint when pipx is missing (HINT heredoc — not a comment).
    assert "pipx.pypa.io" in script


def test_session_start_script_runs_scaffold_after_install():
    """Spec 065 follow-up (PR #19 P1 + P2 fixes): the hook uses
    `agency install --scaffold-only` (NOT --scaffold-db) so we never
    overwrite the user's .mcp.json / hooks/ / skills/ / commands/
    when CLAUDE_PROJECT_DIR is the install root."""
    script = _files()["hooks/session-start"]
    assert "agency install --scaffold-only" in script
    assert "${CLAUDE_PROJECT_DIR}" in script
    # Explicit absence: don't use the system python3 form.
    assert "python3 -m agency.install" not in script
    # PR #19 P1 fix: --scaffold-db would call write() against the
    # project root, overwriting the user's plugin install files.
    assert "agency install --scaffold-db" not in script


def test_session_start_probes_pipx_bin_dir_and_validates_path():
    """Spec 065 round-3 (PR #19 P2 PRRT_kwDOSj5Qos6HSqkN): after
    `pipx install` succeeds, pipx's app dir (PIPX_BIN_DIR, default
    ~/.local/bin) may not yet be on PATH if the user hasn't run
    `pipx ensurepath` + restarted the shell. The hook MUST:
      1. Probe PIPX_BIN_DIR via `pipx environment --value PIPX_BIN_DIR`
      2. Prepend it to PATH for this process
      3. Run `pipx ensurepath` so future sessions inherit it
      4. Hard-validate `command -v agency-mcp` and surface an
         actionable HINT if missing (don't silently fall through)."""
    script = _files()["hooks/session-start"]
    assert "pipx environment --value PIPX_BIN_DIR" in script
    assert "export PATH=" in script
    assert "pipx ensurepath" in script
    # The post-install validation block must check agency-mcp and
    # print a hint pointing at ensurepath + shell restart.
    post_install = script.split("pipx install --editable", 1)[1]
    assert "command -v agency-mcp" in post_install
    assert "pipx ensurepath" in post_install


def test_session_start_scaffolds_before_install_early_exit():
    """Spec 065 follow-up (PR #19 P2 fix #PRRT_kwDOSj5Qos6HSLSR):
    when the user already has agency-mcp on PATH (e.g. from a prior
    project or manual pipx install), the scaffold step MUST still run
    in a fresh target repo. Concretely: the scaffold-only block must
    appear in the script BEFORE the `command -v agency-mcp` early-
    exit guard."""
    script = _files()["hooks/session-start"]
    scaffold_idx = script.find("agency install --scaffold-only")
    guard_idx = script.find("command -v agency-mcp")
    assert scaffold_idx > 0, "scaffold block missing"
    assert guard_idx > 0, "idempotency guard missing"
    assert scaffold_idx < guard_idx, (
        "scaffold must run BEFORE the install-check early-exit so "
        "already-installed users still get .agency/ in fresh project "
        "repos (PR #19 P2)")


def test_session_start_script_starts_with_shebang():
    script = _files()["hooks/session-start"]
    assert script.startswith("#!/usr/bin/env bash"), (
        f"hook script must start with the bash shebang for SessionStart "
        f"hooks to execute it directly; got: {script[:40]!r}"
    )


# ---------------------------------------------------------------------------
# install.write() marks the script executable.
# ---------------------------------------------------------------------------


def test_install_write_marks_hook_executable(tmp_path):
    e = Engine(":memory:")
    try:
        write(str(tmp_path))
    finally:
        e.memory.close()
    hook = tmp_path / "hooks" / "session-start"
    assert hook.exists(), f"hook not written: {hook}"
    mode = hook.stat().st_mode
    assert mode & stat.S_IXUSR, (
        f"hook script must be executable; mode={oct(mode)}"
    )


# ---------------------------------------------------------------------------
# plugin.json should NOT also reference hooks (avoid Duplicate-hooks error).
# ---------------------------------------------------------------------------


def test_plugin_json_does_not_reference_hooks():
    """Per developing-claude-code-plugins skill: declaring hooks both in
    plugin.json's manifest.hooks AND in hooks/hooks.json triggers
    "Duplicate hooks file detected" errors. Spec 062 uses the
    auto-loaded hooks.json path only."""
    files = _files()
    manifest = json.loads(files[".claude-plugin/plugin.json"])
    assert "hooks" not in manifest, (
        "plugin.json must not carry a top-level 'hooks' key — Claude "
        "Code auto-loads hooks/hooks.json; declaring both raises a "
        "Duplicate hooks file error."
    )


# ---------------------------------------------------------------------------
# Spec 064 — plugin-reference compliance: matcher, async, polyglot wrapper,
# extensionless hook script.
# ---------------------------------------------------------------------------


def test_hooks_json_declares_session_start_matcher():
    """Spec 064: SessionStart should match startup|resume|clear but
    NOT compact (we don't want to reinstall on every compaction)."""
    cfg = json.loads(_files()["hooks/hooks.json"])
    entry = cfg["hooks"]["SessionStart"][0]
    assert entry["matcher"] == "startup|resume|clear", (
        f"unexpected matcher: {entry.get('matcher')!r}")


def test_hooks_json_declares_async_false():
    """Spec 064: async=false so subsequent session work waits for the
    install to finish before MCP boots."""
    cfg = json.loads(_files()["hooks/hooks.json"])
    cmd = cfg["hooks"]["SessionStart"][0]["hooks"][0]
    assert cmd.get("async") is False, (
        f"async should be False (waits for install); got {cmd.get('async')!r}")


def test_hooks_json_uses_run_hook_cmd_polyglot_wrapper():
    """Spec 064: hooks/run-hook.cmd is the cross-platform entry; the
    script-name is passed as the first arg."""
    cfg = json.loads(_files()["hooks/hooks.json"])
    cmd = cfg["hooks"]["SessionStart"][0]["hooks"][0]["command"]
    assert "run-hook.cmd" in cmd
    assert "session-start" in cmd
    # Spec 065 (PR #19 round-3 P2): the command-substitution layer does
    # NOT honor bash parameter-expansion (${VAR:-default}). Use the
    # documented ${CLAUDE_PLUGIN_ROOT} token only.
    assert "${CLAUDE_PLUGIN_ROOT}" in cmd
    assert "${PLUGIN_ROOT:-" not in cmd


def test_polyglot_wrapper_is_generated():
    """Spec 064: hooks/run-hook.cmd ships as part of the install. Valid
    in both CMD batch (Windows) and bash (Unix) via the heredoc trick."""
    files = _files()
    assert "hooks/run-hook.cmd" in files, sorted(files)
    wrapper = files["hooks/run-hook.cmd"]
    # The opening polyglot marker.
    assert wrapper.startswith(": << 'CMDBLOCK'"), (
        f"unexpected wrapper head: {wrapper[:30]!r}")
    # Closes the CMD block then runs Unix tail.
    assert "CMDBLOCK" in wrapper
    assert "exec bash" in wrapper


def test_hook_script_is_extensionless():
    """Spec 064: hook script renamed `session-start.sh` → `session-start`
    so Claude Code's Windows `.sh` auto-bash-prepend doesn't fire."""
    files = _files()
    assert "hooks/session-start" in files
    # The legacy `.sh`-suffixed entry must NOT appear (Windows would
    # auto-prepend `bash` and break on systems without bash on PATH).
    assert "hooks/session-start.sh" not in files


def test_hook_files_get_executable_mode(tmp_path):
    """Spec 064: install.write chmods every file under hooks/ to 0o755,
    not just `.sh`-suffixed ones. The polyglot wrapper has no extension."""
    e = Engine(":memory:")
    try:
        write(str(tmp_path))
    finally:
        e.memory.close()
    for rel in ("hooks/run-hook.cmd", "hooks/session-start"):
        path = tmp_path / rel
        assert path.exists(), f"missing: {path}"
        assert path.stat().st_mode & stat.S_IXUSR, (
            f"not executable: {path} (mode={oct(path.stat().st_mode)})")


def test_using_agency_skill_is_generated():
    """Spec 064: using-agency is the broad-trigger meta-skill.
    Modelled on using-superpowers — orchestrator MUST call
    agency_welcome + intent_bootstrap before any verb call."""
    files = _files()
    assert "skills/using-agency/SKILL.md" in files
    skill = files["skills/using-agency/SKILL.md"]
    # YAML frontmatter with the load-bearing fields.
    assert "name: using-agency" in skill
    assert "description: Use when starting any conversation" in skill
    # The bootstrap chain is the load-bearing message.
    assert "agency_welcome" in skill
    assert "intent_bootstrap" in skill
    # MCP tools allowed (the bootstrap chain goes through execute).
    assert "mcp__plugin_agency_agency__execute" in skill
