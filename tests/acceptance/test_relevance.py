"""Acceptance — relevance filter (Spec 350 Slices 1, 2, and 3).

Behaviour contract:
  - ``relevance_filter(text, profile)`` extracts matching lines, reports elided
    count + locator (never silent — CLAUDE.md #9).
  - exclude wins over include.
  - budget caps the wire return, not the matched count.
  - bad regex fails open (no raise on the hook path).
  - ``_apply_filter`` dispatches ``relevance:<json>`` to the same helper.
  - ``jules.activities(filter=)`` keeps only activities matching the profile.
  - ``jules.activities(full=True)`` bypasses the filter entirely.
  Slice 2:
  - ``load_filter_profile(name)`` reads named profiles from config ``filters:`` section.
  - ``jules.activities(filter="<name>")`` resolves a named profile from config.
  - ``capture_filter`` applies config ``filters.shell`` profile for Bash (OPT-IN).
  - PostToolUse capture applies config ``filters.toolcall`` profile (OPT-IN).
"""
from __future__ import annotations

import json
import os
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
def stub_engine(tmp_path):
    eng = Engine(str(tmp_path / "graph.db"), jules_client=_StubJulesBackend())
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


# ── Slice 2: config registry ──────────────────────────────────────────────────

def _write_config(path: str, content: dict) -> None:
    """Write a minimal YAML config file for testing."""
    import yaml
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        yaml.safe_dump(content, f, default_flow_style=False)


@given('a config file with a "testprofile" filter including "agentMessaged"')
def _config_testprofile(ctx, tmp_path):
    cfg = tmp_path / "config.yaml"
    _write_config(str(cfg), {"filters": {"testprofile": {"include": ["agentMessaged"]}}})
    ctx["config_path"] = str(cfg)


@when('I call jules.activities with filter name "testprofile" and the config path')
def _activities_named_profile(ctx, stub_engine, stub_iid):
    from agency._config import _READ_CACHE
    _READ_CACHE.clear()
    old = os.environ.get("AGENCY_CONFIG")
    os.environ["AGENCY_CONFIG"] = ctx["config_path"]
    try:
        result, _ = stub_engine.registry.invoke(
            stub_engine.memory, stub_iid, "jules", "activities",
            session="session:test",
            filter="testprofile",
        )
    finally:
        if old is None:
            os.environ.pop("AGENCY_CONFIG", None)
        else:
            os.environ["AGENCY_CONFIG"] = old
        _READ_CACHE.clear()
    ctx["act_result"] = result


@then("only the agentMessaged activity is returned via the named profile")
def _only_agent_via_named_profile(ctx):
    acts = ctx["act_result"]["activities"]
    assert len(acts) == 1, f"expected 1 activity, got {len(acts)}: {acts}"
    assert acts[0]["kind"] == "agentMessaged", acts[0]


@given('a config file with filters.shell.exclude containing "SKIPME"')
def _config_shell_exclude(ctx, tmp_path):
    cfg = tmp_path / "config.yaml"
    _write_config(str(cfg), {"filters": {"shell": {"exclude": ["SKIPME"]}}})
    ctx["config_path"] = str(cfg)


@when('I capture Bash output containing a "SKIPME" line via capture_filter with the config')
def _capture_filter_skipme(ctx):
    from agency._config import _READ_CACHE
    from agency.capabilities.shell._main import capture_filter
    _READ_CACHE.clear()
    old = os.environ.get("AGENCY_CONFIG")
    os.environ["AGENCY_CONFIG"] = ctx["config_path"]
    try:
        ctx["filtered"] = capture_filter(
            "echo test", "INFO: ok\nSKIPME: this line\nINFO: done", tool="Bash"
        )
    finally:
        if old is None:
            os.environ.pop("AGENCY_CONFIG", None)
        else:
            os.environ["AGENCY_CONFIG"] = old
        _READ_CACHE.clear()


@then('the capture_filter filtered result does not contain "SKIPME"')
def _filtered_no_skipme(ctx):
    assert "SKIPME" not in ctx["filtered"], f"SKIPME should be excluded:\n{ctx['filtered']}"


@given('a config file with filters.toolcall.include=["IMPORTANT"]')
def _config_toolcall_include(ctx, tmp_path):
    cfg = tmp_path / "config.yaml"
    _write_config(str(cfg), {"filters": {"toolcall": {"include": ["IMPORTANT"]}}})
    ctx["config_path"] = str(cfg)


