"""Spec 030 §B — agency_doctor substrate tool.

Health-check substrate tool. Reports python version, deps, DB
reachability, JULES_API_KEY presence (NEVER the value), and a
copy-pasteable next_steps list for any issue found.
"""
import asyncio
import json
import tempfile

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


def test_agency_doctor_report_shape():
    """Doctor returns the documented structured report."""
    e = Engine(tempfile.mktemp(suffix=".db"))
    mcp = e.build_mcp(codemode=False)
    try:
        async def main():
            async with Client(mcp) as client:
                return _sc(await client.call_tool("agency_doctor", {}))
        out = asyncio.run(main())
    finally:
        e.memory.close()
    assert isinstance(out, dict)
    assert "ok" in out and isinstance(out["ok"], bool)
    assert "python_version" in out and "." in out["python_version"]
    assert "deps" in out and isinstance(out["deps"], dict)
    for dep in ("fastmcp", "graphqlite"):
        assert dep in out["deps"]
    assert "db" in out and "path" in out["db"]
    assert "exists" in out["db"] and "writable" in out["db"]
    assert "env" in out
    assert "JULES_API_KEY" in out["env"]
    assert "CLAUDE_PROJECT_DIR" in out["env"]
    assert "next_steps" in out and isinstance(out["next_steps"], list)


def test_doctor_does_not_leak_jules_key(monkeypatch):
    """Spec 030 §B security invariant: the KEY VALUE must never appear
    in the doctor report — only its presence/absence."""
    secret = "sk-test-deadbeef-leak-canary-9876543210"
    monkeypatch.setenv("JULES_API_KEY", secret)
    e = Engine(tempfile.mktemp(suffix=".db"))
    mcp = e.build_mcp(codemode=False)
    try:
        async def main():
            async with Client(mcp) as client:
                return _sc(await client.call_tool("agency_doctor", {}))
        out = asyncio.run(main())
    finally:
        e.memory.close()
    payload = json.dumps(out)
    assert secret not in payload, "JULES_API_KEY value leaked into doctor report"
    assert out["env"]["JULES_API_KEY"] == "set"


def test_doctor_reports_missing_jules_key(monkeypatch):
    """When the key is absent, env.JULES_API_KEY=='missing' and a
    next_step names the user_config wiring."""
    monkeypatch.delenv("JULES_API_KEY", raising=False)
    e = Engine(tempfile.mktemp(suffix=".db"))
    mcp = e.build_mcp(codemode=False)
    try:
        async def main():
            async with Client(mcp) as client:
                return _sc(await client.call_tool("agency_doctor", {}))
        out = asyncio.run(main())
    finally:
        e.memory.close()
    assert out["env"]["JULES_API_KEY"] == "missing"
    next_steps_text = " ".join(out["next_steps"])
    assert "user_config" in next_steps_text or "JULES_API_KEY" in next_steps_text


def test_doctor_marks_ok_when_all_present(monkeypatch, tmp_path):
    """Healthy environment → ok=True, next_steps=[]."""
    monkeypatch.setenv("JULES_API_KEY", "x")
    monkeypatch.setenv("AGENCY_DB", str(tmp_path / "session.db"))
    e = Engine(str(tmp_path / "session.db"))   # creates the file
    mcp = e.build_mcp(codemode=False)
    try:
        async def main():
            async with Client(mcp) as client:
                return _sc(await client.call_tool("agency_doctor", {}))
        out = asyncio.run(main())
    finally:
        e.memory.close()
    assert out["ok"] is True, f"unexpected issues: {out['next_steps']}"
    assert out["next_steps"] == []
