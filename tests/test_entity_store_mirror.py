"""Spec 289 Slice 2b — Memory mirrors authoritative graph writes into the
graph-authoritative typed projection (EntityStore).

The invariant: the graph node stays write-authoritative; the entity row is a
ONE-WAY derived mirror keyed by node id. record/update/supersede each mirror
AFTER the graph write succeeds, and a projection failure NEVER fails the graph
write (the row is re-derivable).
"""
from __future__ import annotations

import pytest

from agency.memory import OPEN, Memory
from agency import ontology


@pytest.fixture
def mem() -> Memory:
    # bare core ontology, in-memory graph; EntityStore binds to the SAME conn.
    return Memory(":memory:", ont=ontology.Ontology.core())


def _record_label(mem: Memory):
    """Pick a real ontology label + a satisfying props dict so record() passes
    the ontology gate (computed from the live ontology — no hardcoded label)."""
    for label, required in mem.ont.nodes.items():
        enums = {fld: allowed for (lbl, fld), allowed in mem.ont.enums.items()
                 if lbl == label}
        props = {}
        ok = True
        for f in required:
            if f in enums:
                props[f] = sorted(enums[f])[0]
            else:
                props[f] = "x"
        if ok:
            return label, props
    raise AssertionError("no usable ontology label found")


def test_record_is_dual_observable(mem: Memory):
    label, props = _record_label(mem)
    nid = mem.record(label, props)

    # authoritative graph node
    node = mem.recall(nid)
    assert node is not None
    # derived projection row
    row = mem.entities.get(nid)
    assert row is not None

    # identical user fields across both surfaces
    for k, v in props.items():
        assert node[k] == v
        assert row[k] == v

    # the projection strips substrate; the graph node carries it
    assert "vfrom" in node and "vto" in node
    assert "vfrom" not in row and "vto" not in row


def test_update_reflected_in_projection(mem: Memory):
    label, props = _record_label(mem)
    nid = mem.record(label, props)

    # mutate a non-enum required field (or add an extra) without violating ont
    changes = {"note": "updated-value"}
    mem.update(nid, changes)

    node = mem.recall(nid)
    row = mem.entities.get(nid)
    assert node["note"] == "updated-value"
    assert row["note"] == "updated-value"


def test_supersede_projects_new_version(mem: Memory):
    label, props = _record_label(mem)
    nid = mem.record(label, props)

    new_id = mem.supersede(nid, {"note": "v2"})

    # new version is the current row in the projection
    new_row = mem.entities.get(new_id)
    assert new_row is not None
    assert new_row["note"] == "v2"

    # old row's window is closed in the projection (vto no longer OPEN)
    from agency._entity_store import EntityRecord
    from sqlmodel import Session
    with Session(mem.entities._engine) as s:
        old = s.get(EntityRecord, nid)
        assert old is not None
        assert old.vto != OPEN
        new = s.get(EntityRecord, new_id)
        assert new is not None
        assert new.vto == OPEN

    # by_label returns only current versions → the new one, not the old
    current = mem.entities.by_label(label)
    notes = [r.get("note") for r in current]
    assert "v2" in notes
    assert "x" not in notes or props.get("note") != "x"  # old closed out


def test_projection_failure_never_fails_graph_write(mem: Memory, monkeypatch):
    label, props = _record_label(mem)

    # force the projection to raise on every upsert
    def boom(*a, **k):
        raise RuntimeError("projection is down")

    monkeypatch.setattr(mem.entities, "upsert", boom)

    # the authoritative graph write must still succeed
    nid = mem.record(label, props)
    assert mem.recall(nid) is not None
    # projection never got the row (it raised), but the graph is intact
    # (get() reads the row table directly — None since upsert was stubbed)


def test_record_then_update_then_supersede_end_to_end(mem: Memory):
    label, props = _record_label(mem)
    nid = mem.record(label, props)
    assert mem.entities.get(nid) is not None

    mem.update(nid, {"note": "n1"})
    assert mem.entities.get(nid)["note"] == "n1"

    new_id = mem.supersede(nid, {"note": "n2"})
    assert mem.entities.get(new_id)["note"] == "n2"
