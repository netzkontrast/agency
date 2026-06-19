"""Session-graph snapshot export/import — round-trip + value-only (Spec follow-up).

The durable provenance must survive export→import with no loss; the ephemeral
Event noise must be excluded ("only export what has value").
"""
from __future__ import annotations

from agency import _session_snapshot as snap
from agency.engine import Engine


def test_snapshot_round_trips_durable_provenance_and_excludes_events(tmp_path):
    db = str(tmp_path / "session.db")
    e = Engine(db)
    e.intent.capture_and_confirm("real durable work", "ship it", "tests pass")
    e.memory.record("Event", {"name": "PostToolUse", "session": "s"})   # ephemeral noise
    e.memory.close()

    out = str(tmp_path / "sql" / "snap.sql")
    r = snap.export(graph_db=db, out=out)
    assert r["exported"] and r["nodes"] >= 1, r
    sql = open(out, encoding="utf-8").read()
    assert "real durable work" in sql, "durable Intent must be exported"
    assert "PostToolUse" not in sql, "ephemeral Event must be excluded (value-only)"

    restored = str(tmp_path / "restored.db")
    ri = snap.import_snapshot(sql=out, target_db=restored)
    assert ri["imported"], ri
    e2 = Engine(restored)
    intents = e2.memory.find("Intent")
    assert any(i["purpose"] == "real durable work" for i in intents), \
        "the durable Intent must be restored into a fresh db"
    assert e2.memory.find("Event") == [], "no ephemeral Events restored"
    e2.memory.close()


def test_snapshot_export_is_deterministic(tmp_path):
    db = str(tmp_path / "session.db")
    e = Engine(db)
    e.intent.capture_and_confirm("p", "d", "a")
    e.memory.close()
    a = str(tmp_path / "a.sql")
    b = str(tmp_path / "b.sql")
    snap.export(graph_db=db, out=a)
    snap.export(graph_db=db, out=b)
    # deterministic (sorted) → identical bytes → minimal git diffs
    assert open(a, encoding="utf-8").read() == open(b, encoding="utf-8").read()
