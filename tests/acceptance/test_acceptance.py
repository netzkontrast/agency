"""Gherkin acceptance suite — BEHAVIOUR only, never implementation.

Owned by the Vision-owner / Review-partner session (GitHub CI disabled; this is
the gate, run in the background against the refactor branch). Scenarios specify
what the agency engine DOES — the wire contract, provenance, the four pillars'
behaviour, and behaviour-preservation across the Spec-286 refactor — NOT how it
is built. Structural cleanliness (OOP separation, no raw `.g`, folders) is a
REVIEW concern, not a test here.

Co-evolution: when a valid, good change legitimately moves a behaviour a
scenario pinned, the scenario is UPDATED; a change that breaks observable
behaviour leaves its scenario red.
"""
from __future__ import annotations

import asyncio
import tempfile

import pytest
from pytest_bdd import given, when, then, parsers, scenarios

from agency.engine import Engine

scenarios("features")


@pytest.fixture
def engine():
    eng = Engine(tempfile.mktemp(suffix=".db"))
    yield eng
    eng.memory.close()


# ─────────────────────────── wire contract ───────────────────────────


@given("a fresh agency engine in code-mode")
def _fresh(engine):
    # the `engine` fixture provides it; code-mode is selected at list time
    return engine


@when("a client lists the available tools", target_fixture="tool_names")
def _list_tools(engine):
    from fastmcp import Client

    mcp = engine.build_mcp(codemode=True)

    async def _l():
        async with Client(mcp) as c:
            return {t.name for t in await c.list_tools()}

    return asyncio.run(_l())


@then(parsers.parse('"{a}", "{b}" and "{c}" are all available'))
def _verbs_available(tool_names, a, b, c):
    assert {a, b, c} <= tool_names, f"missing wire verbs: {{{a},{b},{c}}} - {tool_names}"


@then("no capability verb is exposed directly at the wire")
def _no_leak(tool_names):
    leaked = {n for n in tool_names if n.startswith("capability_")}
    assert not leaked, f"capability verbs leaked to the wire: {sorted(leaked)[:5]}"


@then("the execute verb is available to run capability code")
def _execute_present(tool_names):
    assert "execute" in tool_names


# ─────────────────────────── provenance ───────────────────────────


@given("a confirmed intent", target_fixture="intent_id")
def _intent(engine):
    iid = engine.intent.capture("acceptance", "behaviour preserved", "verified")
    engine.intent.confirm(iid)
    return iid


def _served_invocations(engine, intent_id) -> int:
    rows = engine.memory.g.query(
        "MATCH (i:Invocation)-[:SERVES]->(t) WHERE t.id = $iid RETURN i",
        {"iid": intent_id})
    return len(rows)


@when("I invoke a capability verb under that intent")
def _invoke(engine, intent_id):
    engine.registry.invoke(engine.memory, intent_id, "reflect", "note",
                           scope="observation", text="behaviour check")


@then("an Invocation is recorded in the graph")
def _invocation_recorded(engine):
    assert engine.memory.find("Invocation"), "no Invocation node recorded"


@then("that Invocation SERVES the intent")
def _invocation_serves(engine, intent_id):
    assert _served_invocations(engine, intent_id) >= 1, "no Invocation SERVES the intent"


@then("the intent has no served invocations")
def _no_served(engine, intent_id):
    assert _served_invocations(engine, intent_id) == 0


# ─────────────────────────── capability surface + health ───────────────────────────


@when("a client lists the capability verbs", target_fixture="verb_names")
def _list_verbs(engine):
    from fastmcp import Client

    mcp = engine.build_mcp(codemode=False)   # codemode-off exposes one tool per verb

    async def _l():
        async with Client(mcp) as c:
            return {t.name for t in await c.list_tools() if t.name.startswith("capability_")}

    return asyncio.run(_l())


@then("many capability verbs are available")
def _many_verbs(verb_names):
    # relationship, not a frozen count (rule 8): the refactor must not collapse the surface
    assert len(verb_names) > 50, f"verb surface collapsed to {len(verb_names)}"


@when("I ask the engine doctor for a health report", target_fixture="health")
def _doctor(engine):
    from fastmcp import Client

    mcp = engine.build_mcp(codemode=False)

    async def _l():
        async with Client(mcp) as c:
            r = await c.call_tool("agency_doctor", {})
            sc = r.structured_content
            return sc.get("result", sc) if isinstance(sc, dict) else sc

    return asyncio.run(_l())


@then("a non-empty health report is returned")
def _health_ok(health):
    assert isinstance(health, dict) and health, "doctor returned no health report"


@then(parsers.parse('the "{cap}" capability exposes a full clustered verb suite'))
def _clustered_suite_intact(verb_names, cap):
    # relationship guard (rule 8): a clustered god-class (music ~103, novel ~91)
    # split into mixins must keep a large, contiguous verb suite — not a frozen count.
    n = len([v for v in verb_names if v.startswith(f"capability_{cap}_")])
    assert n > 80, f"capability {cap!r} verb suite collapsed to {n} after the cluster split"
