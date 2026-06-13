"""Acceptance — gate capability + gate predicates (Spec 011).

Converted from tests/test_gate_predicates.py + tests/test_coverage_gate.py.

Dropped as implementation/structural (not behaviour):
- test_gate_result_typed_shape: tests the GateResult dataclass constructor — internal shape
- test_evaluate_pass_when_coverage_grows_no_flakes_no_missing: tests _coverage_gate module
  internals (private function evaluate()), not an observable verb output
- test_evaluate_fail_when_coverage_drops_past_epsilon: same
- spec_validate / confidence_check unit tests on the private _predicates module where
  those functions don't surface through the gate.check verb wire shape —
  kept only the integration scenario (sub-threshold → gate.check → paused lifecycle)
"""
from __future__ import annotations

import tempfile

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from conftest import invoke
from agency.engine import Engine
from agency._predicates import confidence_check, spec_validate

scenarios("features/gate.feature")


@pytest.fixture
def engine():
    e = Engine(tempfile.mktemp(suffix=".db"))
    yield e
    e.memory.close()


@pytest.fixture
def confirmed_intent(engine):
    iid = engine.intent.capture("gate acceptance", "behaviour", "verified")
    engine.intent.confirm(iid)
    return iid


def _check(engine, confirmed_intent, lifecycle_id, name, passed, evidence=""):
    res, inv = invoke(engine, confirmed_intent, "gate", "check",
                      lifecycle_id=lifecycle_id, name=name, passed=passed, evidence=evidence)
    return res, inv


# ── Given steps ───────────────────────────────────────────────────────────────

@given("a fresh agency engine in code-mode", target_fixture="engine")
def _given_engine(engine):
    return engine


@given("a confirmed intent", target_fixture="confirmed_intent")
def _given_intent(confirmed_intent):
    return confirmed_intent


@given("an open lifecycle", target_fixture="lifecycle_id")
def _lifecycle(engine, confirmed_intent):
    lc = engine.memory.record("Lifecycle", {"state": "working", "phase": 0})
    engine.memory.link(lc, confirmed_intent, "SERVES")
    return lc


# ── passing gate ───────────────────────────────────────────────────────────────

@when(parsers.parse('I check gate "{name}" with passed true'), target_fixture="gate_result")
def _check_pass(engine, confirmed_intent, lifecycle_id, name):
    res, inv = _check(engine, confirmed_intent, lifecycle_id, name, True, "all green")
    return res, lifecycle_id


@then("the gate result reports passed true")
def _gate_passed(gate_result):
    res, lc = gate_result
    assert res["result"]["passed"] is True


@then(parsers.parse('a Gate node named "{name}" is in the graph'))
def _gate_node(engine, confirmed_intent, lifecycle_id, name):
    rows = engine.memory.g.query(
        "MATCH (g:Gate) WHERE g.name=$n RETURN g", {"n": name})
    assert rows


# ── blocking gate ─────────────────────────────────────────────────────────────

@when(parsers.parse('I check gate "{name}" with passed false'), target_fixture="gate_blocked")
def _check_fail(engine, confirmed_intent, lifecycle_id, name):
    res, inv = _check(engine, confirmed_intent, lifecycle_id, name, False, "blocked")
    return res, lifecycle_id


@then("the direct gate result is blocked")
def _gate_not_passed(gate_blocked):
    res, lc = gate_blocked
    assert res["result"]["passed"] is False


@then(parsers.parse('the blocked lifecycle state is "{state}"'))
def _lifecycle_state(engine, gate_blocked, state):
    res, lc = gate_blocked
    assert engine.memory.recall(lc).get("state") == state


# ── foreign lifecycle guard ───────────────────────────────────────────────────

@when('I check gate "any" against a foreign lifecycle', target_fixture="foreign_result")
def _check_foreign(engine, confirmed_intent):
    # Create a lifecycle that does NOT serve the current intent
    e2 = Engine(tempfile.mktemp(suffix=".db"))
    other_iid = e2.intent.capture("other", "d", "a")
    e2.intent.confirm(other_iid)
    other_lc = e2.memory.record("Lifecycle", {"state": "working", "phase": 0})
    e2.memory.link(other_lc, other_iid, "SERVES")
    e2.memory.close()
    # Now use an unlinked lifecycle id in the main engine
    foreign_lc = engine.memory.record("Lifecycle", {"state": "working", "phase": 0})
    # deliberately do NOT link it to the confirmed_intent
    res, inv = invoke(engine, confirmed_intent, "gate", "check",
                      lifecycle_id=foreign_lc, name="any", passed=True)
    return res


