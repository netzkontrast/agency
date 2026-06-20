"""Acceptance — TokenCounter typed result + cache + band (Spec 201).

The authoritative `messages.count_tokens` backend already ships (Spec 082).
These scenarios guard Spec 201's additions, network-free via a forced proxy
counter: the typed `CountResult`, the per-(content, model) cache, and the
band-agreement helper. Code in `agency/_tokens.py`.
"""
from __future__ import annotations

import pytest
from pytest_bdd import given, when, then, scenarios, parsers

from agency import _tokens

scenarios("features/token_count_api.feature")


@pytest.fixture
def ctx() -> dict:
    return {}


# ── typed CountResult + cache ─────────────────────────────────────────────────
@given("a proxy-backed token counter")
def _proxy_counter(ctx):
    ctx["counter"] = _tokens.TokenCounter("proxy", _tokens._proxy)


@when(parsers.parse('I count_result "{text}" against "{model}"'))
def _count_one(ctx, text, model):
    ctx["result"] = ctx["counter"].count_result(text, model)


@when(parsers.parse('I count_result empty text against "{model}"'))
def _count_empty(ctx, model):
    ctx["result"] = ctx["counter"].count_result("", model)


@when(parsers.parse('I count_result "{text}" against "{model}" twice'))
def _count_twice(ctx, text, model):
    ctx["first"] = ctx["counter"].count_result(text, model)
    ctx["second"] = ctx["counter"].count_result(text, model)


@then("the result tokens are positive")
def _tokens_positive(ctx):
    assert ctx["result"].tokens > 0


@then("the result tokens are zero")
def _tokens_zero(ctx):
    assert ctx["result"].tokens == 0


@then(parsers.parse('the result backend is "{backend}"'))
def _result_backend(ctx, backend):
    assert ctx["result"].backend == backend


@then(parsers.parse('the result model is "{model}"'))
def _result_model(ctx, model):
    assert ctx["result"].model == model


@then("the result is not cached")
def _result_uncached(ctx):
    assert ctx["result"].cached is False


@then("the second result is cached")
def _second_cached(ctx):
    assert ctx["second"].cached is True


@then("both results have equal tokens")
def _equal_tokens(ctx):
    assert ctx["first"].tokens == ctx["second"].tokens


@then("the second model's result is not cached")
def _cross_model_uncached(ctx):
    # the second `count_result` (different model, same text) must be a cache miss
    assert ctx["result"].cached is False
    assert ctx["result"].model == "claude-haiku-4-5"


# ── band agreement ────────────────────────────────────────────────────────────
@given(parsers.parse("the band thresholds {low:g} and {high:g}"))
def _band(ctx, low, high):
    ctx["low"], ctx["high"] = low, high


@then(parsers.parse("{a:d} against {b:d} is within the band"))
def _within(ctx, a, b):
    assert _tokens.band_ok(a, b, low=ctx["low"], high=ctx["high"]) is True


@then(parsers.parse("{a:d} against {b:d} is outside the band"))
def _outside(ctx, a, b):
    assert _tokens.band_ok(a, b, low=ctx["low"], high=ctx["high"]) is False
