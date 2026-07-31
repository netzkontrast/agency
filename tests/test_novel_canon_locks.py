"""Spec 137 — canon provenance markers & locks (the KP [K]/[V]/[S]/[L] discipline).

``canon_status`` rides as a cross-cutting property on any novel-domain node;
``Lock`` nodes carry canonized decisions with a newer-wins supersession chain;
the Master-Index (``lock_index``) is consulted before contested drafting; the
``canon_gate`` predicate refuses to treat proposal/quarry as fact without an
explicit override — never silent canonization of speculation.
"""
from __future__ import annotations

import tempfile

from agency.engine import Engine


def _fresh() -> Engine:
    return Engine(tempfile.mktemp(suffix=".db"))


def _iid(e: Engine) -> str:
    iid = e.intent.capture("spec 137", "canon locks", "verified")
    e.intent.confirm(iid)
    return iid


def _invoke(e: Engine, iid: str, verb: str, **kw):
    r, _ = e.registry.invoke(e.memory, iid, "novel", verb, **kw)
    return r


def _setup(e, iid):
    nid = _invoke(e, iid, "create_novel", title="KP", author="A")["novel_id"]
    entry = _invoke(e, iid, "create_codex_entry", novel_id=nid, slug="kw1",
                    name="Kernwelt 1", kind="concept",
                    body="the first Kernwelt")["entry_id"]
    return nid, entry


def test_canon_status_enum_and_lock_node_registered() -> None:
    e = _fresh()
    cap = e.registry.get("novel")
    assert "Lock" in cap.ontology.nodes
    assert "LOCKS" in cap.ontology.edges
    from agency.capabilities.novel.clusters.canon import CANON_STATUS
    assert CANON_STATUS == {"canonical", "proposal", "quarry", "gap"}
    e.memory.close()


def test_set_canon_status_happy_and_reject_unknown() -> None:
    e = _fresh()
    iid = _iid(e)
    _, entry = _setup(e, iid)
    out = _invoke(e, iid, "set_canon_status", node_id=entry,
                  status="proposal")
    assert out["canon_status"] == "proposal" and out["was"] == ""
    again = _invoke(e, iid, "set_canon_status", node_id=entry,
                    status="canonical")
    assert again["was"] == "proposal"
    assert _invoke(e, iid, "set_canon_status", node_id=entry,
                   status="nope") is None


def test_record_lock_and_supersession_chain() -> None:
    e = _fresh()
    iid = _iid(e)
    nid, _ = _setup(e, iid)
    l1 = _invoke(e, iid, "record_lock", novel_id=nid, topic="kw1-physik",
                 content="Gravity reverses at dusk.", source="log-A",
                 locked_on="2026-05-30")["lock_id"]
    l2 = _invoke(e, iid, "record_lock", novel_id=nid, topic="kw1-physik",
                 content="Gravity reverses at dawn.", source="kompendium",
                 locked_on="2026-05-31", supersedes=l1)
    assert l2["supersedes"] == l1
    assert e.memory.recall(l1).get("superseded_by") == l2["lock_id"]
    # superseded lock survives (audit chain) but leaves the active index
    idx = _invoke(e, iid, "lock_index", novel_id=nid)
    ids = [l["id"] for l in idx["locks"]]
    assert l2["lock_id"] in ids and l1 not in ids
    assert idx["by_topic"]["kw1-physik"] == 1


def test_lock_index_sorted_newest_first_and_topic_filter() -> None:
    e = _fresh()
    iid = _iid(e)
    nid, _ = _setup(e, iid)
    _invoke(e, iid, "record_lock", novel_id=nid, topic="a",
            content="x", source="s", locked_on="2026-01-01")
    _invoke(e, iid, "record_lock", novel_id=nid, topic="b",
            content="y", source="s", locked_on="2026-06-01")
    idx = _invoke(e, iid, "lock_index", novel_id=nid)
    dates = [l["locked_on"] for l in idx["locks"]]
    assert dates == sorted(dates, reverse=True)
    only_b = _invoke(e, iid, "lock_index", novel_id=nid, topic="b")
    assert only_b["count"] == 1 and only_b["locks"][0]["topic"] == "b"


