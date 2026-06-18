"""Acceptance — discover.clarity, the Intent readiness score (Spec 322).

Invariants (rule 8 — relationships, not pinned scores): score normalized to
[0,1]; ready = score >= threshold; the score is MONOTONE in satisfied signals
(adding a signal raises it); missing lists the unsatisfied signals; clarity is
read-only (scoring writes no discovery node).
"""
from __future__ import annotations

from pytest_bdd import scenarios, then, when

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
