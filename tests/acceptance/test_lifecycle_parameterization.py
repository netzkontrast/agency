"""Acceptance — Agent as a Lifecycle parameterization (Spec 342).

An agent IS a Lifecycle parameterization: a named machine variant (Spec 345)
whose transitions insert an observer state (verify / in-review) so
COMPLETED != done. One reducer — ``ctx.lifecycle.advance`` — runs the declared
observer BY NAME through the registry and maps its verdict to a move. Every
driver caller calls the SAME advance; a new parameterization needs zero caller
edits.
"""
from __future__ import annotations

import tempfile

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from agency.engine import Engine
from agency._lifecycle_machines import register_machine, resolve_machine
from agency._lifecycle_transitions import IllegalTransition

scenarios("features/lifecycle_parameterization.feature")


class _StubVCSExists:
    def remote_exists(self, branch, remote="origin"):
        return {"ok": True, "exists": True, "sha": "deadbeef"}


class _StubVCSMissing:
    def remote_exists(self, branch, remote="origin"):
        return {"ok": True, "exists": False, "sha": ""}


class _StubVCSErrors:
    def remote_exists(self, branch, remote="origin"):
        return {"ok": False, "exists": False, "detail": "network unreachable"}


@pytest.fixture
def box():
    return {}


@given("a fresh agency engine for parameterization", target_fixture="engine")
def _given_engine(box):
    # vcs backend is swapped per-scenario via the Given steps below; default exists.
    e = Engine(tempfile.mktemp(suffix=".db"), vcs_backend=_StubVCSExists())
    box["engine"] = e
    yield e
    e.memory.close()


@given("a confirmed parameterization intent", target_fixture="intent_id")
def _given_intent(engine, box):
    iid = engine.intent.capture("parameterization", "behaviour", "verified")
    engine.intent.confirm(iid)
    box["intent_id"] = iid
    return iid


def _reopen_engine(box, vcs):
    """Swap the engine's vcs backend in place (the observer re-checks origin
    through it) and reuse the standing engine + intent."""
    e = box["engine"]
    e.drivers.register("vcs", vcs)
    return e, box["intent_id"]


# ── Given ─────────────────────────────────────────────────────────────────────

@given(parsers.parse('a lifecycle opened with parameterization "{param}" moved to "working"'))
def _open_param_working(engine, intent_id, box, param):
    machine = "a2a" if param == "default" else param
    lc = engine.lifecycle.open(intent_id, parameterization=param, machine=machine)
    engine.lifecycle.move(lc, "working")
    box["lc"] = lc


def _verify_child(box, vcs, branch, machine="remote-async"):
    e, iid = _reopen_engine(box, vcs)
    lc = e.lifecycle.open(iid, parameterization=machine, machine=machine)
    e.lifecycle.annotate(lc, branch=branch)
    e.lifecycle.move(lc, "working")
    e.lifecycle.move(lc, "verify")
    box["lc"] = lc
    return lc


@given(parsers.parse('a remote-async child in "verify" with branch "{branch}" present on origin'))
def _child_present(box, branch):
    _verify_child(box, _StubVCSExists(), branch)


@given(parsers.parse('a remote-async child in "verify" with branch "{branch}" absent from origin'))
def _child_absent(box, branch):
    _verify_child(box, _StubVCSMissing(), branch)


@given('a remote-async child in "verify" whose remote check errors')
def _child_errors(box):
    _verify_child(box, _StubVCSErrors(), "feat/x")


@given(parsers.parse('a registered parameterization "{name}" whose observer is "{cap}.{verb}"'))
def _register_audited(name, cap, verb):
    base = resolve_machine("remote-async")
    # A brand-new machine NO caller knows about, observer declared by name.
    register_machine(name, {
        "derives": "a2a",
        "add_states": ["verify"],
        "replace": {
            "working": {"remove": ["completed"], "add": ["verify"]},
            "verify": ["completed", "input-required", "failed"],
        },
        "observer": {"capability": cap, "verb": verb,
                     "on_done": "completed", "on_not_done": "input-required",
                     "on_error": "verify"},
    })


