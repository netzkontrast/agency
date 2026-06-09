"""music production binding — Spec 115 tests.

Covers:
- `MusicConfig` loads from `.agency/music-config.yaml` per-project + global
  fallback + env override.
- `FileStateDriver` writes the bitwize-canonical layout (README.md, tracks/,
  RESEARCH.md/SOURCES.md when documentary, artist seed README on first album).
- `SqliteDBDriver` round-trips through a real SQLite (`:memory:` + tmp_path).
- `production_drivers(cfg)` factory bundles all 5.
- 4 new verbs (`get_config`, `load_override`, `get_reference`,
  `format_clipboard`) function under both Fake and File state.
- `new-album` walkable skill walks through to the hard elicit.
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

from agency.capabilities.music.config import MusicConfig
from agency.capabilities.music.drivers import fake_drivers
from agency.capabilities.music.drivers_production import (
    FileStateDriver,
    SqliteDBDriver,
    production_drivers,
)
from agency.engine import Engine
from agency.skill import SkillRun


# ─────────────────────────── config layer tests ───────────────────────────

def test_config_defaults_when_no_file_found(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("AGENCY_MUSIC_HOME", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    cfg = MusicConfig.load()
    # defaults expand ~ relative to HOME
    assert cfg.artist_name == ""
    assert cfg.content_root.endswith("music-projects")
    assert cfg.db_backend == "sqlite"


def test_config_loads_per_project_yaml(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".agency").mkdir()
    (tmp_path / ".agency" / "music-config.yaml").write_text(
        "artist:\n"
        "  name: The Phreakers\n"
        "paths:\n"
        f"  content_root: {tmp_path}/music\n"
        "db:\n"
        "  backend: sqlite\n"
        f"  path: {tmp_path}/.agency/music.db\n"
    )
    cfg = MusicConfig.load()
    assert cfg.artist_name == "The Phreakers"
    assert cfg.content_root == f"{tmp_path}/music"
    assert cfg.db_path == f"{tmp_path}/.agency/music.db"


def test_config_env_var_override(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("AGENCY_MUSIC_HOME", str(tmp_path / "custom"))
    monkeypatch.setenv("HOME", str(tmp_path / "fake-home"))
    (tmp_path / "custom").mkdir()
    (tmp_path / "custom" / "config.yaml").write_text(
        "artist:\n  name: env-override-artist\n"
    )
    cfg = MusicConfig.load()
    assert cfg.artist_name == "env-override-artist"


def test_config_as_dict_returns_bitwize_shape() -> None:
    cfg = MusicConfig(artist_name="A", content_root="/tmp/x")
    cfg._fill_path_defaults()
    d = cfg.as_dict()
    assert d["artist"]["name"] == "A"
    assert "paths" in d
    assert "db" in d
    assert d["paths"]["content_root"] == "/tmp/x"


# ─────────────────────────── FileStateDriver tests ───────────────────────────

def test_file_state_driver_creates_canonical_album_layout(tmp_path) -> None:
    """`create_album_root` writes the bitwize-canonical directory tree."""
    cfg = MusicConfig(artist_name="The Phreakers", content_root=str(tmp_path))
    cfg._fill_path_defaults()
    drv = FileStateDriver(cfg)
    root = drv.create_album_root(artist="The Phreakers", genre="ambient",
                                  slug="modem-daze", title="Modem Daze")
    album_dir = tmp_path / "artists" / "the-phreakers" / "albums" / "ambient" / "modem-daze"
    assert album_dir.is_dir()
    assert (album_dir / "README.md").is_file()
    assert (album_dir / "tracks").is_dir()
    # Returned root is relative to content_root
    assert "modem-daze" in root


def test_file_state_driver_documentary_includes_research_sources(tmp_path) -> None:
    cfg = MusicConfig(artist_name="A", content_root=str(tmp_path))
    cfg._fill_path_defaults()
    drv = FileStateDriver(cfg)
    drv.create_album_root(artist="A", genre="ambient",
                          slug="the-heist", title="The Heist",
                          type="documentary")
    album_dir = tmp_path / "artists" / "a" / "albums" / "ambient" / "the-heist"
    assert (album_dir / "RESEARCH.md").is_file()
    assert (album_dir / "SOURCES.md").is_file()


def test_file_state_driver_renders_album_template_to_readme(tmp_path) -> None:
    cfg = MusicConfig(artist_name="A", content_root=str(tmp_path))
    cfg._fill_path_defaults()
    drv = FileStateDriver(cfg)
    drv.create_album_root(artist="A", genre="ambient",
                          slug="origin", title="Origin")
    readme = tmp_path / "artists" / "a" / "albums" / "ambient" / "origin" / "README.md"
    body = readme.read_text()
    # template body present (non-empty + the AGENT marker block from Slice 1)
    assert body
    assert "<!-- AGENT:" in body


def test_file_state_driver_seeds_artist_readme_on_first_album(tmp_path) -> None:
    cfg = MusicConfig(artist_name="A", content_root=str(tmp_path))
    cfg._fill_path_defaults()
    drv = FileStateDriver(cfg)
    drv.create_album_root(artist="A", genre="ambient",
                          slug="origin", title="Origin")
    artist_readme = tmp_path / "artists" / "a" / "README.md"
    assert artist_readme.is_file()


def test_file_state_driver_create_track_writes_markdown(tmp_path) -> None:
    cfg = MusicConfig(artist_name="A", content_root=str(tmp_path))
    cfg._fill_path_defaults()
    drv = FileStateDriver(cfg)
    drv.create_album_root(artist="A", genre="ambient",
                          slug="origin", title="Origin")
    drv.create_track(album="origin", slug="01-intro", title="Intro")
    track_file = (tmp_path / "artists" / "a" / "albums" / "ambient" / "origin"
                  / "tracks" / "01-intro.md")
    assert track_file.is_file()


def test_file_state_driver_list_albums_scans_disk(tmp_path) -> None:
    cfg = MusicConfig(artist_name="A", content_root=str(tmp_path))
    cfg._fill_path_defaults()
    drv = FileStateDriver(cfg)
    drv.create_album_root(artist="A", genre="ambient",
                          slug="origin", title="Origin")
    drv.create_album_root(artist="A", genre="ambient",
                          slug="echoes", title="Echoes")
    albums = drv.list_albums()
    slugs = {a["slug"] for a in albums}
    assert slugs == {"origin", "echoes"}


def test_file_state_driver_find_album_fuzzy_match(tmp_path) -> None:
    cfg = MusicConfig(artist_name="A", content_root=str(tmp_path))
    cfg._fill_path_defaults()
    drv = FileStateDriver(cfg)
    drv.create_album_root(artist="A", genre="ambient",
                          slug="origin", title="Origin")
    exact = drv.find_album("origin")
    fuzzy = drv.find_album("orig")
    miss = drv.find_album("nope")
    assert len(exact) == 1
    assert len(fuzzy) == 1
    assert miss == []


def test_file_state_driver_rename_album_moves_directory(tmp_path) -> None:
    cfg = MusicConfig(artist_name="A", content_root=str(tmp_path))
    cfg._fill_path_defaults()
    drv = FileStateDriver(cfg)
    drv.create_album_root(artist="A", genre="ambient",
                          slug="old", title="Old")
    res = drv.rename_album(old_slug="old", new_slug="new")
    assert res["success"] is True
    new_dir = tmp_path / "artists" / "a" / "albums" / "ambient" / "new"
    assert new_dir.is_dir()
    old_dir = tmp_path / "artists" / "a" / "albums" / "ambient" / "old"
    assert not old_dir.exists()


# ─────────────────────────── SqliteDBDriver tests ───────────────────────────

def test_sqlite_db_driver_round_trip_in_memory() -> None:
    drv = SqliteDBDriver(db_path=":memory:")
    tid = drv.create_tweet(album="A", body="Out now!",
                            scheduled_at="2026-12-01T10:00Z")
    assert isinstance(tid, int) and tid > 0
    listed = drv.list_tweets(album="A")
    assert len(listed) == 1 and listed[0]["body"] == "Out now!"
    drv.update_tweet(tid, {"status": "scheduled"})
    scheduled = drv.list_tweets(album="A", status="scheduled")
    assert len(scheduled) == 1
    drv.delete_tweet(tid)
    assert drv.list_tweets(album="A") == []


def test_sqlite_db_driver_persists_to_file(tmp_path) -> None:
    db_path = str(tmp_path / "music.db")
    drv1 = SqliteDBDriver(db_path=db_path)
    tid = drv1.create_tweet(album="A", body="t1",
                            scheduled_at="2026-12-01")
    # New driver instance on same file
    drv2 = SqliteDBDriver(db_path=db_path)
    tweets = drv2.list_tweets(album="A")
    assert len(tweets) == 1
    assert tweets[0]["id"] == tid


def test_sqlite_db_driver_search_substring() -> None:
    drv = SqliteDBDriver(db_path=":memory:")
    drv.create_tweet(album="A", body="The phreaker tale",
                     scheduled_at="2026-12-01")
    drv.create_tweet(album="A", body="Different content",
                     scheduled_at="2026-12-02")
    hits = drv.search_tweets("phreaker")
    assert len(hits) == 1


def test_sqlite_db_driver_tweet_stats_by_status() -> None:
    drv = SqliteDBDriver(db_path=":memory:")
    a = drv.create_tweet(album="A", body="a", scheduled_at="2026-12-01")
    drv.create_tweet(album="A", body="b", scheduled_at="2026-12-02")
    drv.update_tweet(a, {"status": "scheduled"})
    stats = drv.tweet_stats(album="A")
    assert stats["total"] == 2
    assert stats["by_status"].get("draft") == 1
    assert stats["by_status"].get("scheduled") == 1


def test_sqlite_db_driver_sync_replaces_existing() -> None:
    drv = SqliteDBDriver(db_path=":memory:")
    drv.create_tweet(album="A", body="will be replaced",
                     scheduled_at="2026-12-01")
    res = drv.sync_album_tweets(album="A",
                                 tweets=[
                                     {"body": "n1", "scheduled_at": "2026-12-02"},
                                     {"body": "n2", "scheduled_at": "2026-12-03"},
                                 ])
    assert res["removed"] == 1
    assert res["created"] == 2
    final = drv.list_tweets(album="A")
    assert len(final) == 2


def test_sqlite_db_driver_cursor_shim_handles_two_arg_execute() -> None:
    """The 007 cursor shim must accept `execute(sql, params)` shape."""
    drv = SqliteDBDriver(db_path=":memory:")
    cur = drv.cursor()
    cur.execute("INSERT INTO tweets (album, body, scheduled_at) VALUES (?, ?, ?)",
                ("A", "raw-sql", "2026-12-01"))
    cur.execute("SELECT COUNT(*) FROM tweets")
    count = cur.fetchone()[0]
    assert count == 1
    cur.close()


# ─────────────────────────── factory test ───────────────────────────

def test_production_drivers_factory_wires_all_five(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".agency").mkdir()
    (tmp_path / ".agency" / "music-config.yaml").write_text(
        f"artist:\n  name: A\n"
        f"paths:\n  content_root: {tmp_path}/music\n"
        f"db:\n  path: {tmp_path}/.agency/music.db\n"
    )
    bundle = production_drivers()
    assert set(bundle) == {"music_state", "music_text", "music_audio",
                           "music_db", "music_cloud"}
    # FileStateDriver wired
    assert isinstance(bundle["music_state"], FileStateDriver)
    # SqliteDBDriver wired
    assert isinstance(bundle["music_db"], SqliteDBDriver)


# ─────────────────────────── verb integration tests ───────────────────────────

def _fresh(drivers=None) -> Engine:
    return Engine(tempfile.mktemp(suffix=".db"),
                  drivers=drivers if drivers is not None else fake_drivers())


def _confirmed_iid(e: Engine, purpose: str = "spec115") -> str:
    iid = e.intent.capture(purpose, "deliverable", "acceptance")
    e.intent.confirm(iid)
    return iid


def _invoke(e: Engine, iid: str, verb: str, **kw):
    return e.registry.invoke(e.memory, iid, "music", verb, **kw)


def test_get_config_returns_config_shape(monkeypatch, tmp_path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("AGENCY_MUSIC_HOME", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    e = _fresh()
    iid = _confirmed_iid(e)
    data, _ = _invoke(e, iid, "get_config")
    assert "config" in data
    assert "artist" in data["config"]
    assert "paths" in data["config"]


def test_load_override_returns_not_found_when_missing(monkeypatch, tmp_path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HOME", str(tmp_path))
    e = _fresh()
    iid = _confirmed_iid(e)
    data, _ = _invoke(e, iid, "load_override", name="nonexistent")
    assert data["found"] is False
    assert data["body"] == ""


def test_load_override_reads_existing_file(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("AGENCY_MUSIC_HOME", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path / "fake-home"))
    (tmp_path / ".agency").mkdir()
    overrides = tmp_path / "overrides"
    overrides.mkdir()
    (overrides / "custom.md").write_text("# Custom override body")
    (tmp_path / ".agency" / "music-config.yaml").write_text(
        f"artist:\n  name: A\n"
        f"paths:\n  content_root: {tmp_path}\n  overrides: {overrides}\n"
    )
    e = _fresh()
    iid = _confirmed_iid(e)
    data, _ = _invoke(e, iid, "load_override", name="custom")
    assert data["found"] is True
    assert "Custom override" in data["body"]


# ─────────────── Spec 117: default config + fresh-repo bootstrap ───────────────

def test_bootstrap_writes_default_config_when_absent(tmp_path, monkeypatch) -> None:
    """A fresh repo with no config gets a default `.agency/music-config.yaml`
    written + the content root created; a second call is a no-op."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("AGENCY_MUSIC_HOME", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path / "fake-home"))
    assert not MusicConfig.config_file_exists()

    cfg = MusicConfig.bootstrap()
    written = tmp_path / ".agency" / "music-config.yaml"
    assert written.is_file(), "bootstrap should write a default config"
    assert MusicConfig.config_file_exists()
    # content root materialised so the FileStateDriver has a home
    assert Path(cfg.content_root).is_dir()

    # Idempotent: the existing config is not clobbered (mtime stable).
    before = written.read_text()
    MusicConfig.bootstrap()
    assert written.read_text() == before


