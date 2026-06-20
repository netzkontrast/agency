"""Acceptance — hook dispatch, BoundaryUse, foreign-hook install (Spec 076 / 195 / 280).

Converted from tests/test_hooks_dispatch.py, tests/test_hook_event_replay.py,
tests/test_hooks_install.py.

Dropped (implementation / structural / not observable behaviour):
- test_cli_hook_reads_event_from_stdin: tests a CLI subcommand entry point via
  subprocess stdin — integration test of the shell layer, not wire behaviour.
- test_install_emits_unified_dispatch_hooks: covered by test_install.py
  "hooks/hooks.json wires PostToolUse UserPromptSubmit and Stop" scenario.
- test_hooks_json_has_correct_async_flags: covered by the async-doctrine
  scenario in this file.
- test_register_hook_handler_overrides_default: tests an internal extension
  point (register_hook_handler) by injecting a Python lambda — implementation
  detail of the open-set handler registry.
- Replay + overflow slice scenarios (test_hook_event_replay): dogfood.replay_events
  and dogfood.recall_overflow_slice are already covered by test_dogfood.py in
  the acceptance suite or planned for that module.
- test_patch_raises_on_invalid_json / test_check_install_requires_run_hook_cmd /
  test_wrap_uses_agency_hook_wrap_cli_subcommand / test_hook_wrap_cli_* and
  test_install_patch_only_skips_plugin_regen: CLI subprocess side-effects; the
  observable behaviours (merge idempotence, wrap records _wrapped_from, etc.) are
  covered by the pure-library scenarios.
- test_hooks_json_has_correct_async_flags: covered via ASYNC_BY_EVENT table check.
"""
from __future__ import annotations

import asyncio
import json
import os
import tempfile

import pytest
from fastmcp import Client
from pytest_bdd import given, scenarios, then, when

from agency.engine import Engine
from agency._hooks import (
    ASYNC_BY_EVENT,
    CANONICAL_SETTINGS_PATCH,
    ForeignHook,
    apply_foreign_wraps,
    check_install,
    detect_foreign_hooks,
    merge_settings,
    wrap_foreign_hook,
)

scenarios("features/hooks.feature")


# ── helpers ───────────────────────────────────────────────────────────────────

def _call_wire(eng: Engine, tool: str, args: dict) -> dict:
    mcp = eng.build_mcp(codemode=False)

    async def _run():
        r = await mcp.call_tool(tool, args)
        sc = r.structured_content
        if isinstance(sc, dict):
            return sc.get("result", sc)
        return sc

    return asyncio.run(_run())


# ── shared Given override ─────────────────────────────────────────────────────

@given("a fresh agency engine in code-mode", target_fixture="hook_engine")
def _fresh_hook_engine(tmp_path, monkeypatch):
    # Isolate the Spec 336 tool-call store PER TEST (mirrors the conftest `engine`
    # fixture). Without this, every mktemp graph db shares one dir (/tmp), so the
    # derived toolcalls.db (resolve_path: ".agency/toolcalls.db" beside the graph
    # db) is ONE shared, persistent file accumulating capture across tests + runs.
    # That makes the `rows[-1]` store assertions order-dependent in a cross-file run
    # — a PreToolUse from another test leaks in as the latest row.
    monkeypatch.setenv("AGENCY_TOOLCALLS_DB", str(tmp_path / "toolcalls.db"))
    e = Engine(tempfile.mktemp(suffix=".db"))
    return e


# ── given — intent / env ──────────────────────────────────────────────────────

@given("a confirmed intent set as AGENCY_INTENT",
       target_fixture="active_intent")
def _active_intent(hook_engine, monkeypatch):
    iid = hook_engine.intent.capture("hook prov", "events serve intent", "OBSERVED")
    hook_engine.intent.confirm(iid)
    monkeypatch.setenv("AGENCY_INTENT", iid)
    return iid


@given("no AGENCY_INTENT is set")
def _no_intent(monkeypatch):
    monkeypatch.delenv("AGENCY_INTENT", raising=False)