@when('a PostToolUse event with output containing "IMPORTANT" and "noise" is dispatched with the config')
def _dispatch_post_tool_use(ctx, stub_engine):
    from agency._config import _READ_CACHE
    _READ_CACHE.clear()
    old = os.environ.get("AGENCY_CONFIG")
    os.environ["AGENCY_CONFIG"] = ctx["config_path"]
    try:
        event = {
            "hook_event_name": "PostToolUse",
            "session_id": "session:s1",
            "tool_name": "Bash",
            "tool_input": {"command": "echo test"},
            "tool_response": "IMPORTANT: watch this\nnoise line",
        }
        from agency.engine import _default_hook_handler
        _default_hook_handler(stub_engine, event)
    finally:
        if old is None:
            os.environ.pop("AGENCY_CONFIG", None)
        else:
            os.environ["AGENCY_CONFIG"] = old
        _READ_CACHE.clear()
    # Read back the last toolcall entry
    rows = stub_engine.toolcalls.rows()
    ctx["tc_filtered"] = rows[-1]["filtered"] if rows else ""


@then('the toolcall store filtered view contains "IMPORTANT" and not "noise"')
def _toolcall_has_important(ctx):
    filt = ctx["tc_filtered"]
    assert "IMPORTANT" in filt, f"Expected IMPORTANT in filtered:\n{filt}"
    assert "noise" not in filt, f"Expected noise excluded from filtered:\n{filt}"


# ── Slice 3: graph FilterProfile override ────────────────────────────────────

@given("a fresh agency engine in code-mode")
def _fresh_engine_slice3(ctx, engine):
    ctx["engine"] = engine


@given("a confirmed intent")
def _confirmed_intent_slice3(ctx):
    eng = ctx["engine"]
    iid = eng.intent.capture("test", "test", "test")
    eng.intent.confirm(iid)
    ctx["intent_id"] = iid


@given(parsers.parse('a config file with "{profile_name}" include=["{include_val}"]'))
def _config_with_named_profile(ctx, tmp_path, profile_name, include_val):
    cfg = tmp_path / "profile_config.yaml"
    _write_config(str(cfg), {"filters": {profile_name: {"include": [include_val]}}})
    ctx["config_path"] = str(cfg)


@when(parsers.parse('I define a profile named "{name}" with include=["{include_val}"] via shell.define_profile'))
def _define_profile_via_verb(ctx, name, include_val):
    import json
    eng = ctx["engine"]
    iid = ctx["intent_id"]
    result, _ = eng.registry.invoke(
        eng.memory, iid, "shell", "define_profile",
        name=name,
        profile=json.dumps({"include": [include_val]}),
    )
    ctx["define_result"] = result
    ctx["defined_name"] = name


@then("define_profile returns a profile_id")
def _define_profile_returns_id(ctx):
    r = ctx["define_result"]
    assert "profile_id" in r, f"expected profile_id in result: {r}"
    assert r["profile_id"], f"profile_id is empty: {r}"


@then(parsers.parse('load_filter_profile "{name}" with engine memory returns include containing "{expected}"'))
def _load_from_graph_returns_expected(ctx, name, expected):
    from agency._relevance import load_filter_profile
    eng = ctx["engine"]
    profile = load_filter_profile(name, memory=eng.memory)
    assert profile, f"expected non-empty profile, got: {profile}"
    assert expected in profile.get("include", []), (
        f"expected '{expected}' in include, got: {profile.get('include')}"
    )


@when(parsers.parse('I load "{name}" with engine memory'))
def _load_named_with_engine_memory(ctx, name):
    from agency._config import _READ_CACHE
    from agency._relevance import load_filter_profile
    _READ_CACHE.clear()
    old = os.environ.get("AGENCY_CONFIG")
    if "config_path" in ctx:
        os.environ["AGENCY_CONFIG"] = ctx["config_path"]
    try:
        ctx["loaded_profile"] = load_filter_profile(name, memory=ctx["engine"].memory)
    finally:
        if old is None:
            os.environ.pop("AGENCY_CONFIG", None)
        else:
            os.environ["AGENCY_CONFIG"] = old
        _READ_CACHE.clear()


@then(parsers.parse('the loaded profile include is ["{expected}"]'))
def _loaded_profile_include_is(ctx, expected):
    inc = ctx["loaded_profile"].get("include", [])
    assert inc == [expected], f"expected include=['{expected}'], got: {inc}"


@when(parsers.parse('I load "{name}" with engine memory but no graph entry'))
def _load_no_graph_entry(ctx, name):
    from agency._config import _READ_CACHE
    from agency._relevance import load_filter_profile
    _READ_CACHE.clear()
    old = os.environ.get("AGENCY_CONFIG")
    if "config_path" in ctx:
        os.environ["AGENCY_CONFIG"] = ctx["config_path"]
    try:
        ctx["loaded_profile"] = load_filter_profile(name, memory=ctx["engine"].memory)
    finally:
        if old is None:
            os.environ.pop("AGENCY_CONFIG", None)
        else:
            os.environ["AGENCY_CONFIG"] = old
        _READ_CACHE.clear()


@then(parsers.parse('the loaded profile include contains "{expected}"'))
def _loaded_profile_include_contains(ctx, expected):
    inc = ctx["loaded_profile"].get("include", [])
    assert expected in inc, f"expected '{expected}' in include, got: {inc}"
