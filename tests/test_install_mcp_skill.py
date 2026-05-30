"""Generated help skill + /agency:help command MUST teach BOTH the MCP form
(the Claude-Code-with-plugin happy path) AND the bash bootstrap (the Jules /
no-MCP fallback). The MCP form leads — that is the discoverable contract for
agents whose harness already has `mcp__plugin_agency_agency__*` tools.

Also: the help skill's `allowed-tools` must list the agency MCP tools, not
the generic `Read/Write/Edit` default — otherwise the agent reading the skill
cannot actually call what the skill teaches.
"""
from __future__ import annotations

from agency.engine import Engine
from agency.install import generate


def _files():
    e = Engine(":memory:")
    try:
        return generate(e)
    finally:
        e.memory.close()


def test_help_skill_teaches_mcp_form():
    files = _files()
    skill = files["skills/help/SKILL.md"]
    # MCP-first quick start
    assert "mcp__plugin_agency_agency__execute" in skill, skill
    assert "call_tool(" in skill
    # The auto-discovered capability list still renders
    assert "capability_plugin_help" in skill or "plugin_help" in skill


def test_help_skill_keeps_bash_fallback():
    files = _files()
    skill = files["skills/help/SKILL.md"]
    # Bash bootstrap for Jules / no-MCP hosts
    assert "${CLAUDE_PLUGIN_ROOT}/bin/agency" in skill


def test_help_skill_allowed_tools_lists_agency_mcp_tools():
    files = _files()
    skill = files["skills/help/SKILL.md"]
    # The skill teaches calls into the agency MCP server — the allowlist
    # MUST cover them or the agent reading the skill can't execute it.
    for tool in (
        "mcp__plugin_agency_agency__search",
        "mcp__plugin_agency_agency__get_schema",
        "mcp__plugin_agency_agency__execute",
    ):
        assert tool in skill, f"missing {tool} in allowed-tools:\n{skill}"


def test_help_command_teaches_mcp_form():
    files = _files()
    cmd = files["commands/help.md"]
    assert "mcp__plugin_agency_agency__execute" in cmd, cmd
    # Bash form remains as a fallback block
    assert "${CLAUDE_PLUGIN_ROOT}/bin/agency" in cmd
