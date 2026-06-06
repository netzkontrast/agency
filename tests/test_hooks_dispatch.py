"""Spec 076 — unified event-hook: one dispatcher → a single agency handler surface.

Claude Code has no top-level wildcard hook, so unity = every event block invokes
the SAME dispatcher (`hooks/dispatch`), which pipes the event JSON to `agency
hook` → the engine's `dispatch_hook`. A default handler records an `Event` node
(provenance); the handler surface is an OPEN SET (`register_hook_handler`) so
per-event filtering/loop-detection plug in without hardcoding.

Behaviour-first: synthetic events of each kind route to a handler and land in the
graph; tool events carry a trimmed payload; an active AGENCY_INTENT links the
Event as provenance.
"""
from __future__ import annotations

import json
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


def _events(engine):
    return engine.memory.find("Event")


# --- the default handler records provenance -----------------------------------

def test_dispatch_records_event_node(engine):
    out = engine.dispatch_hook({
        "hook_event_name": "UserPromptSubmit", "session_id": "s1",
        "prompt": "do the thing"})
    assert out.get("recorded")
    evs = _events(engine)
    assert any(e["name"] == "UserPromptSubmit" and e["session"] == "s1" for e in evs)


def test_tool_event_captures_tool_and_trimmed_input(engine):
    engine.dispatch_hook({
        "hook_event_name": "PostToolUse", "session_id": "s1",
        "tool_name": "Bash", "tool_input": {"command": "x\n" * 200}})
    ev = next(e for e in _events(engine) if e["name"] == "PostToolUse")
    assert ev["tool"] == "Bash"
    assert ev.get("summary")                      # a trimmed payload, not the full dump
    assert len(ev["summary"]) <= 600


def test_missing_event_name_does_not_crash(engine):
    out = engine.dispatch_hook({"session_id": "s1"})   # no hook_event_name
    assert out.get("recorded") or out.get("skipped")   # routes cleanly either way


# --- open-set handler registration --------------------------------------------

def test_register_hook_handler_overrides_default(engine):
    seen = {}

    def handler(eng, event):
        seen["hit"] = event.get("hook_event_name")
        return {"recorded": None, "custom": True}

    engine.register_hook_handler("Stop", handler)
    out = engine.dispatch_hook({"hook_event_name": "Stop", "session_id": "s1"})
    assert out.get("custom") is True and seen["hit"] == "Stop"
    # a non-overridden event still hits the default (records an Event)
    engine.dispatch_hook({"hook_event_name": "SessionEnd", "session_id": "s1"})
    assert any(e["name"] == "SessionEnd" for e in _events(engine))


# --- AGENCY_INTENT (Win 3) integration: events become intent provenance --------

def test_event_links_to_active_intent(engine, monkeypatch):
    iid = engine.intent.capture("hook prov", "events serve the intent", "OBSERVED_DURING edge")
    engine.intent.confirm(iid)
    monkeypatch.setenv("AGENCY_INTENT", iid)
    out = engine.dispatch_hook({"hook_event_name": "PreToolUse", "session_id": "s1",
                                "tool_name": "Edit", "tool_input": {}})
    eid = out["recorded"]
    rows = engine.memory.g.query(
        "MATCH (e:Event)-[:OBSERVED_DURING]->(i:Intent) WHERE e.id=$e AND i.id=$i RETURN i",
        {"e": eid, "i": iid})
    assert rows, "an event during an active intent must be linked OBSERVED_DURING"


def test_event_without_intent_still_records(engine, monkeypatch):
    monkeypatch.delenv("AGENCY_INTENT", raising=False)
    out = engine.dispatch_hook({"hook_event_name": "Notification", "session_id": "s1"})
    assert out.get("recorded")                    # no intent needed (substrate write)


# --- the substrate tool + CLI surface -----------------------------------------

def test_hook_event_substrate_tool(engine):
    import asyncio
    mcp = engine.build_mcp(codemode=False)
    res = asyncio.run(mcp.call_tool("hook_event", {
        "event": {"hook_event_name": "SubagentStop", "session_id": "s1"}}))
    sc = res.structured_content
    assert sc and (sc.get("result") or sc)
    assert any(e["name"] == "SubagentStop" for e in _events(engine))


def test_cli_hook_reads_event_from_stdin(tmp_path, monkeypatch, capsys):
    import io
    from agency.cli import main as cli_main
    db = str(tmp_path / "g.db")
    event = json.dumps({"hook_event_name": "Stop", "session_id": "s9"})
    monkeypatch.setattr("sys.stdin", io.StringIO(event))
    rc = cli_main(["--db", db, "hook"])
    assert rc == 0
    # re-open + confirm the event landed
    e2 = Engine(db)
    try:
        assert any(ev["name"] == "Stop" for ev in e2.memory.find("Event"))
    finally:
        e2.memory.close()


# --- install wiring: one dispatcher for every capture event -------------------

def test_install_emits_unified_dispatch_hooks(engine):
    from agency import install
    files = install.generate(engine)
    hooks_json = files.get("hooks/hooks.json")
    assert hooks_json, "install must emit hooks/hooks.json"
    parsed = json.loads(hooks_json)
    events = parsed["hooks"]
    # the capture events all route to the ONE dispatcher script
    for ev in ("PostToolUse", "UserPromptSubmit", "Stop"):
        assert ev in events, f"{ev} must be wired"
        cmd = events[ev][0]["hooks"][0]["command"]
        assert "dispatch" in cmd, f"{ev} must invoke the dispatch script"
    # the dispatcher script itself is emitted
    assert "hooks/dispatch" in files
