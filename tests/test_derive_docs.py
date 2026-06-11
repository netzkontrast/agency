"""Spec 149 Slice 2 — `scripts/derive-docs` core derivation library.

Spec 149 Slice 1 shipped the `vision_goals:` frontmatter validator + 129-
spec baseline. Slice 2 ships the core DERIVATION engine that closes the
drift gap: per-spec test counts derived from `pytest --collect-only` keyed
by `affects:` test files, so the alignment matrix stops carrying hand-
authored counts that rot on every PR.

This slice ships the pure functions (parse frontmatter `affects:`, walk
the pytest collection output, map test files → counts) + a `--dry-run`
CLI that prints what would change. The spec.md derived-zone write side is
Slice 2.2; the `check-doc-drift` integration is Slice 2.3.

Pattern follows Spec 149 Slice 1 (`scripts/check_vision_goals.py`): pure
functions importable as `scripts.derive_docs`, typed shapes, CLI exit
codes per Spec 169 doctrine.
"""
from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from scripts.derive_docs import (
    Derivation,
    DeriveReport,
    parse_affects,
    parse_collect_output,
    derive_test_counts,
    derive_spec,
)


# ── parse_affects: read `affects:` field from spec frontmatter ──────────────
def _spec(tmp: Path, name: str, frontmatter: str) -> Path:
    d = tmp / name
    d.mkdir()
    f = d / "spec.md"
    f.write_text(f"---\n{frontmatter}\n---\n\n# {name}\n")
    return f


def test_parse_affects_returns_list_of_paths(tmp_path):
    """`affects:` is a YAML list; parser returns the strings unchanged
    (paths are NOT validated here — that's the audit layer's job)."""
    f = _spec(tmp_path, "042-x",
              "spec_id: '042'\nvision_goals: [1]\n"
              "affects:\n  - tests/test_analyze.py\n  - tests/test_quality.py")
    out = parse_affects(f)
    assert out == ["tests/test_analyze.py", "tests/test_quality.py"]


def test_parse_affects_returns_empty_when_field_absent(tmp_path):
    """A spec without `affects:` returns []; not an error (per Spec 054
    drift baseline — many older specs lack the field)."""
    f = _spec(tmp_path, "001-x", "spec_id: '001'\nvision_goals: [1]")
    assert parse_affects(f) == []


def test_parse_affects_filters_non_string_entries(tmp_path):
    """Malformed entries (ints, nested dicts) are silently dropped;
    Slice 3 will surface them via `Codes.DERIVE_AMBIGUOUS`."""
    f = _spec(tmp_path, "042-x",
              "spec_id: '042'\nvision_goals: [1]\n"
              "affects:\n  - tests/test_a.py\n  - 42\n  - tests/test_b.py")
    out = parse_affects(f)
    assert out == ["tests/test_a.py", "tests/test_b.py"]


def test_parse_affects_handles_malformed_frontmatter(tmp_path):
    f = tmp_path / "broken.md"
    f.write_text("---\nspec_id: 'unterminated\n---\nbody")
    assert parse_affects(f) == []


# ── parse_collect_output: turn pytest --collect-only into a file → count map ─
def test_parse_collect_output_groups_by_file():
    """`pytest --collect-only -q` emits one line per test as
    `tests/test_foo.py::test_bar`. Parser groups by filename."""
    raw = textwrap.dedent("""\
        tests/test_foo.py::test_a
        tests/test_foo.py::test_b
        tests/test_foo.py::test_c
        tests/test_bar.py::test_x

        4 tests collected in 0.10s
    """)
    counts = parse_collect_output(raw)
    assert counts == {"tests/test_foo.py": 3, "tests/test_bar.py": 1}


def test_parse_collect_output_ignores_summary_and_blank_lines():
    raw = textwrap.dedent("""\

        tests/test_a.py::test_one
        ===== 1 test collected =====
        ====================== passed ======================
    """)
    assert parse_collect_output(raw) == {"tests/test_a.py": 1}


def test_parse_collect_output_handles_parametrized_tests():
    """Parametrized tests show up with [param-id] suffixes — counted as
    distinct tests per the pytest convention."""
    raw = textwrap.dedent("""\
        tests/test_p.py::test_x[case-a]
        tests/test_p.py::test_x[case-b]
        tests/test_p.py::test_x[case-c]
    """)
    assert parse_collect_output(raw) == {"tests/test_p.py": 3}


