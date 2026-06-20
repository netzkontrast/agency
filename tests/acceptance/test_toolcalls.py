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


@when("a Bash PostToolUse with an unknown command and 50-line output is captured")
def _bash_capture(ctx):
    ctx["engine"].dispatch_hook({
        "hook_event_name": "PostToolUse", "session_id": "s", "tool_name": "Bash",
        "tool_input": {"command": "custom-script.sh --run"},
        "tool_response": "line\n" * 50})


@then("the captured Bash row carries a shell-filtered view of the command")
def _filtered_view(ctx):
    rows = ctx["engine"].toolcalls.rows(where="tool='Bash'")
    assert rows, "the Bash call must be captured"
    filtered = rows[-1]["filtered"]
    assert filtered.startswith("$ custom-script.sh"), filtered
    # the filter is a BOUNDED view (head:20 for unknown commands), not the full 50 lines
    assert 0 < filtered.count("line") <= 20, filtered.count("line")


@then("the full 50-line output is preserved in the row alongside the filtered view")
def _full_output(ctx):
    rows = ctx["engine"].toolcalls.rows(where="tool='Bash'")
    # the FULL output lives in output_json (no-truncate), all 50 lines
    assert rows[-1]["output_json"].count("line") == 50, rows[-1]["output_json"].count("line")


# ── S4 — the export ───────────────────────────────────────────────────────────

@when("I call toolcalls.export with apply", target_fixture="result")
def _export(ctx):
    return _call(ctx, "export", apply=True)


@then("the export ranks the repeated Bash call first in its top list")
def _export_top(result):
    top = result["top"]
    assert top and top[0]["tool"] == "Bash" and top[0]["calls"] == 3, top


@then("the export proposes a new-spec suggestion for the repeated command")
def _export_suggestion(result):
    assert result["suggestions"], result
    assert any("template" in s["suggestion"] for s in result["suggestions"]), \
        result["suggestions"]


@then("a ToolcallExport artefact is recorded in the durable graph")
def _export_artefact(result, ctx):
    assert result["export_id"], result
    assert ctx["engine"].memory.recall(result["export_id"]) is not None


# ── Spec 337 — per-tool output filters ────────────────────────────────────────

@when("a Bash pytest PostToolUse with 200 dots then a failure summary is captured")
def _pytest_capture(ctx):
    ctx["engine"].dispatch_hook({
        "hook_event_name": "PostToolUse", "session_id": "s", "tool_name": "Bash",
        "tool_input": {"command": "python -m pytest tests/ -q"},
        "tool_response": "." * 200 + "\nFAILED test_foo.py::test_a - AssertionError\n"
                         "3 failed, 197 passed in 12.3s"})


@then("the pytest filtered view contains the failure summary")
def _pytest_has_summary(ctx):
    rows = ctx["engine"].toolcalls.rows(where="tool='Bash'")
    assert rows, "the pytest call must be captured"
    filtered = rows[-1]["filtered"]
    assert "failed" in filtered.lower() or "FAILED" in filtered, filtered


@then("the pytest filtered view does not contain the dot progress stream")
def _pytest_no_dots(ctx):
    rows = ctx["engine"].toolcalls.rows(where="tool='Bash'")
    filtered = rows[-1]["filtered"]
    assert "." * 10 not in filtered, "dot progress stream should be stripped"


@then("the full pytest output is retained verbatim in output_json")
def _pytest_full_output(ctx):
    rows = ctx["engine"].toolcalls.rows(where="tool='Bash'")
    output_json = rows[-1]["output_json"]
    assert "." * 100 in output_json, "dot stream must be in output_json"


@when("a Read PostToolUse for a 500-line file is captured")
def _read_capture(ctx):
    ctx["engine"].dispatch_hook({
        "hook_event_name": "PostToolUse", "session_id": "s", "tool_name": "Read",
        "tool_input": {"file_path": "/home/user/agency/big_file.py"},
        "tool_response": "content line X\n" * 500})


