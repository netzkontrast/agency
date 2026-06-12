"""Spec 195 Slice 1 — BoundaryUse capture via the unified hook layer.

Spec 076 ships the unified event-hook dispatcher (`hooks/dispatch` →
`agency hook` → `engine.dispatch_hook`). Slice 1 extends the default
handler to ALSO record a typed `BoundaryUse{tool, target, verb_shadow,
intent_id}` node when an agent uses a raw mutating tool (Write / Edit /
Bash) under an active intent. `dogfood.boundary_use_audit` aggregates
the bypass rate so the dogfood loop (Spec 150) + Spec 280 Slice 2
blocking-route promotion can both consume the baseline.

Slice 1 covers Open Q1 (mutating-only) + the engine handler wiring +
the audit report shape. Slice 2 adds replay + monotonic chain + PII
discipline (Spec 192).
"""
from __future__ import annotations

import tempfile

import pytest

from agency.engine import Engine


def _fresh() -> Engine:
    return Engine(tempfile.mktemp(suffix=".db"))


def _intent(e: Engine) -> str:
    iid = e.intent.capture("spec 195 boundary use", "ship slice 1", "verified")
    e.intent.confirm(iid)
    return iid


def _fire_hook(e: Engine, payload: dict) -> dict:
    """Invoke the engine's default hook handler with a synthetic payload."""
    return e.dispatch_hook(payload)


# ── BoundaryUse capture: raw Bash under active intent ─────────────────────
def test_raw_bash_under_intent_records_boundary_use(monkeypatch):
    """A raw `Bash("git commit ...")` PreToolUse event under an
    active intent records a BoundaryUse node with `verb_shadow`
    pointing at `branch.commit_smart`."""
    e = _fresh()
    iid = _intent(e)
    monkeypatch.setenv("AGENCY_INTENT", iid)
    _fire_hook(e, {
        "hook_event_name": "PreToolUse",
        "tool_name":       "Bash",
        "session_id":      "sess-1",
        "tool_input":      {"command": "git commit -m 'x'"},
    })
    nodes = e.memory.find("BoundaryUse")
    assert len(nodes) == 1
    bu = nodes[0]
    assert bu["tool"] == "Bash"
    assert bu["verb_shadow"] == "branch.commit_smart"
    assert "git commit" in bu["target"]
    assert bu["intent_id"] == iid


def test_raw_pytest_routes_to_develop_test(monkeypatch):
    e = _fresh()
    iid = _intent(e)
    monkeypatch.setenv("AGENCY_INTENT", iid)
    _fire_hook(e, {
        "hook_event_name": "PreToolUse",
        "tool_name":       "Bash",
        "session_id":      "sess-2",
        "tool_input":      {"command": "pytest tests/"},
    })
    bu = e.memory.find("BoundaryUse")[0]
    assert bu["verb_shadow"] == "develop.test"


def test_raw_spec_edit_routes_to_dogfood_observe(monkeypatch):
    e = _fresh()
    iid = _intent(e)
    monkeypatch.setenv("AGENCY_INTENT", iid)
    _fire_hook(e, {
        "hook_event_name": "PreToolUse",
        "tool_name":       "Edit",
        "session_id":      "sess-3",
        "tool_input":      {"file_path": "Plan/280-foo/spec.md"},
    })
    bu = e.memory.find("BoundaryUse")[0]
    assert bu["tool"] == "Edit"
    assert bu["verb_shadow"] == "dogfood.observe"
    assert "Plan/280-foo/spec.md" in bu["target"]


def test_raw_write_to_random_file_uses_shadow_placeholder(monkeypatch):
    """When no specific routing applies, `verb_shadow` carries a
    placeholder so the audit can still group by tool."""
    e = _fresh()
    iid = _intent(e)
    monkeypatch.setenv("AGENCY_INTENT", iid)
    _fire_hook(e, {
        "hook_event_name": "PreToolUse",
        "tool_name":       "Write",
        "session_id":      "sess-4",
        "tool_input":      {"file_path": "/tmp/random.txt"},
    })
    bu = e.memory.find("BoundaryUse")[0]
    assert bu["tool"] == "Write"
    assert "capability_verb_for" in bu["verb_shadow"]


# ── No BoundaryUse when there's no intent / not PreToolUse / wrong tool ──
def test_no_boundary_use_without_active_intent(monkeypatch):
    """Without an active intent, only the Event node is recorded; no
    BoundaryUse — the moat doesn't apply when there's no intent to
    serve."""
    e = _fresh()
    monkeypatch.delenv("AGENCY_INTENT", raising=False)
    _fire_hook(e, {
        "hook_event_name": "PreToolUse",
        "tool_name":       "Bash",
        "session_id":      "sess-5",
        "tool_input":      {"command": "git commit -m x"},
    })
    assert e.memory.find("BoundaryUse") == []


