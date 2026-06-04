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
    # Spec 063: also bail if the per-project venv binary exists.
    assert ".agency/.venv/bin/agency-mcp" in script
    # pipx is the canonical install path (Spec 055).
    assert "pipx install --editable" in script
    # Pip fallback for environments without pipx.
    assert "pip install --user" in script
    # Fail-soft: don't block session start when neither tool is present.
    assert "exit 0" in script


# ---------------------------------------------------------------------------
# Spec 063 — venv fallback path + post-install scaffold-db.
# ---------------------------------------------------------------------------


def test_session_start_script_includes_venv_fallback():
    """Spec 063: when pipx + pip --user both fail, the hook creates a
    per-project venv at ${CLAUDE_PROJECT_DIR}/.agency/.venv and pip-
    installs the agency package into it. The bin/agency-mcp shim
    knows to prefer that venv over PATH."""
    script = _files()["hooks/session-start"]
    assert "python3 -m venv" in script
    assert "${CLAUDE_PROJECT_DIR}/.agency/.venv" in script
    # The venv's pip is invoked directly (not the system pip).
    assert "/.agency/.venv/bin/pip" in script


def test_session_start_script_runs_scaffold_db_after_install():
    """Spec 063: after ANY successful install path, the hook scaffolds
    the target repo's .agency/ via Spec 020's --scaffold-db CLI so
    session.db + README + .gitattributes land in the project root."""
    script = _files()["hooks/session-start"]
    assert "python3 -m agency.install --scaffold-db" in script
    assert "${CLAUDE_PROJECT_DIR}" in script


def test_session_start_script_documents_three_paths():
    """Sanity: the three install paths are visible in the comment
    block so a debugger reading the script knows the fallback order."""
    script = _files()["hooks/session-start"]
    assert "Path 1" in script and "Path 2" in script and "Path 3" in script


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
    # Spec 064: PLUGIN_ROOT fallback for Cursor/Codex.
    assert "${PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT}}" in cmd


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
