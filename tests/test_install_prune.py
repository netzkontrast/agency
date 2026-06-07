"""Spec 092 G1 — the installer prunes generator-owned files for removed verbs."""
from agency.install import _prune_orphans, write


def test_prune_removes_orphans_keeps_live_and_entrypoints(tmp_path):
    (tmp_path / "bin").mkdir()
    (tmp_path / "bin" / "agency-analyze-graph").write_text("x")   # live (in expected)
    (tmp_path / "bin" / "agency-analyze-gone").write_text("x")    # orphan (not expected)
    (tmp_path / "bin" / "agency-mcp").write_text("x")             # entry point — survives
    refdir = tmp_path / "skills" / "analyze" / "references"
    refdir.mkdir(parents=True)
    (refdir / "graph.md").write_text("x")                         # live
    (refdir / "gone.md").write_text("x")                          # orphan

    expected = {"bin/agency-analyze-graph", "skills/analyze/references/graph.md"}
    pruned = _prune_orphans(str(tmp_path), expected, ["analyze"])

    assert "bin/agency-analyze-gone" in pruned
    assert "skills/analyze/references/gone.md" in pruned
    assert not (tmp_path / "bin" / "agency-analyze-gone").exists()
    assert not (refdir / "gone.md").exists()
    # live files + the entry point (outside any cap namespace) are untouched
    assert (tmp_path / "bin" / "agency-analyze-graph").exists()
    assert (tmp_path / "bin" / "agency-mcp").exists()
    assert (refdir / "graph.md").exists()


def test_prune_only_touches_a_live_capabilitys_namespace(tmp_path):
    # a bin wrapper for an UNKNOWN capability is left alone (not our namespace to prune)
    (tmp_path / "bin").mkdir()
    (tmp_path / "bin" / "agency-unknowncap-verb").write_text("x")
    pruned = _prune_orphans(str(tmp_path), set(), ["analyze"])    # 'unknowncap' not live
    assert pruned == []
    assert (tmp_path / "bin" / "agency-unknowncap-verb").exists()


def test_write_prunes_a_planted_orphan_on_regen(tmp_path):
    root = str(tmp_path)
    write(root)                                                  # full install into temp
    orphan = tmp_path / "bin" / "agency-analyze-zzz_removed"
    orphan.write_text("#!/bin/sh\n")
    assert orphan.exists()
    write(root)                                                  # regen → prunes the orphan
    assert not orphan.exists()
    # a real wrapper from the same regen is still present
    assert (tmp_path / "bin" / "agency-analyze-graph").exists()
