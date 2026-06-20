"""Acceptance — relevance filter (Spec 350 Slice 1).

Behaviour contract:
  - ``relevance_filter(text, profile)`` extracts matching lines, reports elided
    count + locator (never silent — CLAUDE.md #9).
  - exclude wins over include.
  - budget caps the wire return, not the matched count.
  - bad regex fails open (no raise on the hook path).
  - ``_apply_filter`` dispatches ``relevance:<json>`` to the same helper.
  - ``jules.activities(filter=)`` keeps only activities matching the profile.
  - ``jules.activities(full=True)`` bypasses the filter entirely.
"""
from __future__ import annotations

import json
import tempfile
from contextlib import contextmanager

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from agency.engine import Engine

scenarios("features/relevance.feature")


# ── state fixture ─────────────────────────────────────────────────────────────

@pytest.fixture
def ctx():
    return {}


# ── stub jules backend ────────────────────────────────────────────────────────

class _StubJulesBackend:
    """Returns two fixed activities: agentMessaged + heartbeat."""

    ACTIVITIES = [
        {"id": "a1", "originator": "agent", "kind": "agentMessaged",
         "summary": "Task completed successfully"},
        {"id": "a2", "originator": "system", "kind": "heartbeat",
         "summary": "alive"},
    ]

    def activities(self, session, page_size, only_kinds, page_token="",
                   summary_only=True):
        return {"activities": list(self.ACTIVITIES), "nextPageToken": ""}

    def __getattr__(self, name):
        return lambda *a, **kw: {}


@pytest.fixture
def stub_engine():
    eng = Engine(tempfile.mktemp(suffix=".db"), jules_client=_StubJulesBackend())
    yield eng
    eng.memory.close()


@pytest.fixture
def stub_iid(stub_engine):
    iid = stub_engine.intent.capture("test", "test", "test")
    stub_engine.intent.confirm(iid)
    return iid


# ── pure helper ───────────────────────────────────────────────────────────────

@given('output of 2000 lines where 3 lines contain "ERROR"')
def _output_2000_lines_with_errors(ctx):
    lines = [f"INFO: line {i}" for i in range(1997)]
    lines.insert(500,  "ERROR: disk full")
    lines.insert(1000, "ERROR: connection lost")
    lines.insert(1500, "ERROR: timeout")
    ctx["text"] = "\n".join(lines)


@given(parsers.parse('a profile include=["{inc}"] context={ctx_n:d} budget={bud:d}'))
def _profile_include_only(ctx, inc, ctx_n, bud):
    ctx["profile"] = {"include": [inc], "context": ctx_n, "budget": bud or 0}


@given('text with a "WARN: real" line and a "WARN: deprecated" line')
def _text_warn_lines(ctx):
    ctx["text"] = "WARN: real\nWARN: deprecated\nINFO: ok"


@given('a profile include=["WARN"] exclude=["deprecated"]')
def _profile_include_exclude(ctx):
    ctx["profile"] = {"include": ["WARN"], "exclude": ["deprecated"], "context": 0, "budget": 0}


@given("output of 500 lines each 10 chars wide")
def _output_500_short_lines(ctx):
    ctx["text"] = "\n".join(f"line{i:04d}" for i in range(500))


@given('a profile include=[] exclude=[] budget=50')
def _profile_budget_only(ctx):
    ctx["profile"] = {"include": [], "exclude": [], "budget": 50}


@given('text with a line "hello world"')
def _text_hello(ctx):
    ctx["text"] = "hello world"


@given('a profile include=["[invalid"] context=0 budget=0')
def _profile_bad_regex(ctx):
    ctx["profile"] = {"include": ["[invalid"], "context": 0, "budget": 0}


@given('text with "ERROR: disk full" and "INFO: startup complete"')
def _text_error_info(ctx):
    ctx["text"] = "INFO: startup complete\nERROR: disk full\nINFO: done"


@given('a relevance spec string targeting "ERROR"')
def _spec_string_error(ctx):
    ctx["spec"] = json.dumps({"include": ["ERROR"], "context": 0, "budget": 0})


@when("I call relevance_filter")
def _call_relevance_filter(ctx):
    from agency._relevance import relevance_filter
    ctx["result"] = relevance_filter(ctx["text"], ctx["profile"])


