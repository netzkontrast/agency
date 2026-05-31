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
