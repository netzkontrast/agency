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
        and "session-start.sh" in h["command"]
        and "${CLAUDE_PLUGIN_ROOT}" in h["command"]
        for h in commands
    ), f"unexpected hook shape: {commands}"


# ---------------------------------------------------------------------------
# session-start.sh idempotency + fallback shape.
# ---------------------------------------------------------------------------


def test_session_start_script_has_idempotency_guard():
    files = _files()
    assert "hooks/session-start.sh" in files, sorted(files)
    script = files["hooks/session-start.sh"]
    # Idempotency: bail out if agency-mcp is already on PATH.
    assert "command -v agency-mcp" in script
    # pipx is the canonical install path (Spec 055).
    assert "pipx install --editable" in script
    # Pip fallback for environments without pipx.
    assert "pip install --user" in script
    # Fail-soft: don't block session start when neither tool is present.
    assert "exit 0" in script


def test_session_start_script_starts_with_shebang():
    script = _files()["hooks/session-start.sh"]
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
    hook = tmp_path / "hooks" / "session-start.sh"
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