@then("the read filtered view contains the file path and line count")
def _read_has_locator(ctx):
    rows = ctx["engine"].toolcalls.rows(where="tool='Read'")
    assert rows, "the Read call must be captured"
    filtered = rows[-1]["filtered"]
    assert "big_file.py" in filtered, filtered
    assert "500" in filtered, filtered


@then("the read filtered view does not contain the file body")
def _read_no_body(ctx):
    rows = ctx["engine"].toolcalls.rows(where="tool='Read'")
    filtered = rows[-1]["filtered"]
    assert "content line X" not in filtered, "file body must not appear in locator view"


@then("the full file body is retained verbatim in output_json")
def _read_full_body(ctx):
    rows = ctx["engine"].toolcalls.rows(where="tool='Read'")
    output_json = rows[-1]["output_json"]
    assert "content line X" in output_json, "full file body must be in output_json"


@then("the fallback filtered view is bounded to 20 lines")
def _fallback_bounded(ctx):
    rows = ctx["engine"].toolcalls.rows(where="tool='Bash'")
    assert rows, "the Bash call must be captured"
    filtered = rows[-1]["filtered"]
    assert 0 < filtered.count("line") <= 20, filtered.count("line")


@then("the full output is retained verbatim")
def _fallback_full(ctx):
    rows = ctx["engine"].toolcalls.rows(where="tool='Bash'")
    output_json = rows[-1]["output_json"]
    assert output_json.count("line") == 50, output_json.count("line")


@when("a mcp__github__pull_request_read PostToolUse with a rich envelope is captured")
def _github_capture(ctx):
    import json
    envelope = {
        "number": 42, "state": "open", "mergeable_state": "clean",
        "title": "Add new feature", "body": "A very long PR description " * 100,
        "labels": [{"name": "bug"}, {"name": "enhancement"}],
        "requested_reviewers": [{"login": "alice"}, {"login": "bob"}],
        "head": {"sha": "abc123def456", "ref": "feature/foo"},
        "base": {"ref": "main"},
    }
    ctx["engine"].dispatch_hook({
        "hook_event_name": "PostToolUse", "session_id": "s",
        "tool_name": "mcp__github__pull_request_read",
        "tool_input": {"owner": "org", "repo": "repo", "pull_number": 42},
        "tool_response": json.dumps(envelope)})


@then("the github filtered view names the key decision fields")
def _github_has_fields(ctx):
    rows = ctx["engine"].toolcalls.rows(where="tool='mcp__github__pull_request_read'")
    assert rows, "the github call must be captured"
    filtered = rows[-1]["filtered"]
    assert "42" in filtered or "number" in filtered.lower(), filtered
    assert "open" in filtered or "state" in filtered.lower(), filtered


@then("the github filtered view omits the envelope bulk")
def _github_no_bulk(ctx):
    rows = ctx["engine"].toolcalls.rows(where="tool='mcp__github__pull_request_read'")
    filtered = rows[-1]["filtered"]
    assert "A very long PR description" not in filtered, "long body should be stripped"


@then("the full envelope is retained verbatim in output_json")
def _github_full_envelope(ctx):
    rows = ctx["engine"].toolcalls.rows(where="tool='mcp__github__pull_request_read'")
    output_json = rows[-1]["output_json"]
    assert "A very long PR description" in output_json, "full body must be in output_json"


@when("I call toolcalls.export")
def _export_plain(ctx):
    result = _call(ctx, "export", apply=False)
    ctx["_export_result"] = result


@then("the export top list uses the locator view for the Read call")
def _export_uses_locator(ctx):
    result = ctx["_export_result"]
    top = result.get("top", [])
    read_rows = [r for r in top if r.get("tool") == "Read"]
    assert read_rows, f"Read should appear in top calls; got tools: {[r['tool'] for r in top]}"
    sample = read_rows[0].get("sample", "") or read_rows[0].get("shape", "")
    # the locator view contains the path, not the file body
    assert "big_file.py" in sample or "500" in sample or "sha16" in sample, sample
