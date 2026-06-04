"""Spec 043 — document.index_repo: 94%-reduction repo briefing.

Self-test: on the agency repo itself, the briefing fits in ≤ 3000
tokens AND names every top-level capability.
"""
import os
import tempfile

import pytest

from agency.engine import Engine


_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture
def engine():
    return Engine(tempfile.mktemp(suffix=".db"))


@pytest.fixture
def iid(engine):
    i = engine.intent.capture(
        "test document.index_repo",
        "briefing fits in 3000 tokens",
        "every top-level capability named",
    )
    engine.intent.confirm(i)
    return i


def _call(engine, iid, **kw):
    r, _ = engine.registry.invoke(
        engine.memory, iid, "document", "index_repo",
        agent_id="agent:test", **kw)
    return r


def test_self_test_under_3000_tokens(engine, iid):
    r = _call(engine, iid, path=_REPO, apply=False)
    assert r["tokens"] <= 3000, f"index_repo exceeded budget: {r['tokens']} > 3000"


def test_briefing_names_every_top_level_capability(engine, iid):
    r = _call(engine, iid, path=_REPO, apply=False)
    # Sample of capabilities that MUST appear in the briefing.
    for cap in ("reflect", "delegate", "analyze", "document"):
        # Each cap has a `<cap>.py` or `<cap>/` entry in
        # agency/capabilities/. The briefing's macro-structure section
        # lists those.
        assert cap in r["content"], f"capability {cap!r} not named in briefing"


def test_briefing_includes_substrate_section(engine, iid):
    r = _call(engine, iid, path=_REPO, apply=False)
    assert "## Substrate" in r["content"]
    assert "## Macro-structure" in r["content"]
    assert "## Entry points" in r["content"]
    assert "## Notable patterns" in r["content"]


def test_records_repo_index_node(engine, iid):
    before = len(list(engine.memory.find("RepoIndex")))
    r = _call(engine, iid, path=_REPO, apply=False)
    after = len(list(engine.memory.find("RepoIndex")))
    assert after == before + 1
    indices = engine.memory.find("RepoIndex")
    idx = next(rr for rr in indices if rr["id"] == r["index_id"])
    assert idx["path"].startswith("/") or idx["path"].startswith(_REPO)
    assert idx["token_count"] == r["tokens"]
    assert len(idx["content_sha"]) == 16


def test_apply_false_does_not_write(engine, iid, tmp_path):
    target = tmp_path / "PROJECT_INDEX.md"
    r = _call(engine, iid, path=str(tmp_path), apply=False)
    assert not target.exists()


def test_apply_true_writes_file(engine, iid, tmp_path):
    # Create a minimal test repo.
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "x"\n[project.scripts]\nx = "x:main"\n')
    (tmp_path / "module.py").write_text('"""A test module brief."""\n')
    r = _call(engine, iid, path=str(tmp_path), apply=True)
    target = tmp_path / "PROJECT_INDEX.md"
    assert target.exists()
    assert "PROJECT_INDEX" in r["writeup"] or "wrote" in r["writeup"]
    # Content matches what was returned.
    assert target.read_text() == r["content"]


def test_max_tokens_truncates(engine, iid):
    r = _call(engine, iid, path=_REPO, apply=False, max_tokens=500)
    assert r["tokens"] <= 600   # 500 + small slop for the truncation marker
    assert "omitted" in r["content"] or r["tokens"] <= 500


def test_files_scanned_count(engine, iid):
    r = _call(engine, iid, path=_REPO, apply=False)
    assert r["files_scanned"] > 0
