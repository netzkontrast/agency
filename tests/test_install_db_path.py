"""Verify the plugin's `.mcp.json` AGENCY_DB matches the CLI's default
resolution so MCP and bash CLI surfaces share one DB per project.

Background — finding from a live session (reflection:9cd97a38, recorded
2026-05-30): the committed `.mcp.json` set AGENCY_DB to
`${CLAUDE_PLUGIN_DATA}/agency.db` (e.g.
`/root/.claude/plugins/data/agency-agency/agency.db`) — entirely
outside the project. Meanwhile `python -m agency.cli` defaulted to
`./.agency/session.db` (Spec 020). Two surfaces, two stores; an
observation recorded via one was invisible to the other. The doctrine
(GOALS.md goal #2 — provenance as a free byproduct) needs both surfaces
to write to the same graph.

This test pins the fix: the install emits AGENCY_DB pointing at
`${CLAUDE_PROJECT_DIR}/.agency/session.db`, matching the CLI default
when run from a scaffolded project directory.
"""
from agency.install import _mcp_config


def test_mcp_config_agency_db_uses_project_dir_session_db():
    cfg = _mcp_config()
    env = cfg["mcpServers"]["agency"]["env"]
    assert env["AGENCY_DB"] == "${CLAUDE_PROJECT_DIR}/.agency/session.db", (
        "MCP must share the CLI's .agency/session.db so both surfaces "
        "converge on one graph per project (reflection:9cd97a38)."
    )


def test_mcp_config_keeps_plugin_root_for_command():
    """The launcher script stays under ${CLAUDE_PLUGIN_ROOT} because
    it lives inside the installed plugin, not the user's project.
    Only the *data* (the graph) moves to the project.

    Spec 061: PYTHONPATH was removed from the generated env block —
    pipx-only doctrine (Spec 055) makes it vestigial; the pipx venv
    resolves `agency` from its own site-packages."""
    cfg = _mcp_config()
    s = cfg["mcpServers"]["agency"]
    assert s["command"] == "${CLAUDE_PLUGIN_ROOT}/bin/agency-mcp"
    assert "PYTHONPATH" not in s["env"], (
        "PYTHONPATH should be absent under Spec 061")
