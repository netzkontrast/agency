"""Spec 121 — novel production binding (NovelConfig + FileNovelStateDriver).

Per Spec 121's done-when:
- NovelConfig 4-level resolution (per-project + global + env + defaults)
- FileNovelStateDriver writes prior-spec-010 layout (works/{author}/works/{genre}/{slug}/)
- Template substitution (F3) + frontmatter `status` as single source (F4/F5)
- Lazy auto-wiring (mirrors Spec 117): production flag → drivers register on
  first miss; bare unit-test engines keep typed DEPENDENCY_MISSING.
- create_novel + create_chapter gain optional disk side-effects.
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from agency.capabilities.novel.config import NovelConfig
from agency.capabilities.novel.drivers_production import (
    FileNovelStateDriver, production_drivers,
)
from agency.engine import Engine


def _fresh() -> Engine:
    return Engine(tempfile.mktemp(suffix=".db"))


def _iid(e: Engine) -> str:
    return e.intent.capture_and_confirm(
        "spec 121 production", "disk layout", "verbs round-trip",
        owner="user")


def _invoke(e: Engine, iid: str, verb: str, **kw):
    r, _ = e.registry.invoke(e.memory, iid, "novel", verb,
                             agent_id="agent:test", **kw)
    return r


# ---------------------------------------------------------------------------
# NovelConfig — 4-level resolution + bootstrap.
# ---------------------------------------------------------------------------


def test_novel_config_defaults_load() -> None:
    cfg = NovelConfig.defaults()
    assert cfg.content_root.endswith("novel-projects")
    assert cfg.default_genre == "novel"
    assert cfg.default_target_word_count == 80000


def test_novel_config_loads_from_per_project_yaml(tmp_path) -> None:
    cfg_path = tmp_path / ".agency" / "novel-config.yaml"
    cfg_path.parent.mkdir(parents=True)
    cfg_path.write_text("""\
author:
  name: "Ursula Test"
paths:
  content_root: "%s/works"
defaults:
  genre: "scifi"
  target_word_count: 60000