def test_no_boundary_use_for_post_tool_use(monkeypatch):
    """Bypass detection fires ONLY at PreToolUse — the moment the
    bypass happens. PostToolUse is record-only."""
    e = _fresh()
    iid = _intent(e)
    monkeypatch.setenv("AGENCY_INTENT", iid)
    _fire_hook(e, {
        "hook_event_name": "PostToolUse",
        "tool_name":       "Bash",
        "session_id":      "sess-6",
        "tool_input":      {"command": "git commit -m x"},
    })
    assert e.memory.find("BoundaryUse") == []


def test_no_boundary_use_for_read_only_tools(monkeypatch):
    """Open Q1: only MUTATING tools (Write/Edit/Bash) count as moat
    bypass. Reads (Read/Grep/Glob/WebFetch) don't fire."""
    e = _fresh()
    iid = _intent(e)
    monkeypatch.setenv("AGENCY_INTENT", iid)
    for tool in ("Read", "Grep", "Glob", "WebFetch"):
        _fire_hook(e, {
            "hook_event_name": "PreToolUse",
            "tool_name":       tool,
            "session_id":      "sess-r",
            "tool_input":      {"file_path": "/x"},
        })
    assert e.memory.find("BoundaryUse") == []


# ── Provenance moat invariant: SERVES + RECORDED_BY ──────────────────────
def test_boundary_use_serves_intent_and_links_event(monkeypatch):
    """The BoundaryUse node SERVES the active intent (so the audit
    traversal recovers it) AND RECORDED_BY the Event node (so replay
    can chain back to the raw payload)."""
    e = _fresh()
    iid = _intent(e)
    monkeypatch.setenv("AGENCY_INTENT", iid)
    _fire_hook(e, {
        "hook_event_name": "PreToolUse",
        "tool_name":       "Bash",
        "session_id":      "sess-7",
        "tool_input":      {"command": "git commit -m x"},
    })
    rows = e.memory.g.query(
        "MATCH (b:BoundaryUse)-[:SERVES]->(i:Intent) "
        "WHERE i.id = $iid RETURN b", {"iid": iid})
    assert len(rows) == 1
    rows = e.memory.g.query(
        "MATCH (b:BoundaryUse)-[:RECORDED_BY]->(e:Event) RETURN b, e")
    assert len(rows) == 1


# ── dogfood.boundary_use_audit aggregates the bypass rate ────────────────
def _call_audit(e: Engine, iid: str, **kw):
    """Invoke `dogfood.boundary_use_audit` via the registry."""
    res, _ = e.registry.invoke(
        e.memory, iid, "dogfood", "boundary_use_audit",
        agent_id="agent:test", **kw)
    return res


def test_audit_reports_bypass_count_and_by_tool(monkeypatch):
    e = _fresh()
    iid = _intent(e)
    monkeypatch.setenv("AGENCY_INTENT", iid)
    for cmd in ["git commit -m a", "pytest tests/", "git push"]:
        _fire_hook(e, {
            "hook_event_name": "PreToolUse",
            "tool_name":       "Bash",
            "session_id":      "s",
            "tool_input":      {"command": cmd},
        })
    _fire_hook(e, {
        "hook_event_name": "PreToolUse",
        "tool_name":       "Edit",
        "session_id":      "s",
        "tool_input":      {"file_path": "Plan/195-foo/spec.md"},
    })
    rep = _call_audit(e, iid, for_intent_id=iid)
    assert rep["bypass_count"] == 4
    assert rep["by_tool"]["Bash"] == 3
    assert rep["by_tool"]["Edit"] == 1
    # Samples preserve verb_shadow so the dogfood loop can use them
    # as proposal feedstock.
    shadows = {s["verb_shadow"] for s in rep["samples"]}
    assert "branch.commit_smart" in shadows
    assert "branch.finish_branch" in shadows
    assert "develop.test" in shadows
    assert "dogfood.observe" in shadows


def test_audit_filters_by_intent_id(monkeypatch):
    """Cross-intent contamination invariant: with a `for_intent_id`
    filter, only BoundaryUses serving THAT intent appear."""
    e = _fresh()
    iid_a = _intent(e)
    iid_b = e.intent.capture("other", "x", "y")
    e.intent.confirm(iid_b)
    monkeypatch.setenv("AGENCY_INTENT", iid_a)
    _fire_hook(e, {
        "hook_event_name": "PreToolUse", "tool_name": "Bash",
        "session_id": "s", "tool_input": {"command": "git commit -m a"},
    })
    monkeypatch.setenv("AGENCY_INTENT", iid_b)
    _fire_hook(e, {
        "hook_event_name": "PreToolUse", "tool_name": "Bash",
        "session_id": "s", "tool_input": {"command": "git push"},
    })
    rep_a = _call_audit(e, iid_a, for_intent_id=iid_a)
    rep_b = _call_audit(e, iid_b, for_intent_id=iid_b)
    assert rep_a["bypass_count"] == 1
    assert rep_b["bypass_count"] == 1
    # Global (no filter) sees both.
    rep_global = _call_audit(e, iid_a)
    assert rep_global["bypass_count"] == 2


