"""Spec 031 §E / Task 2.4 — atomic JSON cache for skill emit pipeline.

Panel F-3 (TEST-3): simulate a commit interrupted between .tmp write and
os.replace; subsequent peek returns None (cache miss); next emit regenerates
cleanly. No corrupt JSON crashes the loader.
"""
import json
import os
from pathlib import Path

import pytest

from agency.cache import peek, commit


def test_peek_returns_none_when_cache_file_absent(tmp_path):
    assert peek(tmp_path, "foo", "any-hash") is None


def test_commit_then_peek_roundtrip(tmp_path):
    commit(tmp_path, "foo", "h1", ["skills/foo/SKILL.md"])
    result = peek(tmp_path, "foo", "h1")
    assert result is not None
    assert result["hash"] == "h1"
    assert result["files"] == ["skills/foo/SKILL.md"]


def test_peek_returns_none_on_hash_miss(tmp_path):
    """If the stored hash doesn't match the queried hash, peek returns None."""
    commit(tmp_path, "foo", "h1", ["a"])
    assert peek(tmp_path, "foo", "h2") is None


def test_peek_returns_none_on_corrupt_json(tmp_path):
    """A partial-write (corrupt JSON) cache file returns None, not raises."""
    cache_file = tmp_path / "skill-cache.json"
    cache_file.write_text("{ this is not valid json")
    assert peek(tmp_path, "foo", "any") is None


def test_peek_returns_none_for_unknown_capability(tmp_path):
    commit(tmp_path, "foo", "h1", ["a"])
    assert peek(tmp_path, "other", "h1") is None


def test_commit_merges_multiple_capabilities(tmp_path):
    commit(tmp_path, "foo", "h1", ["a"])
    commit(tmp_path, "bar", "h2", ["b"])
    # Both rows preserved
    assert peek(tmp_path, "foo", "h1")["files"] == ["a"]
    assert peek(tmp_path, "bar", "h2")["files"] == ["b"]


def test_commit_overwrites_same_cap(tmp_path):
    """Re-committing the same capability with new hash supersedes the old entry."""
    commit(tmp_path, "foo", "h1", ["a"])
    commit(tmp_path, "foo", "h2", ["b"])
    # Old hash no longer matches
    assert peek(tmp_path, "foo", "h1") is None
    # New hash does
    assert peek(tmp_path, "foo", "h2")["files"] == ["b"]


def test_commit_is_atomic_TEST_3(tmp_path, monkeypatch):
    """TEST-3 (panel F-3): if commit is interrupted between .tmp write and
    os.replace, the on-disk skill-cache.json is unchanged (still missing).
    Subsequent peek returns None — no corrupt JSON crashes the loader."""
    # Simulate interruption: monkeypatch os.replace to raise mid-commit
    called = {"replace": False}
    def fake_replace(src, dst):
        called["replace"] = True
        raise KeyboardInterrupt("simulated kill")

    monkeypatch.setattr("os.replace", fake_replace)
    with pytest.raises(KeyboardInterrupt):
        commit(tmp_path, "foo", "h1", ["a"])

    # The .tmp file may exist (partial write) but skill-cache.json must NOT
    cache_file = tmp_path / "skill-cache.json"
    assert not cache_file.exists()
    # peek returns None — no crash, no corrupt parse
    monkeypatch.undo()  # restore os.replace for cleanup
    assert peek(tmp_path, "foo", "h1") is None


def test_cache_file_is_human_readable(tmp_path):
    """The cache JSON has version field + readable indentation."""
    commit(tmp_path, "foo", "h1", ["a"])
    cache_file = tmp_path / "skill-cache.json"
    content = cache_file.read_text()
    # Indented JSON (humans inspect it)
    assert "\n  " in content or "\n    " in content
    parsed = json.loads(content)
    assert parsed.get("version") == 1
    assert "capabilities" in parsed