# ── when — dispatch_hook ──────────────────────────────────────────────────────

@when("a UserPromptSubmit hook event fires with session s1",
      target_fixture="hook_out")
def _userprompt(hook_engine):
    return hook_engine.dispatch_hook(
        {"hook_event_name": "UserPromptSubmit", "session_id": "s1",
         "prompt": "do the thing"})


@when("a PostToolUse hook event fires with a 500-line Bash command",
      target_fixture="hook_out")
def _posttooluse(hook_engine):
    return hook_engine.dispatch_hook(
        {"hook_event_name": "PostToolUse", "session_id": "s1",
         "tool_name": "Bash", "tool_input": {"command": "x\n" * 500}})


@when("a hook event fires without a hook_event_name",
      target_fixture="hook_out")
def _missing_name(hook_engine):
    return hook_engine.dispatch_hook({"session_id": "s1"})


@when("a Notification hook event fires", target_fixture="hook_out")
def _notification(hook_engine):
    return hook_engine.dispatch_hook(
        {"hook_event_name": "Notification", "session_id": "s1"})


@when("a PreToolUse hook event fires with tool Edit",
      target_fixture="hook_out")
def _pretooluse_edit(hook_engine, active_intent):
    return hook_engine.dispatch_hook(
        {"hook_event_name": "PreToolUse", "session_id": "s1",
         "tool_name": "Edit", "tool_input": {}})


@when("a PreToolUse Bash event fires with command git commit -m x",
      target_fixture="hook_out")
def _pretooluse_git_commit(hook_engine, active_intent):
    return hook_engine.dispatch_hook(
        {"hook_event_name": "PreToolUse", "session_id": "s1",
         "tool_name": "Bash", "tool_input": {"command": "git commit -m x"}})


@when("a PreToolUse Bash event fires with command pytest tests/",
      target_fixture="hook_out")
def _pretooluse_pytest(hook_engine, active_intent):
    return hook_engine.dispatch_hook(
        {"hook_event_name": "PreToolUse", "session_id": "s1",
         "tool_name": "Bash", "tool_input": {"command": "pytest tests/"}})


@when("a PreToolUse Edit event fires with file_path Plan/280-foo/spec.md",
      target_fixture="hook_out")
def _pretooluse_spec_edit(hook_engine, active_intent):
    return hook_engine.dispatch_hook(
        {"hook_event_name": "PreToolUse", "session_id": "s1",
         "tool_name": "Edit", "tool_input": {"file_path": "Plan/280-foo/spec.md"}})


@when("a PostToolUse Bash event fires with command git commit -m x",
      target_fixture="hook_out")
def _posttooluse_bash(hook_engine, active_intent):
    return hook_engine.dispatch_hook(
        {"hook_event_name": "PostToolUse", "session_id": "s1",
         "tool_name": "Bash", "tool_input": {"command": "git commit -m x"}})


@when("PreToolUse events fire for Read Grep Glob and WebFetch",
      target_fixture="hook_out")
def _read_only_tools(hook_engine, active_intent):
    for tool in ("Read", "Grep", "Glob", "WebFetch"):
        hook_engine.dispatch_hook(
            {"hook_event_name": "PreToolUse", "session_id": "s1",
             "tool_name": tool, "tool_input": {"file_path": "/x"}})
    return None


@when("a PreToolUse Bash git commit event fires under that intent",
      target_fixture="hook_out")
def _pretooluse_commit_for_moat(hook_engine, active_intent):
    return hook_engine.dispatch_hook(
        {"hook_event_name": "PreToolUse", "session_id": "s1",
         "tool_name": "Bash", "tool_input": {"command": "git commit -m x"}})


@when("I call hook_event via the wire with a SubagentStop event",
      target_fixture="wire_hook_out")
def _wire_hook(hook_engine):
    _call_wire(hook_engine, "hook_event",
               {"event": {"hook_event_name": "SubagentStop", "session_id": "s1"}})
    return hook_engine


