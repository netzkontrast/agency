"""Acceptance — symbols capability (Spec 300)."""
from __future__ import annotations

from pytest_bdd import parsers, scenarios, then, when

from conftest import invoke


scenarios("features/symbols.feature")


def _s(engine, intent, verb, **kw):
    r, _ = invoke(engine, intent, "symbols", verb, agent_id="agent:test", **kw)
    return r


@when("I read the symbols legend", target_fixture="legend")
def _legend(engine, confirmed_intent):
    return _s(engine, confirmed_intent, "legend")


@then('the legend maps "because" and "therefore"')
def _legend_maps(legend):
    phrases = {e["phrase"] for e in legend["legend"]}
    assert {"because", "therefore"} <= phrases


@when(parsers.parse('I compress "{text}"'), target_fixture="compressed")
def _compress(engine, confirmed_intent, text):
    return _s(engine, confirmed_intent, "compress", text=text)


@then("the compressed text contains the failed and therefore symbols")
def _has_symbols(compressed):
    assert "❌" in compressed["compressed"] and "∴" in compressed["compressed"], compressed


@then("the compression reports a positive token reduction")
def _reduction(compressed):
    assert compressed["reduction"] >= 0 and compressed["compressed_tokens"] <= compressed["original_tokens"]


@when("I expand a symbol-dense status line", target_fixture="expanded")
def _expand(engine, confirmed_intent):
    return _s(engine, confirmed_intent, "expand", text="build ✅ » deploy 🔄")


@then("the expanded text contains the words for the symbols")
def _expanded(expanded):
    t = expanded["expanded"]
    assert "completed" in t and "then" in t and "in progress" in t, t
