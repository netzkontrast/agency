"""Spec 357 follow-up — the spec-tree walker that resurrects the state-migration
broken CI gates.

Four spec-walking scripts globbed `Plan/*/spec.md` (one level) and matched ZERO
specs after specs moved into `Plan/<state>/<NNN>/spec.md` — silently turning
their CI gates (`check_vision_goals`, `derive_docs --check`) into no-ops. The
shared `spec_files` walker globs recursively and excludes `_research`/`_planning`
artefacts.
"""
from __future__ import annotations

from pathlib import Path

from scripts._spec_tree import spec_files

_REPO = Path(__file__).resolve().parents[1]
_PLAN = _REPO / "Plan"


def test_spec_files_finds_the_state_folder_specs():
    files = spec_files(_PLAN)
    # the live tree has hundreds of specs across state folders; the OLD one-level
    # glob found zero — this is the regression guard.
    assert len(files) > 100
    assert all(p.name == "spec.md" for p in files)


def test_spec_files_excludes_underscore_dirs():
    files = spec_files(_PLAN)
    # no research/planning artefact leaks in (Plan/_research/…, Plan/_planning/…)
    assert not any("_research" in p.parts or "_planning" in p.parts
                   for p in files)


def test_spec_files_is_sorted_and_deterministic():
    a = spec_files(_PLAN)
    b = spec_files(_PLAN)
    assert a == b == sorted(a)


def test_check_vision_goals_gate_is_live_again():
    # the resurrected gate must actually audit specs (not the old vacuous 0)
    from scripts.check_vision_goals import check_tree
    results = check_tree(_PLAN)
    assert len(results) > 100
    # and the live tree has no NON-baseline regression (394 was backfilled)
    bad = [r for r in results if not r.ok]
    baseline = {
        line.split()[0].strip()
        for line in (_PLAN / "_planning" / "vision-goals-baseline.txt").read_text().splitlines()
        if line.strip() and not line.startswith("#")
    }
    regressions = [r.spec_id for r in bad if r.spec_id not in baseline]
    assert regressions == [], regressions
