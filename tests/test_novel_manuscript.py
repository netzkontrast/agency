"""Spec 107 Slice 1 — novel manuscript cluster (driver-free renderers).

3 driver-free deterministic artefact renderers for publication packages:
- render_blurb (back-cover copy)
- render_query_letter (agent query template)
- render_synopsis (chapter aggregate)

FormatDriver-backed verbs (epub / PDF / docx export via pandoc + the
shell-out fakes) + publication_gate + walkable skills land in Slice 2.
"""
from __future__ import annotations

import tempfile

import pytest

from agency.engine import Engine


def _fresh() -> Engine:
    return Engine(tempfile.mktemp(suffix=".db"))


def _confirmed_iid(e: Engine, purpose: str = "spec 107") -> str:
    iid = e.intent.capture(purpose, "manuscript", "verified")
    e.intent.confirm(iid)
    return iid


def _invoke(e: Engine, iid: str, verb: str, **kw):
    return e.registry.invoke(e.memory, iid, "novel", verb, **kw)


def test_novel_capability_registers_manuscript_verbs() -> None:
    e = _fresh()
    cap = e.registry._caps["novel"]
    expected = {"render_blurb", "render_query_letter", "render_synopsis"}
    missing = expected - set(cap.verbs)
    assert not missing, f"missing manuscript verbs: {missing}"
    e.memory.close()


def test_render_blurb_produces_artefact() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    novel, _ = _invoke(e, iid, "create_novel",
                       title="Modem Daze", author="The Phreakers")
    data, _ = _invoke(e, iid, "render_blurb",
                      novel_id=novel["novel_id"],
                      hook="A phreaker discovers a secret BBS",
                      stakes="The sysop is watching")
    assert data["artefact"]["kind"] == "blurb"
    assert "Modem Daze" in data["result"]
    assert "phreaker" in data["result"].lower()
    assert "sysop" in data["result"].lower()
    e.memory.close()


def test_render_blurb_not_found() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    data, inv = _invoke(e, iid, "render_blurb",
                        novel_id="novel:nope",
                        hook="x", stakes="y")
    assert data is None
    err = e.memory.recall(inv).get("error", "")
    assert "NOT_FOUND" in err
    e.memory.close()


def test_render_query_letter_produces_artefact() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    novel, _ = _invoke(e, iid, "create_novel",
                       title="Modem Daze", author="The Phreakers")
    data, _ = _invoke(e, iid, "render_query_letter",
                      novel_id=novel["novel_id"],
                      agent_name="Jane Smith",
                      comp_titles="Neuromancer, Snow Crash")
    assert data["artefact"]["kind"] == "query-letter"
    body = data["result"]
    assert "Jane Smith" in body
    assert "Modem Daze" in body
    assert "The Phreakers" in body
    assert "Neuromancer" in body
    e.memory.close()


def test_render_synopsis_aggregates_chapters() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    novel, _ = _invoke(e, iid, "create_novel",
                       title="Modem Daze", author="The Phreakers")
    _invoke(e, iid, "create_chapter",
            novel_id=novel["novel_id"], number=1, title="Connection")
    _invoke(e, iid, "create_chapter",
            novel_id=novel["novel_id"], number=2, title="Discovery")
    _invoke(e, iid, "create_chapter",
            novel_id=novel["novel_id"], number=3, title="Confrontation")
    data, _ = _invoke(e, iid, "render_synopsis",
                      novel_id=novel["novel_id"])
    assert data["artefact"]["kind"] == "synopsis"
    body = data["result"]
    # Chapter titles appear in order
    assert body.index("Connection") < body.index("Discovery")
    assert body.index("Discovery") < body.index("Confrontation")


def test_render_synopsis_not_found() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    data, inv = _invoke(e, iid, "render_synopsis",
                        novel_id="novel:nope")
    assert data is None
    err = e.memory.recall(inv).get("error", "")
    assert "NOT_FOUND" in err
    e.memory.close()
