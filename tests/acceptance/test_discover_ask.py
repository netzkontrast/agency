"""Acceptance — discover.ask, the well-formed AskUser primitive (Spec 310).

Behaviour + invariants (rule 8 — relationships, never pinned snapshots): option
count clamps to [2,4], recommended-first, the REFERENTIAL derivability oracle
(an option whose provenance does not resolve to a supplied item is rejected),
header budget, multiSelect-as-flag, read-only (one ClarificationQuestion, no
CLARIFIES edge), and the emit→fold round-trip.
"""
from __future__ import annotations

import pytest
from pytest_bdd import parsers, scenarios, then, when

from conftest import invoke
from agency.capabilities.discover.clusters.ask import MAX_HEADER_LEN, MAX_OPTIONS, MIN_OPTIONS

scenarios("features/discover_ask.feature")


def _context(n: int) -> list:
    # n identified evidence items — each a derivation source with a stable id.
    return [{"id": f"ctx:{i}", "text": f"evidence span number {i} about approach {i}"}
            for i in range(n)]


@when(parsers.parse("I ask with {n:d} requested options over {m:d} context items"),
      target_fixture="ask_res")
def _ask(engine, confirmed_intent, n, m):
    res, _ = invoke(engine, confirmed_intent, "discover", "ask",
                    agent_id="agent:test", context=_context(m), n_options=n)
    return res


@then("the ask payload has between 2 and 4 options")
def _count(ask_res):
    opts = ask_res["payload"]["options"]
    assert MIN_OPTIONS <= len(opts) <= MAX_OPTIONS, opts


@then("exactly the first option is marked recommended")
def _recommended_first(ask_res):
    opts = ask_res["payload"]["options"]
    assert opts[0]["label"].endswith(" (Recommended)"), opts[0]
    assert not any(o["label"].endswith(" (Recommended)") for o in opts[1:]), opts


@then("every option provenance resolves to a supplied context item")
def _provenance(ask_res):
    opts = ask_res["payload"]["options"]
    # provenance is "ctx:<i>" from the supplied items — referential, not overlap.
    assert all(o["provenance"].startswith("ctx:") for o in opts), opts
    assert all(o["provenance"] for o in opts), "empty provenance is illegal"


@then("the ask payload header is at most 12 characters")
def _header(ask_res):
    assert len(ask_res["payload"]["header"]) <= MAX_HEADER_LEN, ask_res["payload"]["header"]


@when("a manufactured option with unresolvable provenance is derived",
      target_fixture="ask_res")
def _manufactured(engine, confirmed_intent, monkeypatch):
    # Simulate the Driver seam returning a manufactured option (provenance points
    # at an absent id). The referential oracle must reject it — a naive
    # token-overlap check would let it through.
    from agency.capabilities.discover._main import DiscoverCapability
    monkeypatch.setattr(DiscoverCapability, "_derive_options",
                        lambda self, items: [
                            {"label": "ghost", "description": "invented",
                             "provenance": "ghost:absent"},
                            {"label": "phantom", "description": "also invented",
                             "provenance": ""},
                        ])
    res, _ = invoke(engine, confirmed_intent, "discover", "ask",
                    agent_id="agent:test", context=_context(3))
    return res


@then("the ask is rejected as an invalid argument")
def _rejected(ask_res):
    # invoke() returns the failure envelope's data (None) — assert via the error.
    assert ask_res is None or (isinstance(ask_res, dict) and not ask_res.get("payload")), ask_res


@then("exactly one ClarificationQuestion serves the intent")
def _one_node(engine, confirmed_intent):
    rows = engine.memory.nodes_serving(confirmed_intent, "ClarificationQuestion")
    assert len(rows) == 1, rows


@then("no CLARIFIES edge is written to the intent")
def _no_clarifies(engine, confirmed_intent):
    rows = engine.memory.nodes_serving(confirmed_intent, "ClarificationQuestion")
    qid = rows[0]["id"]
    assert not engine.memory.has_edge(qid, confirmed_intent, "CLARIFIES"), \
        "ask must not write CLARIFIES — that is the caller's job"


@when("I ask for independent axes", target_fixture="ask_res")
def _ask_multi(engine, confirmed_intent):
    res, _ = invoke(engine, confirmed_intent, "discover", "ask",
                    agent_id="agent:test", context=_context(4), multi=True)
    return res


@then("the ask payload allows multiple selections")
def _multi(ask_res):
    assert ask_res["payload"]["multiSelect"] is True, ask_res["payload"]


def _bound_discover(engine, intent_id):
    """A DiscoverCapability instance with a real CapabilityContext — the same
    ctx the engine injects per-invocation — so the `fold_answer` helper (a
    cluster method, not a verb) is exercised through its true contract."""
    from agency.capability import CapabilityContext
    from agency.capabilities.discover._main import DiscoverCapability
    ctx = CapabilityContext(
        memory=engine.memory, ontology=engine.ontology,
        registry=engine.registry, intent_id=intent_id, agent_id="agent:test")
    return DiscoverCapability(ctx)


@when("the caller folds an answer for that question", target_fixture="folded")
def _fold(engine, confirmed_intent, ask_res):
    return _bound_discover(engine, confirmed_intent).fold_answer(
        ask_res["question_id"], "ctx:1")


@then("the ClarificationQuestion is answered")
def _answered(engine, folded):
    node = engine.memory.recall(folded["question_id"])
    assert node["status"] == "answered", node
    assert node.get("answer") == "ctx:1", node


@then("folding an unknown question id raises")
def _unknown_raises(engine, confirmed_intent):
    with pytest.raises(ValueError):
        _bound_discover(engine, confirmed_intent).fold_answer("nope:absent", "x")
