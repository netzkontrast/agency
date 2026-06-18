"""Acceptance — discover.interview, the adaptive elicitation engine (Spec 309).

Tested invariants (rule 8 — relationships, never pinned counts): turn-count ==
beats (via the ELICITS traversal), adaptivity (beat-2 question is a function of
beat-1 answer), draft-not-confirmed + DISCOVERED edge, data-driven termination
(complete-early vs max_beats), provenance-whole (non-empty verbatim answers), and
the Driver seam never leaks (a stub NextBeat records the same node/edge surface).
"""
from __future__ import annotations

from pytest_bdd import given, parsers, scenarios, then, when

from conftest import invoke

scenarios("features/discover_interview.feature")


@given("a stub next-beat driver is injected")
def _stub_driver(monkeypatch):
    # Simulate the Spec 147 structured-output Driver returning a typed NextBeat.
    # The seam must not leak: same node/edge surface as the deterministic path.
    from agency.capabilities.discover._main import DiscoverCapability
    monkeypatch.setattr(
        DiscoverCapability, "_next_beat",
        lambda self, idx, prior: ("clarify", "stub beat {prior} / {seed}"))


@when(parsers.parse('I interview "{seed}" with answers "{answers}" and max {n:d} beats'),
      target_fixture="outcome")
def _interview(engine, confirmed_intent, seed, answers, n):
    res, _ = invoke(engine, confirmed_intent, "discover", "interview",
                    agent_id="agent:test", seed=seed,
                    answers=answers.split("|"), max_beats=n)
    return res


@then("the session elicits as many turns as beats reported")
def _turn_count(engine, outcome):
    turns = engine.memory.neighbors(outcome["session_id"], "ELICITS", direction="out")
    assert len(turns) == len(outcome["beats"]), (len(turns), len(outcome["beats"]))


@then("every turn carries a non-empty verbatim answer")
def _provenance_whole(outcome):
    assert all(b["answer"].strip() for b in outcome["beats"]), outcome["beats"]


@then("the second beat question embeds the first beat answer")
def _adaptivity(outcome):
    beats = outcome["beats"]
    assert len(beats) >= 2, beats
    assert beats[0]["answer"] in beats[1]["question"], (beats[0]["answer"], beats[1]["question"])


@then("the produced intent has status draft")
def _draft(engine, outcome):
    node = engine.memory.recall(outcome["intent_id"])
    assert node["status"] == "draft", node
    assert node["status"] != "confirmed"


@then("the session discovered the produced intent")
def _discovered(engine, outcome):
    assert engine.memory.has_edge(outcome["session_id"], outcome["intent_id"],
                                  "DISCOVERED"), "missing DISCOVERED edge"


@then("the interview terminates complete with fewer turns than the budget")
def _complete_early(outcome):
    assert outcome["terminated_by"] == "complete", outcome["terminated_by"]
    assert len(outcome["beats"]) < 6, len(outcome["beats"])


@then(parsers.parse("the interview terminates by max_beats with exactly {n:d} turns"))
def _max_beats(outcome, n):
    assert outcome["terminated_by"] == "max_beats", outcome["terminated_by"]
    assert len(outcome["beats"]) == n, len(outcome["beats"])