# ── then — event recording ────────────────────────────────────────────────────

@then("an Event node with name UserPromptSubmit and session s1 is in the graph")
def _event_userprompt(hook_engine):
    evs = hook_engine.memory.find("Event")
    assert any(e["name"] == "UserPromptSubmit" and e["session"] == "s1" for e in evs)


@then("no Event node for PostToolUse is in the graph")
def _no_posttooluse_event(hook_engine):
    evs = hook_engine.memory.find("Event")
    assert not any(e["name"] == "PostToolUse" for e in evs), \
        "Spec 336 S2 — tool calls go to the ephemeral store, not the durable graph"


@then("the tool-call store holds the FULL 500-line payload")
def _store_payload_full(hook_engine):
    rows = hook_engine.toolcalls.rows(where="phase='post'")
    assert rows, "the PostToolUse call must be captured in the tool-call store"
    payload = rows[-1]["input_json"] + rows[-1]["output_json"]
    # FULL capture (no-truncate policy): every one of the 500 lines survives,
    # uncapped (the value is NOT cut to the old 600-char budget).
    assert payload.count("x\\n") == 500 or payload.count("x") == 500, payload.count("x")
    assert len(payload) > 600


@then("the tool-call store records the active intent")
def _store_records_intent(hook_engine, active_intent):
    rows = hook_engine.toolcalls.rows()
    assert rows, "the tool call must be captured in the store"
    assert any(r["intent"] == active_intent for r in rows), \
        [r["intent"] for r in rows]


@then("the result carries recorded or skipped without raising")
def _recorded_or_skipped(hook_out):
    assert hook_out.get("recorded") is not None or hook_out.get("skipped") is not None


@then("a SubagentStop Event node is in the graph")
def _subagent_stop_event(wire_hook_out):
    evs = wire_hook_out.memory.find("Event")
    assert any(e["name"] == "SubagentStop" for e in evs)


@then("a Notification Event node is in the graph")
def _notification_event(hook_engine):
    evs = hook_engine.memory.find("Event")
    assert any(e["name"] == "Notification" for e in evs)


# ── then — OBSERVED_DURING edge ───────────────────────────────────────────────

@then("an OBSERVED_DURING edge connects the Event to the intent")
def _observed_during(hook_engine, hook_out, active_intent):
    eid = hook_out.get("recorded")
    rows = hook_engine.memory.g.query(
        "MATCH (e:Event)-[:OBSERVED_DURING]->(i:Intent) WHERE e.id=$e AND i.id=$i RETURN i",
        {"e": eid, "i": active_intent})
    assert rows, "event must link OBSERVED_DURING the active intent"


# ── then — BoundaryUse ────────────────────────────────────────────────────────

@then("a BoundaryUse node is recorded")
def _boundary_use_recorded(hook_engine):
    assert len(hook_engine.memory.find("BoundaryUse")) == 1


@then("the verb_shadow is branch.commit_smart")
def _shadow_commit(hook_engine):
    bu = hook_engine.memory.find("BoundaryUse")[0]
    assert bu["verb_shadow"] == "branch.commit_smart"


@then("the BoundaryUse tool is Bash")
def _bu_tool(hook_engine):
    bu = hook_engine.memory.find("BoundaryUse")[0]
    assert bu["tool"] == "Bash"


@then("the verb_shadow is shell.run('pytest')")
def _shadow_test(hook_engine):
    bu = hook_engine.memory.find("BoundaryUse")[0]
    assert bu["verb_shadow"] == "shell.run('pytest')"


@then("the verb_shadow is dogfood.note")
def _shadow_observe(hook_engine):
    bu = hook_engine.memory.find("BoundaryUse")[0]
    assert bu["verb_shadow"] == "dogfood.note"


@then("no BoundaryUse node is created")
def _no_boundary_use(hook_engine):
    assert hook_engine.memory.find("BoundaryUse") == []


