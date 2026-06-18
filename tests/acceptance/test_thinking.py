"""Acceptance — thinking capability: critical-thinking method scaffolds (Spec 110)."""
from __future__ import annotations

from pytest_bdd import parsers, scenarios, then, when

from conftest import invoke

scenarios("features/thinking.feature")


def _t(engine, intent, verb, **kw):
    r, _ = invoke(engine, intent, "thinking", verb, agent_id="agent:test", **kw)
    return r


@when("I run thinking.decompose with no subject", target_fixture="scaffold")
def _decompose(engine, confirmed_intent):
    return _t(engine, confirmed_intent, "decompose")


@when(parsers.parse('I run thinking.assumptions for "{subject}"'),
      target_fixture="scaffold")
def _assumptions(engine, confirmed_intent, subject):
    return _t(engine, confirmed_intent, "assumptions", subject=subject)


@when(parsers.parse('I run thinking.red_team for "{subject}"'),
      target_fixture="scaffold")
def _red_team(engine, confirmed_intent, subject):
    return _t(engine, confirmed_intent, "red_team", subject=subject)


@then(parsers.parse('the scaffold method is "{method}"'))
def _method(scaffold, method):
    assert scaffold["method"] == method, scaffold


@then("the scaffold subject is non-empty")
def _subject_nonempty(scaffold):
    assert scaffold["subject"], scaffold


@then(parsers.parse('the scaffold subject is "{subject}"'))
def _subject_is(scaffold, subject):
    assert scaffold["subject"] == subject, scaffold


@then("the scaffold lists reasoning steps")
def _steps(scaffold):
    assert isinstance(scaffold["steps"], list) and len(scaffold["steps"]) >= 2, scaffold


# ── apply_full_review composite ───────────────────────────────────────────────

@when("I run thinking.apply_full_review", target_fixture="review")
def _full_review(engine, confirmed_intent):
    return _t(engine, confirmed_intent, "apply_full_review")


@then("the analysis covers eight founding methods")
def _covers_eight(review):
    # Assert the documented founding set is covered (a relationship, not a
    # frozen count — rule 8); a future composite may cover more.
    founding = {"decompose", "assumptions", "premortem", "first_principles",
                "inversion", "steelman", "second_order", "tradeoffs"}
    assert founding <= set(review["artefact"]["methods"]), review


@then("every covered method carries a scaffold")
def _each_scaffold(review):
    methods = set(review["artefact"]["methods"])
    scaffolded = {s["method"] for s in review["artefact"]["scaffolds"]}
    assert methods == scaffolded, review


@when(parsers.parse('I run thinking.apply_full_review with depth "{depth}"'),
      target_fixture="review_bad")
def _full_review_bad(engine, confirmed_intent, depth):
    return _t(engine, confirmed_intent, "apply_full_review", depth=depth)


@then("no analysis is produced")
def _no_analysis(review_bad):
    assert not review_bad, review_bad
