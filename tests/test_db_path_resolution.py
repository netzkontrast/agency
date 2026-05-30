"""Spec 020 — central graph DB path resolution.

Resolution order (verified by these tests):
  1. ``explicit`` arg (--db flag) wins over everything.
  2. ``AGENCY_DB`` env var wins over local + home.
  3. ``./.agency/session.db`` wins over home when the .agency dir exists.
  4. ``~/.agency.db`` is the system fallback.

Plus coverage for the install-side scaffold (``scaffold_agency_dir`` +
``update_gitattributes``) idempotency.
"""
from __future__ import annotations

import os

import pytest

from agency._db_path import resolve_db_path
from agency.install import scaffold_agency_dir, scaffold_db, update_gitattributes


# ---------------------------------------------------------------------------
# resolve_db_path — the resolution order.
# ---------------------------------------------------------------------------


def test_explicit_wins_over_everything(monkeypatch, tmp_path):
    monkeypatch.setenv("AGENCY_DB", "/from/env.db")
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".agency").mkdir()
    assert resolve_db_path("/explicit.db") == "/explicit.db"


def test_env_overrides_local_and_home(monkeypatch, tmp_path):
    monkeypatch.setenv("AGENCY_DB", "/from/env.db")
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".agency").mkdir()
    assert resolve_db_path() == "/from/env.db"


def test_cwd_local_when_agency_dir_exists(monkeypatch, tmp_path):
    monkeypatch.delenv("AGENCY_DB", raising=False)
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".agency").mkdir()
    assert resolve_db_path() == str(tmp_path / ".agency" / "session.db")


def test_home_fallback_when_no_env_no_local(monkeypatch, tmp_path):
    monkeypatch.delenv("AGENCY_DB", raising=False)
    monkeypatch.chdir(tmp_path)
    # No .agency/ dir in cwd
    result = resolve_db_path()
    assert result.endswith(".agency.db")
    assert "~" not in result  # tilde expanded


def test_local_not_selected_without_agency_dir(monkeypatch, tmp_path):
    """The CWD-local path is only selected when .agency/ EXISTS — the
    resolver doesn't silently create DBs in arbitrary directories."""
    monkeypatch.delenv("AGENCY_DB", raising=False)
    monkeypatch.chdir(tmp_path)
    # tmp_path has no .agency/ → should fall through to home
    result = resolve_db_path()
    assert "session.db" not in result   # NOT the local form
    assert result.endswith(".agency.db")


# ---------------------------------------------------------------------------
# scaffold_agency_dir — install-side directory scaffold (Spec 020).
# ---------------------------------------------------------------------------


def test_scaffold_creates_directory_with_marker_files(tmp_path):
    written = scaffold_agency_dir(str(tmp_path))
    agency = tmp_path / ".agency"
    assert agency.is_dir()
    assert (agency / ".gitkeep").exists()
    assert (agency / "README.md").exists()
    # README content names Spec 020 (so future readers reach the design).
    assert "Spec 020" in (agency / "README.md").read_text()
    # Both new files reported.
    assert any(str(p).endswith(".gitkeep") for p in written)
    assert any(str(p).endswith("README.md") for p in written)


def test_scaffold_is_idempotent(tmp_path):
    """Re-running on a populated dir creates nothing new."""
    scaffold_agency_dir(str(tmp_path))
    second = scaffold_agency_dir(str(tmp_path))
    assert second == []   # nothing newly written


# ---------------------------------------------------------------------------
# update_gitattributes — binary marker, idempotent.
# ---------------------------------------------------------------------------


def test_update_gitattributes_creates_file_when_missing(tmp_path):
    changed = update_gitattributes(str(tmp_path))
    assert changed is True
    body = (tmp_path / ".gitattributes").read_text()
    assert ".agency/session.db binary" in body
    assert "Spec 020" in body


def test_update_gitattributes_appends_to_existing(tmp_path):
    existing = "# existing rules\n*.png binary\n"
    (tmp_path / ".gitattributes").write_text(existing)
    changed = update_gitattributes(str(tmp_path))
    assert changed is True
    body = (tmp_path / ".gitattributes").read_text()
    assert existing in body                  # preserved
    assert ".agency/session.db binary" in body


def test_update_gitattributes_idempotent(tmp_path):
    update_gitattributes(str(tmp_path))
    changed = update_gitattributes(str(tmp_path))
    assert changed is False
    # Marker appears exactly once.
    body = (tmp_path / ".gitattributes").read_text()
    assert body.count("Spec 020 — central graph DB") == 1


# ---------------------------------------------------------------------------
# scaffold_db — both halves wired together.
# ---------------------------------------------------------------------------


def test_scaffold_db_runs_both_halves(tmp_path):
    result = scaffold_db(str(tmp_path))
    assert (tmp_path / ".agency").is_dir()
    assert (tmp_path / ".gitattributes").exists()
    assert len(result["written"]) >= 2   # gitkeep + README
    assert result["gitattributes_updated"] is True


def test_scaffold_db_second_call_idempotent(tmp_path):
    scaffold_db(str(tmp_path))
    result = scaffold_db(str(tmp_path))
    assert result["written"] == []
    assert result["gitattributes_updated"] is False
