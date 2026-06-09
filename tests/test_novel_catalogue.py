"""Spec 106 Slice 1 — novel catalogue cluster (graph-only).

Slice 1 ships 1 graph-only coherence verb: `manuscript_coherence_check`.
DBDriver-backed verbs (beta reader registry / edit notes / version log)
+ composite beta_feedback_gate land in Slice 2 once the DBDriver protocol
is declared (parallel to music's 097 pattern).
"""
from __future__ import annotations

import tempfile

import pytest

from agency.engine import Engine


def _fresh() -> Engine:
    return Engine(tempfile.mktemp(suffix=".db"))


def _confirmed_iid(e: Engine, purpose: str = "spec 106") -> str:
    iid = e.intent.capture(purpose, "catalogue", "verified")
    e.intent.confirm(iid)
    return iid


def _invoke(e: Engine, iid: str, verb: str, **kw):
    return e.registry.invoke(e.memory, iid, "novel", verb, **kw)


def test_novel_capability_registers_manuscript_coherence_check() -> None:
    e = _fresh()
    cap = e.registry._caps["novel"]
    assert "manuscript_coherence_check" in cap.verbs
    e.memory.close()


def test_manuscript_coherence_check_passes_contiguous_chapters() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    novel, _ = _invoke(e, iid, "create_novel", title="X", author="Y")
    _invoke(e, iid, "create_chapter",
            novel_id=novel["novel_id"], number=1, title="A")
    _invoke(e, iid, "create_chapter",
            novel_id=novel["novel_id"], number=2, title="B")
    _invoke(e, iid, "create_chapter",
            novel_id=novel["novel_id"], number=3, title="C")
    data, _ = _invoke(e, iid, "manuscript_coherence_check",
                      novel_id=novel["novel_id"])
    assert data["passed"] is True
    assert data["chapter_count"] == 3
    assert data["gaps"] == []
    e.memory.close()


def test_manuscript_coherence_check_detects_gaps() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    novel, _ = _invoke(e, iid, "create_novel", title="X", author="Y")
    _invoke(e, iid, "create_chapter",
            novel_id=novel["novel_id"], number=1, title="A")
    _invoke(e, iid, "create_chapter",
            novel_id=novel["novel_id"], number=3, title="C")
    _invoke(e, iid, "create_chapter",
            novel_id=novel["novel_id"], number=5, title="E")
    data, _ = _invoke(e, iid, "manuscript_coherence_check",
                      novel_id=novel["novel_id"])
    assert data["passed"] is False
    assert data["gaps"] == [2, 4]
    e.memory.close()


def test_manuscript_coherence_check_empty_novel() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    novel, _ = _invoke(e, iid, "create_novel", title="X", author="Y")
    data, _ = _invoke(e, iid, "manuscript_coherence_check",
                      novel_id=novel["novel_id"])
    # No chapters → no gaps, but passes vacuously
    assert data["chapter_count"] == 0
    assert data["passed"] is True
    e.memory.close()


def test_manuscript_coherence_check_not_found() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    data, inv = _invoke(e, iid, "manuscript_coherence_check",
                        novel_id="novel:nope")
    assert data is None
    err = e.memory.recall(inv).get("error", "")
    assert "NOT_FOUND" in err
    e.memory.close()
