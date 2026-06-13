"""Acceptance — engine substrate: monitor, wire unwrap, lifespan, typed shapes,
ToolResult, branch.commit_smart, develop.estimate (Spec 012/019/021/046/059/171/175/176).

Converted from: test_engine_lifespan, test_engine_monitor, test_engine_unwrap_contract,
test_engine_brief_descriptions, test_micro_extensions_046, test_toolresult_convenience,
test_typed_shapes_wave1, test_typed_shapes_wave1_part2, test_typed_shapes_wave3.

Dropped (implementation / structural / not observable behaviour):
- test_monitor_event_json_roundtrip: already covered as "MonitorEvent serializes"
  in this suite.
- test_emit_autofills_ts_when_zero: internal timestamp auto-fill; not a wire
  behaviour.
- test_atomic_budget_holds_after_json_escaping: internal byte-counting of the
  POSIX write guarantee; covered by the "truncates to 4096 bytes" scenario.
- test_resolve_path_sibling_of_db: internal path resolution; covered by "prefer
  explicit then env" scenario.
- test_engine_owns_monitor / test_capability_context_emit_monitor_autofills /
  test_emit_monitor_noop_without_engine: internal wiring; the observable
  behaviour (events appear in the log file) is covered.
- All typed-shape FIELD / attribute introspection tests (wave1 / wave1_part2 /
  wave3): typed-shape construction invariants are implementation detail of the
  dataclass validators; we keep only the construction-rejection (ValueError)
  behaviours since those are observable contracts.
- test_guard_typed_shape / test_capability_row_typed_shape / etc. field reads:
  structural dataclass attribute access — not observable behaviour.
- test_build_mcp_passes_lifespan_to_fastmcp: asserts on `mcp._lifespan` private
  attribute vs FastMCP's `default_lifespan`; implementation detail.
- test_lifespan_is_idempotent_across_re_entry: tests a re-entry edge case that
  is explicitly documented as shouldn't happen in real usage — not a wire contract.
- test_verbs_reach_watcher_through_engine_after_lifespan_enter: deep e2e through
  private CapabilityContext.engine path; watcher reachability is covered by the
  lifespan attach scenario.
- Codes canonical string tests: string literals (Codes.UNSUPPORTED == "unsupported")
  are frozen-snapshot assertions on internal constants (CLAUDE.md rule 8 violation).
- test_registry_invoke_preserves_caller_supplied_trace_id: tests a CapabilityContext
  raw fn call path — internal wiring not reachable via the wire.
- wave3 typed-shape tests (JudgeVerdict / NarrativeSection / ChainHint / etc.):
  those shapes are domain-specific to research/novel capabilities and are covered
  (or will be) in those capability acceptance suites.
- FragmentVerdict / MigrationVerdict / RefFinding / DeriveStatus typed shapes:
  book-keeping data classes, not engine wire behaviour.
- test_micro_extensions_closure verdicts.json structural checks: JSON file layout
  is structural, not behaviour.
"""
from __future__ import annotations

import asyncio
import json
import tempfile
import time

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from agency.engine import Engine
from agency._monitor import MonitorEmitter, MonitorEvent
from agency.toolresult import Codes, ToolResult, TypedError
from agency.capability import CapabilityBase, OntologyExtension, verb
from agency._typed_shapes_wave1 import (
    CapabilityRow, CommandFile, GuardFinding, InstallSurface, IntentCapture,
)

scenarios("features/engine.feature")


# ── shared Given override ─────────────────────────────────────────────────────

@given("a fresh agency engine in code-mode", target_fixture="eng")
def _fresh_eng():
    return Engine(tempfile.mktemp(suffix=".db"))


@given("a fresh engine with confirmed intent for wire tests",
       target_fixture="eng_iid")
def _eng_iid():
    e = Engine(tempfile.mktemp(suffix=".db"))
    iid = e.intent.capture_and_confirm("test engine", "behaviour", "verified",
                                        owner="user")
    return e, iid


# ── when — MonitorEvent ───────────────────────────────────────────────────────

@when("I create a MonitorEvent and serialize it",
      target_fixture="monitor_event_pair")
def _make_event():
    ev = MonitorEvent(
        source="jules", kind="state_transition",
        message="session abc -> COMPLETED", intent_id="intent:1", ts=123.0,
    )
    line = ev.to_json()
    return ev, line


@then("the JSON line contains no newlines")
def _no_newlines(monitor_event_pair):
    _, line = monitor_event_pair
    assert "\n" not in line


@then("deserializing it returns an equal event")
def _roundtrip(monitor_event_pair):
    ev, line = monitor_event_pair
    assert MonitorEvent.from_json(line) == ev


