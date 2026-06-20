"""Acceptance — live vision-alignment matrix (Spec 191).

The matrix is DERIVED from each spec's `vision_goals:` + `status:`
frontmatter (Spec 149), never hand-maintained. These scenarios guard the
observable behaviour: goal status is computed from named shipped-fraction
thresholds, the three biggest gaps recompute, the goal catalogue derives
from GOALS.md, and every live spec with `vision_goals:` lands in a row.

Code ships in `scripts/vision_matrix.py`.
"""
from __future__ import annotations

from pathlib import Path

from pytest_bdd import given, scenarios, then, when, parsers

from scripts import vision_matrix as vm

scenarios("features/vision_matrix.feature")

_REPO = Path(__file__).resolve().parents[2]
_GOALS_MD = _REPO / "docs" / "vision" / "GOALS.md"
_PLAN = _REPO / "Plan"


def _ref(status: str, *goals: int) -> "vm.SpecRef":
    return vm.SpecRef(spec_id=f"x{id(status)}", slug="s", status=status, goals=tuple(goals))


# ── shared state ────────────────────────────────────────────────────────────
class Ctx(dict):
    pass


import pytest


@pytest.fixture
def ctx() -> Ctx:
    return Ctx()


# ── goal status ─────────────────────────────────────────────────────────────
@given(parsers.parse("a goal with {shipped:d} shipped, {partial:d} partial, and {ns:d} not-started spec"))
def _goal_row(ctx, shipped, partial, ns):
    specs = (
        [_ref("shipped", 1) for _ in range(shipped)]
        + [_ref("partial", 1) for _ in range(partial)]
        + [_ref("not_started", 1) for _ in range(ns)]
    )
    ctx["row"] = vm.GoalRow(goal_id=1, title="T", specs=tuple(specs))


@when("I build the goal row")
def _noop_build(ctx):
    pass  # row built in the given


@then(parsers.parse('the shipped fraction is "{frac}"'))
def _frac(ctx, frac):
    assert f"{ctx['row'].shipped_fraction:.2f}" == frac


@then(parsers.parse('the goal status is "{status}"'))
def _status(ctx, status):
    assert ctx["row"].status == status


# ── threshold classification ────────────────────────────────────────────────
@given(parsers.parse('shipped fractions "{a}", "{b}", "{c}"'))
def _fracs(ctx, a, b, c):
    ctx["fracs"] = [float(a), float(b), float(c)]


@when("I classify each fraction")
def _classify(ctx):
    ctx["statuses"] = [vm.goal_status(f) for f in ctx["fracs"]]


@then(parsers.parse('the statuses are "{a}", "{b}", "{c}"'))
def _check_statuses(ctx, a, b, c):
    assert ctx["statuses"] == [a, b, c]


# ── biggest gaps ────────────────────────────────────────────────────────────
@given(parsers.parse('goals with shipped fractions "{f1}", "{f2}", "{f3}", "{f4}", "{f5}"'))
def _gap_goals(ctx, f1, f2, f3, f4, f5):
    rows = []
    for i, f in enumerate([f1, f2, f3, f4, f5], start=1):
        # synthesize a row whose shipped_fraction equals f: 10 specs, round(f*10) shipped
        n_ship = round(float(f) * 10)
        specs = [_ref("shipped", i) for _ in range(n_ship)] + [
            _ref("not_started", i) for _ in range(10 - n_ship)
        ]
        rows.append(vm.GoalRow(goal_id=i, title=f"G{i}", specs=tuple(specs)))
    ctx["rows"] = rows


@when("I take the three biggest gaps")
def _take_gaps(ctx):
    ctx["gaps"] = vm.biggest_gaps(ctx["rows"], 3)


@then(parsers.parse('the gap fractions in order are "{a}", "{b}", "{c}"'))
def _check_gaps(ctx, a, b, c):
    got = [f"{g.shipped_fraction:.1f}" for g in ctx["gaps"]]
    assert got == [a, b, c]


# ── goal catalogue derived from GOALS.md ────────────────────────────────────
@when("I parse the goals from the live GOALS.md")
def _parse_goals(ctx):
    ctx["goals"] = vm.parse_goals(_GOALS_MD.read_text(encoding="utf-8"))


@then("each goal id maps to a non-empty title")
def _titles(ctx):
    assert ctx["goals"], "no goals parsed"
    assert all(isinstance(t, str) and t.strip() for t in ctx["goals"].values())


@then("the goal ids are contiguous starting from 1")
def _contiguous(ctx):
    ids = sorted(ctx["goals"])
    assert ids == list(range(1, len(ids) + 1)), ids


# ── status source: TODO.md binding index ─────────────────────────────────────
@given(parsers.parse('a TODO verdict listing "{a}" and "{b}" as shipped'))
def _todo_verdict(ctx, a, b):
    ctx["todo"] = f"| **Shipped** | 2 | {a}, **{b}** |\n"


@when("I parse the status index")
def _parse_index(ctx):
    ctx["index"] = vm.parse_status_index(ctx["todo"])


@then(parsers.parse('"{a}" and "{b}" resolve to "{status}"'))
def _index_resolves(ctx, a, b, status):
    assert ctx["index"].get(a) == status
    assert ctx["index"].get(b) == status


@then("an unlisted spec id resolves to nothing")
def _index_unlisted(ctx):
    assert ctx["index"].get("999") is None


# ── coverage invariant over the live tree ───────────────────────────────────
@given("the matrix is built over the live Plan tree")
def _build_live(ctx):
    ctx["goals"] = vm.parse_goals(_GOALS_MD.read_text(encoding="utf-8"))
    ctx["specs"] = vm.collect_specs(_PLAN)
    ctx["rows"] = vm.build_rows(ctx["specs"], ctx["goals"])


@then("every spec with vision_goals appears in at least one goal row")
def _no_orphans(ctx):
    rep = vm.coverage_report(ctx["specs"], ctx["rows"])
    assert rep["orphan_specs"] == [], rep["orphan_specs"]


@then("no spec references a goal id absent from GOALS.md")
def _no_unknown(ctx):
    rep = vm.coverage_report(ctx["specs"], ctx["rows"])
    assert rep["unknown_goal_refs"] == [], rep["unknown_goal_refs"]
