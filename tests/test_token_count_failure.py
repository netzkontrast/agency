"""Spec 201 — the remaining two Done-When items: error_code population on
per-call backend fallback, and the rich agency_doctor.token_backend report.

CountResult/band_ok/the anthropic backend/cache already ship; this closes the
failure-mode coverage (item 7) and the Spec-170 doctor surface (item 8).
"""
from __future__ import annotations

import asyncio
import tempfile

from agency._tokens import TokenCounter, backends_available
from agency.engine import Engine


def test_count_result_sets_error_code_and_falls_back_on_backend_failure():
    def boom(text, model):
        raise RuntimeError("rate limited")

    tc = TokenCounter("count_tokens", boom)        # claims the API backend…
    r = tc.count_result("hello world over the band", "claude-x")
    assert r.error_code != ""        # the typed fallback signal (item 7)
    assert r.backend == "proxy"      # honest: the count came from the proxy, not the API
    assert r.tokens >= 1             # never crashes the caller's budget check


def test_count_result_happy_path_has_no_error_code():
    tc = TokenCounter("tiktoken", lambda t, m: 5)
    r = tc.count_result("hi", "m")
    assert r.error_code == ""
    assert r.backend == "tiktoken"
    assert r.tokens == 5


def test_backends_available_lists_proxy_at_minimum():
    avail = backends_available()
    assert "proxy" in avail          # proxy is always resolvable


def test_doctor_token_backend_is_the_rich_report():
    e = Engine(tempfile.mktemp(suffix=".db"))
    mcp = e.build_mcp(codemode=False)

    async def main():
        return await mcp.call_tool("agency_doctor", {})

    try:
        res = asyncio.run(main())
        tb = res.structured_content["token_backend"]
        assert isinstance(tb, dict)
        assert set(tb) >= {"available", "preferred", "last_used", "band_check_ok"}
        assert "proxy" in tb["available"]
        assert isinstance(tb["preferred"], str) and tb["preferred"]
    finally:
        e.memory.close()
