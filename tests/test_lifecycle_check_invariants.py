"""Spec 011 — the structural Lifecycle check (no orphaned `working` children).

Post-hoc read over a delegation, recorded through `gate.check` (no new label, no
new verb). Asserts the single non-redundant invariant; depth + quota are already
enforced elsewhere and dropped.
"""
from __future__ import annotations

import tempfile

from agency._checks import check_no_orphans, orphaned_working_children
from agency.capability import CapabilityContext
from agency.engine import Engine


def test_pure_orphan_detection():
    children = [{"id": "a", "state": "working"}, {"id": "b", "state": "completed"},
                {"id": "c", "state": "working"}]
    assert orphaned_working_children(children) == ["a", "c"]
    assert orphaned_working_children([{"id": "x", "state": "completed"}]) == []


def _ctx(e, iid):
    return CapabilityContext(memory=e.memory, ontology=e.ontology,
                             registry=e.registry, intent_id=iid, engine=e)


def _delegation_with_children(e, iid, states):
    d = e.memory.record("Delegation", {"driver": "x", "driver_verb": "y",
                                        "count": len(states), "quota": 8})
    e.memory.link(d, iid, "SERVES")
    child_ids = []
    for st in states:
        lc = e.memory.record("Lifecycle", {"state": st, "phase": 0})
        e.memory.link(lc, iid, "SERVES")
        e.memory.link(d, lc, "DELEGATES_TO")
        child_ids.append(lc)
    return d, child_ids


def test_check_fails_with_orphaned_working_child():
    e = Engine(tempfile.mktemp(suffix=".db"))
    try:
        iid = e.intent.capture("p", "d", "a")
        e.intent.confirm(iid)
        d, kids = _delegation_with_children(e, iid, ["completed", "working"])
        res = check_no_orphans(_ctx(e, iid), d, lifecycle_id=kids[0])
        assert res["ok"] is False
        assert res["children"] == 2 and len(res["orphans"]) == 1
        assert res["gate"]["result"]["passed"] is False
        # the orphan id is a real Agency node id (walkable via recall), not a row id
        assert e.memory.recall(res["orphans"][0]) is not None
        assert res["orphans"][0] == kids[1]
        # the gated lifecycle paused for re-entry
        assert e.memory.recall(kids[0])["state"] == "input-required"
    finally:
        e.memory.close()


def test_check_passes_when_all_children_completed():
    e = Engine(tempfile.mktemp(suffix=".db"))
    try:
        iid = e.intent.capture("p", "d", "a")
        e.intent.confirm(iid)
        d, kids = _delegation_with_children(e, iid, ["completed", "completed"])
        res = check_no_orphans(_ctx(e, iid), d, lifecycle_id=kids[0])
        assert res["ok"] is True and res["orphans"] == []
        assert res["gate"]["result"]["passed"] is True
    finally:
        e.memory.close()


def test_check_rejects_lifecycle_not_in_delegation():
    # A lifecycle that isn't a child of this delegation must be rejected BEFORE
    # recording a gate (the spec requires the gated lifecycle to be a child).
    e = Engine(tempfile.mktemp(suffix=".db"))
    try:
        iid = e.intent.capture("p", "d", "a")
        e.intent.confirm(iid)
        d, _ = _delegation_with_children(e, iid, ["working"])
        stray = e.memory.record("Lifecycle", {"state": "working", "phase": 0})
        e.memory.link(stray, iid, "SERVES")  # serves intent, but NOT a child of d
        res = check_no_orphans(_ctx(e, iid), d, lifecycle_id=stray)
        assert "error" in res and "not a child" in res["error"]
        assert "gate" not in res  # nothing recorded
    finally:
        e.memory.close()


def test_check_rejects_cross_intent_delegation():
    # A delegation from another intent must be rejected before reading its
    # children (mirrors delegate.join's cross-intent guard).
    e = Engine(tempfile.mktemp(suffix=".db"))
    try:
        iid = e.intent.capture("p", "d", "a")
        e.intent.confirm(iid)
        other = e.intent.capture("p2", "d2", "a2")
        e.intent.confirm(other)
        d_other, kids = _delegation_with_children(e, other, ["working"])  # serves OTHER intent
        res = check_no_orphans(_ctx(e, iid), d_other, lifecycle_id=kids[0])
        assert "error" in res and "does not serve" in res["error"]
        assert "gate" not in res
    finally:
        e.memory.close()