def test_parse_collect_output_empty_input_yields_empty_map():
    assert parse_collect_output("") == {}
    assert parse_collect_output("\n\n") == {}


# ── derive_test_counts: combine affects + counts → per-spec total ───────────
def test_derive_test_counts_sums_affects_files():
    counts = {"tests/test_a.py": 5, "tests/test_b.py": 3,
              "tests/test_unrelated.py": 99}
    total = derive_test_counts(
        affects=["tests/test_a.py", "tests/test_b.py"],
        counts=counts,
    )
    assert total == 8


def test_derive_test_counts_zero_when_no_affects():
    assert derive_test_counts(affects=[], counts={"x": 5}) == 0


def test_derive_test_counts_zero_for_unknown_affects_file():
    """A spec that lists a test file with no collected tests reports 0
    rather than raising (the live test suite may legitimately have an
    affects entry with no @pytest.mark yet)."""
    total = derive_test_counts(
        affects=["tests/test_doesnotexist.py"],
        counts={"tests/test_a.py": 5},
    )
    assert total == 0


# ── derive_spec: typed per-spec derivation payload ─────────────────────────
def test_derive_spec_yields_typed_derivation(tmp_path):
    f = _spec(tmp_path, "042-foo",
              "spec_id: '042'\nvision_goals: [1]\n"
              "affects:\n  - tests/test_analyze.py")
    counts = {"tests/test_analyze.py": 33}
    d = derive_spec(f, counts=counts)
    assert isinstance(d, Derivation)
    assert d.spec_id == "042"
    assert d.test_count == 33
    assert d.affects_files == ("tests/test_analyze.py",)


def test_derive_spec_works_when_affects_absent(tmp_path):
    f = _spec(tmp_path, "001-foo", "spec_id: '001'\nvision_goals: [1]")
    d = derive_spec(f, counts={})
    assert d.spec_id == "001"
    assert d.test_count == 0
    assert d.affects_files == ()


# ── DeriveReport: tree-wide derivation rollup ──────────────────────────────
def test_derive_report_walks_plan_tree(tmp_path):
    _spec(tmp_path, "042-foo",
          "spec_id: '042'\nvision_goals: [1]\n"
          "affects:\n  - tests/test_analyze.py")
    _spec(tmp_path, "043-bar",
          "spec_id: '043'\nvision_goals: [2]\n"
          "affects:\n  - tests/test_document.py")
    from scripts.derive_docs import derive_tree
    rep = derive_tree(tmp_path, counts={"tests/test_analyze.py": 5,
                                         "tests/test_document.py": 7})
    assert isinstance(rep, DeriveReport)
    by_id = {d.spec_id: d for d in rep.derivations}
    assert by_id["042"].test_count == 5
    assert by_id["043"].test_count == 7


def test_derive_report_is_deterministic_across_runs(tmp_path):
    """Per CLAUDE.md rule 8 + Slice 2 idempotence invariant: running
    twice yields the same derivation list in the same order."""
    _spec(tmp_path, "001-a", "spec_id: '001'\nvision_goals: [1]")
    _spec(tmp_path, "002-b", "spec_id: '002'\nvision_goals: [2]")
    from scripts.derive_docs import derive_tree
    r1 = derive_tree(tmp_path, counts={})
    r2 = derive_tree(tmp_path, counts={})
    assert [d.spec_id for d in r1.derivations] == \
           [d.spec_id for d in r2.derivations]


# ── live-tree smoke test (informational; not a count assertion) ─────────────
def test_live_tree_derive_runs_without_crashing():
    """Slice 2.1: assert the derivation engine WALKS the live tree
    against an empty collect map without crashing. Slice 2.2 wires the
    actual `pytest --collect-only` invocation."""
    from scripts.derive_docs import derive_tree
    repo = Path(__file__).parent.parent
    rep = derive_tree(repo / "Plan", counts={})
    assert isinstance(rep, DeriveReport)
    assert len(rep.derivations) > 100                              # many specs in Plan/
    # Every derivation has a spec_id and a non-negative count (Slice 2.1
    # passes an empty count map so all counts are 0; the shape is what
    # matters here).
    for d in rep.derivations:
        assert d.spec_id
        assert d.test_count >= 0
