"""Spec 280 Slice 1 — hooks install verification + foreign-hook wrapping.

The plugin ALREADY ships hooks (Spec 076). Spec 280 is the
verification + install + composition surface that makes the
dispatcher actually fire in a fresh repo + composes with foreign hooks
(other plugins, hand-authored) so they fall under agency's provenance
umbrella.

Slice 1 ships:
- Pure library (`agency/_hooks.py`): CANONICAL_SETTINGS_PATCH,
  merge_settings, detect_foreign_hooks, wrap_foreign_hook,
  apply_foreign_wraps, check_install → InstallStatus,
  patch_settings_file (the install side-effect)
- `agency.install --patch-claude-settings` writes/merges with .bak
- `agency_doctor.hooks` field
- `agency hook self-test` CLI command
- `agency hook uninstall` CLI command
- `hooks/dispatch` extended with PreToolUse routing advice
- `hooks/hooks.json` async flags corrected per the doctrine table
"""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path

import pytest

from agency._hooks import (
    ASYNC_BY_EVENT,
    CANONICAL_SETTINGS_PATCH,
    ForeignHook,
    HOOKS_SPEC_VERSION,
    InstallStatus,
    apply_foreign_wraps,
    check_install,
    detect_foreign_hooks,
    merge_settings,
    patch_settings_file,
    wrap_foreign_hook,
)


# ── canonical patch shape ─────────────────────────────────────────────────
def test_canonical_settings_patch_carries_plugin_entry():
    """The patch enables `agency@netzkontrast` in enabledPlugins."""
    enabled = CANONICAL_SETTINGS_PATCH.get("enabledPlugins") or {}
    assert "agency@netzkontrast" in enabled


def test_canonical_settings_patch_carries_marketplace_entry():
    """The marketplace entry tells Claude Code WHERE to fetch the
    agency plugin from."""
    mkt = CANONICAL_SETTINGS_PATCH.get("extraKnownMarketplaces") or {}
    assert "netzkontrast" in mkt
    src = mkt["netzkontrast"].get("source", {})
    assert src.get("source") == "github"
    assert "agency" in src.get("repo", "")


def test_canonical_settings_patch_carries_version_marker():
    """Drift detection key (Spec 054 pattern)."""
    assert CANONICAL_SETTINGS_PATCH.get("_agency_version") == HOOKS_SPEC_VERSION


def test_async_table_blocks_pretool_and_userprompt():
    """User-raised point: PreToolUse + UserPromptSubmit should be SYNC
    (blocking) so routes can land in Slice 2 + intent-context injection
    can happen pre-prompt. PostToolUse/Stop/SessionEnd stay async."""
    assert ASYNC_BY_EVENT["PreToolUse"] is False
    assert ASYNC_BY_EVENT["UserPromptSubmit"] is False
    assert ASYNC_BY_EVENT["SessionStart"] is False
    assert ASYNC_BY_EVENT["PostToolUse"] is True
    assert ASYNC_BY_EVENT["Stop"] is True
    assert ASYNC_BY_EVENT["SessionEnd"] is True
    assert ASYNC_BY_EVENT["SubagentStop"] is True


# ── merge_settings: preservation + idempotence ────────────────────────────
def test_merge_preserves_other_enabled_plugins():
    """Other plugins' enabledPlugins entries survive (preservation
    invariant)."""
    user = {"enabledPlugins": {"bitwize-music@bitwize-music": True}}
    merged = merge_settings(user)
    enabled = merged["enabledPlugins"]
    assert enabled.get("bitwize-music@bitwize-music") is True
    assert enabled.get("agency@netzkontrast") is True


def test_merge_preserves_unrelated_top_level_keys():
    """`extraKnownMarketplaces` for other plugins, custom user keys,
    even unrelated `hooks` entries — all survive."""
    user = {
        "extraKnownMarketplaces": {
            "other-marketplace": {"source": {"source": "github",
                                              "repo": "x/y"}},
        },
        "custom_user_key": "preserved",
    }
    merged = merge_settings(user)
    assert merged["custom_user_key"] == "preserved"
    mkt = merged["extraKnownMarketplaces"]
    assert "other-marketplace" in mkt
    assert "netzkontrast" in mkt


def test_merge_is_idempotent():
    """Running merge twice yields the same content (byte-identical
    after json round-trip)."""
    user = {"enabledPlugins": {"bitwize-music@bitwize-music": True}}
    once = merge_settings(user)
    twice = merge_settings(once)
    assert json.dumps(once, sort_keys=True) == json.dumps(twice, sort_keys=True)


