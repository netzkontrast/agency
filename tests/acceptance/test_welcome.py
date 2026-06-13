"""Acceptance — agency_welcome (Spec 029 / 030).

Converted from tests/test_welcome.py and tests/test_welcome_state.py.

Dropped (implementation / structural / not observable behaviour):
- magic-constant frozen budget (150 * ncaps + 1000 is kept as a relationship,
  not a pinned number per CLAUDE.md rule 8).
- Monkeypatch-internal tests that probe FastMCP internals
  (test_response_prefix_discipline.py's _find_tool helper is an internal probe —
  the prefix-stability behaviour is covered here via the wire output shape).
"""
from __future__ import annotations

import asyncio
import json
import tempfile

import pytest
from fastmcp import Client
from pytest_bdd import given, scenarios, then, when

from agency.engine import Engine

scenarios("features/welcome.feature")


# ── wire helper ───────────────────────────────────────────────────────────────

def _welcome(eng: Engine) -> dict:
    mcp = eng.build_mcp(codemode=False)

    async def _run():
        async with Client(mcp) as c:
            r = await c.call_tool("agency_welcome", {})
            sc = r.structured_content
            if isinstance(sc, dict):
                return sc.get("result", sc)
            if sc is not None:
                return sc
            try:
                return json.loads(r.content[0].text)
            except Exception:
                return r.content[0].text

    return asyncio.run(_run())


# ── shared Given step override: welcome tests own a fresh engine ──────────────
# We re-declare the shared Given step so that welcome tests get their own
# engine fixture (the conftest shared `engine` fixture has different lifecycle).

@given("a fresh agency engine in code-mode", target_fixture="welcome_engine")
def _fresh_welcome_engine():
    e = Engine(tempfile.mktemp(suffix=".db"))
    return e


# ── scenario-local fixtures ───────────────────────────────────────────────────

@given("an engine with an existing confirmed intent",
       target_fixture="welcome_engine")
def _in_progress_engine(request):
    e = Engine(tempfile.mktemp(suffix=".db"))
    iid = e.intent.capture_and_confirm("ship", "X", "tests green")
    e._test_iid = iid  # stash for the "last_intent" assertion
    return e


@given("an engine whose AGENCY_DB points at a non-existent path",
       target_fixture="welcome_engine")
