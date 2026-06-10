"""Spec 124 — novel FormatDriver + 3 export verbs + publication_gate.

FakeFormatDriver (zero binaries in CI) + 3 export verbs + composite
publication_gate + publish-prep walkable skill.
"""
from __future__ import annotations

import tempfile

import pytest

from agency.capabilities.novel.drivers_production import (
    FakeFormatDriver, production_drivers,
)
from agency.capabilities.novel.config import NovelConfig
from agency.engine import Engine


def _fresh_production_engine(tmp_path):
    e = Engine(tempfile.mktemp(suffix=".db"))
    e._novel_production = True
    return e


def _iid(e):
    return e.intent.capture_and_confirm(
        "spec 124 format", "exports written", "publication gate fires",
        owner="user")


def _invoke(e, iid, verb, **kw):
    r, _ = e.registry.invoke(e.memory, iid, "novel", verb,
                              agent_id="agent:test", **kw)
    return r


# ---------------------------------------------------------------------------
# FakeFormatDriver — deterministic, no binaries.
# ---------------------------------------------------------------------------


def test_fake_driver_lists_three_formats():
    drv = FakeFormatDriver()
    assert set(drv.available_formats()) == {"epub", "pdf", "docx"}


def test_fake_driver_records_calls():
    drv = FakeFormatDriver()
    drv.to_epub("# Manuscript body\n", {"title": "Test", "slug": "test"})
    drv.to_pdf("# Other body\n", {"title": "Test 2", "slug": "test-2"})
    assert len(drv.calls) == 2
    assert drv.calls[0]["format"] == "epub"
    assert drv.calls[1]["format"] == "pdf"


def test_fake_driver_paths_are_deterministic():
    drv1 = FakeFormatDriver()
    drv2 = FakeFormatDriver()
    p1 = drv1.to_epub("# Body\n", {"title": "Test", "slug": "test"})
    p2 = drv2.to_epub("# Body\n", {"title": "Test", "slug": "test"})
    assert p1 == p2  # same input → same path


def test_fake_driver_path_changes_with_manuscript():
    drv = FakeFormatDriver()
    p1 = drv.to_epub("# Body A\n", {"slug": "test"})
    p2 = drv.to_epub("# Body B\n", {"slug": "test"})
    assert p1 != p2


# ---------------------------------------------------------------------------
# production_drivers bundle wires novel_format.
# ---------------------------------------------------------------------------


def test_production_drivers_bundle_includes_format():
    bundle = production_drivers(NovelConfig.defaults())
    assert "novel_format" in bundle
    assert isinstance(bundle["novel_format"], FakeFormatDriver)


# ---------------------------------------------------------------------------
# Export verbs — graph-only path is typed DEPENDENCY_MISSING; production
# path writes through the driver + records Artefact.
# ---------------------------------------------------------------------------


def test_export_epub_bare_engine_dependency_missing():
    e = Engine(tempfile.mktemp(suffix=".db"))
    iid = e.intent.capture_and_confirm(
        "t", "d", "a", owner="user")
    nv, _ = e.registry.invoke(
        e.memory, iid, "novel", "create_novel",
        agent_id="a", title="Test", author="A", genre="lit")
    r = _invoke(e, iid, "export_epub", novel_id=nv["novel_id"])
    # ToolResult.failure unwraps to None via registry — confirms typed failure.
    assert r is None


