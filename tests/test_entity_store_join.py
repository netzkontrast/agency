"""Spec 289 Slice 2b — EntityStore.entity_join(node_ids): inline content query.

The spec's named verb (spec.md:70,82,102): given graph node ids (e.g. from a
Cypher id-only query), return each one's mirrored entity content in ONE round-trip
— the "querying entity contents inline" the owner directive asks for. Order-
preserving, absent ids skipped. Purely additive (no existing caller), so zero
blast radius on the graph-authoritative mirror.
"""
from __future__ import annotations

from agency._entity_store import EntityStore


def test_entity_join_returns_content_in_order_skipping_absent():
    store = EntityStore()  # standalone in-memory
    store.upsert("n1", "Intent", {"purpose": "p1"})
    store.upsert("n2", "Reflection", {"text": "r2"})
    store.upsert("n3", "Document", {"path": "d3"})

    rows = store.entity_join(["n2", "missing", "n1"])

    # order of the input ids is preserved; the absent id is skipped, not faked.
    assert [r["id"] for r in rows] == ["n2", "n1"]
    assert rows[0]["label"] == "Reflection"
    assert rows[0]["data"]["text"] == "r2"
    assert rows[1]["label"] == "Intent"
    assert rows[1]["data"]["purpose"] == "p1"


def test_entity_join_empty_input_is_empty():
    store = EntityStore()
    store.upsert("n1", "Intent", {"purpose": "p"})
    assert store.entity_join([]) == []
