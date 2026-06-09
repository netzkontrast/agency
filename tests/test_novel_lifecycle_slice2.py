"""Spec 102 Slice 2 — novel lifecycle delta: chapter + scene + session verbs.

6 NEW verbs extending Slice 1's lifecycle surface:
- list_chapters(novel_id) — transform, ordered by number
- create_scene(chapter_id, slug, pov) — effect, Scene node + SCENE_OF edge
- set_chapter_status(chapter_id, status) — effect, CHAPTER_STATUS-checked
- rename_novel(novel_id, new_title) — effect, mutate Novel.title
- novel_progress(novel_id) — transform, aggregate word-count + chapter-status
- resume_session() — transform, return last-novel context

Plus ontology additions: Scene node + SCENE_OF edge + SCENE_POV enum.
"""
from __future__ import annotations

import tempfile

import pytest

from agency.engine import Engine


def _fresh() -> Engine:
    return Engine(tempfile.mktemp(suffix=".db"))


def _confirmed_iid(e: Engine, purpose: str = "spec 102 slice 2") -> str:
    iid = e.intent.capture(purpose, "chapter+scene+session", "verified")
    e.intent.confirm(iid)
    return iid


def _invoke(e: Engine, iid: str, verb: str, **kw):
    return e.registry.invoke(e.memory, iid, "novel", verb, **kw)


# ─────────────────────── ontology additions ───────────────────────


def test_scene_node_declared_with_pov_enum() -> None:
    e = _fresh()
    cap = e.registry._caps["novel"]
    assert "Scene" in cap.ontology.nodes
    assert ("Scene", "pov") in cap.ontology.enums
    povs = cap.ontology.enums[("Scene", "pov")]
    # Standard POV set covers the canonical scene-craft choices.
    assert {"first", "third-limited", "third-omniscient", "second"} <= povs
    e.memory.close()


def test_scene_of_edge_declared() -> None:
    e = _fresh()
    cap = e.registry._caps["novel"]
    assert "SCENE_OF" in cap.ontology.edges
    e.memory.close()


# ─────────────────────── list_chapters ───────────────────────


def test_list_chapters_returns_ordered_by_number() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    novel, _ = _invoke(e, iid, "create_novel", title="X", author="Y")
    nid = novel["novel_id"]
    _invoke(e, iid, "create_chapter", novel_id=nid, number=3, title="C")
    _invoke(e, iid, "create_chapter", novel_id=nid, number=1, title="A")
    _invoke(e, iid, "create_chapter", novel_id=nid, number=2, title="B")
    data, _ = _invoke(e, iid, "list_chapters", novel_id=nid)
    assert data["count"] == 3
    nums = [c["number"] for c in data["chapters"]]
    assert nums == [1, 2, 3]
    e.memory.close()


def test_list_chapters_empty_novel() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    novel, _ = _invoke(e, iid, "create_novel", title="X", author="Y")
    data, _ = _invoke(e, iid, "list_chapters", novel_id=novel["novel_id"])
    assert data["count"] == 0
    assert data["chapters"] == []
    e.memory.close()


def test_list_chapters_not_found() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    data, inv = _invoke(e, iid, "list_chapters", novel_id="novel:nope")
    assert data is None
    err = e.memory.recall(inv).get("error", "")
    assert "NOT_FOUND" in err
    e.memory.close()


# ─────────────────────── create_scene ───────────────────────


def test_create_scene_records_node_and_scene_of_edge() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    novel, _ = _invoke(e, iid, "create_novel", title="X", author="Y")
    chap, _ = _invoke(e, iid, "create_chapter",
                      novel_id=novel["novel_id"], number=1, title="Opening")
    data, _ = _invoke(e, iid, "create_scene",
                      chapter_id=chap["chapter_id"],
                      slug="cold-open",
                      pov="third-limited")
    assert data["scene_id"].startswith("scene:")
    assert data["chapter_id"] == chap["chapter_id"]
    assert data["pov"] == "third-limited"
    rows = e.memory.g.query(
        "MATCH (s)-[r:SCENE_OF]->(c) WHERE s.id = $sid AND c.id = $cid RETURN r",
        {"sid": data["scene_id"], "cid": chap["chapter_id"]})
    assert rows
    e.memory.close()


