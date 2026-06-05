"""Spec 029 §A — agency_install MCP substrate tool.

Closes the "user wants an install verb" gap: scaffold_db() is reachable
via MCP, plus a marker-bounded CLAUDE.md snippet that names the
canonical first calls.
"""
import asyncio
import json
import os
import stat
import tempfile

import pytest
from fastmcp import Client

from agency.engine import Engine


def _sc(result):
    sc = result.structured_content
    if isinstance(sc, dict):
        return sc.get("result", sc)
    if sc is not None:
        return sc
    if result.content:
        try:
            return json.loads(result.content[0].text)
        except (ValueError, TypeError):
            return result.content[0].text
    return None


def test_agency_install_creates_dot_agency_dir(tmp_path):
    """Scaffolds .agency/ under the target. Returns the literal paths
    that were created (Spec 029 §A — claude_md_path is absolute)."""
    e = Engine(tempfile.mktemp(suffix=".db"))
    mcp = e.build_mcp(codemode=False)
    try:
        async def main():
            async with Client(mcp) as client:
                return _sc(await client.call_tool("agency_install", {"target": str(tmp_path)}))
        out = asyncio.run(main())
    finally:
        e.memory.close()
    assert out["target"] == str(tmp_path)
    assert (tmp_path / ".agency").is_dir()
    assert (tmp_path / ".agency" / "README.md").exists()
    assert (tmp_path / ".gitattributes").exists()
    assert out["claude_md_path"] == str(tmp_path / "CLAUDE.md")
    assert (tmp_path / "CLAUDE.md").exists()
    assert "agency_welcome" in (tmp_path / "CLAUDE.md").read_text()


def test_agency_install_idempotent(tmp_path):
    """Re-running on a populated tree changes nothing material."""
    e = Engine(tempfile.mktemp(suffix=".db"))
    mcp = e.build_mcp(codemode=False)
    try:
        async def call():
            async with Client(mcp) as client:
                return _sc(await client.call_tool("agency_install", {"target": str(tmp_path)}))
        first = asyncio.run(call())
        second = asyncio.run(call())
    finally:
        e.memory.close()
    assert first["claude_md_updated"] is True
    assert second["claude_md_updated"] is False
    body = (tmp_path / "CLAUDE.md").read_text()
    assert body.count("<!-- agency:onboarding:start -->") == 1
    assert body.count("<!-- agency:onboarding:end -->") == 1


def test_agency_install_preserves_existing_claude_md(tmp_path):
    """If CLAUDE.md exists without our marker, APPEND the marked block —
    never modify user content outside the markers."""
    (tmp_path / "CLAUDE.md").write_text("# My project\n\nMy own notes.\n")
    e = Engine(tempfile.mktemp(suffix=".db"))
    mcp = e.build_mcp(codemode=False)
    try:
        async def main():
            async with Client(mcp) as client:
                return _sc(await client.call_tool("agency_install", {"target": str(tmp_path)}))
        asyncio.run(main())
    finally:
        e.memory.close()
    body = (tmp_path / "CLAUDE.md").read_text()
    assert "# My project" in body                       # user content preserved
    assert "My own notes." in body                       # user content preserved
    assert "<!-- agency:onboarding:start -->" in body    # marker present
    assert "agency_welcome" in body                      # snippet present


def test_agency_install_replaces_marker_block_on_rerun(tmp_path):
    """Re-running replaces the content between markers, not the whole file."""
    pre = (
        "# My project\n\nMy own notes.\n\n"
        "<!-- agency:onboarding:start -->\nOLD GUIDANCE\n<!-- agency:onboarding:end -->\n"
        "After block.\n"
    )
    (tmp_path / "CLAUDE.md").write_text(pre)
    e = Engine(tempfile.mktemp(suffix=".db"))
    mcp = e.build_mcp(codemode=False)
    try:
        async def main():
            async with Client(mcp) as client:
                return _sc(await client.call_tool("agency_install", {"target": str(tmp_path)}))
        asyncio.run(main())
    finally:
        e.memory.close()
    body = (tmp_path / "CLAUDE.md").read_text()
    assert "# My project" in body
    assert "OLD GUIDANCE" not in body            # replaced
    assert "agency_welcome" in body              # new snippet
    assert "After block." in body                # post-marker content preserved


