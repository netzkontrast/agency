"""Spec 103 Slice 2 — 2 more decidable storyform check verbs.

Per the goal-loop "honest retraction beats over-claiming" lesson from
Slice 1: ship only verbs where the broken-fixture exact-fail contract
holds without ontology lookup OR check-chaining.

This slice ships 2 verbs that ARE shape-decidable:

- check_slot_fill (row 4) — null required-slot detection. Fires on
  broken_work_slot_fill (null concern_id). All other broken fixtures
  pass: they replace values, never null them.
- check_storybeat_moment_refs (row 11) — referential integrity:
  moments[*].storybeat_ref ∈ storybeats[*].id. Fires on
  broken_work_storybeat_moment_refs. Purely structural.

`check_signpost_permutation` (row 10) was investigated but retracted
mid-slice: its decidable check over-fires on
broken_work_throughline_partition (which mutates mc.class_id, leaving
signposts mismatched under the new class). Slice 3 will chain the
two checks (gate on partition-clean, then audit signpost-canonical)
so the over-fire becomes structural rather than spurious.
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from agency.engine import Engine

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "novel"


def _fresh() -> Engine:
    return Engine(tempfile.mktemp(suffix=".db"))


def _confirmed_iid(e: Engine, purpose: str = "spec 103 slice 2") -> str:
    iid = e.intent.capture(purpose, "storyform checks", "verified")
    e.intent.confirm(iid)
    return iid


def _invoke(e: Engine, iid: str, verb: str, **kw):
    return e.registry.invoke(e.memory, iid, "novel", verb, **kw)


def _load_fixture(name: str) -> dict:
    return json.loads((FIXTURE_DIR / f"{name}.ncp.json").read_text())


_BROKEN_FIXTURES = (
    "broken_work_approach_concern",
    "broken_work_crucial_element_placement",
    "broken_work_ktad_coverage",
    "broken_work_mental_sex_problem_solving",
    "broken_work_pair_reciprocity",
    "broken_work_quad_completeness",
    "broken_work_resolve_outcome_judgment",
    "broken_work_signpost_permutation",
    "broken_work_slot_fill",
    "broken_work_storybeat_moment_refs",
    "broken_work_throughline_partition",
)


# ─────────────────────── verb registration ───────────────────────


def test_slice2_registers_two_more_check_verbs() -> None:
    e = _fresh()
    cap = e.registry._caps["novel"]
    expected = {"check_slot_fill", "check_storybeat_moment_refs"}
    missing = expected - set(cap.verbs)
    assert not missing, f"missing: {missing}"
    e.memory.close()


# ─────────────────────── check_slot_fill ───────────────────────


def test_check_slot_fill_passes_good_work() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    ncp = _load_fixture("good_work")
    data, _ = _invoke(e, iid, "check_slot_fill", ncp=ncp)
    assert data["passed"] is True
    assert data["violations"] == []
    e.memory.close()


def test_check_slot_fill_fails_named_fixture() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    ncp = _load_fixture("broken_work_slot_fill")
    data, _ = _invoke(e, iid, "check_slot_fill", ncp=ncp)
    assert data["passed"] is False
    assert data["violations"]
    e.memory.close()


def test_check_slot_fill_does_not_fail_other_broken_fixtures() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    for name in _BROKEN_FIXTURES:
        if name == "broken_work_slot_fill":
            continue
        ncp = _load_fixture(name)
        data, _ = _invoke(e, iid, "check_slot_fill", ncp=ncp)
        assert data["passed"] is True, (
            f"fixture {name} unexpectedly broke slot_fill")
    e.memory.close()


# ─────────────────────── check_storybeat_moment_refs ───────────────────────


def test_check_storybeat_moment_refs_passes_good_work() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    ncp = _load_fixture("good_work")
    data, _ = _invoke(e, iid, "check_storybeat_moment_refs", ncp=ncp)
    assert data["passed"] is True
    e.memory.close()


def test_check_storybeat_moment_refs_fails_named_fixture() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    ncp = _load_fixture("broken_work_storybeat_moment_refs")
    data, _ = _invoke(e, iid, "check_storybeat_moment_refs", ncp=ncp)
    assert data["passed"] is False
    assert data["violations"]
    e.memory.close()


def test_check_storybeat_moment_refs_does_not_fail_other_broken_fixtures() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    for name in _BROKEN_FIXTURES:
        if name == "broken_work_storybeat_moment_refs":
            continue
        ncp = _load_fixture(name)
        data, _ = _invoke(e, iid, "check_storybeat_moment_refs", ncp=ncp)
        assert data["passed"] is True, (
            f"fixture {name} unexpectedly broke storybeat_moment_refs")
    e.memory.close()