def test_audit_empty_when_no_bypasses(monkeypatch):
    e = _fresh()
    iid = _intent(e)
    rep = _call_audit(e, iid, for_intent_id=iid)
    assert rep["bypass_count"] == 0
    assert rep["by_tool"] == {}
    assert rep["samples"] == []


# ─────────── Slice 2 — dogfood.replay_events + monotonic chain ─────────
def _call_replay(e: Engine, iid: str, **kw):
    kw.setdefault("for_intent_id", iid)
    res, _ = e.registry.invoke(
        e.memory, iid, "dogfood", "replay_events",
        agent_id="agent:test", **kw)
    return res


def test_replay_empty_for_unknown_intent():
    e = _fresh()
    rep = _call_replay(e, _intent(e), for_intent_id="intent:no-such")
    assert rep["events"] == []
    assert rep["count"] == 0


def test_replay_returns_events_in_record_order(monkeypatch):
    """A sequence of three hook events lands in record order with
    prior_event_id linking each to its predecessor."""
    e = _fresh()
    iid = _intent(e)
    monkeypatch.setenv("AGENCY_INTENT", iid)
    cmds = ["git commit -m a", "pytest tests/", "git push"]
    for cmd in cmds:
        _fire_hook(e, {
            "hook_event_name": "PreToolUse",
            "tool_name":       "Bash",
            "session_id":      "s",
            "tool_input":      {"command": cmd},
        })
    rep = _call_replay(e, iid)
    assert rep["count"] == 3
    # Monotonic chain: first event has empty prior; each subsequent
    # event's prior is the previous event's id.
    evs = rep["events"]
    assert evs[0]["prior_event_id"] == ""
    for i in range(1, 3):
        assert evs[i]["prior_event_id"] == evs[i - 1]["event_id"]
    # The replay attaches the BoundaryUse `verb_shadow` to the Event
    # via the RECORDED_BY join (Slice 1 invariant).
    shadows = [ev["verb_shadow"] for ev in evs]
    assert "branch.commit_smart" in shadows
    assert "develop.test" in shadows
    assert "branch.finish_branch" in shadows


def test_replay_filters_by_tool(monkeypatch):
    """`tool='Bash'` returns only Bash events; reads (Edit on a spec)
    drop out."""
    e = _fresh()
    iid = _intent(e)
    monkeypatch.setenv("AGENCY_INTENT", iid)
    _fire_hook(e, {
        "hook_event_name": "PreToolUse", "tool_name": "Bash",
        "session_id": "s", "tool_input": {"command": "git commit -m x"},
    })
    _fire_hook(e, {
        "hook_event_name": "PreToolUse", "tool_name": "Edit",
        "session_id": "s",
        "tool_input": {"file_path": "Plan/195-foo/spec.md"},
    })
    rep = _call_replay(e, iid, tool="Bash")
    assert rep["count"] == 1
    assert rep["events"][0]["tool"] == "Bash"


def test_replay_respects_limit(monkeypatch):
    """`limit=2` returns the first 2 events; count matches."""
    e = _fresh()
    iid = _intent(e)
    monkeypatch.setenv("AGENCY_INTENT", iid)
    for cmd in ["git commit -m a", "git commit -m b", "git commit -m c"]:
        _fire_hook(e, {
            "hook_event_name": "PreToolUse", "tool_name": "Bash",
            "session_id": "s", "tool_input": {"command": cmd},
        })
    rep = _call_replay(e, iid, limit=2)
    assert rep["count"] == 2


def test_replay_does_not_leak_other_intents(monkeypatch):
    """Cross-intent contamination invariant — replay only returns
    Events linked to the requested intent."""
    e = _fresh()
    iid_a = _intent(e)
    iid_b = e.intent.capture("other", "x", "y")
    e.intent.confirm(iid_b)
    monkeypatch.setenv("AGENCY_INTENT", iid_a)
    _fire_hook(e, {
        "hook_event_name": "PreToolUse", "tool_name": "Bash",
        "session_id": "s", "tool_input": {"command": "git commit -m a"},
    })
    monkeypatch.setenv("AGENCY_INTENT", iid_b)
    _fire_hook(e, {
        "hook_event_name": "PreToolUse", "tool_name": "Bash",
        "session_id": "s", "tool_input": {"command": "git push"},
    })
    rep_a = _call_replay(e, iid_a)
    assert rep_a["count"] == 1
    assert rep_a["events"][0]["verb_shadow"] == "branch.commit_smart"
    rep_b = _call_replay(e, iid_b)
    assert rep_b["count"] == 1
    assert rep_b["events"][0]["verb_shadow"] == "branch.finish_branch"