# ── detect_foreign_hooks ──────────────────────────────────────────────────
def test_detect_finds_user_authored_hooks():
    """Hand-authored hook at `.claude/settings.json` hooks level is
    classified as foreign (it doesn't route through agency's
    dispatcher)."""
    user = {
        "hooks": {
            "PreToolUse": [{
                "matcher": "Bash",
                "hooks": [{"type": "command",
                            "command": "/usr/local/bin/audit-cmd.sh",
                            "async": False}],
            }],
        },
    }
    foreign = detect_foreign_hooks(user)
    assert len(foreign) == 1
    assert foreign[0].event == "PreToolUse"
    assert foreign[0].matcher == "Bash"
    assert foreign[0].command == "/usr/local/bin/audit-cmd.sh"
    assert foreign[0].async_ is False


def test_detect_skips_agency_dispatcher_entries():
    """Entries that already invoke agency's dispatcher are NOT
    foreign — they're already wired."""
    user = {
        "hooks": {
            "PreToolUse": [{
                "matcher": "*",
                "hooks": [{"type": "command",
                            "command": ('"${CLAUDE_PLUGIN_ROOT}/hooks/'
                                        'run-hook.cmd" dispatch')}],
            }],
        },
    }
    assert detect_foreign_hooks(user) == []


def test_detect_skips_already_wrapped_entries():
    """A re-run on a settings that already has shell-wrapped foreign
    hooks must NOT re-classify them as foreign (no double-wrap)."""
    user = {
        "hooks": {
            "PreToolUse": [{
                "matcher": "Bash",
                "hooks": [{"type": "command",
                            "command": ("agency shell run --hook-wrap -- "
                                        "/usr/local/bin/audit.sh"),
                            "_wrapped_from": "/usr/local/bin/audit.sh"}],
            }],
        },
    }
    assert detect_foreign_hooks(user) == []


# ── wrap_foreign_hook ─────────────────────────────────────────────────────
def test_wrap_preserves_async_flag():
    """A sync-blocking foreign hook STAYS sync after wrap. Changing
    semantics is a doctrine violation."""
    foreign = ForeignHook(
        event="PreToolUse", matcher="Bash",
        command="/usr/local/bin/audit.sh",
        type_="command", async_=False)
    wrapped = wrap_foreign_hook(foreign)
    assert wrapped is not None
    assert wrapped["async"] is False
    assert wrapped["type"] == "command"


def test_wrap_preserves_async_true_too():
    foreign = ForeignHook(
        event="PostToolUse", matcher="*",
        command="curl https://example.com/hook",
        async_=True)
    wrapped = wrap_foreign_hook(foreign)
    assert wrapped["async"] is True


def test_wrap_records_original_command():
    """The wrapped entry carries `_wrapped_from` so the user can
    audit + Slice 5 uninstall can restore."""
    foreign = ForeignHook(
        event="PreToolUse", matcher="Bash",
        command="/usr/local/bin/audit.sh",
        async_=False)
    wrapped = wrap_foreign_hook(foreign)
    assert wrapped["_wrapped_from"] == "/usr/local/bin/audit.sh"
    assert "agency shell run --hook-wrap" in wrapped["command"]


def test_wrap_returns_none_for_unparseable_command():
    """A foreign command with unbalanced quotes can't be safely
    shell-quoted; wrap returns None so caller maps to
    HOOKS_FOREIGN_UNWRAPPABLE and PRESERVES the original."""
    foreign = ForeignHook(
        event="PreToolUse", matcher="Bash",
        command="echo 'unterminated")
    assert wrap_foreign_hook(foreign) is None


# ── apply_foreign_wraps idempotence ───────────────────────────────────────
def test_apply_foreign_wraps_does_not_double_wrap():
    """Running install twice on the same settings produces the same
    result — no nesting of wraps."""
    user = {
        "hooks": {
            "PreToolUse": [{
                "matcher": "Bash",
                "hooks": [{"type": "command",
                            "command": "/usr/local/bin/audit.sh",
                            "async": False}],
            }],
        },
    }
    once, n_once = apply_foreign_wraps(user)
    twice, n_twice = apply_foreign_wraps(once)
    assert n_once == 1
    assert n_twice == 0                                            # no foreign left
    assert (json.dumps(once, sort_keys=True) ==
            json.dumps(twice, sort_keys=True))