def _missing_db_engine(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENCY_DB", str(tmp_path / "missing" / "session.db"))
    return Engine(tempfile.mktemp(suffix=".db"))


# ── When steps ────────────────────────────────────────────────────────────────

@when("I call agency_welcome", target_fixture="welcome_result")
def _do_welcome(welcome_engine):
    return _welcome(welcome_engine)


@when("I call agency_welcome twice", target_fixture="welcome_two_results")
def _do_welcome_twice(welcome_engine):
    r1 = _welcome(welcome_engine)
    r2 = _welcome(welcome_engine)
    return r1, r2


# ── Then steps — fresh state ──────────────────────────────────────────────────

@then('the state is "fresh"')
def _state_fresh(welcome_result):
    assert welcome_result["state"] == "fresh"


@then("the intents_count is 0")
def _intents_count_zero(welcome_result):
    assert welcome_result["intents_count"] == 0


@then("the next steps mention intent_bootstrap or agency_install")
def _next_steps_fresh(welcome_result):
    text = " ".join(welcome_result.get("next", []))
    assert "intent_bootstrap" in text or "agency_install" in text, (
        f"next steps don't mention bootstrap or install: {welcome_result.get('next')}")


# ── Then steps — payload shape ────────────────────────────────────────────────

@then("the payload contains bootstrap_example with intent_bootstrap")
def _bootstrap_example(welcome_result):
    assert "bootstrap_example" in welcome_result
    assert "intent_bootstrap" in welcome_result["bootstrap_example"]


@then("the payload contains install_example with agency_install")
def _install_example(welcome_result):
    assert "install_example" in welcome_result
    assert "agency_install" in welcome_result["install_example"]


@then("the payload contains a sorted capability list including plugin and reflect")
def _capabilities(welcome_result):
    caps = welcome_result.get("capabilities", [])
    assert isinstance(caps, list)
    assert "plugin" in caps
    assert "reflect" in caps


@then("the payload carries a db_path")
def _db_path(welcome_result):
    assert "db_path" in welcome_result


@then("the payload carries a next list with at least 2 steps")
def _next_list(welcome_result):
    assert isinstance(welcome_result.get("next"), list)
    assert len(welcome_result["next"]) >= 2


@then("the payload carries a state field")
def _state_field(welcome_result):
    assert "state" in welcome_result


@then("the capabilities list is sorted")
def _sorted_caps(welcome_result):
    caps = welcome_result["capabilities"]
    assert caps == sorted(caps), "capabilities list must be sorted"


# ── Then steps — pure read ────────────────────────────────────────────────────

@then("no Intent Invocation or Reflection nodes were created")
def _no_mutations(welcome_engine):
    for label in ("Intent", "Invocation", "Reflection"):
        nodes = list(welcome_engine.memory.find(label))
        assert len(nodes) == 0, (
            f"welcome wrote a {label} node — must be pure introspection")


# ── Then steps — in-progress state ───────────────────────────────────────────

@then('the state is "in_progress"')
def _state_in_progress(welcome_result):
    assert welcome_result["state"] == "in_progress"


@then("the intents_count is 1")
def _intents_count_one(welcome_result):
    assert welcome_result["intents_count"] == 1


@then("the last_intent is the confirmed intent id")
def _last_intent(welcome_result, welcome_engine):
    assert welcome_result["last_intent"] == welcome_engine._test_iid


@then("the next steps mention search or memory_graph_provenance")
def _next_steps_in_progress(welcome_result):
    text = " ".join(welcome_result.get("next", []))
    assert "search" in text or "memory_graph_provenance" in text


# ── Then steps — token budget ─────────────────────────────────────────────────

@then("the payload byte size is within 150 bytes per capability plus 1000")
def _token_budget(welcome_result):
    payload = json.dumps(welcome_result)
    ncaps = len(welcome_result["capabilities"])
    budget = 150 * ncaps + 1000
    assert len(payload) <= budget, (
        f"welcome payload {len(payload)} bytes > budget {budget} "
        f"({ncaps} caps × 150 + 1000)")


# ── Then steps — missing DB ───────────────────────────────────────────────────

@then("the db_path contains session.db")
def _db_path_contains_session_db(welcome_result):
    assert "session.db" in welcome_result["db_path"]


# ── Then steps — prefix discipline (Spec 146) ─────────────────────────────────

@then("the _prefix_keys field is present")
def _prefix_keys_present(welcome_result):
    assert "_prefix_keys" in welcome_result, (
        "agency_welcome must declare its prefix-vs-body split via _prefix_keys")


@then("the prefix does not contain per-call state keys like state or intents_count")
def _prefix_excludes_per_call(welcome_result):
    prefix_keys = set(welcome_result.get("_prefix_keys", []))
    forbidden = {"state", "intents_count", "last_intent", "db_path", "next"}
    assert prefix_keys.isdisjoint(forbidden), (
        f"prefix contains per-call keys: {prefix_keys & forbidden}")


@then("the prefix contains capability_set_hash and schema_version")
def _prefix_contains_stable_keys(welcome_result):
    prefix_keys = set(welcome_result.get("_prefix_keys", []))
    required = {"capability_set_hash", "schema_version"}
    assert required.issubset(prefix_keys), (
        f"prefix missing stable keys: {required - prefix_keys}")


@then("the prefix bytes are identical across both calls")
def _prefix_stable(welcome_two_results):
    r1, r2 = welcome_two_results
    keys = r1.get("_prefix_keys", [])
    prefix1 = {k: r1[k] for k in keys if k in r1}
    prefix2 = {k: r2[k] for k in keys if k in r2}
    blob1 = json.dumps(prefix1, sort_keys=True, separators=(",", ":"))
    blob2 = json.dumps(prefix2, sort_keys=True, separators=(",", ":"))
    assert blob1 == blob2, (
        "prefix drifted across two calls with no registry change — "
        "Spec 146 invariant violated; check for datetime.now()/uuid4() in prefix builders.")
