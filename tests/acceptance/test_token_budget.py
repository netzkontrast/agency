"""Acceptance — token budget (Spec 023 / 082).

Converted from tests/test_token_budget.py and tests/test_token_counter.py.

Dropped (implementation / structural / not observable behaviour):
- test_proxy_tier_forced / test_tiktoken_tier_forced: these assert on internal
  backend selection and the `backend` attribute — implementation detail not
  observable via the wire.
- test_injected_real_counter_is_used: tests injection of a lambda into a private
  constructor — internal wiring, not wire behaviour.
- test_proxy_and_tiktoken_agree_within_a_band: asserts an internal relationship
  between two private functions (_proxy, _tiktoken_fn) — not observable from
  outside the module.
- test_empty_text_is_zero: trivial internal API test — not a system behaviour.
"""
from __future__ import annotations

import asyncio

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from agency.engine import Engine
from agency._tokens import TokenCounter

scenarios("features/token_budget.feature")


# ── helpers ───────────────────────────────────────────────────────────────────

def _count_tokens(text: str) -> int:
    try:
        import tiktoken
        return len(tiktoken.encoding_for_model("gpt-4").encode(text))
    except ImportError:
        pytest.skip("tiktoken not installed; token-budget gate needs the real tokenizer")


async def _search_text(query: str, limit: int) -> str:
    e = Engine(":memory:")
    try:
        mcp = e.build_mcp(codemode=True)
        result = await mcp.call_tool("search", {"query": query, "limit": limit})
        return result.content[0].text
    finally:
        e.memory.close()


def _search(query: str, limit: int) -> str:
    return asyncio.run(_search_text(query, limit))


# ── shared Given override ─────────────────────────────────────────────────────

@given("a fresh agency engine in code-mode", target_fixture="budget_engine")
def _fresh_budget_engine():
    e = Engine(":memory:")
    return e


# ── when ─────────────────────────────────────────────────────────────────────

@when(parsers.parse('I search for "{query}" with limit {limit:d}'),
      target_fixture="search_body")
def _search_step(query, limit):
    return _search(query, limit)


@when("I inspect the engine token counter", target_fixture="token_counter")
def _inspect_counter(budget_engine):
    return budget_engine.token_counter


@given("a token counter whose backend always raises",
       target_fixture="failing_counter")
def _failing_counter():
    def boom(t, m):
        raise RuntimeError("backend down")
    return TokenCounter("count_tokens", boom)


@when("I count tokens for a 40-character string", target_fixture="token_result")
def _count_with_failing(failing_counter):
    return failing_counter.count("a" * 40)


# ── then ──────────────────────────────────────────────────────────────────────

@then(parsers.parse("the result token count is at most {budget:d}"))
def _under_budget(search_body, budget):
    tokens = _count_tokens(search_body)
    assert tokens <= budget, (
        f"search returned {tokens} tokens (budget={budget}). "
        f"Body ({len(search_body)} chars):\n{search_body}")


@then("it has a non-empty backend name")
def _backend_name(token_counter):
    assert token_counter.backend and isinstance(token_counter.backend, str)


@then("it returns a positive count for a non-empty string")
def _positive_count(token_counter):
    assert token_counter.count("hello world") > 0


@then("the result is the char/4 proxy value of 10")
def _proxy_fallback(token_result):
    assert token_result == 10, (
        "a failing backend must fall back to len//4 proxy, not raise")