# ── check_install: doctor invariants ──────────────────────────────────────
def test_check_install_reports_plugin_not_enabled():
    """Fresh settings → plugin_enabled=False + repair pointer."""
    status = check_install({}, env={}, plugin_root=None)
    assert status.plugin_enabled is False
    assert any("not enabled" in s for s in status.next_steps)


def test_check_install_reports_plugin_enabled_when_present():
    user = merge_settings({})                                      # has the entry
    status = check_install(user, cli_available=True)
    assert status.plugin_enabled is True
    # `plugin_enabled=True` should NOT carry the "not enabled" repair
    assert not any("not enabled" in s for s in status.next_steps)


def test_check_install_reports_cli_off_path():
    """When the cli_available flag is False, next_steps points at
    pipx."""
    user = merge_settings({})
    status = check_install(user, cli_available=False)
    assert status.cli_on_path is False
    assert any("pipx" in s for s in status.next_steps)


def test_check_install_reports_foreign_hooks(tmp_path):
    """Foreign hooks surface in the status + next_steps tells the
    user how to wrap them."""
    user = {
        "hooks": {
            "PreToolUse": [{
                "matcher": "Bash",
                "hooks": [{"type": "command",
                            "command": "/usr/local/bin/audit.sh",
                            "async": False}],
            }],
        },
    }
    status = check_install(user)
    assert len(status.foreign_hooks) == 1
    assert any("foreign hook" in s for s in status.next_steps)


def test_install_status_to_dict_round_trip():
    status = InstallStatus(
        plugin_enabled=True, cli_on_path=True,
        hook_scripts_present=True, plugin_root="/x", settings_path="/y")
    d = status.to_dict()
    assert d["plugin_enabled"] is True
    assert d["cli_on_path"] is True
    assert d["foreign_hooks"] == []
    assert d["next_steps"] == []


# ── patch_settings_file: side effects ─────────────────────────────────────
def test_patch_writes_settings_when_missing(tmp_path):
    settings = tmp_path / ".claude" / "settings.json"
    result = patch_settings_file(settings)
    assert result["wrote"] is True
    assert result["backup_path"] == ""                              # nothing to back up
    content = json.loads(settings.read_text())
    assert content["enabledPlugins"]["agency@netzkontrast"] is True


def test_patch_creates_bak_on_existing_file(tmp_path):
    settings = tmp_path / ".claude" / "settings.json"
    settings.parent.mkdir(parents=True)
    prior = {"enabledPlugins": {"bitwize-music@bitwize-music": True}}
    settings.write_text(json.dumps(prior, indent=2))
    result = patch_settings_file(settings)
    backup = Path(result["backup_path"])
    assert backup.exists()
    restored = json.loads(backup.read_text())
    assert restored == prior                                        # backup is the prior state


def test_patch_preserves_other_plugins_after_merge(tmp_path):
    settings = tmp_path / ".claude" / "settings.json"
    settings.parent.mkdir(parents=True)
    settings.write_text(json.dumps({
        "enabledPlugins": {"bitwize-music@bitwize-music": True},
    }))
    patch_settings_file(settings)
    content = json.loads(settings.read_text())
    assert content["enabledPlugins"]["bitwize-music@bitwize-music"] is True
    assert content["enabledPlugins"]["agency@netzkontrast"] is True


def test_patch_is_idempotent(tmp_path):
    """Running install twice yields a byte-identical settings file."""
    settings = tmp_path / ".claude" / "settings.json"
    patch_settings_file(settings)
    first = settings.read_text()
    patch_settings_file(settings)
    second = settings.read_text()
    assert first == second


def test_patch_wraps_foreign_hooks(tmp_path):
    settings = tmp_path / ".claude" / "settings.json"
    settings.parent.mkdir(parents=True)
    settings.write_text(json.dumps({
        "hooks": {
            "PreToolUse": [{
                "matcher": "Bash",
                "hooks": [{"type": "command",
                            "command": "/usr/local/bin/audit.sh",
                            "async": False}],
            }],
        },
    }))
    result = patch_settings_file(settings)
    assert result["wrapped_count"] == 1
    content = json.loads(settings.read_text())
    entry = content["hooks"]["PreToolUse"][0]["hooks"][0]
    assert "agency shell run --hook-wrap" in entry["command"]
    assert entry["async"] is False                                  # preserved
    assert entry["_wrapped_from"] == "/usr/local/bin/audit.sh"


