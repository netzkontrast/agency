"""Spec 222 — novel catalogue graph-query + budget.

Cross-work queries traverse the declared edges (CHAPTER_OF/SCENE_OF/
ECHOES_IN), the output honors max_rows + next_cursor paging, the prefix block
is byte-stable per author scope, and fields projects the rows.
"""
from __future__ import annotations

import inspect
import json
import tempfile

from agency.engine import Engine


def _fresh() -> Engine:
    return Engine(tempfile.mktemp(suffix=".db"))


def _iid(e: Engine) -> str:
    iid = e.intent.capture("spec 222", "catalogue query", "verified")
    e.intent.confirm(iid)
    return iid


def _invoke(e, iid, verb, **kw):
    r, _ = e.registry.invoke(e.memory, iid, "novel", verb, **kw)
    return r


def _corpus(e, iid):
    """Two novels by one author, one by another; a motif echoing across
    works."""
    scenes = []
    for title in ("Alpha", "Beta"):
        nid = _invoke(e, iid, "create_novel", title=title,
                      author="miriam")["novel_id"]
        ch = _invoke(e, iid, "create_chapter", novel_id=nid, number=1,
                     title="I")["chapter_id"]
        sid = _invoke(e, iid, "create_scene", chapter_id=ch,
                      slug=f"{title.lower()}-s1", pov="first")["scene_id"]
        scenes.append(sid)
    other = _invoke(e, iid, "create_novel", title="Gamma",
                    author="someone-else")["novel_id"]
    och = _invoke(e, iid, "create_chapter", novel_id=other, number=1,
                  title="I")["chapter_id"]
    _invoke(e, iid, "create_scene", chapter_id=och, slug="gamma-s1",
            pov="first")
    _invoke(e, iid, "record_motif_echo", scene_id=scenes[0],
            motif_slug="betrayal")
    return scenes


def test_cross_work_query_traverses_edges() -> None:
    e = _fresh()
    iid = _iid(e)
    scenes = _corpus(e, iid)
    out = _invoke(e, iid, "catalogue_query", author="miriam")
    body = out["body"]
    assert body["total"] == 2                     # other author excluded
    assert {"CHAPTER_OF", "SCENE_OF"} <= set(body["edges_traversed"])
    # motif filter narrows via the ECHOES_IN edge
    hit = _invoke(e, iid, "catalogue_query", author="miriam",
                  motif="betrayal")
    assert hit["body"]["total"] == 1
    assert hit["body"]["rows"][0]["scene_id"] == scenes[0]
    assert "ECHOES_IN" in hit["body"]["edges_traversed"]


def test_no_dormant_edge_scan_in_impl() -> None:
    from agency.capabilities.novel.clusters.lifecycle import LifecycleMixin
    src = inspect.getsource(LifecycleMixin.catalogue_query)
    assert 'find("Scene")' not in src             # traversal, not scan
    assert "neighbors" in src


def test_budget_paging_and_fields_projection() -> None:
    e = _fresh()
    iid = _iid(e)
    nid = _invoke(e, iid, "create_novel", title="Big",
                  author="paginator")["novel_id"]
    ch = _invoke(e, iid, "create_chapter", novel_id=nid, number=1,
                 title="I")["chapter_id"]
    for i in range(5):
        _invoke(e, iid, "create_scene", chapter_id=ch, slug=f"s{i}",
                pov="first")
    page1 = _invoke(e, iid, "catalogue_query", author="paginator",
                    max_rows=2)["body"]
    assert page1["shown"] == 2 and page1["total"] == 5
    assert page1["next_cursor"] == 2
    page2 = _invoke(e, iid, "catalogue_query", author="paginator",
                    max_rows=2, cursor=page1["next_cursor"])["body"]
    assert page2["shown"] == 2 and page2["next_cursor"] == 4
    last = _invoke(e, iid, "catalogue_query", author="paginator",
                   max_rows=2, cursor=4)["body"]
    assert last["shown"] == 1 and last["next_cursor"] is None
    proj = _invoke(e, iid, "catalogue_query", author="paginator",
                   fields="scene_id,slug", max_rows=1)["body"]
    assert set(proj["rows"][0]) == {"scene_id", "slug"}


def test_prefix_byte_stable_per_author_scope() -> None:
    e = _fresh()
    iid = _iid(e)
    _corpus(e, iid)
    a = _invoke(e, iid, "catalogue_query", author="miriam")["prefix"]
    b = _invoke(e, iid, "catalogue_query", author="miriam",
                motif="betrayal")["prefix"]
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)
    assert a["author_id"] == "miriam" and a["capability_set_hash"]
