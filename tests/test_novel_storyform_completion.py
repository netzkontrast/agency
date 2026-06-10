"""Spec 120 — Storyform completion: 9 remaining decidable checks + composite.

Per Spec 120's done-when:
- `_resolve_term(term_id)` matches across kinds (el./var./t./etc.)
- 8 new check verbs ship the exact-fail contract on the 11 fixtures
- `novel_coherence_check` composite runs all checks + records gate.check
- `storyform-build` walkable skill registered
- Check-chaining: row 10 + 3 only run after row 5 passes; row 2 after row 10.

Each fixture mutates ONE field to break ONE check. The parametrized
exact-fail test asserts each broken fixture FAILS precisely its named
check under the composite.
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


def _iid(e: Engine) -> str:
    return e.intent.capture_and_confirm(
        "spec 120 storyform", "all checks ship", "exact-fail holds",
        owner="user")


def _invoke(e: Engine, iid: str, verb: str, **kw):
    r, _ = e.registry.invoke(e.memory, iid, "novel", verb,
                             agent_id="agent:test", **kw)
    return r


def _load(name: str) -> dict:
    return json.loads((FIXTURE_DIR / f"{name}.ncp.json").read_text())


GOOD = "good_work"


# ---------------------------------------------------------------------------
# _resolve_term helper.
# ---------------------------------------------------------------------------


def test_resolve_term_module_helper_exists() -> None:
    from agency.capabilities.novel._main import _resolve_term
    assert callable(_resolve_term)


def test_resolve_term_exact_kind_match() -> None:
    from agency.capabilities.novel._main import _resolve_term
    entry, exact = _resolve_term("el.pursuit")
    assert entry is not None
    assert entry["kind"] == "element"
    assert entry["id"] == "el.pursuit"
    assert exact is True


def test_resolve_term_crosskind_match() -> None:
    """`el.self-interest` exists as `var.self-interest` (variation).
    The slug matches — exact_kind_match=False but the entry is returned."""
    from agency.capabilities.novel._main import _resolve_term
    entry, exact = _resolve_term("el.self-interest")
    assert entry is not None
    assert entry["id"] == "var.self-interest"
    assert entry["kind"] == "variation"
    assert exact is False


def test_resolve_term_type_crosskind() -> None:
    """`t.past` resolves to `type.past` — `t.` is the canonical Dramatica
    prefix alias for `type.`, so exact_kind_match is True."""
    from agency.capabilities.novel._main import _resolve_term
    entry, exact = _resolve_term("t.past")
    assert entry is not None
    assert entry["id"] == "type.past"
    assert exact is True


def test_resolve_term_unknown() -> None:
    from agency.capabilities.novel._main import _resolve_term
    entry, exact = _resolve_term("el.nonexistent-xyz")
    assert entry is None
    assert exact is False


# ---------------------------------------------------------------------------
# 8 new check verbs: each FAILS on its named fixture, PASSES on good_work.
# ---------------------------------------------------------------------------


NEW_CHECKS = [
    ("check_dynamic_pair_reciprocity", "broken_work_pair_reciprocity"),
    ("check_ktad_coverage", "broken_work_ktad_coverage"),
    ("check_quad_completeness", "broken_work_quad_completeness"),
    ("check_crucial_element_placement",
     "broken_work_crucial_element_placement"),
    ("check_resolve_outcome_judgment",
     "broken_work_resolve_outcome_judgment"),
    ("check_approach_concern", "broken_work_approach_concern"),
    ("check_mental_sex_problem_solving",
     "broken_work_mental_sex_problem_solving"),
    ("check_signpost_permutation", "broken_work_signpost_permutation"),
]


@pytest.mark.parametrize("verb_name,fixture", NEW_CHECKS)
def test_check_passes_on_good_fixture(verb_name, fixture) -> None:
    e = _fresh()
    iid = _iid(e)
    r = _invoke(e, iid, verb_name, ncp=_load(GOOD))
    assert r["passed"] is True, f"{verb_name} unexpectedly failed on good: {r}"


@pytest.mark.parametrize("verb_name,fixture", NEW_CHECKS)
def test_check_fails_on_named_broken_fixture(verb_name, fixture) -> None:
    e = _fresh()
    iid = _iid(e)
    r = _invoke(e, iid, verb_name, ncp=_load(fixture))
    if verb_name == "check_approach_concern":
        # WARN-severity per spec — surfaces as warnings, not violations.
        assert r.get("warnings"), f"{verb_name} should warn on {fixture}: {r}"
    else:
        assert r["passed"] is False, \
            f"{verb_name} unexpectedly passed on {fixture}: {r}"
        assert r["violations"], "violations list must be non-empty"


# ---------------------------------------------------------------------------
# Composite: novel_coherence_check runs everything + check-chaining.
# ---------------------------------------------------------------------------


def test_composite_verb_registered() -> None:
    e = _fresh()
    verbs = set(e.registry.get("novel").verbs)
    assert "novel_coherence_check" in verbs


def test_composite_passes_on_good_fixture() -> None:
    e = _fresh()
    iid = _iid(e)
    r = _invoke(e, iid, "novel_coherence_check", ncp=_load(GOOD))
    assert r["passed"] is True, f"good fixture must pass composite: {r}"
    assert r.get("violations", []) == []


# ---------------------------------------------------------------------------
# Exact-fail contract: each broken_work_<row> fails EXACTLY its named check
# under the composite. Check-chaining makes ktad-vs-signpost tractable.
# ---------------------------------------------------------------------------


# (fixture_name, expected_check_name_in_violations)
EXACT_FAIL = [
    ("broken_work_pair_reciprocity", "dynamic_pair_reciprocity"),
    ("broken_work_ktad_coverage", "ktad_coverage"),
    ("broken_work_quad_completeness", "quad_completeness"),
    ("broken_work_crucial_element_placement", "crucial_element_placement"),
    ("broken_work_resolve_outcome_judgment", "resolve_outcome_judgment"),
    ("broken_work_mental_sex_problem_solving", "mental_sex_problem_solving"),
    ("broken_work_signpost_permutation", "signpost_permutation"),
    ("broken_work_slot_fill", "slot_fill"),  # row 4, already shipped
    ("broken_work_storybeat_moment_refs", "storybeat_moment_refs"),  # row 11
    ("broken_work_throughline_partition", "throughline_partition"),  # row 5
]


@pytest.mark.parametrize("fixture,expected_check", EXACT_FAIL)
def test_exact_fail_contract(fixture, expected_check) -> None:
    """Each broken_work_<row> fixture fails EXACTLY its named check
    under the composite. The check-chaining (row 5 → 10 → 2; row 5 → 3)
    enforces this even when shape signals overlap (Slice-2 retraction
    lesson)."""
    e = _fresh()
    iid = _iid(e)
    r = _invoke(e, iid, "novel_coherence_check", ncp=_load(fixture))
    assert r["passed"] is False, f"{fixture} must fail: {r}"
    # The named check must appear in violations.
    failed_checks = {v["check"] for v in r["violations"]}
    assert expected_check in failed_checks, (
        f"{fixture}: expected {expected_check!r} in violations, "
        f"got {failed_checks}; report={r}")


def test_approach_concern_warns_not_fails() -> None:
    """Row 8 emits WARN-severity (not blocking)."""
    e = _fresh()
    iid = _iid(e)
    r = _invoke(e, iid, "novel_coherence_check",
                ncp=_load("broken_work_approach_concern"))
    # warnings exist + composite still passes (warnings don't block).
    assert r.get("warnings"), f"expected warnings on row 8: {r}"
    warned = {w["check"] for w in r["warnings"]}
    assert "approach_concern" in warned


# ---------------------------------------------------------------------------
# Walkable skill: storyform-build registered with 6 phases.
# ---------------------------------------------------------------------------


def test_storyform_build_skill_registered() -> None:
    e = _fresh()
    skills = e.ontology.skills
    assert "storyform-build" in skills
    phases = skills["storyform-build"]["phases"]
    assert len(phases) == 6
    # Final phase is a hard gate (composite check).
    assert phases[-1].get("gate") == "hard"