# ── when — emitter JSONL ──────────────────────────────────────────────────────

@when("I emit two monitor events to a log file",
      target_fixture="emitter_log")
def _emit_two(tmp_path):
    log = tmp_path / "monitor.log"
    em = MonitorEmitter(str(log))
    em.emit(MonitorEvent("engine", "info", "first"))
    em.emit(MonitorEvent("delegate", "fanout_complete", "second"))
    return log


@then("the log file contains exactly two lines")
def _two_lines(emitter_log):
    lines = emitter_log.read_text().splitlines()
    assert len(lines) == 2


@then("the first line has the first event's message")
def _first_message(emitter_log):
    lines = emitter_log.read_text().splitlines()
    assert json.loads(lines[0])["message"] == "first"


@then("the second line has the second event's kind")
def _second_kind(emitter_log):
    lines = emitter_log.read_text().splitlines()
    assert json.loads(lines[1])["kind"] == "fanout_complete"


# ── when — rotation ───────────────────────────────────────────────────────────

@when("I emit many events to a log with a small rotation threshold",
      target_fixture="rotation_log")
def _rotation(tmp_path):
    log = tmp_path / "monitor.log"
    em = MonitorEmitter(str(log), rotate_bytes=200)
    (tmp_path / "monitor.log.1").write_text("OLD")
    for i in range(50):
        em.emit(MonitorEvent("engine", "info", f"event-{i}-padding-padding"))
    return tmp_path, log


@then("the .1 backup file is created")
def _backup_created(rotation_log):
    tmp_path, _ = rotation_log
    assert (tmp_path / "monitor.log.1").exists()
    assert (tmp_path / "monitor.log.1").read_text() != "OLD"


@then("the live log file stays near the threshold size")
def _log_size(rotation_log):
    _, log = rotation_log
    assert log.stat().st_size < 200 * 4


# ── when — atomic budget ─────────────────────────────────────────────────────

@when("I emit a MonitorEvent with a 10000-character message",
      target_fixture="long_line_log")
def _long_message(tmp_path):
    log = tmp_path / "monitor.log"
    MonitorEmitter(str(log)).emit(MonitorEvent("engine", "info", "M" * 10_000))
    return log


@then("the log line is at most 4096 bytes")
def _atomic_budget(long_line_log):
    line = long_line_log.read_text().splitlines()[0]
    assert len(line.encode("utf-8")) <= 4096


@then("the line is still valid JSON")
def _valid_json(long_line_log):
    line = long_line_log.read_text().splitlines()[0]
    parsed = json.loads(line)
    assert parsed["source"] == "engine"


# ── when — path resolution ────────────────────────────────────────────────────

@when("I resolve the monitor log path with an explicit path set",
      target_fixture="explicit_path_result")
def _explicit_path(tmp_path, monkeypatch):
    from agency._monitor import resolve_monitor_log_path
    monkeypatch.setenv("AGENCY_MONITOR_LOG", str(tmp_path / "from-env.log"))
    explicit = str(tmp_path / "x.log")
    return explicit, resolve_monitor_log_path(explicit=explicit)


@then("the result is the explicit path")
def _result_explicit(explicit_path_result):
    explicit, result = explicit_path_result
    assert result == explicit


@when("I resolve with only AGENCY_MONITOR_LOG set",
      target_fixture="env_path_result")
def _env_path(tmp_path, monkeypatch):
    from agency._monitor import resolve_monitor_log_path
    env_path = str(tmp_path / "from-env.log")
    monkeypatch.setenv("AGENCY_MONITOR_LOG", env_path)
    return env_path, resolve_monitor_log_path()


@then("the result is from the env var")
def _result_env(env_path_result):
    env_path, result = env_path_result
    assert result == env_path


# ── then — engine owns monitor ────────────────────────────────────────────────

@then("the engine has a monitor attribute that is a MonitorEmitter")
def _engine_monitor(eng):
    assert isinstance(eng.monitor, MonitorEmitter)


# ── when — wire unwrap ────────────────────────────────────────────────────────

async def _wire_call(eng: Engine, tool: str, **kwargs):
    mcp = eng.build_mcp(codemode=True)
    res = await mcp.call_tool(tool, kwargs)
    sc = res.structured_content or res.data
    return sc


@when("I call reflect.recall via the wire", target_fixture="wire_recall")
def _wire_recall(eng_iid):
    eng, iid = eng_iid
    # Seed one note first
    eng.registry.invoke(eng.memory, iid, "reflect", "note",
                         agent_id="agent:test", scope="observation", text="x")
    return asyncio.run(_wire_call(
        eng, "capability_reflect_recall", intent_id=iid, scope=""))


