"""Acceptance — discover.scope, in/out boundary elicitation (Spec 318).

Invariants (rule 8): candidates derive from GROUNDS citations (not invented);
the question is composed via discover.ask (well-formed); BOUNDS edges == decided
count; in/out/open partition the candidates; ScopeBoundary.side ∈ {in,out}.
"""
from __future__ import annotations

from pytest_bdd import scenarios, then, when

from conftest import invoke

scenarios("features/discover_scope.feature")

# Three grounded claims; the run decides the first two (in/out), leaving the
# third undecided (→ open). Stored on the fixture so the assertions can check
# derivation against the live grounding set.
_CLAIMS = ["cover feature X", "cover feature Y", "cover feature Z"]


def _ground(engine, intent_id, claim):
    cid = engine.memory.record("Citation", {
        "source_kind": "codebase", "source_url_or_path": "f.py",
        "evidence_text": "evidence", "confidence": 0.9,
        "claim_supported": claim, "research_id": "r1"})
    engine.memory.link(cid, intent_id, "GROUNDS")


@when("I scope a grounded intent", target_fixture="scoped")
def _scope(engine, confirmed_intent):
    target = engine.intent.capture("a purpose", "a deliverable", "an acceptance")
    for claim in _CLAIMS:
        _ground(engine, target, claim)
    res, _ = invoke(engine, confirmed_intent, "discover", "scope",
                    agent_id="agent:test", for_intent_id=target,
                    decisions={_CLAIMS[0]: "in", _CLAIMS[1]: "out"})
    return {"target": target, "res": res}


@then("every scope candidate derives from a grounding citation")
def _derived(scoped):
    res = scoped["res"]
    seen = set(res["in_scope"]) | set(res["out_of_scope"]) | set(res["open"])
    assert seen <= set(_CLAIMS), seen  # every decided/open item is a grounded claim
    assert seen, res


@then("the scope question is a well-formed ask payload")
def _well_formed(scoped):
    q = scoped["res"]["question"]
    assert q is not None, "scope must compose discover.ask"
    assert 2 <= len(q["options"]) <= 4, q
    assert q["options"][0]["label"].endswith(" (Recommended)"), q


@then("bounds edges equal the decided boundary count")
def _bounds(engine, scoped):
    res = scoped["res"]
    edges = engine.memory.neighbors(scoped["target"], "BOUNDS", direction="in")
    assert len(edges) == len(res["in_scope"]) + len(res["out_of_scope"]), edges


@then("in-scope out-of-scope and open partition the candidates")
def _partition(scoped):
    res = scoped["res"]
    total = len(res["in_scope"]) + len(res["out_of_scope"]) + len(res["open"])
    assert total == len(_CLAIMS), (total, len(_CLAIMS))
    # disjoint
    assert not (set(res["in_scope"]) & set(res["out_of_scope"])), res
    assert not (set(res["open"]) & (set(res["in_scope"]) | set(res["out_of_scope"]))), res


@then("every boundary side is in or out")
def _sides(engine, scoped):
    for b in engine.memory.neighbors(scoped["target"], "BOUNDS", direction="in"):
        assert b["side"] in ("in", "out"), b


@then("the undecided candidate is open with no boundary node")
def _open(engine, scoped):
    res = scoped["res"]
    assert _CLAIMS[2] in res["open"], res
    # no ScopeBoundary minted for the undecided claim
    items = {b["item"] for b in engine.memory.neighbors(scoped["target"], "BOUNDS", direction="in")}
    assert _CLAIMS[2] not in items, items
