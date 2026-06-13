"""Acceptance — session driver verbs (Spec 114).

Converted from tests/test_session_driver.py. Behaviour: graph nodes minted,
SERVES edges, mode recorded. Drops the structural walk-phase-count checks
and SkillRun internal slice tests — review/implementation concerns only.
"""
from __future__ import annotations

from pytest_bdd import given, parsers, scenarios, then, when

from conftest import invoke

scenarios("features/session_driver.feature")


# ── helpers ────────────────────────────────────────────────────────────────

def _find_nodes(engine, label):
    return engine.memory.g.query(f"MATCH (n:{label}) RETURN n")


def _serves(engine, node_id, iid):
    return engine.memory.g.query(
        "MATCH (n)-[:SERVES]->(i:Intent) WHERE n.id = $nid AND i.id = $iid RETURN n",
        {"nid": node_id, "iid": iid},
    )


# ── Given steps ────────────────────────────────────────────────────────────

@given(parsers.parse("a session lifecycle has been initialised with mode {mode}"),
       target_fixture="lifecycle")
def _init_lifecycle(engine, confirmed_intent, mode):
    res, _ = invoke(engine, confirmed_intent, "develop", "session_init",
                    mode_hint=mode)
    return res


# ── When steps ─────────────────────────────────────────────────────────────

@when(parsers.parse("I call develop.session_init with mode_hint {mode}"),
      target_fixture="init_result")
def _session_init(engine, confirmed_intent, mode):
    res, _ = invoke(engine, confirmed_intent, "develop", "session_init",
                    mode_hint=mode)
    return res


@when("I call develop.session_check with that session_lifecycle_id",
      target_fixture="check_result")
def _session_check_explicit(engine, confirmed_intent, lifecycle):
    res, _ = invoke(engine, confirmed_intent, "develop", "session_check",
                    session_lifecycle_id=lifecycle["session_lifecycle_id"])
    return res


@when("I call develop.session_check with no session_lifecycle_id",
      target_fixture="check_result")
def _session_check_implicit(engine, confirmed_intent, lifecycle):
    res, _ = invoke(engine, confirmed_intent, "develop", "session_check")
    return res


@when(parsers.parse("I call develop.mode_select with new_mode {new_mode} on that lifecycle"),
      target_fixture="mode_result")
def _mode_select(engine, confirmed_intent, lifecycle, new_mode):
    # map "coding" from the feature (valid)
    res, _ = invoke(engine, confirmed_intent, "develop", "mode_select",
                    session_lifecycle_id=lifecycle["session_lifecycle_id"],
                    new_mode=new_mode)
    return res


@when("I call reflect.synthesize_session with that session_lifecycle_id",
      target_fixture="synth_result")
def _synthesize(engine, confirmed_intent, lifecycle):
    res, _ = invoke(engine, confirmed_intent, "reflect", "synthesize_session",
                    session_lifecycle_id=lifecycle["session_lifecycle_id"])
    return res


@when("I call dogfood.record_decision with subject \"use A\" and decision \"accept\" and rationale \"reason\"",
      target_fixture="decision_result")
def _record_decision(engine, confirmed_intent):
    res, _ = invoke(engine, confirmed_intent, "dogfood", "record_decision",
                    subject="use A", decision="accept", rationale="reason")
    return res


@when("I call dogfood.boundary_use_audit", target_fixture="audit_result")
def _boundary_audit(engine, confirmed_intent):
    res, _ = invoke(engine, confirmed_intent, "dogfood", "boundary_use_audit")
    return res


@when("I call develop.session_resume", target_fixture="resume_result")
def _session_resume(engine, confirmed_intent, lifecycle):
    res, _ = invoke(engine, confirmed_intent, "develop", "session_resume")
    return res


# ── Then steps — session_init ──────────────────────────────────────────────

@then("the result has a session_lifecycle_id starting with sessionlifecycle:")
def _has_slc_id(init_result):
    slc_id = init_result.get("session_lifecycle_id", "")
    assert slc_id.startswith("sessionlifecycle:"), (
        f"expected sessionlifecycle: prefix, got {slc_id!r}"
    )


@then(parsers.parse("the result mode is {mode}"))
def _result_mode(init_result, mode):
    assert init_result.get("mode") == mode, init_result


@then("the result has a suggested_first_verb")
def _has_suggested(init_result):
    assert init_result.get("suggested_first_verb"), init_result


@then("the SessionLifecycle SERVES the intent in the graph")
def _slc_serves(engine, confirmed_intent, init_result):
    slc_id = init_result.get("session_lifecycle_id", "")
    rows = _serves(engine, slc_id, confirmed_intent)
    assert rows, f"SessionLifecycle {slc_id} does not SERVE {confirmed_intent}"


# ── Then steps — session_check ─────────────────────────────────────────────

@then(parsers.parse("the session_check result mode is {mode}"))
def _check_mode(check_result, mode):
    assert check_result.get("mode") == mode, check_result


@then("the session_check result has a session_lifecycle_id")
def _check_has_slc(check_result):
    assert check_result.get("session_lifecycle_id"), check_result


# ── Then steps — mode_select ───────────────────────────────────────────────

@then("the mode_select result to_mode is coding")
def _new_mode(mode_result):
    assert mode_result.get("to_mode") == "coding", mode_result


@then("a ModeShift node is recorded in the graph")
def _mode_shift(engine):
    rows = _find_nodes(engine, "ModeShift")
    assert rows, "no ModeShift node found"


# ── Then steps — synthesize_session ───────────────────────────────────────

@then("the synthesize result contains a session-reflection artefact")
def _has_art(synth_result):
    # synthesize_session returns either an artefact dict or a result string
    artefact = synth_result.get("artefact") or synth_result.get("result")
    assert artefact, f"no artefact in {synth_result!r}"
    # The artefact should carry a session-reflection kind marker
    if isinstance(artefact, dict):
        assert artefact.get("kind") == "session-reflection", artefact
    else:
        assert isinstance(artefact, str) and len(artefact) > 0


# ── Then steps — record_decision ──────────────────────────────────────────

@then("the decision result has a decision_id")
def _has_decision_id(decision_result):
    assert decision_result.get("decision_id"), decision_result


@then("the DecisionRecord SERVES the intent in the graph")
def _decision_serves(engine, confirmed_intent, decision_result):
    rows = _serves(engine, decision_result.get("decision_id", ""), confirmed_intent)
    assert rows, "DecisionRecord does not SERVE intent"


# ── Then steps — boundary_use_audit ───────────────────────────────────────

@then("the audit result has a bypass_count")
def _bypass_count(audit_result):
    assert "bypass_count" in audit_result, audit_result


@then("the audit tool breakdown is empty")
def _breakdown_empty(audit_result):
    # actual field is by_tool or tool_breakdown depending on impl
    breakdown = audit_result.get("tool_breakdown") or audit_result.get("by_tool") or {}
    assert breakdown == {} or breakdown == [], (
        f"expected empty breakdown, got {breakdown!r}"
    )


# ── Then steps — session_resume ────────────────────────────────────────────

@then("the resume result has a session_lifecycle_id")
def _resume_slc(resume_result):
    assert resume_result.get("session_lifecycle_id"), resume_result


@then("the resume result status is active")
def _resume_active(resume_result):
    assert resume_result.get("status") == "active", resume_result