@then("the BoundaryUse SERVES the intent")
def _bu_serves(hook_engine, active_intent):
    rows = hook_engine.memory.g.query(
        "MATCH (b:BoundaryUse)-[:SERVES]->(i:Intent) WHERE i.id = $iid RETURN b",
        {"iid": active_intent})
    assert len(rows) == 1


@then("the PreToolUse call is captured in the tool-call store")
def _pretooluse_in_store(hook_engine):
    rows = hook_engine.toolcalls.rows(where="phase='pre'")
    assert rows, "the PreToolUse call must be captured in the tool-call store"
    assert rows[-1]["tool"] in ("Bash", "Edit"), rows[-1]
    assert "Bash" in [r["tool"] for r in rows], rows[-1]


@then("the BoundaryUse is RECORDED_BY the Event")
def _bu_recorded lol_by(hook_engine):
    rows = hook_engine.memory.g.query(
        "MATCH (b:BoundaryUse)-[:RECORDED_BY]->(e:Event) RETURN b, e")
    assert len(rows) == 1


# ── when/then — merge_settings ───────────────────────────────────────────────

@when("I merge settings with another plugin already enabled",
      target_fixture="merged")
def _merge_with_other():
    user = {"enabledPlugins": {"bitwize-music@bitwize-music": True}}
    return merge_settings(user), user


@then("agency@agency is added to enabledPlugins")
def _agency_added(merged):
    result, _ = merged
    assert result["enabledPlugins"].get("agency@agency") is True


@then("the other plugin's entry is preserved")
def _other_preserved(merged):
    result, _ = merged
    assert result["enabledPlugins"].get("bitwize-music@bitwize-music") is True


@then("merging again produces no change")
def _idempotent_merge(merged):
    result, _ = merged
    once = json.dumps(result, sort_keys=True)
    twice = json.dumps(merge_settings(result), sort_keys=True)
    assert once == twice


# ── when/then — detect_foreign_hooks ─────────────────────────────────────────

@when("I call detect_foreign_hooks on settings containing a hand-authored PreToolUse hook",
      target_fixture="foreign_result")
def _detect_hand_authored():
    user = {
        "hooks": {
            "PreToolUse": [{
                "matcher": "Bash",
                "hooks": [{"type": "command",
                           "command": "/usr/local/bin/audit-cmd.sh",
                           "async": False}],
            }],
        },
    }
    return detect_foreign_hooks(user)


@then("one ForeignHook is found")
def _one_foreign(foreign_result):
    assert len(foreign_result) == 1
    assert foreign_result[0].event == "PreToolUse"


@when("I call detect_foreign_hooks on settings already containing the agency dispatcher",
      target_fixture="foreign_result")
def _detect_agency_dispatcher():
    user = {
        "hooks": {
            "PreToolUse": [{
                "matcher": "*",
                "hooks": [{"type": "command",
                           "command": '"${CLAUDE_PLUGIN_ROOT}/hooks/run-hook.cmd" dispatch'}],
            }],
        },
    }
    return detect_foreign_hooks(user)


@then("no ForeignHook is found")
def _no_foreign(foreign_result):
    assert foreign_result == []


# ── when/then — wrap_foreign_hook ────────────────────────────────────────────

@when("I wrap a sync ForeignHook", target_fixture="wrapped")
def _wrap_sync():
    foreign = ForeignHook(
        event="PreToolUse", matcher="Bash",
        command="/usr/local/bin/audit.sh",
        type_="command", async_=False)
    return wrap_foreign_hook(foreign)


@then("the wrapped entry has async False")
def _wrapped_async_false(wrapped):
    assert wrapped is not None
    assert wrapped["async"] is False


@then("the wrapped entry has _wrapped_from set to the original command")
def _wrapped_from(wrapped):
    assert wrapped["_wrapped_from"] == "/usr/local/bin/audit.sh"


@then("the wrapped command uses agency hook wrap")
def _wrapped_agency_cmd(wrapped):
    assert "agency hook wrap" in wrapped["command"]


# ── when/then — apply_foreign_wraps idempotence ──────────────────────────────

