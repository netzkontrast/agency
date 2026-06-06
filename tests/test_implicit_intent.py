"""Spec 018 Win 3 RED — implicit `intent_id` via the AGENCY_INTENT env.

Every capability verb needs an `intent_id` (the SERVES guard). In a long
bash/code-mode session against ONE intent, repeating
`intent_id="intent:abc"` on every call is pure ceremony (~25 tokens/call).
Win 3: the engine wire falls back to the `AGENCY_INTENT` env var when no
`intent_id` is supplied — set it once, omit it thereafter. An explicit
`intent_id` always wins; with neither, the existing helpful SERVES-guard
error still fires.
"""
from __future__ import annotations

import tempfile

import pytest

from agency.engine import Engine


@pytest.fixture
def engine():
    e = Engine(tempfile.mktemp(suffix=".db"))
    try:
        yield e
    finally:
        e.memory.close()


@pytest.fixture
def iid(engine):
    intent = engine.intent.capture(
        "drive a session against one intent",
        "verbs resolve intent_id from AGENCY_INTENT",
        "omitting intent_id still records SERVES",
    )
    engine.intent.confirm(intent)
    return intent


async def _call(mcp, name, params):
    return await mcp.call_tool(name, params)


def test_verb_falls_back_to_AGENCY_INTENT_env(engine, iid, monkeypatch):
    """With AGENCY_INTENT set and NO intent_id in the call, the verb runs
    and its Invocation SERVES the env-supplied intent."""
    import asyncio
    monkeypatch.setenv("AGENCY_INTENT", iid)
    mcp = engine.build_mcp(codemode=False)
    # checklist is a pure transform; the SERVES guard still requires a real intent
    res = asyncio.run(_call(mcp, "capability_develop_checklist", {"discipline": "tdd"}))
    sc = res.structured_content
    assert sc and (sc.get("result") or sc), f"verb should run via env intent; got {sc!r}"
    # an Invocation SERVES the env intent (provenance recorded)
    rows = engine.memory.g.query(
        "MATCH (inv:Invocation)-[:SERVES]->(i:Intent) WHERE i.id = $iid RETURN inv",
        {"iid": iid},
    )
    assert len(rows) >= 1


def test_explicit_intent_id_wins_over_env(engine, monkeypatch):
    """An explicit intent_id in the call beats AGENCY_INTENT — the env is
    only a fallback, never an override."""
    import asyncio
    real = engine.intent.capture("explicit wins", "x", "y")
    engine.intent.confirm(real)
    monkeypatch.setenv("AGENCY_INTENT", "intent:bogus-env-value")
    mcp = engine.build_mcp(codemode=False)
    asyncio.run(_call(mcp, "capability_develop_checklist",
                      {"discipline": "tdd", "intent_id": real}))
    rows = engine.memory.g.query(
        "MATCH (inv:Invocation)-[:SERVES]->(i:Intent) WHERE i.id = $iid RETURN inv",
        {"iid": real},
    )
    assert len(rows) >= 1


def test_no_intent_and_no_env_still_errors(engine, monkeypatch):
    """With neither an explicit intent_id nor AGENCY_INTENT, the SERVES guard
    still fires its helpful error — implicit resolution must not paper over a
    genuinely missing intent."""
    import asyncio
    monkeypatch.delenv("AGENCY_INTENT", raising=False)
    mcp = engine.build_mcp(codemode=False)
    with pytest.raises(Exception) as ei:
        asyncio.run(_call(mcp, "capability_develop_checklist", {"discipline": "tdd"}))
    assert "Intent" in str(ei.value) or "intent" in str(ei.value)
