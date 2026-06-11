"""Spec 149 Slice 1 — `vision_goals:` frontmatter validator.

The drift-derivation chain anchor needs every spec to declare its Vision-goal
mapping in frontmatter so the alignment matrix (Spec 191) + per-spec Followup
(Spec 269) + closing audit (Spec 261) can derive from one source. This validator
ships first because every later piece of 149 depends on the frontmatter being
machine-readable.

Pattern follows Spec 054 (drift management): a BASELINE file documents the
existing gaps so CI gates on REGRESSION only — adding a new spec without
`vision_goals:` fails; the 129 historical gaps are tracked, not blocked. Backfill
is a follow-up.
"""
from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from scripts.check_vision_goals import (
    GoalsCheck,
    check_spec,
    check_tree,
    parse_frontmatter,
    valid_goals,
)


# ── frontmatter parsing ──────────────────────────────────────────────────────
def test_parse_extracts_dict_from_yaml_frontmatter():
    body = "---\nspec_id: '146'\nvision_goals: [1, 6]\n---\n\n# Title\n"
    fm = parse_frontmatter(body)
    assert fm["spec_id"] == "146"
    assert fm["vision_goals"] == [1, 6]


def test_parse_returns_empty_dict_without_frontmatter():
    assert parse_frontmatter("# Spec without frontmatter\n\nBody\n") == {}


def test_parse_returns_empty_on_malformed_yaml():
    body = "---\nspec_id: 'unterminated string\n---\nbody"
    assert parse_frontmatter(body) == {}


# ── per-spec rules ───────────────────────────────────────────────────────────
def _spec(tmp: Path, name: str, frontmatter: str = "") -> Path:
    d = tmp / name
    d.mkdir()
    f = d / "spec.md"
    if frontmatter:
        f.write_text(f"---\n{frontmatter}\n---\n\n# {name}\n")
    else:
        f.write_text(f"# {name}\n\nNo frontmatter at all.\n")
    return f


def test_present_and_valid_goals_passes(tmp_path):
    f = _spec(tmp_path, "146-x", "spec_id: '146'\nvision_goals: [1, 6]")
    r = check_spec(f)
    assert r.ok and r.code == "ok"


def test_missing_field_fails_with_missing_code(tmp_path):
    f = _spec(tmp_path, "099-x", "spec_id: '099'")
    r = check_spec(f)
    assert not r.ok and r.code == "missing"


def test_no_frontmatter_at_all_fails_with_missing_code(tmp_path):
    f = _spec(tmp_path, "099-y")
    r = check_spec(f)
    assert not r.ok and r.code == "missing"


def test_empty_list_fails_with_empty_code(tmp_path):
    f = _spec(tmp_path, "099-z", "spec_id: '099'\nvision_goals: []")
    r = check_spec(f)
    assert not r.ok and r.code == "empty"


def test_non_int_entry_fails_with_invalid_code(tmp_path):
    f = _spec(tmp_path, "099-a", "spec_id: '099'\nvision_goals: [1, 'two']")
    r = check_spec(f)
    assert not r.ok and r.code == "invalid"


def test_out_of_range_goal_fails_with_invalid_code(tmp_path):
    # Goals are 1-8 per GOALS.md.
    f = _spec(tmp_path, "099-b", "spec_id: '099'\nvision_goals: [1, 9]")
    r = check_spec(f)
    assert not r.ok and r.code == "invalid"


def test_duplicate_goals_fails_with_invalid_code(tmp_path):
    f = _spec(tmp_path, "099-c", "spec_id: '099'\nvision_goals: [1, 1, 2]")
    r = check_spec(f)
    assert not r.ok and r.code == "invalid"


def test_valid_goals_constant_is_1_through_8():
    # GOALS.md ships exactly 8 goals; the validator must not silently widen.
    assert valid_goals() == {1, 2, 3, 4, 5, 6, 7, 8}