@given(parsers.parse('a child opened with parameterization "{name}" in "verify" with branch present'))
def _audited_child(box, name):
    _verify_child(box, _StubVCSExists(), "feat/x", machine=name)


@given(parsers.parse('a remote-async child fanned out and driver-reported into "verify" '
                     'with branch absent'))
def _fanned_child(box):
    e, iid = _reopen_engine(box, _StubVCSMissing())
    fan = e.registry.invoke(e.memory, iid, "delegate", "fan_out",
                            driver="jules", driver_verb="verify",
                            items=[{"state": "working", "branch": "feat/x"}], quota=1)[0]
    child = fan["result"]["children"][0]["lifecycle"]
    e.lifecycle.move(child, "verify")             # the driver reports completion
    box["delegation"] = fan["result"]["delegation"]
    box["lc"] = child


# ── When ──────────────────────────────────────────────────────────────────────

@when(parsers.parse('I move the parameterized lifecycle directly to "{to_state}"'))
def _move_direct(engine, box, to_state):
    try:
        engine.lifecycle.move(box["lc"], to_state)
        box["error"] = None
    except IllegalTransition as e:
        box["error"] = e


@when("I advance the child")
def _advance(engine, box):
    box["result"] = engine.lifecycle.advance(box["lc"])


@when(parsers.parse("I fan out 1 jules-driven item"))
def _fan_jules(engine, intent_id, box):
    fan = engine.registry.invoke(engine.memory, intent_id, "delegate", "fan_out",
                                 driver="jules", driver_verb="verify",
                                 items=[{"state": "working", "branch": "feat/x"}], quota=1)[0]
    box["lc"] = fan["result"]["children"][0]["lifecycle"]


@when("delegate.join reduces the delegation")
def _join(engine, intent_id, box):
    res = engine.registry.invoke(engine.memory, intent_id, "delegate", "join",
                                 delegation=box["delegation"])[0]
    box["result"] = res["result"]


# ── Then ──────────────────────────────────────────────────────────────────────

@then("the parameterized move raises IllegalTransition")
def _raised(box):
    assert isinstance(box["error"], IllegalTransition), box.get("error")


@then("moving it through \"verify\" then \"completed\" succeeds")
def _through_verify(engine, box):
    engine.lifecycle.move(box["lc"], "verify")
    engine.lifecycle.move(box["lc"], "completed")
    assert engine.memory.recall(box["lc"]).get("state") == "completed"


@then("the parameterized move succeeds")
def _move_ok(box):
    assert box["error"] is None, box["error"]


@then(parsers.parse('the "{machine}" machine declares observer capability "{cap}" verb "{verb}"'))
def _declares_observer(machine, cap, verb):
    obs = resolve_machine(machine).get("observer")
    assert obs is not None, f"{machine} has no observer"
    assert obs["capability"] == cap and obs["verb"] == verb, obs


@then(parsers.parse('the jules capability declares parameterization "{param}"'))
def _jules_param(engine, param):
    assert engine.registry._caps["jules"].parameterization == param


@then(parsers.parse('the fanned child lifecycle has machine "{machine}"'))
def _child_machine(engine, box, machine):
    assert engine.memory.recall(box["lc"]).get("machine") == machine


@then(parsers.parse('the child moves to "{state}"'))
def _child_moved(engine, box, state):
    assert engine.memory.recall(box["lc"]).get("state") == state


@then(parsers.parse('the child stays in "{state}"'))
def _child_stays(engine, box, state):
    assert engine.memory.recall(box["lc"]).get("state") == state


@then("advance reports done true")
def _done_true(box):
    assert box["result"].get("done") is True, box["result"]


@then("advance reports done false")
def _done_false(box):
    assert box["result"].get("done") is False, box["result"]


@then("advance reports no observer ran")
def _no_observer(box):
    assert box["result"].get("advanced") is False, box["result"]
    assert box["result"].get("observer") is None, box["result"]


@then("join reports done false")
def _join_done_false(box):
    assert box["result"].get("done") is False, box["result"]


@then(parsers.parse('the joined child is in "{state}"'))
def _joined_child(engine, box, state):
    assert engine.memory.recall(box["lc"]).get("state") == state