def test_export_epub_production_writes_artefact(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    cfg_path = tmp_path / ".agency" / "novel-config.yaml"
    cfg_path.parent.mkdir(parents=True)
    cfg_path.write_text(f"""\
author:
  name: "Test"
paths:
  content_root: "{tmp_path}/output"
""")
    e = _fresh_production_engine(tmp_path)
    iid = _iid(e)
    nv = _invoke(e, iid, "create_novel",
                 title="Export Test", author="A. Author", genre="lit")
    _invoke(e, iid, "create_chapter",
            novel_id=nv["novel_id"], number=1, title="Ch 1",
            body="The opening line.")
    r = _invoke(e, iid, "export_epub", novel_id=nv["novel_id"])
    assert r["format"] == "epub"
    assert r["path"].endswith(".epub")
    assert r["artefact_id"]
    # Artefact carries kind + format + path + novel_id
    node = e.memory.g.get_node(r["artefact_id"])
    props = node["properties"]
    assert props["kind"] == "published-manuscript"
    assert props["format"] == "epub"


def test_export_pdf_and_docx_each_produce_artefact(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    cfg_path = tmp_path / ".agency" / "novel-config.yaml"
    cfg_path.parent.mkdir(parents=True)
    cfg_path.write_text(f"""\
author:
  name: "Test"
paths:
  content_root: "{tmp_path}/output"
""")
    e = _fresh_production_engine(tmp_path)
    iid = _iid(e)
    nv = _invoke(e, iid, "create_novel",
                 title="Multi-format Test", author="A", genre="lit")
    _invoke(e, iid, "create_chapter",
            novel_id=nv["novel_id"], number=1, title="Ch 1", body="Body")
    pdf = _invoke(e, iid, "export_pdf", novel_id=nv["novel_id"])
    docx = _invoke(e, iid, "export_docx", novel_id=nv["novel_id"])
    assert pdf["format"] == "pdf"
    assert docx["format"] == "docx"
    assert pdf["artefact_id"] != docx["artefact_id"]


# ---------------------------------------------------------------------------
# publication_gate composite.
# ---------------------------------------------------------------------------


def test_publication_gate_blocks_without_exports(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    cfg_path = tmp_path / ".agency" / "novel-config.yaml"
    cfg_path.parent.mkdir(parents=True)
    cfg_path.write_text(f"""\
author:
  name: "Test"
paths:
  content_root: "{tmp_path}/output"
""")
    e = _fresh_production_engine(tmp_path)
    iid = _iid(e)
    nv = _invoke(e, iid, "create_novel",
                 title="Gate Test", author="A", genre="lit")
    _invoke(e, iid, "create_chapter",
            novel_id=nv["novel_id"], number=1, title="Ch 1")
    r = _invoke(e, iid, "publication_gate", novel_id=nv["novel_id"])
    # No exports yet → GATE_FAILED
    assert r is None


def test_publication_gate_passes_with_exports_and_declarations(
        tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    cfg_path = tmp_path / ".agency" / "novel-config.yaml"
    cfg_path.parent.mkdir(parents=True)
    cfg_path.write_text(f"""\
author:
  name: "Test"
paths:
  content_root: "{tmp_path}/output"
""")
    e = _fresh_production_engine(tmp_path)
    iid = _iid(e)
    nv = _invoke(e, iid, "create_novel",
                 title="Pass Test", author="A", genre="lit")
    _invoke(e, iid, "create_chapter",
            novel_id=nv["novel_id"], number=1, title="Ch 1", body="Body")
    # Flip status so publish_ready_gate doesn't block.
    e.memory.update(nv["novel_id"], {
        "status": "querying",
        "content_warnings": "",   # declared, even if empty
    })
    _invoke(e, iid, "export_epub", novel_id=nv["novel_id"])
    r = _invoke(e, iid, "publication_gate", novel_id=nv["novel_id"])
    assert r["passed"] is True
    assert r["checks"]["has_exports"] is True
    assert len(r["exports"]) >= 1


# ---------------------------------------------------------------------------
# Walkable skill registration.
# ---------------------------------------------------------------------------


def test_publish_prep_skill_registered():
    e = Engine(tempfile.mktemp(suffix=".db"))
    skill = e.ontology.skills.get("publish-prep")
    assert skill is not None
    phases = {p["name"]: p for p in skill["phases"]}
    assert {"manuscript-pass", "export-pass", "publication-gate",
             "sign-off"} <= set(phases)
    # Phase 3 binds to publication_gate; phase 4 is hard gate.
    assert "novel.publication_gate" in phases["publication-gate"]["verbs"]
    assert phases["sign-off"]["gate"] == "hard"


def test_export_verbs_registered():
    e = Engine(tempfile.mktemp(suffix=".db"))
    verbs = set(e.registry.get("novel").verbs)
    assert {"export_epub", "export_pdf", "export_docx",
             "publication_gate"} <= verbs
