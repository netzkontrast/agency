"""Spec 048 — analyze.paths intent-shape analyzer.

Three fixture shapes, three rules: IP001 long chain, IP002 long verb
sequence, IP003 repeated verb.
"""
import tempfile

import pytest

from agency.engine import Engine


@pytest.fixture
def engine():
    return Engine(tempfile.mktemp(suffix=".db"))


@pytest.fixture
def root_iid(engine):
    """A confirmed user-owned root intent for fixtures to anchor on."""
    return engine.intent.capture_and_confirm("root", "x", "x", owner="user")


def _call_paths(engine, iid, **kw):
    r, _ = engine.registry.invoke(
        engine.memory, iid, "analyze", "paths",
        agent_id="agent:test", **kw)
    return r


# ---------------------------------------------------------------------------
# IP001 — long sub-intent chain.
# ---------------------------------------------------------------------------


def test_ip001_long_chain(engine, root_iid):
    # Build a 6-deep chain under root.
    prev = root_iid
    for _ in range(6):
        prev = engine.intent.capture_and_confirm(
            "level", "x", "x", parent_intent_id=prev)
    r = _call_paths(engine, root_iid)
    ip001 = [f for f in r["findings"] if f["rule"] =="IP001"]
    assert ip001, "IP001 should fire on 6-deep chain"
    assert ip001[0]["severity"] == "info"
    assert root_iid in ip001[0]["file"]


def test_no_ip001_for_shallow_chain(engine, root_iid):
    a = engine.intent.capture_and_confirm("a", "x", "x", parent_intent_id=root_iid)
    b = engine.intent.capture_and_confirm("b", "x", "x", parent_intent_id=a)
    r = _call_paths(engine, root_iid)
    assert not [f for f in r["findings"] if f["rule"] =="IP001"]


# ---------------------------------------------------------------------------
# IP002 — long verb sequence per intent.
# ---------------------------------------------------------------------------


def test_ip002_long_verb_sequence(engine, root_iid):
    # Simulate 14 Invocation nodes serving the same intent.
    for i in range(14):
        inv_id = engine.memory.record("Invocation", {
            "capability": "reflect", "verb": "note",
            "role": "act"})
        engine.memory.link(inv_id, root_iid, "SERVES")
    r = _call_paths(engine, root_iid)
    ip002 = [f for f in r["findings"] if f["rule"] =="IP002"]
    assert ip002, "IP002 should fire on 14-invocation sequence"
    assert ip002[0]["severity"] == "warn"


def test_no_ip002_for_short_sequence(engine, root_iid):
    for i in range(5):
        inv_id = engine.memory.record("Invocation", {
            "capability": "x", "verb": "y", "role": "transform"})
        engine.memory.link(inv_id, root_iid, "SERVES")
    r = _call_paths(engine, root_iid)
    assert not [f for f in r["findings"] if f["rule"] =="IP002"]


# ---------------------------------------------------------------------------
# IP003 — repeated verb pattern.
# ---------------------------------------------------------------------------


def test_ip003_repeated_verb(engine, root_iid):
    # 5 invocations of analyze.quality + 3 of document.render.
    # IP003 should fire only on analyze.quality.
    for _ in range(5):
        inv = engine.memory.record("Invocation", {
            "capability": "analyze", "verb": "quality",
            "role": "transform"})
        engine.memory.link(inv, root_iid, "SERVES")
    for _ in range(3):
        inv = engine.memory.record("Invocation", {
            "capability": "document", "verb": "render",
            "role": "transform"})
        engine.memory.link(inv, root_iid, "SERVES")
    r = _call_paths(engine, root_iid)
    ip003 = [f for f in r["findings"] if f["rule"] =="IP003"]
    assert any("analyze.quality" in f["message"] for f in ip003)
    assert not any("document.render" in f["message"] for f in ip003)


# ---------------------------------------------------------------------------
# Scope handling.
# ---------------------------------------------------------------------------


def test_default_scans_all_user_roots(engine):
    root1 = engine.intent.capture_and_confirm("r1", "x", "x", owner="user")
    root2 = engine.intent.capture_and_confirm("r2", "x", "x", owner="user")
    # Long chain under each.
    for prev_root in (root1, root2):
        prev = prev_root
        for _ in range(6):
            prev = engine.intent.capture_and_confirm(
                "level", "x", "x", parent_intent_id=prev)
    # No root_intent_id → scan all user roots.
    r = _call_paths(engine, root1)    # iid here is the SERVES anchor, not the scope
    ip001 = [f for f in r["findings"] if f["rule"] =="IP001"]
    # Both roots are user-owned with deep chains; both should appear.
    files = {f["file"] for f in ip001}
    assert root1 in files
    assert root2 in files


def test_max_paths_cap(engine):
    # Build 5 user roots, each with a long chain.
    for _ in range(5):
        root = engine.intent.capture_and_confirm("r", "x", "x", owner="user")
        prev = root
        for _ in range(6):
            prev = engine.intent.capture_and_confirm(
                "l", "x", "x", parent_intent_id=prev)
    use = engine.intent.capture_and_confirm("u", "x", "x")
    r = _call_paths(engine, use, max_paths=2)
    ip001 = [f for f in r["findings"] if f["rule"] =="IP001"]
    # max_paths=2 → only 2 of the 5 roots get scanned.
    assert len(ip001) <= 2


# ---------------------------------------------------------------------------
# Ontology + verb registration.
# ---------------------------------------------------------------------------


def test_analyze_has_paths_verb(engine):
    cap = engine.registry.get("analyze")
    assert "paths" in cap.verbs


def test_paths_in_analysis_axis_enum(engine):
    enums = engine.ontology.enums
    assert "paths" in enums[("Analysis", "axis")]
