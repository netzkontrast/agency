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
    # Spec 065: pipx-installed `agency` console-script (no bin/ shim).
    assert "agency intent" in skill or "agency execute" in skill


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
    # Spec 065: pipx-installed `agency` console-script (no bin/ shim).
    assert "agency intent" in cmd or "agency execute" in cmd


# ---------------------------------------------------------------------------
# Spec 061 — install surface refresh.
# ---------------------------------------------------------------------------


def test_mcp_json_has_no_pythonpath():
    """Spec 061: PYTHONPATH was a vestige of the pre-Spec-055 .venv
    bootstrap path. Under pipx-only doctrine the pipx venv carries its
    own site-packages; PYTHONPATH=${CLAUDE_PLUGIN_ROOT} would shadow
    the pipx-installed `agency` package with the plugin-tree source.
    Generated `.mcp.json` must drop the env entry."""
    import json
    files = _files()
    mcp_cfg = json.loads(files[".mcp.json"])
    env = mcp_cfg["mcpServers"]["agency"]["env"]
    assert "PYTHONPATH" not in env, (
        f"PYTHONPATH unexpectedly present in .mcp.json env: {sorted(env)}")
    # Substrate config that DOES stay.
    assert "AGENCY_DB" in env
    assert "JULES_API_KEY" in env


def test_mcp_json_pins_cwd_to_project_dir():
    """Spec 064: cwd is pinned to ${CLAUDE_PROJECT_DIR} so the MCP
    subprocess's path resolver lands the graph DB at the right place
    even if AGENCY_DB substitution fails. Mirrors episodic-memory."""
    import json
    files = _files()
    mcp_cfg = json.loads(files[".mcp.json"])
    server = mcp_cfg["mcpServers"]["agency"]
    assert server.get("cwd") == "${CLAUDE_PROJECT_DIR}", (
        f"cwd should pin to project root; got {server.get('cwd')!r}")


def test_mcp_json_declares_env_vars_passthrough():
    """Spec 064: env_vars list declares which session env vars Claude
    Code should pass through. Without this, AGENCY_EMBEDDER set in the
    user's shell is silently dropped."""
    import json
    files = _files()
    mcp_cfg = json.loads(files[".mcp.json"])
    env_vars = mcp_cfg["mcpServers"]["agency"].get("env_vars")
    assert isinstance(env_vars, list), (
        f"env_vars should be a list; got {type(env_vars)}")
    # AGENCY_EMBEDDER is the canary — Spec 045 BGE opt-in needs it.
    assert "AGENCY_EMBEDDER" in env_vars
    assert "AGENCY_DB" in env_vars
    assert "JULES_API_KEY" in env_vars


def test_mcp_json_command_is_bare_agency_mcp():
    """Spec 065 (pipx-direct doctrine): the bin/agency-mcp shim is
    removed; .mcp.json `command` is now just `agency-mcp`, resolved
    from PATH where pipx install lands the console-script. Mirrors
    episodic-memory's pattern."""
    import json
    files = _files()
    mcp_cfg = json.loads(files[".mcp.json"])
    cmd = mcp_cfg["mcpServers"]["agency"]["command"]
    assert cmd == "agency-mcp", f"expected bare 'agency-mcp'; got {cmd!r}"
    # Explicit absence: no bin/ path prefix, no ${PLUGIN_ROOT} fallback
    # (the old Spec 064 shape).
    assert "/bin/" not in cmd
    assert "${" not in cmd


def test_marketplace_description_names_live_surface():
    """Spec 061: the static DESCRIPTION constant left the marketplace
    description a generic engine pitch with no signal of the
    14-capability surface. The generator now reads the live registry
    so the description names what actually ships."""
    import json
    files = _files()
    mp = json.loads(files[".claude-plugin/marketplace.json"])
    desc = mp["plugins"][0]["description"]
    # Per-cap surface signal: names "capabilities" + at least one of
    # the canonical cap names the count should reflect.
    assert "capabilities" in desc.lower()
    # The count IS dynamic — assert the live registry's count is in
    # the description, not a hardcoded number.
    e = Engine(":memory:")
    try:
        cap_count = len(e.registry.names())
    finally:
        e.memory.close()
    assert str(cap_count) in desc, (
        f"description should name the live cap count ({cap_count}); "
        f"got: {desc!r}")
    # Bound the description so a marketplace UI renders it cleanly.
    assert len(desc) < 400, f"description too long ({len(desc)} chars): {desc!r}"
