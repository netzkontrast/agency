"""Spec 103 Slice 2 (Workstream D) — create_storyform / get_storyform.

Closes the documented ENGINE GAP: the storyform gates + checks read a
`Storyform` node, but no verb minted one. These verbs mint it properly
(STORYFORM_OF edge + JSON body) and read it back.
"""
from __future__ import annotations

import tempfile

from agency.engine import Engine


def _fresh() -> Engine:
    return Engine(tempfile.mktemp(suffix=".db"))


def _iid(e: Engine) -> str:
    iid = e.intent.capture("spec 103 s2", "storyform node verb", "verified")
    e.intent.confirm(iid)
    return iid


def _invoke(e: Engine, iid: str, verb: str, **kw):
    return e.registry.invoke(e.memory, iid, "novel", verb, **kw)


def _novel(e: Engine, iid: str) -> str:
    n, _ = _invoke(e, iid, "create_novel", title="K", author="A")
    return n["novel_id"]


def test_storyform_of_edge_declared() -> None:
    e = _fresh()
    cap = e.registry.get("novel")
    assert "STORYFORM_OF" in cap.ontology.edges
    e.memory.close()


def test_create_storyform_records_node_and_edge() -> None:
    e = _fresh()
    iid = _iid(e)
    nid = _novel(e, iid)
    data, _ = _invoke(e, iid, "create_storyform", novel_id=nid,
                      body={"storyform": {"throughlines": {}}})
    assert data["storyform_id"].startswith("storyform:")
    assert data["novel_id"] == nid
    assert data["has_body"] is True
    rows = e.memory.g.query(
        "MATCH (s)-[r:STORYFORM_OF]->(n) WHERE s.id = $sid AND n.id = $nid RETURN r",
        {"sid": data["storyform_id"], "nid": nid})
    assert rows
    e.memory.close()


def test_create_storyform_is_idempotent_per_novel() -> None:
    e = _fresh()
    iid = _iid(e)
    nid = _novel(e, iid)
    first, _ = _invoke(e, iid, "create_storyform", novel_id=nid)
    second, _ = _invoke(e, iid, "create_storyform", novel_id=nid,
                        body={"storyform": {"crucial_element_id": "el.1"}})
    assert first["storyform_id"] == second["storyform_id"]   # no duplicate
    # exactly one Storyform for this novel
    sfs = [s for s in e.memory.find("Storyform") if s.get("novel") == nid]
    assert len(sfs) == 1
    e.memory.close()


def test_create_storyform_rejects_unknown_novel() -> None:
    e = _fresh()
    iid = _iid(e)
    data, inv = _invoke(e, iid, "create_storyform", novel_id="novel:nope")
    assert data is None
    assert "not_found" in e.memory.recall(inv).get("error", "")
    e.memory.close()


def test_get_storyform_roundtrips_body() -> None:
    e = _fresh()
    iid = _iid(e)
    nid = _novel(e, iid)
    payload = {"storyform": {"throughlines": {"mc": {"class_id": "c.universe"}}}}
    _invoke(e, iid, "create_storyform", novel_id=nid, body=payload)
    got, _ = _invoke(e, iid, "get_storyform", novel_id=nid)
    assert got["found"] is True
    assert got["body"] == payload          # JSON round-trip preserves the NCP
    e.memory.close()


def test_get_storyform_absent_returns_found_false() -> None:
    e = _fresh()
    iid = _iid(e)
    nid = _novel(e, iid)
    got, _ = _invoke(e, iid, "get_storyform", novel_id=nid)
    assert got["found"] is False
    e.memory.close()