# ── tree check + baseline gate (Spec 054 drift pattern) ──────────────────────
def test_check_tree_returns_per_spec_results(tmp_path):
    _spec(tmp_path, "001-foo", "spec_id: '001'")                              # missing
    _spec(tmp_path, "146-bar", "spec_id: '146'\nvision_goals: [1]")           # ok
    _spec(tmp_path, "147-baz", "spec_id: '147'\nvision_goals: [3, 8]")        # ok
    results = check_tree(tmp_path)
    by_id = {r.spec_id: r for r in results}
    assert by_id["001"].code == "missing"
    assert by_id["146"].ok and by_id["147"].ok


def test_regression_gate_passes_when_only_baseline_specs_lack_goals(tmp_path):
    _spec(tmp_path, "001-foo", "spec_id: '001'")                              # missing — baseline
    _spec(tmp_path, "146-bar", "spec_id: '146'\nvision_goals: [1]")
    chk = GoalsCheck(root=tmp_path, baseline={"001"})
    rep = chk.run()
    assert rep.regressions == []
    assert rep.exit_code == 0
    assert "001" in rep.baseline_missing                                       # tracked, not blocked


def test_regression_gate_fails_when_a_new_spec_lacks_goals(tmp_path):
    _spec(tmp_path, "001-foo", "spec_id: '001'")                              # baseline
    _spec(tmp_path, "999-new", "spec_id: '999'")                              # NEW gap
    chk = GoalsCheck(root=tmp_path, baseline={"001"})
    rep = chk.run()
    assert "999" in rep.regressions
    assert rep.exit_code == 1


def test_baseline_shrinks_when_a_baseline_spec_is_fixed(tmp_path):
    _spec(tmp_path, "001-foo", "spec_id: '001'\nvision_goals: [1]")           # fixed!
    _spec(tmp_path, "146-bar", "spec_id: '146'\nvision_goals: [1]")
    chk = GoalsCheck(root=tmp_path, baseline={"001"})
    rep = chk.run()
    # Spec 001 is no longer missing — it should drop OUT of the live baseline.
    # Drift report calls this "baseline_shrinkable" so authors know to update it.
    assert "001" in rep.baseline_shrinkable


def test_regression_gate_treats_invalid_goals_same_as_missing(tmp_path):
    _spec(tmp_path, "999-bad", "spec_id: '999'\nvision_goals: [99]")          # invalid
    chk = GoalsCheck(root=tmp_path, baseline=set())
    rep = chk.run()
    assert "999" in rep.regressions


# ── live-tree audit baseline (the real finding this slice DOCUMENTS) ─────────
def test_live_tree_baseline_is_recorded_and_loadable():
    """The baseline file `Plan/_planning/vision-goals-baseline.txt` is the source
    of truth for the existing gap. Live-tree regressions check against this."""
    from scripts.check_vision_goals import load_baseline
    baseline_path = Path(__file__).parent.parent / "Plan" / "_planning" / "vision-goals-baseline.txt"
    assert baseline_path.exists(), (
        "vision-goals-baseline.txt missing — Spec 149 Slice 1 ships it as the "
        "regression-gate floor")
    baseline = load_baseline(baseline_path)
    assert len(baseline) > 0                                                   # tracked gaps exist


def test_live_tree_has_no_regressions_against_baseline():
    """The live tree on this branch must not introduce a NEW spec without
    vision_goals beyond the baseline. This is the CI-gate invariant."""
    repo = Path(__file__).parent.parent
    chk = GoalsCheck(
        root=repo / "Plan",
        baseline=__import__("scripts.check_vision_goals", fromlist=["load_baseline"]).load_baseline(
            repo / "Plan" / "_planning" / "vision-goals-baseline.txt"
        ),
    )
    rep = chk.run()
    assert rep.regressions == [], (
        f"new specs lack vision_goals: {rep.regressions} — add `vision_goals: "
        f"[int, ...]` to their frontmatter (per GOALS.md goal IDs 1-8)")