@then("the wire result has a result key containing a list")
def _recall_shape(wire_recall):
    assert "result" in wire_recall
    assert isinstance(wire_recall["result"], list)


@when("I call reflect.note via the wire", target_fixture="wire_note")
def _wire_note(eng_iid):
    eng, iid = eng_iid
    return asyncio.run(_wire_call(
        eng, "capability_reflect_note", intent_id=iid,
        scope="observation", text="hello"))


@then("the wire result has a result key containing a string starting with reflection:")
def _note_shape(wire_note):
    assert "result" in wire_note
    assert isinstance(wire_note["result"], str)
    assert wire_note["result"].startswith("reflection:")


@when("I call dogfood.note via the wire", target_fixture="wire_dogfood_note")
def _wire_dogfood_note(eng_iid):
    eng, iid = eng_iid
    return asyncio.run(_wire_call(
        eng, "capability_dogfood_note", intent_id=iid,
        observation="x", plan_slug="019"))


@then("the wire result has reflection_id and plan_slug keys")
def _dogfood_note_shape(wire_dogfood_note):
    assert "reflection_id" in wire_dogfood_note
    assert "plan_slug" in wire_dogfood_note


@then("the wire result does not have a result key")
def _no_result_key(wire_dogfood_note):
    assert "result" not in wire_dogfood_note


# ── when — lifespan ──────────────────────────────────────────────────────────

@when("I build the MCP server", target_fixture="mcp_server")
def _build_mcp(eng):
    return eng.build_mcp(codemode=False), eng


@when("I enter the engine lifespan", target_fixture="lifespan_ctx")
def _enter_lifespan(eng):
    return eng


@when("I enter and then exit the engine lifespan",
      target_fixture="post_lifespan")
def _exit_lifespan(eng):
    async def _run():
        lifespan = eng._make_lifespan()
        async with lifespan(server=None):
            task = eng._jules_watcher._task
        await asyncio.sleep(0)
        return task
    return asyncio.run(_run())


@then("the lifespan is not the FastMCP default no-op lifespan")
def _custom_lifespan(mcp_server):
    from fastmcp.server.server import default_lifespan
    mcp, _ = mcp_server
    assert mcp._lifespan is not default_lifespan


@then("_jules_watcher is attached to the engine")
def _watcher_attached(lifespan_ctx):
    eng = lifespan_ctx

    async def _run():
        lifespan = eng._make_lifespan()
        async with lifespan(server=None):
            return hasattr(eng, "_jules_watcher") and eng._jules_watcher is not None
    assert asyncio.run(_run())


@then("the watcher task is running")
def _watcher_running(lifespan_ctx):
    eng = lifespan_ctx

    async def _run():
        lifespan = eng._make_lifespan()
        async with lifespan(server=None):
            return not eng._jules_watcher._task.done()
    assert asyncio.run(_run())


@then("the watcher task is done after exit")
def _watcher_done(post_lifespan):
    assert post_lifespan.done()


# ── when — ToolResult ────────────────────────────────────────────────────────

@when("I construct a ToolResult.success with data and warnings",
      target_fixture="success_result")
def _success():
    return ToolResult.success(data={"x": 1}, warnings=["w"])


@then("ok is True and data matches and warnings are set and error is None")
def _success_shape(success_result):
    assert success_result.ok is True
    assert success_result.data == {"x": 1}
    assert success_result.warnings == ["w"]
    assert success_result.error is None


@when("I construct a ToolResult.failure with UNSUPPORTED code",
      target_fixture="failure_result")
def _failure():
    return ToolResult.failure(Codes.UNSUPPORTED, "nope")


@then("ok is False and error.code is unsupported and trace_id is empty")
def _failure_shape(failure_result):
    assert failure_result.ok is False
    assert isinstance(failure_result.error, TypedError)
    assert failure_result.error.code == "unsupported"
    assert failure_result.error.trace_id == ""


# ── when — Registry.invoke stamps trace_id ───────────────────────────────────

class _FailCap(CapabilityBase):
    name = "spec059_accept_fail"
    home = "memory"
    ontology = OntologyExtension(nodes={})

    @verb(role="transform")
    def boom(self, why: str = "no reason") -> ToolResult:
        """Return a typed failure without trace_id.

        Inputs: why (str).
        Returns: <None>.
        chain_next: terminal.
        """
        return ToolResult.failure(Codes.UNSUPPORTED, f"fail: {why}")


@given("a fresh engine with a failure capability and confirmed intent",
       target_fixture="fail_setup")
def _fail_setup():
    e = Engine(tempfile.mktemp(suffix=".db"))
    e.registry.register(_FailCap.as_capability())
    iid = e.intent.capture_and_confirm("test 059", "trace_id stamping", "x", owner="user")
    return e, iid


