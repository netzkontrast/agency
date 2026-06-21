"""Spec 289 Slice 2 — the canonical SQLite-backed entity store.

Proves the store round-trips entities AND coexists with the graph in ONE
SQLite database (shared connection), so the graph node id links to a typed,
SQL-queryable, FastAPI-ready row — the user's 'store entities in sqlite, IDs in
the graph, one db, query inline' vision.
"""
from __future__ import annotations

from agency._entity_store import EntityStore
from agency.memory import Memory


def test_upsert_get_roundtrip():
    store = EntityStore(":memory:")
    store.upsert("plan:abc", "Plan", {"title": "Ship X", "status": "drafted"})
    assert store.get("plan:abc") == {"title": "Ship X", "status": "drafted"}


def test_upsert_is_idempotent_update():
    store = EntityStore(":memory:")
    store.upsert("plan:abc", "Plan", {"title": "v1"})
    store.upsert("plan:abc", "Plan", {"title": "v2"})
    assert store.get("plan:abc")["title"] == "v2"
    assert store.count() == 1


def test_by_label_filters():
    store = EntityStore(":memory:")
    store.upsert("plan:1", "Plan", {"title": "a"})
    store.upsert("plan:2", "Plan", {"title": "b"})
    store.upsert("step:1", "PlanStep", {"index": 1})
    titles = {r["title"] for r in store.by_label("Plan")}
    assert titles == {"a", "b"}
    assert len(store.by_label("PlanStep")) == 1


def test_substrate_fields_are_stripped_from_data():
    store = EntityStore(":memory:")
    store.upsert("plan:abc", "Plan",
                 {"title": "X", "id": "plan:abc", "vfrom": 5, "vto": 99, "labels": ["Plan"]})
    assert store.get("plan:abc") == {"title": "X"}      # substrate excluded from data


def test_shares_one_db_with_the_graph(tmp_path):
    """The entity store binds to the SAME sqlite connection as graphqlite, so a
    graph node and its entity row live in ONE .db, linked by id — and the entity
    table is visible via the graph's own raw-SQL connection (inline-join ready)."""
    db = str(tmp_path / "shared.db")
    mem = Memory(db)
    try:
        raw = mem.g._conn.sqlite_connection                 # graphqlite's real sqlite3 conn
        store = EntityStore(sqlite_connection=raw)
        # record a graph node + the canonical entity row under the SAME id
        # (Artefact is a CORE ontology label — required: ["kind"]).
        nid = mem.record("Artefact", {"kind": "file", "path": "ship.md"})
        store.upsert(nid, "Artefact", mem.recall(nid))
        # the entity row is retrievable from the store
        assert store.get(nid)["path"] == "ship.md"
        # AND the entity table is visible on the graph's own connection (one db)
        rows = raw.execute(
            "SELECT id, label FROM agency_entity WHERE id = ?", (nid,)).fetchall()
        assert rows and rows[0][0] == nid and rows[0][1] == "Artefact"
        # the graph node still exists too (dual representation, same id)
        assert mem.recall(nid)["path"] == "ship.md"
    finally:
        mem.close()