def test_resolve_canon_conflict_newer_wins_and_quarry_loses() -> None:
    e = _fresh()
    iid = _iid(e)
    out = _invoke(e, iid, "resolve_canon_conflict", candidates=[
        {"node_id": "n1", "canon_status": "canonical",
         "source_date": "2026-05-30"},
        {"node_id": "n2", "canon_status": "proposal",
         "source_date": "2026-05-31"},
        {"node_id": "n3", "canon_status": "quarry",
         "source_date": "2026-06-30"},        # newest but quarry — loses
    ])
    assert out["winner"] == "n2"
    assert set(out["losers"]) == {"n1", "n3"}


def test_resolve_canon_conflict_tie_returns_tied() -> None:
    e = _fresh()
    iid = _iid(e)
    out = _invoke(e, iid, "resolve_canon_conflict", candidates=[
        {"node_id": "n1", "canon_status": "canonical",
         "source_date": "2026-05-30"},
        {"node_id": "n2", "canon_status": "canonical",
         "source_date": "2026-05-30"},
    ])
    assert out["tied"] is True


def test_quarry_filter_and_promotion() -> None:
    e = _fresh()
    iid = _iid(e)
    nid, entry = _setup(e, iid)
    _invoke(e, iid, "set_canon_status", node_id=entry, status="quarry")
    q = _invoke(e, iid, "quarry_filter", novel_id=nid)
    assert q["count"] == 1 and q["nodes"][0]["node_id"] == entry
    out = _invoke(e, iid, "promote_from_quarry", node_id=entry,
                  source="review 2026-06-28")
    assert out["new_status"] == "proposal"
    assert e.memory.recall(entry).get("canon_status") == "proposal"
    # the promotion is itself locked (audit)
    assert e.memory.recall(out["lock_id"]).get("topic", "").startswith(
        "promote:")
    # promoting a non-quarry node is a typed failure
    assert _invoke(e, iid, "promote_from_quarry", node_id=entry,
                   source="x") is None


def test_canon_audit_census_gaps_and_unmarked() -> None:
    e = _fresh()
    iid = _iid(e)
    nid, entry = _setup(e, iid)
    gap = _invoke(e, iid, "create_codex_entry", novel_id=nid, slug="tbd",
                  name="TBD", kind="concept", body="?")["entry_id"]
    _invoke(e, iid, "set_canon_status", node_id=entry, status="canonical")
    _invoke(e, iid, "set_canon_status", node_id=gap, status="gap")
    _invoke(e, iid, "create_codex_entry", novel_id=nid, slug="unmarked",
            name="Unmarked", kind="concept", body="no status")
    _invoke(e, iid, "record_lock", novel_id=nid, topic="t", content="c",
            source="s", locked_on="2026-06-01")
    audit = _invoke(e, iid, "canon_audit", novel_id=nid)
    assert audit["counts"]["canonical"] == 1
    assert audit["counts"]["gap"] == 1
    assert audit["counts"]["unmarked"] >= 1
    assert any(g["node_id"] == gap for g in audit["gaps"])
    assert audit["latest_locks"]


def test_canon_gate_blocks_proposal_without_override() -> None:
    e = _fresh()
    iid = _iid(e)
    _, entry = _setup(e, iid)
    _invoke(e, iid, "set_canon_status", node_id=entry, status="proposal")
    out = _invoke(e, iid, "canon_gate", node_id=entry)
    assert out["passed"] is False
    assert "lock_index" in out["advice"]
    ok = _invoke(e, iid, "canon_gate", node_id=entry, override=True)
    assert ok["passed"] is True
    _invoke(e, iid, "set_canon_status", node_id=entry, status="canonical")
    assert _invoke(e, iid, "canon_gate", node_id=entry)["passed"] is True
