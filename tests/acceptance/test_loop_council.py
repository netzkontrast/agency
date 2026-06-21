"""Acceptance — the loop council (Spec 365, looper port on the lifecycle spine).

A council member is a reviewer (notes) or a judge (a gating verdict) bound to a
model family — reuse of persona (297) + panel (294), stored on the loop as the
spine interim. The reviewer-only rule: a revise_until_clean gate needs a verdict
source (judge member or human criterion); cross-model is the coaching default.
"""
from __future__ import annotations

import tempfile

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from agency.engine import Engine

scenarios("features/loop_council.feature")


@pytest.fixture
def engine():
    e = Engine(tempfile.mktemp(suffix=".db"))
    yield e
    e.memory.close()


@pytest.fixture
def box():
    return {}


@given("a fresh agency engine in code-mode", target_fixture="engine")
def _eng(engine):
    return engine


@given("an open loop", target_fixture="box")
def _open_loop(engine):
    from agency._loop import open_loop
    iid = engine.intent.capture("loop council", "behaviour", "verified")
    engine.intent.confirm(iid)
    return {"loop_id": open_loop(engine, iid, max_iterations=3)["loop_id"]}


@when(parsers.parse('I add a judge member on the "{family}" family while the host is "{host_family}"'))
def _add_judge(engine, box, family, host_family):
    from agency._loop import add_member, recommend_council
    add_member(engine, box["loop_id"], "judge", scope="both", family=family)
    box["rec"] = recommend_council(engine, box["loop_id"], host_family=host_family)


@when("the judge returns a revise verdict with blocking issues", target_fixture="box")
def _judge_revise(box):
    from agency._loop import check_criterion
    box["verdict"] = check_criterion(
        {"kind": "judge"},
        judge_output='```json\n{"verdict": "revise", "blocking_issues": ["missing owner on step 3"]}\n```',
    )
    return box


@when("the judge returns non-JSON council text", target_fixture="box")
def _judge_bad(box):
    from agency._loop import check_criterion
    box["verdict"] = check_criterion({"kind": "judge"}, judge_output="Looks good to me, shipping it.")
    return box


@given("the council has only a reviewer member")
def _only_reviewer(engine, box):
    from agency._loop import add_member
    add_member(engine, box["loop_id"], "reviewer", scope="plan")


@when("I recommend_council", target_fixture="box")
def _do_recommend(engine, box):
    from agency._loop import recommend_council
    box["rec"] = recommend_council(engine, box["loop_id"], host_family="claude")
    return box


@then(parsers.parse('a member with role "{role}" and family "{family}" is recorded with a driver'))
def _member_recorded(box, role, family):
    m = next((x for x in box["rec"]["members"] if x["role"] == role and x["family"] == family), None)
    assert m is not None, box["rec"]["members"]
    assert m.get("driver"), m


@then("recommend_council notes the member is cross-family")
def _cross_family(box):
    assert any(m.get("cross_family") for m in box["rec"]["members"]), box["rec"]


@then(parsers.parse('the verdict parses as "{verdict}" and does not pass'))
def _verdict_revise(box, verdict):
    assert box["verdict"]["verdict"] == verdict, box["verdict"]
    assert box["verdict"]["verdict"] != "pass", box["verdict"]


@then(parsers.parse('the verdict is "{verdict}" tagged "{warning}"'))
def _verdict_tagged(box, verdict, warning):
    assert box["verdict"]["verdict"] == verdict, box["verdict"]
    assert box["verdict"].get("warning") == warning, box["verdict"]


@then("verdict_sources_ok is false and a gate is listed as missing a verdict source")
def _missing_source(box):
    assert box["rec"]["verdict_sources_ok"] is False, box["rec"]
    assert box["rec"]["missing"], box["rec"]