@then("the gate result carries a lifecycle-guard error")
def _guard_error(foreign_result):
    res = foreign_result
    assert "error" in res["result"]


# ── spec_validate predicates ──────────────────────────────────────────────────

@when("I validate a spec with normative keywords and a Gherkin scenario",
      target_fixture="sv_pass")
def _sv_pass():
    text = (
        "The system MUST persist the graph.\n"
        "Scenario: a node is recorded\n"
        "  Given an engine\n  When record is called\n  Then a node exists\n"
    )
    return spec_validate(text)


@then("the validation result is ok with no findings")
def _sv_ok(sv_pass):
    assert sv_pass["ok"] is True
    assert sv_pass["findings"] == []


@when("I validate a spec that has only a Gherkin scenario and no normative keywords",
      target_fixture="sv_no_norm")
def _sv_no_norm():
    return spec_validate("Scenario: x\n  Given a\n  When b\n  Then c\n")


@then(parsers.parse('the normative-keyword finding is flagged as "{rule}"'))
def _sv_flags_norm(sv_no_norm, rule):
    assert sv_no_norm["ok"] is False
    assert any(f["rule"] == rule for f in sv_no_norm["findings"])


@then(parsers.parse('the gherkin finding is flagged as "{rule}"'))
def _sv_flags_gherkin(sv_no_gherkin, rule):
    assert sv_no_gherkin["ok"] is False
    assert any(f["rule"] == rule for f in sv_no_gherkin["findings"])


@when("I validate a spec that has normative keywords but no Gherkin scenario",
      target_fixture="sv_no_gherkin")
def _sv_no_gherkin():
    return spec_validate("The engine MUST do the thing. It SHOULD also be fast.")


# ── confidence_check ─────────────────────────────────────────────────────────

@when("I confidence_check with all claims passing", target_fixture="cc_pass")
def _cc_pass():
    return confidence_check([{"claim": "a", "ok": True}, {"claim": "b", "ok": True}])


@then("the confidence score is 1.0 and no claims are blocking")
def _cc_full(cc_pass):
    assert cc_pass["score"] == 1.0
    assert cc_pass["blocking"] == []


@when("I confidence_check with 2 of 5 claims passing", target_fixture="cc_partial")
def _cc_partial():
    return confidence_check([
        {"claim": "tests pass", "ok": True},
        {"claim": "spec validated", "ok": True},
        {"claim": "no orphans", "ok": False},
        {"claim": "drift clean", "ok": False},
        {"claim": "reviewed", "ok": False},
    ])


@then("the confidence score is 0.4 and 3 claims are blocking")
def _cc_partial_check(cc_partial):
    assert abs(cc_partial["score"] - 0.4) < 0.01
    assert len(cc_partial["blocking"]) == 3


# ── sub-threshold confidence through gate.check ───────────────────────────────

@when("I run a sub-threshold confidence check through gate.check",
      target_fixture="sub_gate")
def _sub_gate(engine, confirmed_intent, lifecycle_id):
    score = confidence_check([
        {"claim": "x", "ok": False}, {"claim": "y", "ok": True}, {"claim": "z", "ok": False}
    ])
    res, inv = invoke(engine, confirmed_intent, "gate", "check",
                      lifecycle_id=lifecycle_id, name="confidence",
                      passed=score["score"] >= 0.9, evidence=str(score["blocking"]))
    return res, lifecycle_id


@then("the sub-threshold gate result is blocked")
def _sub_gate_blocked(sub_gate):
    res, lc = sub_gate
    assert res["result"]["passed"] is False


@then(parsers.parse('the sub-threshold lifecycle state is "{state}"'))
def _sub_lifecycle_state(engine, sub_gate, state):
    res, lc = sub_gate
    assert engine.memory.recall(lc).get("state") == state
