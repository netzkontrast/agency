"""Acceptance — discover.clarify, the ambiguity-resolution loop (Spec 311).

Invariants (rule 8): monotonic convergence (round scores non-increasing,
residual drops); one CLARIFIES edge per round; bi-temporal keep-both (the
pre-amend revision survives the supersede); termination both ways.
"""
from __future__ import annotations

from pytest_bdd import parsers, scenarios, then, when

from conftest import invoke

scenarios("features/discover_clarify.feature")

# A draft Intent with a too-brief purpose AND a draft-placeholder acceptance →
# two ambiguities the folded answers resolve.
_PLACEHOLDER = "(draft — acceptance not yet elicited)"
_ANSWERS = {
    "underspecified": "build a fast reliable CLI tool for developers",
    "missing-acceptance": "the binary exits zero and prints its version",
}


@when(parsers.parse("I clarify a vague draft with budget {budget:d}"),
      target_fixture="clarified")
def _clarify(engine, confirmed_intent, budget):
    target = engine.intent.capture("short", "a real deliverable here", _PLACEHOLDER)
    res, _ = invoke(engine, confirmed_intent, "discover", "clarify",
                    agent_id="agent:test", for_intent_id=target,
                    answers=dict(_ANSWERS), max_rounds=budget)
    return {"original": target, "res": res}


@then("the clarify loop exits below threshold")
def _below(clarified):
    assert clarified["res"]["exited_by"] == "below_threshold", clarified["res"]


@then("the residual ambiguity is zero")
def _residual(clarified):
    assert clarified["res"]["residual_ambiguity"] == 0.0, clarified["res"]


@then("each round score is non-increasing")
def _monotone(clarified):
    scores = [r["score"] for r in clarified["res"]["rounds"]]
    assert all(scores[i] >= scores[i + 1] for i in range(len(scores) - 1)), scores


@then("it resolved in fewer rounds than the budget")
def _fewer(clarified):
    assert len(clarified["res"]["rounds"]) < 5, clarified["res"]


@then("the CLARIFIES edge count equals the round count")
def _clarifies(engine, clarified):
    edges = engine.memory.neighbors(clarified["original"], "CLARIFIES", direction="in")
    assert len(edges) == len(clarified["res"]["rounds"]), \
        (len(edges), len(clarified["res"]["rounds"]))


@then("both the original intent and its amended revision are recallable")
def _bitemporal(engine, clarified):
    rounds = clarified["res"]["rounds"]
    assert rounds, "expected at least one fold-back"
    assert engine.memory.recall(clarified["original"]) is not None, "original lost"
    assert engine.memory.recall(rounds[0]["amended_to"]) is not None, "revision missing"


@then("the clarify loop exits by max_rounds")
def _max(clarified):
    assert clarified["res"]["exited_by"] == "max_rounds", clarified["res"]


@then("exactly one round ran")
def _one_round(clarified):
    assert len(clarified["res"]["rounds"]) == 1, clarified["res"]
