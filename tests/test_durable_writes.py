"""Spec 282 Workstream C — durable batch writes.

Evidence (kohaerenzprotokoll): 97 NarrativeBeat nodes, only 12 PRECEDES edges.
Two distinct engine-side defects this guards against:

1. `Memory.link` is non-durable. `graphqlite.upsert_edge` runs `MERGE` then a
   SEPARATE `SET r.vfrom = ...`; under concurrent MCP+CLI writes that SET raises
   `Failed to set property 'vfrom' on edge N`. The edge write must RETRY the
   transient contention (Spec 282 classifies it transient) instead of dropping
   the edge — while a NON-transient error still fails fast.

2. `mark_narrative_beat` records the NarrativeBeat node BEFORE validating
   `predecessor_id`, so a bad predecessor leaves an orphan node + no edge. A
   create-node-AND-edge verb must validate preconditions before any write.
"""
from __future__ import annotations

import tempfile

from agency.engine import Engine


def _iid(e: Engine) -> str:
    iid = e.intent.capture("spec 282 C", "durable writes", "verified")
    e.intent.confirm(iid)
    return iid


def _scene(e: Engine, iid: str) -> str:
    novel, _ = e.registry.invoke(e.memory, iid, "novel", "create_novel",
                                 title="K", author="A")
    ch, _ = e.registry.invoke(e.memory, iid, "novel", "create_chapter",
                              novel_id=novel["novel_id"], number=1, title="C")
    sc, _ = e.registry.invoke(e.memory, iid, "novel", "create_scene",
                              chapter_id=ch["chapter_id"], slug="s1",
                              pov="first")
    return sc["scene_id"]


def _beat_count(e: Engine) -> int:
    rows = e.memory.g.query("MATCH (n:NarrativeBeat) RETURN count(n) AS c")
    return rows[0]["c"] if rows else 0


def _precedes_count(e: Engine) -> int:
    rows = e.memory.g.query("MATCH ()-[r:PRECEDES]->() RETURN count(r) AS c")
    return rows[0]["c"] if rows else 0


# ── 1. Memory.link retries the transient contention and persists the edge ──

def test_link_retries_transient_and_persists() -> None:
    e = Engine(tempfile.mktemp(suffix=".db"))
    iid = _iid(e)
    sid = _scene(e, iid)
    b1, _ = e.registry.invoke(e.memory, iid, "novel", "mark_narrative_beat",
                              scene_id=sid, beat_label="opening")
    b2, _ = e.registry.invoke(e.memory, iid, "novel", "mark_narrative_beat",
                              scene_id=sid, beat_label="inciting")

    # Inject ONE transient contention failure into the next edge write, then
    # let the real upsert proceed.
    real = e.memory.g.upsert_edge
    state = {"failed": False}

    def flaky(src, dst, data, rel_type="RELATED"):
        if rel_type == "PRECEDES" and not state["failed"]:
            state["failed"] = True
            raise RuntimeError("Failed to set property 'vfrom' on edge 9")
        return real(src, dst, data, rel_type=rel_type)

    e.memory.g.upsert_edge = flaky
    before = _precedes_count(e)
    e.memory.link(b2["beat_id"], b1["beat_id"], "PRECEDES")
    assert state["failed"] is True            # the transient was hit
    assert _precedes_count(e) == before + 1   # …and the edge still persisted
    e.memory.close()


def test_link_does_not_retry_non_transient() -> None:
    e = Engine(tempfile.mktemp(suffix=".db"))
    iid = _iid(e)
    sid = _scene(e, iid)
    b1, _ = e.registry.invoke(e.memory, iid, "novel", "mark_narrative_beat",
                              scene_id=sid, beat_label="opening")
    b2, _ = e.registry.invoke(e.memory, iid, "novel", "mark_narrative_beat",
                              scene_id=sid, beat_label="inciting")

    calls = {"n": 0}

    def boom(src, dst, data, rel_type="RELATED"):
        calls["n"] += 1
        raise ValueError("schema is wrong")   # permanent/fatal — not retryable

    e.memory.g.upsert_edge = boom
    raised = False
    try:
        e.memory.link(b2["beat_id"], b1["beat_id"], "PRECEDES")
    except ValueError:
        raised = True
    assert raised is True
    assert calls["n"] == 1                     # failed fast, no retry storm
    e.memory.close()


# ── 2. mark_narrative_beat validates predecessor BEFORE writing the node ──

def test_bad_predecessor_leaves_no_orphan_beat() -> None:
    e = Engine(tempfile.mktemp(suffix=".db"))
    iid = _iid(e)
    sid = _scene(e, iid)
    before = _beat_count(e)
    data, inv = e.registry.invoke(
        e.memory, iid, "novel", "mark_narrative_beat",
        scene_id=sid, beat_label="x", predecessor_id="beat:does-not-exist")
    assert data is None                                   # NOT_FOUND failure
    assert "NOT_FOUND" in e.memory.recall(inv).get("error", "")
    assert _beat_count(e) == before                       # NO orphan node
    e.memory.close()


def test_valid_predecessor_creates_beat_and_edge() -> None:
    e = Engine(tempfile.mktemp(suffix=".db"))
    iid = _iid(e)
    sid = _scene(e, iid)
    b1, _ = e.registry.invoke(e.memory, iid, "novel", "mark_narrative_beat",
                              scene_id=sid, beat_label="opening")
    before_beats, before_edges = _beat_count(e), _precedes_count(e)
    b2, _ = e.registry.invoke(e.memory, iid, "novel", "mark_narrative_beat",
                              scene_id=sid, beat_label="inciting",
                              predecessor_id=b1["beat_id"])
    assert b2 is not None and b2.get("beat_id")
    assert _beat_count(e) == before_beats + 1
    assert _precedes_count(e) == before_edges + 1
    e.memory.close()