@when("I apply foreign wraps once then apply again",
      target_fixture="wrap_twice_result")
def _wrap_twice():
    user = {
        "hooks": {
            "PreToolUse": [{
                "matcher": "Bash",
                "hooks": [{"type": "command",
                           "command": "/usr/local/bin/audit.sh",
                           "async": False}],
            }],
        },
    }
    once, n_once = apply_foreign_wraps(user)
    twice, n_twice = apply_foreign_wraps(once)
    return once, n_once, twice, n_twice


@then("the first run wraps 1 foreign hook")
def _first_wraps_one(wrap_twice_result):
    _, n_once, _, _ = wrap_twice_result
    assert n_once == 1


@then("the second run wraps 0 foreign hooks")
def _second_wraps_zero(wrap_twice_result):
    _, _, _, n_twice = wrap_twice_result
    assert n_twice == 0


@then("the resulting settings are byte-identical")
def _settings_identical(wrap_twice_result):
    once, _, twice, _ = wrap_twice_result
    assert (json.dumps(once, sort_keys=True) == json.dumps(twice, sort_keys=True))


# ── when/then — patch_settings_file ──────────────────────────────────────────

@when("I patch a non-existent settings file", target_fixture="patch_result")
def _patch_new(tmp_path):
    from agency._hooks import patch_settings_file
    settings = tmp_path / ".claude" / "settings.json"
    result = patch_settings_file(settings)
    return result, settings, tmp_path


@then("the settings file is created with agency@agency enabled")
def _settings_created(patch_result):
    result, settings, _ = patch_result
    assert result["wrote"] is True
    content = json.loads(settings.read_text())
    assert content["enabledPlugins"]["agency@agency"] is True


@then("no backup is created")
def _no_backup(patch_result):
    result, _, _ = patch_result
    assert result["backup_path"] == ""


@when("I patch an existing settings file", target_fixture="patch_existing_result")
def _patch_existing(tmp_path):
    from agency._hooks import patch_settings_file
    settings = tmp_path / "existing" / ".claude" / "settings.json"
    settings.parent.mkdir(parents=True)
    prior = {"enabledPlugins": {"bitwize-music@bitwize-music": True}}
    settings.write_text(json.dumps(prior, indent=2))
    result = patch_settings_file(settings)
    return result, settings, prior


@then("a .bak file is created containing the original content")
def _bak_created(patch_existing_result):
    from pathlib import Path
    result, settings, prior = patch_existing_result
    backup = Path(result["backup_path"])
    assert backup.exists()
    assert json.loads(backup.read_text()) == prior


@then("the patched file still has the other plugin entries")
def _other_entries_preserved(patch_existing_result):
    _, settings, _ = patch_existing_result
    content = json.loads(settings.read_text())
    assert content["enabledPlugins"].get("bitwize-music@bitwize-music") is True
    assert content["enabledPlugins"].get("agency@agency") is True


# ── then — CANONICAL_SETTINGS_PATCH ──────────────────────────────────────────

@then("CANONICAL_SETTINGS_PATCH contains the _agency_version marker")
def _has_version_marker():
    from agency._hooks import HOOKS_SPEC_VERSION
    assert CANONICAL_SETTINGS_PATCH.get("_agency_version") == HOOKS_SPEC_VERSION


@then("CANONICAL_SETTINGS_PATCH contains agency in extraKnownMarketplaces")
def _has_marketplace():
    mkt = CANONICAL_SETTINGS_PATCH.get("extraKnownMarketplaces") or {}
    assert "agency" in mkt
    src = mkt["agency"].get("source", {})
    assert src.get("source") == "github"


# ── then — async doctrine table ──────────────────────────────────────────────

@then("PreToolUse and UserPromptSubmit are sync in ASYNC_BY_EVENT")
def _sync_pretooluse():
    assert ASYNC_BY_EVENT["PreToolUse"] is False
    assert ASYNC_BY_EVENT["UserPromptSubmit"] is False
    assert ASYNC_BY_EVENT["SessionStart"] is False