def test_agency_install_non_writable_target_fails(tmp_path):
    """Spec 029 Failure modes (Nygard): non-writable target surfaces
    as an MCP tool error, not a silent partial state."""
    os.chmod(tmp_path, stat.S_IREAD | stat.S_IEXEC)
    if os.access(tmp_path, os.W_OK):
        os.chmod(tmp_path, stat.S_IRWXU)
        pytest.skip("filesystem still writable as root; skipping")
    try:
        e = Engine(tempfile.mktemp(suffix=".db"))
        mcp = e.build_mcp(codemode=False)
        try:
            async def main():
                async with Client(mcp) as client:
                    return await client.call_tool("agency_install", {"target": str(tmp_path)})
            with pytest.raises(Exception):
                asyncio.run(main())
        finally:
            e.memory.close()
    finally:
        os.chmod(tmp_path, stat.S_IRWXU)   # restore so pytest can clean up


# ---------------------------------------------------------------------------
# Spec 065 — `agency install` CLI subcommand (consolidation).
# ---------------------------------------------------------------------------


def test_agency_install_cli_subcommand_dry_run(tmp_path, capsys):
    """Spec 065: `agency install --dry-run` dispatches to
    install.main(['--dry-run']) so the canonical CLI form replaces
    `python -m agency.install --dry-run`."""
    from agency.cli import main as cli_main
    rc = cli_main(["install", "--dry-run"])
    assert rc == 0


def test_agency_install_cli_subcommand_scaffold_db(tmp_path):
    """Spec 065: `agency install --scaffold-db <target>` is the path
    the SessionStart hook uses to seed .agency/ in the project root.

    scaffold_db creates the .agency/ directory + README + .gitattributes
    binary marker. The session.db file appears lazily on the first
    Memory write — not at scaffold time."""
    from agency.cli import main as cli_main
    rc = cli_main(["install", str(tmp_path), "--scaffold-db"])
    assert rc == 0
    assert (tmp_path / ".agency").is_dir()
    assert (tmp_path / ".agency" / "README.md").exists()
    assert (tmp_path / ".gitattributes").exists()


def test_agency_welcome_cli_subcommand(tmp_path, capsys):
    """Spec 065: `agency welcome` is the bash-side wrapper around the
    agency_welcome substrate tool. Returns the canonical onboarding
    payload (capability list, bootstrap example, db_path)."""
    import json as _json
    from agency.cli import main as cli_main
    rc = cli_main(["--db", str(tmp_path / "g.db"), "welcome"])
    assert rc == 0
    out = _json.loads(capsys.readouterr().out)
    # Spec 029 — payload shape: state + capabilities + next steps.
    assert "state" in out
    assert "capabilities" in out and isinstance(out["capabilities"], list)
    assert "bootstrap_example" in out


def test_agency_doctor_cli_subcommand(tmp_path, capsys):
    """Spec 065: `agency doctor` is the bash-side wrapper around the
    agency_doctor substrate tool (Spec 030)."""
    import json as _json
    from agency.cli import main as cli_main
    rc = cli_main(["--db", str(tmp_path / "g.db"), "doctor"])
    assert rc == 0
    out = _json.loads(capsys.readouterr().out)
    # Spec 030 — payload carries python_version + deps + db + ok.
    assert "ok" in out
    assert "python_version" in out
    assert "deps" in out
    assert "db" in out


def test_agency_provenance_cli_subcommand(tmp_path, capsys):
    """Spec 065: `agency provenance <intent_id>` is the bash-side
    wrapper around the memory_graph_provenance substrate tool."""
    import json as _json
    from agency.cli import main as cli_main
    db = str(tmp_path / "g.db")
    # First mint an intent so we have a real id to walk.
    rc = cli_main(["--db", db, "intent",
                   "--purpose", "test",
                   "--deliverable", "x",
                   "--acceptance", "x"])
    assert rc == 0
    captured = capsys.readouterr()
    iid = _json.loads(captured.out)["intent_id"]
    # Now read provenance via the subcommand.
    rc = cli_main(["--db", db, "provenance", iid])
    assert rc == 0
    out = _json.loads(capsys.readouterr().out)
    # Memory.provenance returns {serves, agents, artefacts, gates}.
    assert "serves" in out
    assert "agents" in out