def test_create_scene_rejects_invalid_pov() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    novel, _ = _invoke(e, iid, "create_novel", title="X", author="Y")
    chap, _ = _invoke(e, iid, "create_chapter",
                      novel_id=novel["novel_id"], number=1, title="A")
    data, inv = _invoke(e, iid, "create_scene",
                        chapter_id=chap["chapter_id"],
                        slug="bad-pov", pov="omniscient-but-spelt-wrong")
    assert data is None
    assert "INVALID_ARGUMENT" in e.memory.recall(inv).get("error", "")
    e.memory.close()


def test_create_scene_not_found_chapter() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    data, inv = _invoke(e, iid, "create_scene",
                        chapter_id="chapter:nope",
                        slug="x", pov="first")
    assert data is None
    assert "NOT_FOUND" in e.memory.recall(inv).get("error", "")
    e.memory.close()


# ─────────────────────── set_chapter_status ───────────────────────


def test_set_chapter_status_flips_and_returns() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    novel, _ = _invoke(e, iid, "create_novel", title="X", author="Y")
    chap, _ = _invoke(e, iid, "create_chapter",
                      novel_id=novel["novel_id"], number=1, title="A")
    data, _ = _invoke(e, iid, "set_chapter_status",
                      chapter_id=chap["chapter_id"], status="drafted")
    assert data["status"] == "drafted"
    assert e.memory.recall(chap["chapter_id"])["status"] == "drafted"
    e.memory.close()


def test_set_chapter_status_rejects_invalid() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    novel, _ = _invoke(e, iid, "create_novel", title="X", author="Y")
    chap, _ = _invoke(e, iid, "create_chapter",
                      novel_id=novel["novel_id"], number=1, title="A")
    data, inv = _invoke(e, iid, "set_chapter_status",
                        chapter_id=chap["chapter_id"], status="bogus")
    assert data is None
    assert "INVALID_ARGUMENT" in e.memory.recall(inv).get("error", "")
    e.memory.close()


def test_set_chapter_status_not_found() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    data, inv = _invoke(e, iid, "set_chapter_status",
                        chapter_id="chapter:nope", status="drafted")
    assert data is None
    assert "NOT_FOUND" in e.memory.recall(inv).get("error", "")
    e.memory.close()


# ─────────────────────── rename_novel ───────────────────────


def test_rename_novel_updates_title() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    novel, _ = _invoke(e, iid, "create_novel",
                       title="Original Title", author="Author")
    data, _ = _invoke(e, iid, "rename_novel",
                      novel_id=novel["novel_id"],
                      new_title="Renamed Title")
    assert data["title"] == "Renamed Title"
    assert e.memory.recall(novel["novel_id"])["title"] == "Renamed Title"
    e.memory.close()


def test_rename_novel_not_found() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    data, inv = _invoke(e, iid, "rename_novel",
                        novel_id="novel:nope", new_title="x")
    assert data is None
    assert "NOT_FOUND" in e.memory.recall(inv).get("error", "")
    e.memory.close()


# ─────────────────────── novel_progress ───────────────────────


def test_novel_progress_aggregates_word_count_and_status() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    novel, _ = _invoke(e, iid, "create_novel", title="X", author="Y")
    nid = novel["novel_id"]
    c1, _ = _invoke(e, iid, "create_chapter", novel_id=nid,
                    number=1, title="A", body="word " * 50)
    c2, _ = _invoke(e, iid, "create_chapter", novel_id=nid,
                    number=2, title="B", body="word " * 100)
    _invoke(e, iid, "set_chapter_status",
            chapter_id=c1["chapter_id"], status="drafted")
    data, _ = _invoke(e, iid, "novel_progress", novel_id=nid)
    assert data["chapter_count"] == 2
    assert data["word_count_total"] >= 150
    assert data["by_status"]["drafted"] == 1
    assert data["by_status"]["outlined"] == 1
    e.memory.close()


def test_novel_progress_not_found() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    data, inv = _invoke(e, iid, "novel_progress", novel_id="novel:nope")
    assert data is None
    assert "NOT_FOUND" in e.memory.recall(inv).get("error", "")
    e.memory.close()


# ─────────────────────── resume_session ───────────────────────


def test_resume_session_returns_most_recent_novel() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    _invoke(e, iid, "create_novel", title="First", author="X")
    last, _ = _invoke(e, iid, "create_novel", title="Last", author="Y")
    data, _ = _invoke(e, iid, "resume_session")
    assert data["novel_id"] == last["novel_id"]
    assert data["title"] == "Last"
    e.memory.close()


def test_resume_session_when_no_novels_returns_empty() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    data, _ = _invoke(e, iid, "resume_session")
    assert data["novel_id"] == ""
    assert data["title"] == ""
    e.memory.close()
