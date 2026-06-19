"""Acceptance — the toolcalls capability (Spec 336 S2).

The clear, discoverable MCP surface over the ephemeral tool-call store: stats,
top (frequency ranking), and prune. Capture lands via the hook reroute; these
verbs read/manage it.
"""
from __future__ import annotations

import pytest
from pytest_bdd import given, scenarios, then, when

from agency.engine import Engine

scenarios("features/toolcalls.feature")


@pytest.fixture
def tc(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENCY_TOOLCALLS_DB", ":memory:")
    monkeypatch.delenv("AGENCY_INTENT", raising=False)
    e = Engine(":memory:")
    iid = e.intent.capture_and_confirm("toolcalls test", "verify the verbs", "scenarios pass")
    yield {"engine": e, "intent": iid}
    e.memory.close()


@given("an engine with several captured tool calls", target_fixture="ctx")
def _captured(tc):
    e = tc["engine"]
    for _ in range(3):                                   # the same Bash call ×3
        e.dispatch_hook({"hook_event_name": "PostToolUse", "session_id": "s",
                         "tool_name": "Bash", "tool_input": {"command": "ls"}})
    e.dispatch_hook({"hook_event_name": "PostToolUse", "session_id": "s",
                     "tool_name": "Read", "tool_input": {"file_path": "/x"}})
    return tc


def _call(ctx, verb, **kw):
    e = ctx["engine"]
    r, _ = e.registry.invoke(e.memory, ctx["intent"], "toolcalls", verb,
                             agent_id="agent:test", **kw)
    return r


@when("I call toolcalls.stats", target_fixture="result")
def _stats(ctx):
    return _call(ctx, "stats")


@when("I call toolcalls.top", target_fixture="result")
def _top(ctx):
    return _call(ctx, "top")


@when("I call toolcalls.prune", target_fixture="result")
def _prune(ctx):
    return _call(ctx, "prune")


@then("the stats total matches the captured count")
def _total(result):
    assert result["total"] == 4, result


@then("the by-tool breakdown names Bash three times")
def _bytool(result):
    assert result["by_tool"].get("Bash") == 3, result


@then("the top list ranks the most-repeated call first")
def _ranked(result):
    top = result["top"]
    assert top, result
    assert top[0]["tool"] == "Bash" and top[0]["calls"] == 3, top


@then("the store is emptied")
def _empty(result, ctx):
    assert result["pruned"] == 4, result
    assert ctx["engine"].toolcalls.count() == 0


# ── S3 — the mandatory shell capture-filter ───────────────────────────────────

@given("a fresh engine", target_fixture="ctx")
def _fresh(tc):
    return tc


@when("a Bash PostToolUse with a 50-line output is captured")
def _bash_capture(ctx):
    ctx["engine"].dispatch_hook({
        "hook_event_name": "PostToolUse", "session_id": "s", "tool_name": "Bash",
        "tool_input": {"command": "ls -la /tmp"},
        "tool_response": "line\n" * 50})


@then("the captured Bash row carries a shell-filtered view of the command")
def _filtered_view(ctx):
    rows = ctx["engine"].toolcalls.rows(where="tool='Bash'")
    assert rows, "the Bash call must be captured"
    filtered = rows[-1]["filtered"]
    assert filtered.startswith("$ ls -la /tmp"), filtered
    # the filter is a BOUNDED view (head:20), not the full 50 lines
    assert 0 < filtered.count("line") <= 20, filtered.count("line")


@then("the full 50-line output is preserved in the row alongside the filtered view")
def _full_output(ctx):
    rows = ctx["engine"].toolcalls.rows(where="tool='Bash'")
    # the FULL output lives in output_json (no-truncate), all 50 lines
    assert rows[-1]["output_json"].count("line") == 50, rows[-1]["output_json"].count("line")