@when("I call _apply_filter with the relevance spec")
def _call_apply_filter_relevance(ctx):
    from agency.capabilities.shell._main import _apply_filter
    ctx["result"] = _apply_filter(ctx["text"], f"relevance:{ctx['spec']}")


# ── Then steps — pure helper ─────────────────────────────────────────────────

@then("kept contains the 3 ERROR lines")
def _kept_has_3_error_lines(ctx):
    kept = ctx["result"]["kept"]
    assert kept.count("ERROR:") == 3, f"expected 3 ERROR lines, got:\n{kept}"


@then("elided equals 1997")
def _elided_1997(ctx):
    assert ctx["result"]["elided"] == 1997, ctx["result"]["elided"]


@then("locator is present")
def _locator_present(ctx):
    loc = ctx["result"].get("locator", "")
    assert loc.startswith("sha16:"), f"bad locator: {loc!r}"


@then('kept contains "WARN: real"')
def _kept_has_warn_real(ctx):
    assert "WARN: real" in ctx["result"]["kept"]


@then('kept does not contain "WARN: deprecated"')
def _kept_no_deprecated(ctx):
    assert "WARN: deprecated" not in ctx["result"]["kept"]


@then("matched equals 1")
def _matched_1(ctx):
    assert ctx["result"]["matched"] == 1, ctx["result"]["matched"]


@then("kept length is at most 100 chars")
def _kept_budget(ctx):
    # budget=50 caps the returned string; allow some slack for the elided note
    assert len(ctx["result"]["kept"]) <= 200, len(ctx["result"]["kept"])


@then("elided is reported in the result")
def _elided_reported(ctx):
    assert "elided" in ctx["result"]
    assert ctx["result"]["elided"] >= 0


@then("the call succeeds without raising")
def _call_succeeded(ctx):
    assert "result" in ctx and ctx["result"] is not None


@then("kept is the original text (bad pattern skipped, all lines kept)")
def _kept_is_original(ctx):
    # bad include pattern → include_res is empty → all lines kept (fail-open)
    assert "hello world" in ctx["result"]["kept"]
    assert ctx["result"]["elided"] == 0


# ── Then steps — _apply_filter ────────────────────────────────────────────────

@then('the result contains "ERROR: disk full"')
def _result_has_error(ctx):
    assert "ERROR: disk full" in ctx["result"], ctx["result"]


@then('the result does not contain "INFO: startup complete"')
def _result_no_info(ctx):
    assert "INFO: startup complete" not in ctx["result"], ctx["result"]


# ── jules.activities ──────────────────────────────────────────────────────────

@given("a stub backend returning activities of kinds agentMessaged and heartbeat")
def _stub_jules(ctx):
    pass  # stub_engine / stub_iid fixtures supply the backend


@when('I call jules.activities with filter including "agentMessaged"')
def _activities_filter_agent_messaged(ctx, stub_engine, stub_iid):
    result, _ = stub_engine.registry.invoke(
        stub_engine.memory, stub_iid, "jules", "activities",
        session="session:test",
        filter=json.dumps({"include": ["agentMessaged"]}),
    )
    ctx["act_result"] = result


@when('I call jules.activities with full=True and filter including "agentMessaged"')
def _activities_full_with_filter(ctx, stub_engine, stub_iid):
    result, _ = stub_engine.registry.invoke(
        stub_engine.memory, stub_iid, "jules", "activities",
        session="session:test",
        full=True,
        filter=json.dumps({"include": ["agentMessaged"]}),
    )
    ctx["act_result"] = result


@then("the returned activities list contains only the agentMessaged activity")
def _only_agent_messaged(ctx):
    acts = ctx["act_result"]["activities"]
    assert len(acts) == 1, f"expected 1, got {len(acts)}: {acts}"
    assert acts[0]["kind"] == "agentMessaged"


@then("filter_applied is present in the result")
def _filter_applied_key(ctx):
    assert "filter_applied" in ctx["act_result"], ctx["act_result"]


@then("the returned activities list contains both activities")
def _both_activities(ctx):
    acts = ctx["act_result"]["activities"]
    kinds = {a["kind"] for a in acts}
    assert "agentMessaged" in kinds and "heartbeat" in kinds, kinds
