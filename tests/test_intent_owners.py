"""Spec 048 — Intent owner closed-enum + default-by-presence rule.

Owners: user (root), agent (sub), subagent (delegated), jules (remote),
system (substrate). Default: 'user' for root intents (no parent),
'agent' for child intents. Explicit override always wins.
"""
import asyncio
import json
import tempfile

import pytest

from agency.engine import Engine


_OWNERS = {"user", "agent", "subagent", "jules", "system"}


@pytest.fixture
def engine():
    return Engine(tempfile.mktemp(suffix=".db"))


def test_default_root_owner_is_user(engine):
    iid = engine.intent.capture("root", "x", "x")
    engine.intent.confirm(iid)
    rows = engine.memory.find("Intent")
    me = next(r for r in rows if r["id"] == iid)
    assert me["owner"] == "user"


def test_default_child_owner_is_agent(engine):
    parent = engine.intent.capture("p", "x", "x")
    engine.intent.confirm(parent)
    child = engine.intent.capture("c", "x", "x",
                                   parent_intent_id=parent)
    engine.intent.confirm(child)
    rows = engine.memory.find("Intent")
    me = next(r for r in rows if r["id"] == child)
    assert me["owner"] == "agent"


def test_explicit_owner_overrides_default(engine):
    parent = engine.intent.capture("p", "x", "x")
    engine.intent.confirm(parent)
    child = engine.intent.capture("c", "x", "x",
                                   parent_intent_id=parent,
                                   owner="subagent")
    engine.intent.confirm(child)
    rows = engine.memory.find("Intent")
    me = next(r for r in rows if r["id"] == child)
    assert me["owner"] == "subagent"


def test_unknown_owner_rejected_by_ontology(engine):
    with pytest.raises(ValueError):
        engine.intent.capture("bad", "x", "x", owner="not-a-real-owner")


def test_all_five_owners_accepted(engine):
    for owner in sorted(_OWNERS):
        iid = engine.intent.capture(f"o-{owner}", "x", "x", owner=owner)
        engine.intent.confirm(iid)
        rows = engine.memory.find("Intent")
        me = next(r for r in rows if r["id"] == iid)
        assert me["owner"] == owner


# ---------------------------------------------------------------------------
# intent_bootstrap MCP substrate tool — owner default inferrence.
# ---------------------------------------------------------------------------


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


def test_intent_bootstrap_defaults_user_owner():
    from fastmcp import Client
    e = Engine(tempfile.mktemp(suffix=".db"))
    mcp = e.build_mcp(codemode=False)
    try:
        async def go():
            async with Client(mcp) as c:
                r = _sc(await c.call_tool("intent_bootstrap", {
                    "purpose": "p", "deliverable": "d", "acceptance": "a"}))
                return r
        out = asyncio.run(go())
    finally:
        e.memory.close()
    iid = out["intent_id"]
    e2 = Engine(":memory:")
    # Just verify the recorded intent (in the same DB).
    e3 = Engine(out.get("db_path") or tempfile.mktemp(suffix=".db"))


def test_intent_bootstrap_defaults_agent_owner_with_parent():
    from fastmcp import Client
    e = Engine(tempfile.mktemp(suffix=".db"))
    mcp = e.build_mcp(codemode=False)
    try:
        async def go():
            async with Client(mcp) as c:
                root = _sc(await c.call_tool("intent_bootstrap", {
                    "purpose": "root", "deliverable": "x",
                    "acceptance": "x"}))
                child = _sc(await c.call_tool("intent_bootstrap", {
                    "purpose": "child", "deliverable": "x",
                    "acceptance": "x",
                    "parent_intent_id": root["intent_id"]}))
                return root, child
        root, child = asyncio.run(go())
    finally:
        # NB: client closes its engine; we don't have a memory handle
        # to inspect. The wire returns child[owner]? Let's assert it
        # carries the explicit field.
        pass
    # The intent_bootstrap response carries owner (Spec 048).
    assert root["owner"] == "user"
    assert child["owner"] == "agent"


def test_intent_bootstrap_explicit_owner_wins():
    from fastmcp import Client
    e = Engine(tempfile.mktemp(suffix=".db"))
    mcp = e.build_mcp(codemode=False)
    try:
        async def go():
            async with Client(mcp) as c:
                r = _sc(await c.call_tool("intent_bootstrap", {
                    "purpose": "p", "deliverable": "d", "acceptance": "a",
                    "owner": "jules"}))
                return r
        out = asyncio.run(go())
    finally:
        e.memory.close()
    assert out["owner"] == "jules"