def test_patch_raises_on_invalid_json(tmp_path):
    settings = tmp_path / ".claude" / "settings.json"
    settings.parent.mkdir(parents=True)
    settings.write_text("{not valid json")
    with pytest.raises(ValueError) as exc:
        patch_settings_file(settings)
    assert "HOOKS_INVALID_JSON" in str(exc.value)


# ── hooks/hooks.json async-flag invariant ─────────────────────────────────
def test_hooks_json_has_correct_async_flags():
    """The shipped `hooks/hooks.json` matches the doctrine table:
    SessionStart / PreToolUse / UserPromptSubmit are sync; everything
    else is async."""
    repo = Path(__file__).parent.parent
    config = json.loads((repo / "hooks" / "hooks.json").read_text())
    hooks = config.get("hooks") or {}
    for event_name, want_async in ASYNC_BY_EVENT.items():
        entries = hooks.get(event_name) or []
        if not entries:
            continue                                                # event not in shipped config
        for entry in entries:
            for h in entry.get("hooks") or []:
                got = bool(h.get("async", True))
                assert got is want_async, (
                    f"{event_name}: shipped async={got}, "
                    f"doctrine wants async={want_async}")


# ── live dispatcher: routing-advice integration ───────────────────────────
def _dispatch_with(payload: dict) -> subprocess.CompletedProcess:
    """Run the live `hooks/dispatch` script with a synthetic payload."""
    repo = Path(__file__).parent.parent
    dispatcher = repo / "hooks" / "dispatch"
    return subprocess.run(
        ["bash", str(dispatcher)],
        input=json.dumps(payload),
        text=True, capture_output=True, timeout=10)


def test_dispatch_routes_git_commit_to_branch_commit_smart():
    """The advisory hint references `branch.commit_smart`."""
    proc = _dispatch_with({
        "hook_event_name": "PreToolUse",
        "tool_name":       "Bash",
        "tool_input":      {"command": "git commit -m x"},
    })
    assert proc.returncode == 0, proc.stderr                        # advisory, never blocks
    assert "branch.commit_smart" in proc.stderr


def test_dispatch_routes_pytest_to_develop_test():
    proc = _dispatch_with({
        "hook_event_name": "PreToolUse",
        "tool_name":       "Bash",
        "tool_input":      {"command": "pytest tests/"},
    })
    assert proc.returncode == 0
    assert "develop.test" in proc.stderr


def test_dispatch_routes_spec_edit_to_dogfood_observe():
    proc = _dispatch_with({
        "hook_event_name": "PreToolUse",
        "tool_name":       "Edit",
        "tool_input":      {"file_path": "Plan/280-foo/spec.md"},
    })
    assert proc.returncode == 0
    assert "dogfood.observe" in proc.stderr


def test_agency_doctor_carries_hooks_field(monkeypatch, tmp_path):
    """`agency_doctor()` returns a `hooks` field with the Spec 280
    Slice 1 InstallStatus shape — readable via the FastMCP client
    the way the live MCP server is."""
    import asyncio
    from fastmcp import Client
    from agency.engine import Engine

    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
    e = Engine(tempfile.mktemp(suffix=".db"))
    mcp = e.build_mcp(codemode=False)

    def _sc(result):
        sc = result.structured_content
        if isinstance(sc, dict):
            return sc.get("result", sc)
        return sc

    try:
        async def main():
            async with Client(mcp) as client:
                return _sc(await client.call_tool("agency_doctor", {}))
        out = asyncio.run(main())
    finally:
        e.memory.close()
    assert "hooks" in out
    hooks = out["hooks"]
    for key in ("plugin_enabled", "cli_on_path", "hook_scripts_present",
                 "plugin_root", "settings_path", "foreign_hooks",
                 "wrapped_count", "drift", "next_steps",
                 "installed_version", "shadowed_by_user"):
        assert key in hooks, f"doctor.hooks missing key: {key}"


def test_dispatch_ignores_unrelated_bash():
    """Most Bash commands don't trigger advice — the hint set is small
    + focused."""
    proc = _dispatch_with({
        "hook_event_name": "PreToolUse",
        "tool_name":       "Bash",
        "tool_input":      {"command": "ls -la"},
    })
    assert proc.returncode == 0
    assert "agency hook |" not in proc.stderr
