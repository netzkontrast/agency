"""Spec 029 §A — agency_welcome MCP substrate tool.

Closes F6 (Mittel/DX) + the three-doc-read tax on first contact: one
call returns the bootstrap example, the install example, the capability
map, and the resolved DB path. Token-budget invariant: ≤ 1 KB on the
current core registry.
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


def test_welcome_payload_shape():
    """agency_welcome returns the four onboarding fields + an ordered next list."""
    e = Engine(tempfile.mktemp(suffix=".db"))
    mcp = e.build_mcp(codemode=False)
    try:
        async def main():
            async with Client(mcp) as client:
                return _sc(await client.call_tool("agency_welcome", {}))
        out = asyncio.run(main())
    finally:
        e.memory.close()
    assert isinstance(out, dict)
    assert "bootstrap_example" in out and "intent_bootstrap" in out["bootstrap_example"]
    assert "install_example" in out and "agency_install" in out["install_example"]
    assert "capabilities" in out and isinstance(out["capabilities"], list)
    assert "db_path" in out
    assert "next" in out and isinstance(out["next"], list) and len(out["next"]) >= 3


def test_welcome_capabilities_is_deterministic():
    """Capability list iterates in stable (sorted) order. Per Spec 029
    OQ-3 the welcome carries names only (verbs reachable via
    capability_plugin_help / search) — token-budget bit."""
    e = Engine(tempfile.mktemp(suffix=".db"))
    mcp = e.build_mcp(codemode=False)
    try:
        async def main():
            async with Client(mcp) as client:
                return _sc(await client.call_tool("agency_welcome", {}))
        out = asyncio.run(main())
    finally:
        e.memory.close()
    caps = out["capabilities"]
    assert isinstance(caps, list)
    assert caps == sorted(caps)
    # at least the core caps the engine loads at boot
    for required in ("plugin", "reflect"):
        assert required in caps


def test_welcome_works_on_fresh_target(tmp_path, monkeypatch):
    """Spec 029 §A (Cockburn A1 actor): welcome is purely introspective
    — it must not require the DB file to exist. resolve_db_path(None)
    returns the WOULD-BE path on an empty target."""
    monkeypatch.setenv("AGENCY_DB", str(tmp_path / "missing" / "session.db"))
    e = Engine(tempfile.mktemp(suffix=".db"))   # the engine's own DB stays separate
    mcp = e.build_mcp(codemode=False)
    try:
        async def main():
            async with Client(mcp) as client:
                return _sc(await client.call_tool("agency_welcome", {}))
        out = asyncio.run(main())
    finally:
        e.memory.close()
    assert "session.db" in out["db_path"]


def test_welcome_token_budget_under_1kb():
    """Regression invariant — Spec 029 OQ-3. The welcome payload must
    stay under 1 KB on the current core registry; if a future capability
    pushes it over, the truncation logic must be reintroduced."""
    e = Engine(tempfile.mktemp(suffix=".db"))
    mcp = e.build_mcp(codemode=False)
    try:
        async def main():
            async with Client(mcp) as client:
                return _sc(await client.call_tool("agency_welcome", {}))
        out = asyncio.run(main())
    finally:
        e.memory.close()
    payload = json.dumps(out)
    assert len(payload) <= 1024, (
        f"welcome payload {len(payload)} bytes exceeds the 1 KB budget; "
        f"reintroduce truncation per Spec 029 OQ-3")