@then("PostToolUse Stop and SessionEnd are async in ASYNC_BY_EVENT")
def _async_posttooluse():
    assert ASYNC_BY_EVENT["PostToolUse"] is True
    assert ASYNC_BY_EVENT["Stop"] is True
    assert ASYNC_BY_EVENT["SessionEnd"] is True


# ── when/then — agency_doctor hooks field ────────────────────────────────────

@when("I call agency_doctor", target_fixture="doctor_result")
def _call_doctor(hook_engine, tmp_path, monkeypatch):
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
    return _call_wire(hook_engine, "agency_doctor", {})


@then("the result contains a hooks field")
def _has_hooks_field(doctor_result):
    assert "hooks" in doctor_result


@then("the hooks field has plugin_enabled cli_on_path hook_scripts_present and next_steps")
def _hooks_shape(doctor_result):
    hooks = doctor_result["hooks"]
    for key in ("plugin_enabled", "cli_on_path", "hook_scripts_present", "next_steps"):
        assert key in hooks, f"doctor.hooks missing key: {key}"


# ── SessionEnd → session Document archive (Spec 292) ──────────────────────────

@when("a SessionEnd hook event fires", target_fixture="hook_out")
def _sessionend(hook_engine, active_intent):
    return hook_engine.dispatch_hook(
        {"hook_event_name": "SessionEnd", "session_id": "s1"})


@then("the hook result archives a session Document")
def _archived_doc(hook_out):
    assert hook_out.get("archived", "").startswith("document:"), hook_out


@then("that session Document exists in the graph")
def _archived_in_graph(hook_engine, hook_out):
    assert hook_engine.memory.recall_typed(hook_out["archived"], "Document")


# ── UserPromptSubmit injection — assumption-guard (Spec 292) ──────────────────

@then("the hook injects an assumption-guard naming intent and thinking")
def _inject_guard(hook_out):
    inj = hook_out.get("inject", "")
    assert "intent.assumptions" in inj and "thinking" in inj, inj
    assert "ASSUMPTION" in inj.upper() and "ASK" in inj.upper(), inj


@then("the injected guard names the active intent purpose")
def _inject_names_intent(hook_out):
    assert "Active intent:" in hook_out.get("inject", "")


# ── Session Graph restore (Spec 292) ──────────────────────────────────────────

@when("a UserPromptSubmit then a PostToolUse event fire in session s9")
def _two_events_s9(hook_engine, active_intent):
    hook_engine.dispatch_hook({"hook_event_name": "UserPromptSubmit",
                               "session_id": "s9", "prompt": "go"})
    hook_engine.dispatch_hook({"hook_event_name": "PostToolUse",
                               "session_id": "s9", "tool_name": "Bash",
                               "tool_input": {"command": "ls"}})


@when("a SessionEnd event fires in session s9")
def _sessionend_s9(hook_engine):
    hook_engine.dispatch_hook({"hook_event_name": "SessionEnd", "session_id": "s9"})


@then("restoring session s9 reports a closed session with events and a Document")
def _restore_s9(hook_engine, active_intent):
    r, _ = hook_engine.registry.invoke(
        hook_engine.memory, active_intent, "document", "restore_session",
        agent_id="agent:test", session_id="s9")
    assert r["status"] == "closed", r
    # Spec 336 S2 — the graph keeps the LIFECYCLE events (UserPromptSubmit +
    # SessionEnd); the PostToolUse tool call lives in the ephemeral store.
    assert r["event_count"] >= 2, r
    assert r["document_id"], r
    assert any(rr["tool"] == "Bash" for rr in hook_engine.toolcalls.rows()), \
        "the tool call is recoverable from the store"


# ── Session Graph analytics (Spec 292) ────────────────────────────────────────

def _analytics(eng, intent, **kw):
    r, _ = eng.registry.invoke(eng.memory, intent, "document", "session_analytics",
                               agent_id="agent:test", **kw)
    return r