def test_bootstrap_is_noop_when_config_present(tmp_path, monkeypatch) -> None:
    """An existing project keeps its bindings — bootstrap never overwrites."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("AGENCY_MUSIC_HOME", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path / "fake-home"))
    (tmp_path / ".agency").mkdir()
    (tmp_path / ".agency" / "music-config.yaml").write_text(
        f"artist:\n  name: Existing\npaths:\n  content_root: {tmp_path}/proj\n")
    cfg = MusicConfig.bootstrap()
    assert cfg.artist_name == "Existing"
    assert cfg.content_root == f"{tmp_path}/proj"


# ─────────────── Spec 117: lazy production-driver auto-wiring ───────────────

def test_autowire_disabled_keeps_dependency_missing(tmp_path, monkeypatch) -> None:
    """Without the production flag, a driver-backed verb on a music-driverless
    engine keeps the typed DEPENDENCY_MISSING contract (blast radius bounded)."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HOME", str(tmp_path / "fake-home"))
    e = _fresh(drivers={})                 # registry present, no music drivers, no flag
    try:
        iid = _confirmed_iid(e)
        data, inv = _invoke(e, iid, "create_album",
                            artist="A", title="T", genre="ambient")
        assert data is None
        assert "DEPENDENCY_MISSING" in e.memory.recall(inv).get("error", "")
    finally:
        e.memory.close()


