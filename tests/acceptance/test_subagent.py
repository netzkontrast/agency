"""Acceptance — subagent capability (Spec 041).

Converted from tests/test_subagent*.py (none found in flat suite — coverage gap).
Behaviour: the two-stage gate flow of subagent.develop; observable outputs are
done bool, child lifecycle state, and gate nodes in the graph.

Dropped as implementation/structural (not behaviour):
- subagent-driven-development skill shape (structural inventory)
- skill phase names (structural)
"""
from __future__ import annotations

import tempfile

import pytest
from pytest_bdd import given, scenarios, then, when

from conftest import invoke
from agency.engine import Engine

scenarios("features/subagent.feature")


@pytest.fixture
def engine():
    e = Engine(tempfile.mktemp(suffix=".db"))
    yield e
    e.memory.close()


@pytest.fixture
def confirmed_intent(engine):
    iid = engine.intent.capture("subagent acceptance", "behaviour", "verified")
    engine.intent.confirm(iid)
    return iid


def _develop(engine, confirmed_intent, spec_passed, quality_passed,
             spec_evidence="", quality_evidence=""):
    res, _ = invoke(engine, confirmed_intent, "subagent", "develop",
                    driver="reflect", driver_verb="note",
                    item={"scope": "observation", "text": "task"},
                    spec_passed=spec_passed, quality_passed=quality_passed,
                    spec_evidence=spec_evidence, quality_evidence=quality_evidence)
    return res.get("result", res) if isinstance(res, dict) else res


# ── Given steps ───────────────────────────────────────────────────────────────

@given("a fresh agency engine in code-mode", target_fixture="engine")
def _given_engine(engine):
    return engine


@given("a confirmed intent", target_fixture="confirmed_intent")
def _given_intent(confirmed_intent):
    return confirmed_intent


# ── both gates pass ───────────────────────────────────────────────────────────

@when("I dispatch a subagent task with both gates passing", target_fixture="dev_result")
def _develop_pass(engine, confirmed_intent):
    return _develop(engine, confirmed_intent, spec_passed=True, quality_passed=True,
                    spec_evidence="spec ok", quality_evidence="quality ok")


@then("the develop result reports done true")
def _done_true(dev_result):
    assert dev_result["done"] is True


@then("the child lifecycle is completed")
def _child_completed(engine, dev_result):
    child = dev_result["child"]
    assert engine.memory.recall(child).get("state") == "completed"


@then("the quality gate verdict is recorded")
def _quality_recorded(dev_result):
    quality = dev_result.get("quality")
    assert quality is not None
    assert quality.get("gate")  # Gate node id recorded


# ── spec gate fails ───────────────────────────────────────────────────────────

@when("I dispatch a subagent task with the spec gate failing", target_fixture="dev_spec_fail")
def _develop_spec_fail(engine, confirmed_intent):
    return _develop(engine, confirmed_intent, spec_passed=False, quality_passed=False,
                    spec_evidence="spec failed")


@then("the develop result reports done false")
def _done_false(dev_spec_fail):
    assert dev_spec_fail["done"] is False


@then("the spec gate verdict is recorded")
def _spec_recorded(dev_spec_fail):
    spec = dev_spec_fail.get("spec")
    assert spec is not None
    assert spec.get("gate")  # Gate node id recorded
