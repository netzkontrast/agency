"""Spec 341 Slice 2 — manage.lifecycle_trail(scope=…): the unified cross-lifecycle
transition view.

The per-lifecycle `lifecycle_trail(lifecycle_id)` already ships. Slice 2's remaining
gap is the *scope* mode — a single call that folds the durable transition trail
across every live lifecycle matching a scope (e.g. all `jules` lifecycles), so an
observer sees the whole in-flight board's history without iterating ids. Read-only,
decidable, additive (the per-lifecycle signature is unchanged).
"""
from __future__ import annotations

from agency.engine import Engine


def _trail(eng, iid, **kw):
    return eng.registry.invoke(eng.memory, iid, "manage", "lifecycle_trail", **kw)[0]


def _transition(eng, lid, frm, to):
    ev = eng.memory.record("Event", {"name": "lifecycle_transition",
                                     "session": "test-session",
                                     "from_state": frm, "to_state": to,
                                     "evidence": f"{frm}->{to}"})
    eng.memory.link(ev, lid, "OBSERVED_DURING")
    return ev


def test_lifecycle_trail_scope_aggregates_matching_lifecycles():
    eng = Engine(":memory:")
    try:
        iid = eng.intent.capture("p", "d", "a")
        eng.intent.confirm(iid)

        # two jules-scoped lifecycles, each with a durable transition…
        a = eng.lifecycle.open(iid, kind="jules", machine="remote-async")
        b = eng.lifecycle.open(iid, kind="jules", machine="remote-async")
        _transition(eng, a, "submitted", "completed")
        _transition(eng, b, "submitted", "failed")
        # …and one unrelated lifecycle whose transition must NOT appear.
        c = eng.lifecycle.open(iid, kind="task", machine="a2a")
        _transition(eng, c, "submitted", "completed")

        res = _trail(eng, iid, scope="jules")
        assert "error" not in res, res
        # both jules transitions folded in; the task one excluded.
        assert res["count"] == 2, res
        assert res.get("lifecycles") == 2, res
        tos = sorted(t["to_state"] for t in res["transitions"])
        assert tos == ["completed", "failed"], res
        # each aggregated transition is tagged with its lifecycle id.
        assert all(t.get("lifecycle_id") in (a, b) for t in res["transitions"]), res
    finally:
        eng.memory.close()


def test_lifecycle_trail_per_lifecycle_mode_unchanged():
    """The existing single-lifecycle signature still works (additive change)."""
    eng = Engine(":memory:")
    try:
        iid = eng.intent.capture("p", "d", "a")
        eng.intent.confirm(iid)
        a = eng.lifecycle.open(iid, kind="jules", machine="remote-async")
        _transition(eng, a, "submitted", "completed")
        res = _trail(eng, iid, lifecycle_id=a)
        assert res["lifecycle_id"] == a
        assert res["count"] == 1
        assert res["transitions"][0]["to_state"] == "completed"
    finally:
        eng.memory.close()


def test_lifecycle_trail_needs_an_id_or_a_scope():
    eng = Engine(":memory:")
    try:
        iid = eng.intent.capture("p", "d", "a")
        eng.intent.confirm(iid)
        res = _trail(eng, iid)            # neither id nor scope
        assert "error" in res, res
    finally:
        eng.memory.close()