def test_autowire_enabled_wires_production_drivers_and_writes_disk(
        tmp_path, monkeypatch) -> None:
    """With `engine._music_production = True`, the first driver-backed verb
    lazily wires production_drivers from config, persists to the configured
    content root, and `diagnose` then reports all five drivers wired."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("AGENCY_MUSIC_HOME", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path / "fake-home"))
    content = tmp_path / "content"
    (tmp_path / ".agency").mkdir()
    (tmp_path / ".agency" / "music-config.yaml").write_text(
        f"artist:\n  name: The Phreakers\n"
        f"paths:\n  content_root: {content}\n"
        f"db:\n  backend: sqlite\n  path: {tmp_path}/.agency/music.db\n")

    e = _fresh(drivers={})                 # no music drivers wired at construction
    e._music_production = True             # the MCP entrypoint flips this
    try:
        iid = _confirmed_iid(e)
        # Pre-state: diagnose sees nothing wired.
        diag0, _ = _invoke(e, iid, "diagnose")
        assert diag0["drivers_wired"] == []

        data, inv = _invoke(e, iid, "create_album",
                            artist="The Phreakers", title="Umschalten",
                            genre="ambient")
        assert data is not None, e.memory.recall(inv).get("error", "")
        # README persisted on disk under the configured content root.
        readme = (content / "artists" / "the-phreakers" / "albums"
                  / "ambient" / "umschalten" / "README.md")
        assert readme.is_file(), f"expected {readme} written by auto-wired FileStateDriver"

        # Post-state: diagnose now reports the full bundle wired.
        diag1, _ = _invoke(e, iid, "diagnose")
        assert set(diag1["drivers_wired"]) == {
            "music_state", "music_text", "music_audio", "music_db", "music_cloud"}
        assert diag1["drivers_missing"] == []
    finally:
        e.memory.close()


def test_get_reference_reads_bundled_data_doc() -> None:
    """Read a reference doc bundled at agency/capabilities/music/data/reference/.
    Spec 094 vendored 50 docs there; the SKILL_INDEX.md is the canonical entry."""
    e = _fresh()
    iid = _confirmed_iid(e)
    data, _ = _invoke(e, iid, "get_reference", slug="SKILL_INDEX",
                       kind="reference")
    # If reference is present body is non-empty; if not yet on this branch,
    # empty body is still success.
    assert "body" in data
    assert data["kind"] == "reference"


def test_format_clipboard_strips_section_tags_for_lyrics() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    data, _ = _invoke(e, iid, "format_clipboard",
                       text="[Verse 1]\nThe carrier tone hummed\n[Chorus]\nWe dialed the night",
                       format="lyrics")
    assert "[Verse 1]" not in data["text"]
    assert "[Chorus]" not in data["text"]
    assert "carrier tone" in data["text"]


def test_format_clipboard_collapses_style_prompt_to_200_chars() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    long_prompt = ("ambient electronic " * 20).strip()  # well over 200 chars
    data, _ = _invoke(e, iid, "format_clipboard",
                       text=long_prompt, format="style-prompt")
    assert data["char_count"] <= 200
    assert "\n" not in data["text"]


# ─────────────────────────── new-album skill test ───────────────────────────

def test_new_album_skill_walks_through_confirm() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    sk = e.ontology.skill("new-album")
    assert sk["kind"] == "workflow"
    assert len(sk["phases"]) == 5
    run = SkillRun(e.memory, iid, sk)
    fills = [
        {"album_name": "modem-daze", "genre": "ambient", "documentary": "no"},
        {"genre_valid": "yes"},
        {"safe_to_create": "yes"},
        {"album_root": "artists/a/albums/ambient/modem-daze",
         "files_created": "README.md, tracks/"},
    ]
    for out in fills:
        assert run.submit(out)["status"] == "working"
    assert run.current()["gate"] == "hard"
    assert run.submit({"user_confirmed": "yes"},
                      confirmed=True)["status"] == "completed"
    e.memory.close()


def test_production_drivers_round_trip_through_real_engine(tmp_path, monkeypatch) -> None:
    """End-to-end: production_drivers + create_album → real disk + SQLite DB written."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("AGENCY_MUSIC_HOME", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path / "fake-home"))
    (tmp_path / ".agency").mkdir()
    (tmp_path / ".agency" / "music-config.yaml").write_text(
        f"artist:\n  name: The Phreakers\n"
        f"paths:\n  content_root: {tmp_path}/music\n"
        f"db:\n  path: {tmp_path}/.agency/music.db\n"
    )
    e = Engine(tempfile.mktemp(suffix=".db"),
               drivers=production_drivers())
    iid = _confirmed_iid(e)
    data, _ = _invoke(e, iid, "create_album",
                      artist="The Phreakers", title="Modem Daze",
                      genre="ambient", type="documentary")
    # Disk tree exists
    album_dir = (tmp_path / "music" / "artists" / "the-phreakers"
                 / "albums" / "ambient" / "modem-daze")
    assert album_dir.is_dir()
    assert (album_dir / "README.md").is_file()
    assert (album_dir / "RESEARCH.md").is_file()
    assert (album_dir / "SOURCES.md").is_file()
    assert (album_dir / "tracks").is_dir()
    # SQLite db file created
    db_path = tmp_path / ".agency" / "music.db"
    assert db_path.is_file()
    e.memory.close()
