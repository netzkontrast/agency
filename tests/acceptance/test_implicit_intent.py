"""Acceptance — implicit intent_id via AGENCY_INTENT env var (Spec 018 Win 3).

Converted from tests/test_implicit_intent.py. Behaviour: explicit id wins;
env fallback works + records SERVES; neither gives the SERVES-guard error
that names intent_bootstrap. The error teachability scenario is folded in
since it is the same observable error message.
"""
from __future__ import annotations

import asyncio
import tempfile

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from conftest import served
from agency.engine import Engine

scenarios("features/implicit_intent.feature")


# ── fixtures ───────────────────────────────────────────────────────────────

@pytest.fixture
def fresh_engine():
    """A fresh engine for env-var tests (needs its own lifetime)."""
    e = Engine(tempfile.mktemp(suffix=".db"))
    yield e
    e.memory.close()


# ── shared helpers ─────────────────────────────────────────────────────────

def _call_wire(eng, name, params):
    from fastmcp import Client
    mcp = eng.build_mcp(codemode=False)

    async def _c():
        async with Client(mcp) as c:
            return await c.call_tool(name, params)

    return asyncio.run(_c())


# ── Given steps ────────────────────────────────────────────────────────────

@given("a confirmed intent set as AGENCY_INTENT env var",
       target_fixture="env_intent")
def _env_intent(fresh_engine, monkeypatch):
    iid = fresh_engine.intent.capture("env test", "runs via env", "verified")
    fresh_engine.intent.confirm(iid)
    monkeypatch.setenv("AGENCY_INTENT", iid)
    return {"engine": fresh_engine, "iid": iid}


@given("a second separate confirmed intent", target_fixture="second_intent")
def _second_intent(env_intent):
    e = env_intent["engine"]
    iid2 = e.intent.capture("second", "explicit", "ok")
    e.intent.confirm(iid2)
    return iid2


@given("AGENCY_INTENT is not set")
def _no_env(monkeypatch):
    monkeypatch.delenv("AGENCY_INTENT", raising=False)


# ── When steps ─────────────────────────────────────────────────────────────

@when("I call a verb without supplying an intent_id", target_fixture="wire_result")
def _call_no_iid(env_intent):
    e = env_intent["engine"]
    return _call_wire(e, "capability_develop_checklist", {"discipline": "tdd"})


@when("I call a verb with the second intent_id explicitly", target_fixture="wire_result2")
def _call_explicit(env_intent, second_intent):
    e = env_intent["engine"]
    return _call_wire(e, "capability_develop_checklist",
                      {"discipline": "tdd", "intent_id": second_intent})


@when("I invoke a verb against a non-existent intent with no env fallback",
      target_fixture="guard_error")
def _call_raises(fresh_engine):
    try:
        fresh_engine.registry.invoke(
            fresh_engine.memory, "intent:does-not-exist", "plugin", "help"
        )
        return None
    except ValueError as exc:
        return exc


# ── Then steps ─────────────────────────────────────────────────────────────

@then("the verb succeeds")
def _succeeds(wire_result):
    sc = wire_result.structured_content
    assert sc is not None, f"verb returned nothing: {wire_result!r}"


@then("an Invocation SERVES the intent from the env var")
def _serves_env(env_intent):
    e = env_intent["engine"]
    iid = env_intent["iid"]
    rows = e.memory.g.query(
        "MATCH (inv:Invocation)-[:SERVES]->(i:Intent) WHERE i.id = $iid RETURN inv",
        {"iid": iid},
    )
    assert len(rows) >= 1, f"no Invocation SERVES {iid}"


@then("the Invocation SERVES the second intent")
def _serves_second(env_intent, second_intent):
    e = env_intent["engine"]
    rows = e.memory.g.query(
        "MATCH (inv:Invocation)-[:SERVES]->(i:Intent) WHERE i.id = $iid RETURN inv",
        {"iid": second_intent},
    )
    assert len(rows) >= 1, f"no Invocation SERVES {second_intent}"


@then("a ValueError is raised")
def _val_err(guard_error):
    assert isinstance(guard_error, ValueError), (
        f"expected ValueError, got {guard_error!r}"
    )


@then("the error message mentions intent_bootstrap")
def _error_msg(guard_error):
    assert isinstance(guard_error, ValueError)
    assert "intent_bootstrap" in str(guard_error), str(guard_error)
