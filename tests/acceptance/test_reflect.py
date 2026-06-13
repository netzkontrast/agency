"""Acceptance — reflect (semantic recall). Converted from
tests/test_reflect_recall_semantic.py (behaviour: the recall_semantic return
contract). Dropped as implementation/structural (not behaviour): the
docstring-content tests (test_reflect_scope_enum_in_doc) and the
`_check_reflection_links` lint-internal tests (test_reflection_link_lint) —
those are review/lint concerns, not observable behaviour.
"""
from pytest_bdd import given, parsers, scenarios, then, when

from conftest import invoke

scenarios("features/reflect.feature")


@given("a few technical and project reflections are recorded")
def _seed(engine, confirmed_intent):
    for scope, text in [
        ("technical", "fix MCP startup hang on Linux"),
        ("technical", "solved the FastMCP bind issue with a port retry"),
        ("project", "shipping v0.2 next week"),
    ]:
        invoke(engine, confirmed_intent, "reflect", "note", scope=scope, text=text)


@when(parsers.parse('I semantically recall "{query}" with k {k:d}'),
      target_fixture="recall")
def _recall(engine, confirmed_intent, query, k):
    r, _ = invoke(engine, confirmed_intent, "reflect", "recall_semantic",
                  query=query, k=k)
    return r


@then("the payload names its embedder")
def _embedder(recall):
    assert recall.get("embedder"), "payload must name the embedder backend"


@then("every result carries id, score, scope and text with a score in [0,1]")
def _shape(recall):
    for h in recall["results"]:
        for key in ("id", "score", "scope", "text"):
            assert key in h, f"result missing {key}"
        assert 0.0 <= float(h["score"]) <= 1.0


@then("the result scores are in descending order")
def _sorted(recall):
    scores = [h["score"] for h in recall["results"]]
    assert scores == sorted(scores, reverse=True)


@then(parsers.parse("at most {n:d} result is returned"))
def _limit(recall, n):
    assert len(recall["results"]) <= n


@when("I semantically recall with an empty query", target_fixture="recall")
def _recall_empty(engine, confirmed_intent):
    r, _ = invoke(engine, confirmed_intent, "reflect", "recall_semantic", query="", k=3)
    return r


@then("no results are returned")
def _empty(recall):
    assert recall["results"] == []
