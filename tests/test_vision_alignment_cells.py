"""Spec 191 Slice 2 — the vision-matrix glob fix + typed AlignmentCell projection.

The Slice-1 `scripts/vision_matrix.py` rendered an all-zeros matrix post Spec 357
(its one-level glob missed the `Plan/<state>/<NNN>/spec.md` layout). Slice 2 fixes
the glob and consumes the dormant `AlignmentCell` shape via `to_alignment_cells`,
composing the single matrix source (no second derivation).
"""
from __future__ import annotations

from pathlib import Path

from agency._typed_shapes_waves4_12 import AlignmentCell
from scripts.vision_matrix import (alignment_summary, build_rows, collect_specs,
                                   parse_goals, to_alignment_cells)

_REPO = Path(__file__).resolve().parents[1]
_PLAN = _REPO / "Plan"
_GOALS = _REPO / "docs" / "vision" / "GOALS.md"


def _live_rows():
    goals = parse_goals(_GOALS.read_text(encoding="utf-8"))
    specs = collect_specs(_PLAN)
    return build_rows(specs, goals), specs


def test_glob_fix_collects_the_state_folder_specs():
    # the bug: the old `*/spec.md` glob found ZERO specs post state-migration
    specs = collect_specs(_PLAN)
    assert len(specs) > 100          # the live tree has hundreds of specs


def test_alignment_cells_are_typed_and_valid():
    rows, _ = _live_rows()
    cells = to_alignment_cells(rows)
    assert cells and all(isinstance(c, AlignmentCell) for c in cells)
    assert all(1 <= c.goal_id <= 8 for c in cells)
    assert all(c.status in ("aligned", "partial", "missing") for c in cells)


def test_cells_project_every_spec_goal_pairing_in_1_to_8():
    rows, _ = _live_rows()
    cells = to_alignment_cells(rows)
    # one cell per (spec, goal) for goals 1..8 — matches the rows' membership
    expected = sum(len(r.specs) for r in rows if 1 <= r.goal_id <= 8)
    assert len(cells) == expected


def test_status_maps_from_spec_status():
    # shipped→aligned, partial→partial, not_started→missing (no other values)
    rows, _ = _live_rows()
    cells = to_alignment_cells(rows)
    by_status = {c.status for c in cells}
    assert by_status <= {"aligned", "partial", "missing"}


def test_summary_ready_iff_coverage_clean():
    summ = alignment_summary(_PLAN, _GOALS, _REPO / "TODO.md")
    assert summ["ready"] is True          # live tree: no orphans, no unknown goals
    assert summ["specs"] > 100 and summ["cells"] > 0
    assert len(summ["biggest_gaps"]) <= 3
