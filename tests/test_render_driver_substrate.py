"""Spec 283 Slice 1 (Workstream F) — capability render substrate.

Covers the pure substrate (_frontmatter round-trip, RenderRule/RenderDriver)
and the novel `render_all` full-rebuild path: graph → markdown view + one
Artefact per file (the graph/disk drift closure).
"""
from __future__ import annotations

import tempfile

from agency import _frontmatter
from agency._render import (
    FakeRenderDriver,
    FileRenderDriver,
    RenderRule,
    RenderSpec,
    render_node,
)
from agency.capability import DriverRegistry
from agency.engine import Engine


# ─────────────────────── frontmatter round-trip ───────────────────────


def test_frontmatter_emit_parse_roundtrip() -> None:
    fm = {"id": "chapter:1", "kind": "chapter", "number": 3, "title": "Opening"}
    text = _frontmatter.emit(fm, "the body\nsecond line")
    parsed, body = _frontmatter.parse(text)
    assert parsed["id"] == "chapter:1"
    assert parsed["kind"] == "chapter"
    assert parsed["number"] == 3          # int round-trips
    assert parsed["title"] == "Opening"
    assert body == "the body\nsecond line"


def test_frontmatter_hash_stable_and_sensitive() -> None:
    a = {"id": "x", "title": "A"}
    assert _frontmatter.frontmatter_hash(a) == _frontmatter.frontmatter_hash(dict(a))
    assert _frontmatter.frontmatter_hash(a) != _frontmatter.frontmatter_hash({"id": "x", "title": "B"})


def test_no_frontmatter_parse_is_identity() -> None:
    fm, body = _frontmatter.parse("no frontmatter here")
    assert fm == {}
    assert body == "no frontmatter here"


# ─────────────────────── RenderRule / drivers ───────────────────────


_RULE = RenderRule(
    label="Chapter", kind="chapter",
    output_path=lambda n: f"chapters/{n['number']:02d}.md",
    frontmatter=lambda n: {"id": n["id"], "kind": "chapter"},
    body=lambda n: n.get("body", ""),
)


def test_render_node_is_pure() -> None:
    path, fm, body = render_node(_RULE, {"id": "c:1", "number": 2, "body": "X"})
    assert path == "chapters/02.md"
    assert fm == {"id": "c:1", "kind": "chapter"}
    assert body == "X"


def test_fake_render_driver_records_calls() -> None:
    d = FakeRenderDriver()
    d.write("chapters/01.md", {"id": "c:1"}, "body")
    assert d.calls == ["chapters/01.md"]
    assert "id: \"c:1\"" in d.files["chapters/01.md"]


def test_file_render_driver_is_idempotent(tmp_path) -> None:
    d = FileRenderDriver(tmp_path)
    p1 = d.write("chapters/01.md", {"id": "c:1"}, "body")
    mtime1 = (tmp_path / "chapters" / "01.md").stat().st_mtime_ns
    p2 = d.write("chapters/01.md", {"id": "c:1"}, "body")   # byte-identical
    mtime2 = (tmp_path / "chapters" / "01.md").stat().st_mtime_ns
    assert p1 == p2
    assert mtime1 == mtime2                # no rewrite on identical content
    spec = RenderSpec(rules=[_RULE])
    assert spec.rule_for("Chapter") is _RULE
    assert spec.labels == {"Chapter"}


# ─────────────────────── novel render_all (drift closure) ───────────────────────


def _fresh(**kw) -> Engine:
    return Engine(tempfile.mktemp(suffix=".db"), **kw)


def _iid(e: Engine) -> str:
    iid = e.intent.capture("spec 283", "render view", "verified")
    e.intent.confirm(iid)
    return iid


def _invoke(e, iid, verb, **kw):
    return e.registry.invoke(e.memory, iid, "novel", verb, **kw)


def _novel_with_chapters(e, iid, n: int) -> str:
    novel, _ = _invoke(e, iid, "create_novel", title="K", author="A")
    nid = novel["novel_id"]
    for i in range(1, n + 1):
        _invoke(e, iid, "create_chapter", novel_id=nid, number=i, title=f"Ch {i}")
    return nid


def test_render_all_mints_one_artefact_per_entity() -> None:
    # The drift-closure assertion (inverse of the 2-for-41 evidence): one
    # Artefact per rendered file (1 novel + N chapters).
    e = _fresh()
    iid = _iid(e)
    nid = _novel_with_chapters(e, iid, 3)
    data, _ = _invoke(e, iid, "render_all", novel_id=nid)
    assert data["count"] == 4                       # work.md + 3 chapters
    paths = {r["path"] for r in data["rendered"]}
    assert "work.md" in paths
    assert "chapters/01-ch-1.md" in paths
    render_artefacts = [a for a in e.memory.find("Artefact")
                        if a.get("kind") in ("novel", "chapter")]
    assert len(render_artefacts) == 4               # #Artefacts == #files
    assert data["wrote_disk"] is False              # no driver wired → graph-only
    e.memory.close()


def test_render_all_writes_through_wired_driver() -> None:
    e = _fresh()
    e.drivers.register("render", FakeRenderDriver())
    iid = _iid(e)
    nid = _novel_with_chapters(e, iid, 2)
    data, _ = _invoke(e, iid, "render_all", novel_id=nid)
    assert data["wrote_disk"] is True
    fake = e.drivers.get("render")
    assert set(fake.calls) == {"work.md", "chapters/01-ch-1.md", "chapters/02-ch-2.md"}
    # the written file carries the node id in frontmatter (round-trips)
    fm, _ = _frontmatter.parse(fake.files["chapters/01-ch-1.md"])
    assert fm["kind"] == "chapter"
    assert fm["id"].startswith("chapter:")
    e.memory.close()


def test_render_all_is_idempotent_on_artefact_shape() -> None:
    e = _fresh()
    iid = _iid(e)
    nid = _novel_with_chapters(e, iid, 1)
    first, _ = _invoke(e, iid, "render_all", novel_id=nid)
    hashes_1 = {a["entity_id"]: a.get("frontmatter_hash")
                for a in e.memory.find("Artefact") if a.get("kind") in ("novel", "chapter")}
    second, _ = _invoke(e, iid, "render_all", novel_id=nid)
    # re-render of unchanged nodes yields the same frontmatter hash per entity
    hashes_2 = {a["entity_id"]: a.get("frontmatter_hash")
                for a in e.memory.find("Artefact") if a.get("kind") in ("novel", "chapter")}
    for ent, h in hashes_1.items():
        assert hashes_2.get(ent) == h
    assert first["count"] == second["count"] == 2
    e.memory.close()


def test_render_all_rejects_unknown_novel() -> None:
    e = _fresh()
    iid = _iid(e)
    data, inv = _invoke(e, iid, "render_all", novel_id="novel:nope")
    assert data is None
    assert "not_found" in e.memory.recall(inv).get("error", "")
    e.memory.close()