@when("the verb is invoked via the registry", target_fixture="invocation_node")
def _invoke_boom(fail_setup):
    fail_engine, fail_iid = fail_setup
    _r, inv = fail_engine.registry.invoke(
        fail_engine.memory, fail_iid, "spec059_accept_fail", "boom",
        agent_id="agent:test", why="testing")
    return fail_engine.memory.recall(inv)


@then("the Invocation node has outcome failed")
def _outcome_failed(invocation_node):
    assert invocation_node is not None
    assert invocation_node.get("outcome") == "failed"


@then("the Invocation carries the error code")
def _error_code(invocation_node):
    assert "unsupported" in (invocation_node.get("error") or "")


# ── when — GuardFinding typed shape ──────────────────────────────────────────

@when("I create a GuardFinding with empty verb_id",
      target_fixture="shape_error")
def _guard_empty_verb():
    try:
        GuardFinding(verb_id="", param_name="p", expected_label="L",
                     severity="error")
        return None
    except ValueError as e:
        return e


@when("I create a GuardFinding with severity bogus",
      target_fixture="shape_error")
def _guard_bad_severity():
    try:
        GuardFinding(verb_id="x", param_name="p", expected_label="L",
                     severity="bogus")
        return None
    except ValueError as e:
        return e


@when("I create a CapabilityRow with verb_count -1",
      target_fixture="shape_error")
def _neg_verb_count():
    try:
        CapabilityRow(name="x", verb_count=-1, description="d")
        return None
    except ValueError as e:
        return e


@when("I create an IntentCapture with source bogus",
      target_fixture="shape_error")
def _bad_source():
    try:
        IntentCapture(intent_id="x", captured_at="t", source="bogus")
        return None
    except ValueError as e:
        return e


@when("I create an IntentCapture with turns -1",
      target_fixture="shape_error")
def _neg_turns():
    try:
        IntentCapture(intent_id="x", captured_at="t", source="manual", turns=-1)
        return None
    except ValueError as e:
        return e


@then("a ValueError is raised")
def _value_error(shape_error):
    assert isinstance(shape_error, (ValueError, Exception))


# ── when — branch.commit_smart ───────────────────────────────────────────────

@given("a fresh engine with micro-extension intent",
       target_fixture="micro_eng_iid")
def _micro_eng_iid():
    e = Engine(tempfile.mktemp(suffix=".db"))
    iid = e.intent.capture("dev", "a change", "done")
    e.intent.confirm(iid)
    return e, iid


def _call(e, iid, cap, verb_name, **kw):
    res, _ = e.registry.invoke(e.memory, iid, cap, verb_name, **kw)
    return res["result"] if isinstance(res, dict) and "result" in res else res


@when("I invoke branch.commit_smart with summary Add the parser and path agency/capabilities/analyze/_main.py",
      target_fixture="commit_result")
def _commit_smart(micro_eng_iid):
    e, iid = micro_eng_iid
    return _call(e, iid, "branch", "commit_smart",
                 summary="Add the parser",
                 paths="agency/capabilities/analyze/_main.py")


@then("the commit message is feat(analyze): add the parser")
def _commit_message(commit_result):
    assert commit_result["message"] == "feat(analyze): add the parser"


@then("type is feat and scope is analyze")
def _commit_type_scope(commit_result):
    assert commit_result["type"] == "feat"
    assert commit_result["scope"] == "analyze"


# ── when — develop.estimate ──────────────────────────────────────────────────

@when("I estimate a small change at loc 20 files 1 tests 1",
      target_fixture="small_estimate")
def _small_estimate(micro_eng_iid):
    e, iid = micro_eng_iid
    return _call(e, iid, "develop", "estimate", loc=20, files=1, tests=1)


@when("I estimate a large change at loc 800 files 12 tests 10",
      target_fixture="large_estimate")
def _large_estimate(micro_eng_iid):
    e, iid = micro_eng_iid
    return _call(e, iid, "develop", "estimate", loc=800, files=12, tests=10)


@then("the small change has bucket S and the large change has bucket XL")
def _buckets(small_estimate, large_estimate):
    assert small_estimate["bucket"] == "S"
    assert large_estimate["bucket"] == "XL"


@then("the large change has more points than the small change")
def _monotonic(small_estimate, large_estimate):
    assert large_estimate["points"] > small_estimate["points"]


@then("the same inputs yield the same estimate")
def _deterministic(micro_eng_iid, small_estimate):
    e, iid = micro_eng_iid
    repeat = _call(e, iid, "develop", "estimate", loc=20, files=1, tests=1)
    assert repeat == small_estimate
