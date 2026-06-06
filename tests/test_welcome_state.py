"""Spec 030 §C — stateful agency_welcome.

Subsumes the deferred Spec 029 §B empty-graph search hint: instead of
trying to wrap FastMCP's builtin search, the canonical onboarding tool
itself adapts to graph state.
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


def test_welcome_fresh_state():
    """Empty graph → state='fresh' + next leads with install + bootstrap."""
    e = Engine(tempfile.mktemp(suffix=".db"))
    mcp = e.build_mcp(codemode=False)
    try:
        async def main():
            async with Client(mcp) as client:
                return _sc(await client.call_tool("agency_welcome", {}))
        out = asyncio.run(main())
    finally:
        e.memory.close()
    assert out["state"] == "fresh"
    assert out["intents_count"] == 0
    next_text = " ".join(out["next"])
    assert "intent_bootstrap" in next_text or "agency_install" in next_text


def test_welcome_in_progress_state():
    """Intents present → state='in_progress' + last_intent surfaced."""
    e = Engine(tempfile.mktemp(suffix=".db"))
    iid = e.intent.capture_and_confirm("ship", "X", "tests green")
    mcp = e.build_mcp(codemode=False)
    try:
        async def main():
            async with Client(mcp) as client:
                return _sc(await client.call_tool("agency_welcome", {}))
        out = asyncio.run(main())
    finally:
        e.memory.close()
    assert out["state"] == "in_progress"
    assert out["intents_count"] == 1
    assert out["last_intent"] == iid
    next_text = " ".join(out["next"])
    assert "search" in next_text or "memory_graph_provenance" in next_text


def test_welcome_no_graph_writes_on_call():
    """Pure read — calling welcome must not mutate the graph."""
    e = Engine(tempfile.mktemp(suffix=".db"))
    mcp = e.build_mcp(codemode=False)
    try:
        async def call():
            async with Client(mcp) as client:
                return _sc(await client.call_tool("agency_welcome", {}))
        asyncio.run(call())
        asyncio.run(call())
        # No Intent / Invocation / Reflection nodes from a welcome call
        for label in ("Intent", "Invocation", "Reflection"):
            assert len(list(e.memory.find(label))) == 0, (
                f"welcome wrote a {label} node — must be pure introspection")
    finally:
        e.memory.close()


def test_welcome_token_budget_still_under_2kb_in_progress():
    """The state fields + the Spec 068 capability_tier must stay under the 2 KB
    welcome budget (raised from 1 KB by Spec 068 — the tier is net-token-positive,
    see test_welcome.py)."""
    e = Engine(tempfile.mktemp(suffix=".db"))
    for i in range(3):                                # a few intents on the graph
        e.intent.capture_and_confirm(f"p{i}", f"d{i}", f"a{i}")
    mcp = e.build_mcp(codemode=False)
    try:
        async def main():
            async with Client(mcp) as client:
                return _sc(await client.call_tool("agency_welcome", {}))
        out = asyncio.run(main())
    finally:
        e.memory.close()
    payload = json.dumps(out)
    # Flexible per-capability budget (CLAUDE.md no-hardcoded rule), not a frozen 2 KB.
    ncaps = len(out["capabilities"])
    budget = 150 * ncaps + 600
    assert len(payload) <= budget, (
        f"welcome payload {len(payload)} bytes exceeds {budget} ({ncaps} caps × 150 + 600)")
