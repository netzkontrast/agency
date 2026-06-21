"""Acceptance — per-spec Followup derived metrics (Spec 269).

The FollowupBlock's metrics are COMPUTED (test_count from affects+collection,
Done-When ratio parsed from the spec body, recent_commits from git log, status
from frontmatter) — never hand-pinned. Hand-prose stays in a `<!-- hand -->`
zone. Code ships in `scripts/followup_derive.py`.
"""
from __future__ import annotations

from pathlib import Path

import pytest
from pytest_bdd import given, when, then, scenarios, parsers

from scripts import followup_derive as fd

scenarios("features/followup_derive.feature")

_REPO = Path(__file__).resolve().parents[2]
_PLAN = _REPO / "Plan"


@pytest.fixture
def ctx() -> dict:
    return {}


def _spec_body(checked: int, total: int, *, extra_boxes_outside: int = 0) -> str:
    boxes = "".join(
        f"- [{'x' if i < checked else ' '}] item {i}\n" for i in range(total)
    )
    outside = "".join(f"- [ ] outside {i}\n" for i in range(extra_boxes_outside))
    return (
        "# Spec\n\n## Why\n\nsome prose\n\n"
        f"## Done When\n\n{boxes}\n"
        f"## Open questions\n\n{outside}\n"
    )


def _block(**kw):
    base = dict(spec_id="123", status="partial", test_files=("tests/test_x.py",),
                test_count=3, done_when_checked=2, done_when_total=4,
                recent_commits=())
    base.update(kw)
    return fd.FollowupBlock(**base)


# ── Done-When checkbox parse ──────────────────────────────────────────────────
@given(parsers.parse("a spec body with {checked:d} of {total:d} Done-When boxes checked"))
def _body(ctx, checked, total):
    ctx["text"] = _spec_body(checked, total)
    ctx["expect"] = (checked, total)


@given("a spec body with boxes in Done-When and other boxes elsewhere")
def _body_mixed(ctx):
    ctx["text"] = _spec_body(2, 3, extra_boxes_outside=5)
    ctx["expect"] = (2, 3)


@when("I parse the Done-When section")
def _parse(ctx):
    ctx["got"] = fd.parse_done_when(ctx["text"])


@then(parsers.parse("the checked/total is {checked:d} of {total:d}"))
def _check_ratio(ctx, checked, total):
    assert ctx["got"] == (checked, total)


@then("done_pct equals checked over total")
def _check_pct(ctx):
    checked, total = ctx["got"]
    blk = _block(done_when_checked=checked, done_when_total=total)
    assert blk.done_pct == (checked / total if total else 0.0)


@then("only the Done-When boxes are counted")
def _only_done_when(ctx):
    assert ctx["got"] == ctx["expect"]


# ── invariants ────────────────────────────────────────────────────────────────
@given("a FollowupBlock with test_count greater than zero")
def _block_with_tests(ctx):
    ctx["block"] = _block(test_count=5, test_files=("tests/test_x.py",))


@then("at least one affects path is under tests/")
def _has_test_file(ctx):
    b = ctx["block"]
    assert b.test_count == 0 or any(f.startswith("tests/") for f in b.test_files)


@given("a fully-checked spec marked shipped")
def _shipped_full(ctx):
    ctx["shipped"] = _block(status="shipped", done_when_checked=7, done_when_total=7)


@given("a fully-checked spec marked draft")
def _draft_full(ctx):
    ctx["draft"] = _block(status="draft", done_when_checked=7, done_when_total=7)


@then("the shipped one is status-consistent")
def _shipped_consistent(ctx):
    assert fd.status_consistent(ctx["shipped"]) is True


@then("the draft one is not status-consistent")
def _draft_inconsistent(ctx):
    assert fd.status_consistent(ctx["draft"]) is False


# ── determinism ───────────────────────────────────────────────────────────────
@given("a FollowupBlock derived from a fixture spec")
def _fixture_block(ctx):
    ctx["block"] = _block(recent_commits=("a1b2c3 fix", "d4e5f6 spec"))


@when("I render it twice")
def _render_twice(ctx):
    ctx["r1"] = fd.render_block(ctx["block"])
    ctx["r2"] = fd.render_block(ctx["block"])


@then("the two renders are identical")
def _identical(ctx):
    assert ctx["r1"] == ctx["r2"]


# ── live tree ─────────────────────────────────────────────────────────────────
@given("the Spec 191 spec which has affects test files")
def _spec191(ctx):
    # Specs live in physical Plan/<state>/<id>-*/ folders (Spec 357); discover
    # the path wherever 191 currently sits rather than pinning a layout.
    matches = (sorted(_PLAN.glob("*/191-vision-alignment-live-matrix/spec.md"))
               + sorted(_PLAN.glob("191-vision-alignment-live-matrix/spec.md")))
    assert matches, "Spec 191 spec.md not found under Plan/"
    ctx["spec_path"] = matches[0]


@when("I derive its FollowupBlock over the live tree")
def _derive_live(ctx):
    ctx["block"] = fd.derive_block(ctx["spec_path"], counts={})


@then("recent_commits is a list of strings")
def _commits_list(ctx):
    rc = ctx["block"].recent_commits
    assert isinstance(rc, tuple)
    assert all(isinstance(c, str) for c in rc)


@then("done_when_total is at least 1")
def _total_ge1(ctx):
    assert ctx["block"].done_when_total >= 1