@then("session analytics for s9 report the event-type and tool breakdown")
def _analytics_single(hook_engine, active_intent):
    a = _analytics(hook_engine, active_intent, session_id="s9")
    # Spec 336 S2 — graph analytics cover the LIFECYCLE events; the tool breakdown
    # moved to the ephemeral store (read via the toolcalls capability).
    assert a["found"] and a["event_count"] >= 2, a
    names = {row["name"] for row in a["events_by_type"]}
    assert {"UserPromptSubmit", "SessionEnd"} <= names, a
    assert any(r["tool"] == "Bash" for r in hook_engine.toolcalls.rows()), a


@then("session analytics for s9 attach the archived Document")
def _analytics_doc(hook_engine, active_intent):
    a = _analytics(hook_engine, active_intent, session_id="s9")
    assert a["documents"] and a["documents"][0]["id"].startswith("document:"), a


@then("cross-session analytics report a positive session count and a busiest list")
def _analytics_cross(hook_engine, active_intent):
    a = _analytics(hook_engine, active_intent)
    assert a["session_count"] >= 1, a
    assert any(row["session_id"] == "s9" for row in a["busiest_sessions"]), a


# ── Spec 195 Slice 2 — PreToolUse → agency MCP suggestion + schema ─────────────
from pytest_bdd import parsers as _parsers  # noqa: E402


@when(_parsers.parse('a PreToolUse event fires for a "{cmd}" Bash command'),
      target_fixture="hook_result")
def _pretooluse_bash(hook_engine, cmd):
    return hook_engine.dispatch_hook(
        {"hook_event_name": "PreToolUse", "session_id": "s1",
         "tool_name": "Bash", "tool_input": {"command": cmd}})


@when("a PreToolUse event fires for a Grep tool", target_fixture="hook_result")
def _pretooluse_grep(hook_engine):
    return hook_engine.dispatch_hook(
        {"hook_event_name": "PreToolUse", "session_id": "s1",
         "tool_name": "Grep", "tool_input": {"pattern": "foo"}})


@when("a PreToolUse event fires for a Read tool", target_fixture="hook_result")
def _pretooluse_read(hook_engine):
    return hook_engine.dispatch_hook(
        {"hook_event_name": "PreToolUse", "session_id": "s1",
         "tool_name": "Read", "tool_input": {"file_path": "/x.py"}})


@then(_parsers.parse('the hook returns an agency_suggestion for "{mcp_tool}"'))
def _has_suggestion(hook_result, mcp_tool):
    sugg = hook_result.get("agency_suggestion") or []
    assert any(s["mcp_tool"] == mcp_tool for s in sugg), hook_result


@then("the suggestion carries a JSON object schema for the call")
def _suggestion_schema(hook_result):
    sugg = hook_result["agency_suggestion"]
    assert sugg and isinstance(sugg[0]["schema"], dict)
    assert sugg[0]["schema"].get("type") == "object", sugg[0]


@then("the additionalContext names the execute companion and its schema")
def _additional_context(hook_result):
    ctx = hook_result.get("hookSpecificOutput", {}).get("additionalContext", "")
    assert "mcp__agency__execute" in ctx and "schema" in ctx, ctx
    assert "capability_branch_commit_smart" in ctx, ctx


@then("the hook returns no agency_suggestion")
def _no_suggestion(hook_result):
    assert not hook_result.get("agency_suggestion"), hook_result


def test_every_suggestion_resolves_to_a_live_verb():
    """Dormant-surface guard (CLAUDE.md): every PreToolUse suggestion target must
    resolve to a real MCP tool against the live registry — no dead branch."""
    from agency.engine import _ALL_SUGGESTIONS, _resolve_mcp_suggestion
    eng = Engine(tempfile.mktemp(suffix=".db"))
    try:
        for suggestion, _why in _ALL_SUGGESTIONS:
            assert _resolve_mcp_suggestion(eng, suggestion) is not None, \
                f"dead suggestion target: {suggestion!r}"
    finally:
        eng.memory.close()