""" % tmp_path)
    cfg = NovelConfig.load([str(cfg_path)])
    assert cfg.author_name == "Ursula Test"
    assert cfg.content_root == str(tmp_path / "works")
    assert cfg.default_genre == "scifi"
    assert cfg.default_target_word_count == 60000


def test_novel_config_bootstrap_writes_default(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    # NovelConfig.load caches by absolute paths; a fresh tmp_path is its own key.
    cfg = NovelConfig.bootstrap()
    assert (tmp_path / ".agency" / "novel-config.yaml").is_file()
    # content_root expanded + created
    assert Path(cfg.content_root).is_dir()


def test_novel_config_load_mtime_cache(tmp_path) -> None:
    cfg_path = tmp_path / "novel-config.yaml"
    cfg_path.write_text('author:\n  name: "v1"\n')
    a = NovelConfig.load([str(cfg_path)])
    b = NovelConfig.load([str(cfg_path)])
    assert a is b  # same instance — mtime-cached


# ---------------------------------------------------------------------------
# FileNovelStateDriver — disk layout per prior-spec-010.
# ---------------------------------------------------------------------------


def test_create_work_uses_prior_spec_010_layout(tmp_path) -> None:
    cfg = NovelConfig.defaults()
    cfg.content_root = str(tmp_path)
    drv = FileNovelStateDriver(cfg)
    out = drv.create_work("Ursula K. Le Guin", "scifi", "The Dispossessed")
    expected = (tmp_path / "works" / "ursula-k-le-guin"
                / "works" / "scifi" / "the-dispossessed")
    assert Path(out["path"]) == expected
    assert (expected / "work.md").is_file()
    assert (expected / "chapters").is_dir()
    assert (expected / "scenes").is_dir()


def test_create_work_substitutes_template_fields(tmp_path) -> None:
    """F3 — render fidelity: template placeholders replaced with real values."""
    cfg = NovelConfig.defaults()
    cfg.content_root = str(tmp_path)
    drv = FileNovelStateDriver(cfg)
    drv.create_work("J. Test", "fantasy", "Bridge of Birds",
                    logline="A herbalist's quest across mythic China.")
    work_md = (tmp_path / "works" / "j-test" / "works" / "fantasy"
               / "bridge-of-birds" / "work.md").read_text()
    assert "j-test" in work_md          # author_slug substituted
    assert "bridge-of-birds" in work_md  # work_slug substituted
    assert "Bridge of Birds" in work_md  # work_title substituted
    assert "fantasy" in work_md          # genre_slug substituted
    assert "{{author_slug}}" not in work_md   # no unsubstituted placeholders


def test_update_work_field_round_trip(tmp_path) -> None:
    """F4 — frontmatter status round-trips (no .meta.json sidecar)."""
    cfg = NovelConfig.defaults()
    cfg.content_root = str(tmp_path)
    drv = FileNovelStateDriver(cfg)
    drv.create_work("A. Author", "scifi", "Test Work")
    assert drv.update_work_field("A. Author", "scifi", "Test Work",
                                  "status", "drafting") is True
    text = (tmp_path / "works" / "a-author" / "works" / "scifi"
            / "test-work" / "work.md").read_text()
    assert 'status: "drafting"' in text


def test_create_chapter_writes_numbered_file(tmp_path) -> None:
    cfg = NovelConfig.defaults()
    cfg.content_root = str(tmp_path)
    drv = FileNovelStateDriver(cfg)
    drv.create_work("A. Author", "scifi", "Test Work")
    out = drv.create_chapter("A. Author", "scifi", "Test Work",
                              3, "The Crossing")
    chap = Path(out["path"])
    assert chap.name == "03-the-crossing.md"
    text = chap.read_text()
    assert 'title: "The Crossing"' in text
    assert 'chapter_number: "3"' in text or 'chapter_number: 3' in text


def test_list_chapters_returns_sorted(tmp_path) -> None:
    cfg = NovelConfig.defaults()
    cfg.content_root = str(tmp_path)
    drv = FileNovelStateDriver(cfg)
    drv.create_work("A. Author", "scifi", "Test Work")
    drv.create_chapter("A. Author", "scifi", "Test Work", 2, "Second")
    drv.create_chapter("A. Author", "scifi", "Test Work", 1, "First")
    chs = drv.list_chapters("A. Author", "scifi", "Test Work")
    assert [c["number"] for c in chs] == [1, 2]
    assert chs[0]["title"] == "First"


def test_write_then_read_ncp(tmp_path) -> None:
    cfg = NovelConfig.defaults()
    cfg.content_root = str(tmp_path)
    drv = FileNovelStateDriver(cfg)
    drv.create_work("A. Author", "scifi", "Test Work")
    drv.write_ncp("A. Author", "scifi", "Test Work",
                   {"schema_version": "1.3.0", "storyform": {}})
    body = drv.read_ncp("A. Author", "scifi", "Test Work")
    assert body == {"schema_version": "1.3.0", "storyform": {}}


# ---------------------------------------------------------------------------
# Lazy auto-wiring — Spec 117 pattern for novel.
# ---------------------------------------------------------------------------


def test_bare_engine_no_disk_write(tmp_path) -> None:
    """Unit test default: no production flag → no disk write."""
    e = _fresh()
    iid = _iid(e)
    r = _invoke(e, iid, "create_novel",
                title="Bare Test", author="A. Author")
    assert "work_path" not in r   # no driver wired
    assert r["novel_id"]
    assert not (tmp_path / "works").exists()


def test_production_engine_writes_disk(tmp_path, monkeypatch) -> None:
    """With `_novel_production = True` + content_root pointed at tmp_path,
    create_novel materialises the work tree."""
    monkeypatch.chdir(tmp_path)
    # Pre-write a config so bootstrap finds it (avoids touching $HOME).
    cfg_path = tmp_path / ".agency" / "novel-config.yaml"
    cfg_path.parent.mkdir(parents=True)
    cfg_path.write_text(f"""\
author:
  name: "Production Test"
paths:
  content_root: "{tmp_path}/output"
""")
    e = _fresh()
    e._novel_production = True
    iid = _iid(e)
    r = _invoke(e, iid, "create_novel",
                title="Production Work", author="A. Author",
                genre="literary")
    assert "work_path" in r
    work_root = (tmp_path / "output" / "works" / "a-author"
                 / "works" / "literary" / "production-work")
    assert (work_root / "work.md").is_file()


def test_production_create_chapter_writes_disk(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    cfg_path = tmp_path / ".agency" / "novel-config.yaml"
    cfg_path.parent.mkdir(parents=True)
    cfg_path.write_text(f"""\
author:
  name: "Test"
paths:
  content_root: "{tmp_path}/output"
""")
    e = _fresh()
    e._novel_production = True
    iid = _iid(e)
    nv = _invoke(e, iid, "create_novel",
                 title="Disk Work", author="A. Author", genre="literary")
    _invoke(e, iid, "create_chapter",
            novel_id=nv["novel_id"], number=1, title="Opening")
    expected = (tmp_path / "output" / "works" / "a-author"
                / "works" / "literary" / "disk-work"
                / "chapters" / "01-opening.md")
    assert expected.is_file()


def test_production_drivers_bundle_factory() -> None:
    """The factory returns the canonical driver-name dict, symmetric to music."""
    cfg = NovelConfig.defaults()
    bundle = production_drivers(cfg)
    assert "novel_state" in bundle
    assert isinstance(bundle["novel_state"], FileNovelStateDriver)
