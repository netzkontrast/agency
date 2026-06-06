"""Spec 082 — the token-count boundary (count_tokens → tiktoken → proxy)."""
import pytest

from agency._tokens import (TokenCounter, count_tokens, resolve_token_counter,
                            _proxy, _tiktoken_fn)


def test_empty_text_is_zero():
    assert count_tokens("") == 0


def test_proxy_tier_forced(monkeypatch):
    monkeypatch.setenv("AGENCY_TOKENS", "proxy")
    tc = resolve_token_counter()
    assert tc.backend == "proxy"
    assert tc.count("a" * 40) == 10                 # len//4


def test_tiktoken_tier_forced(monkeypatch):
    monkeypatch.setenv("AGENCY_TOKENS", "tiktoken")
    tc = resolve_token_counter()
    assert tc.backend in ("tiktoken", "proxy")      # proxy only if tiktoken absent
    assert tc.count("hello world functions") > 0


def test_injected_real_counter_is_used():
    tc = TokenCounter("count_tokens", lambda t, m: 999)
    assert tc.backend == "count_tokens"
    assert tc.count("anything") == 999


def test_counter_never_raises_degrades_to_proxy():
    def boom(t, m):
        raise RuntimeError("backend down")
    tc = TokenCounter("count_tokens", boom)
    # a failing backend falls back to the char proxy, not an exception
    assert tc.count("a" * 40) == 10


def test_proxy_and_tiktoken_agree_within_a_band():
    """Invariant (rule 8): on a known sample the two cheap tiers are the same order
    of magnitude — not a pinned constant."""
    sample = "def f(x):\n    return x + 1\n" * 30
    proxy = _proxy(sample, None)
    try:
        tk = _tiktoken_fn()(sample, None)
    except Exception:
        pytest.skip("tiktoken not installed")
    assert tk > 0 and proxy > 0
    assert 0.3 < (tk / proxy) < 3.0                 # same ballpark, relationship not snapshot


def test_engine_exposes_token_counter():
    from agency.engine import Engine
    e = Engine(":memory:")
    try:
        assert hasattr(e, "token_counter")
        assert e.token_counter.backend in ("count_tokens", "tiktoken", "proxy")
        assert e.token_counter.count("hello") > 0
    finally:
        e.memory.close()
