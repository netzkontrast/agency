"""Acceptance — discover.clarity, the Intent readiness score (Spec 322).

Invariants (rule 8 — relationships, not pinned scores): score normalized to
[0,1]; ready = score >= threshold; the score is MONOTONE in satisfied signals
(adding a signal raises it); missing lists the unsatisfied signals; clarity is
read-only (scoring writes no discovery node).
"""
from __future__ import annotations

from pytest_bdd import given, scenarios, then, when

from conftest import invoke

scenarios("features/discover_clarity.feature")

_ANSWERS = ["ship a fast CLI", "a binary", "tests pass"]


@when("I interview and score the resulting draft", target_fixture="clar")
def _interview_score(engine, confirmed_intent):
    out, _ = invoke(engine, confirmed_intent, "discover", "interview",
                    agent_id="agent:test", seed="build a CLI",
                    answers=_ANSWERS, max_beats=6)
    score, _ = invoke(engine, confirmed_intent, "discover", "clarity",
                      agent_id="agent:test", for_intent_id=out["intent_id"])
    return {"draft": out["intent_id"], "score": score}


@when("I interview vaguely and score the resulting draft", target_fixture="clar")
def _interview_vague(engine, confirmed_intent):
    out, _ = invoke(engine, confirmed_intent, "discover", "interview",
                    agent_id="agent:test", seed="vague",
                    answers=["one", "two"], max_beats=2)
    score, _ = invoke(engine, confirmed_intent, "discover", "clarity",
                      agent_id="agent:test", for_intent_id=out["intent_id"])
    return {"draft": out["intent_id"], "score": score}


@then("the clarity score is between 0 and 1")
def _range(clar):
    assert 0.0 <= clar["score"]["score"] <= 1.0, clar["score"]


@then("the draft is not ready")
def _not_ready(clar):
    assert clar["score"]["ready"] is False, clar["score"]


@then("missing lists the unsatisfied readiness signals")
def _missing(clar):
    missing = clar["score"]["missing"]
    assert missing, clar["score"]
    # every missing entry is a real signal that reads False
    assert all(clar["score"]["signals"][m] is False for m in missing), clar["score"]


@then("the has_triple signal is false")
def _no_triple(clar):
    assert clar["score"]["signals"]["has_triple"] is False, clar["score"]


@when("I add a measurable acceptance criterion and a scope boundary to the draft")
def _add_signals(engine, clar):
    draft = clar["draft"]
    ac = engine.memory.record("AcceptanceCriterion",
                              {"text": "the binary runs", "gherkin": "Given/When/Then",
                               "measurable": True})
    engine.memory.link(ac, draft, "VALIDATES")
    sb = engine.memory.record("ScopeBoundary", {"item": "a GUI", "side": "out"})
    engine.memory.link(sb, draft, "BOUNDS")


@when("I re-score the draft")
def _rescore(engine, confirmed_intent, clar):
    score, _ = invoke(engine, confirmed_intent, "discover", "clarity",
                      agent_id="agent:test", for_intent_id=clar["draft"])
    clar["rescore"] = score


@then("the clarity score increased")
def _increased(clar):
    assert clar["rescore"]["score"] > clar["score"]["score"], \
        (clar["score"]["score"], clar["rescore"]["score"])


@then("the draft is now ready")
def _now_ready(clar):
    assert clar["rescore"]["ready"] is True, clar["rescore"]


@then("scoring created no extra acceptance criterion")
def _read_only(engine, confirmed_intent, clar):
    # exactly the ONE AcceptanceCriterion the test added — clarity wrote none.
    rows = engine.memory.neighbors(clar["draft"], "VALIDATES", direction="in")
    assert len(rows) == 1, rows


# ── clarity_gate steps (Spec 322 Slice 2) ────────────────────────────────────

@given("an open lifecycle", target_fixture="lifecycle_id")
def _open_lifecycle(engine, confirmed_intent):
    lc = engine.memory.record("Lifecycle", {"state": "working", "phase": 0})
    engine.memory.link(lc, confirmed_intent, "SERVES")
    return lc


@when("I interview a vague intent and run clarity_gate without override",
      target_fixture="gate_result")
def _gate_no_override(engine, confirmed_intent, lifecycle_id):
    # A vague two-beat interview typically scores below the threshold (missing signals).
    invoke(engine, confirmed_intent, "discover", "interview",
           agent_id="agent:test", seed="vague", answers=["one", "two"], max_beats=2)
    # invoke() returns (data, invocation_id); data is None on ToolResult.failure.
    data, _ = invoke(engine, confirmed_intent, "discover", "clarity_gate",
                     agent_id="agent:test", lifecycle_id=lifecycle_id)
    return {"data": data, "passed": data is not None}


@when("I interview a vague intent and run clarity_gate with an override token",
      target_fixture="gate_result")
def _gate_with_override(engine, confirmed_intent, lifecycle_id):
    invoke(engine, confirmed_intent, "discover", "interview",
           agent_id="agent:test", seed="vague", answers=["one", "two"], max_beats=2)
    data, _ = invoke(engine, confirmed_intent, "discover", "clarity_gate",
                     agent_id="agent:test", lifecycle_id=lifecycle_id,
                     override_token="deliberate-bypass")
    return {"data": data, "passed": data is not None}


@when("I satisfy all signals and run clarity_gate", target_fixture="gate_result")
def _gate_ready(engine, confirmed_intent, lifecycle_id):
    invoke(engine, confirmed_intent, "discover", "interview",
           agent_id="agent:test", seed="build a CLI",
           answers=_ANSWERS, max_beats=6)
    ac = engine.memory.record("AcceptanceCriterion",
                              {"text": "binary runs", "gherkin": "G/W/T",
                               "measurable": True})
    engine.memory.link(ac, confirmed_intent, "VALIDATES")
    sb = engine.memory.record("ScopeBoundary", {"item": "GUI", "side": "out"})
    engine.memory.link(sb, confirmed_intent, "BOUNDS")
    data, _ = invoke(engine, confirmed_intent, "discover", "clarity_gate",
                     agent_id="agent:test", lifecycle_id=lifecycle_id)
    return {"data": data, "passed": data is not None}


@when("I interview a vague intent and run clarity_gate with min_clarity 0.0",
      target_fixture="gate_result")
def _gate_zero_threshold(engine, confirmed_intent, lifecycle_id):
    invoke(engine, confirmed_intent, "discover", "interview",
           agent_id="agent:test", seed="vague", answers=["one", "two"], max_beats=2)
    data, _ = invoke(engine, confirmed_intent, "discover", "clarity_gate",
                     agent_id="agent:test", lifecycle_id=lifecycle_id,
                     min_clarity=0.0)
    return {"data": data, "passed": data is not None}


@then("clarity_gate returns GATE_FAILED")
def _gate_failed(gate_result):
    assert not gate_result["passed"], \
        f"expected GATE_FAILED (None data) but gate passed: {gate_result['data']}"


@then("clarity_gate passes and records the override")
def _gate_override_passes(gate_result):
    assert gate_result["passed"], \
        f"expected gate to pass with override but got None (failure)"
    assert gate_result["data"].get("override_used") is True, gate_result["data"]
    assert gate_result["data"].get("passed") is True, gate_result["data"]


@then("clarity_gate passes without override")
def _gate_passes(gate_result):
    assert gate_result["passed"], \
        f"expected gate to pass but got None (failure)"
    assert gate_result["data"].get("passed") is True, gate_result["data"]
    assert not gate_result["data"].get("override_used"), gate_result["data"]
