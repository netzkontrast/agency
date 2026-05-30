"""Phase 7 — Spec 023 token-budget acceptance gate.

`search "reflect note"` on the live registry returns ≤120 tokens. Measured
via tiktoken's cl100k encoding (project's stable proxy for the Claude
tokenizer; the precision matters less than the regression signal — if a
future commit pushes the count back over the line, this test catches it).

If tiktoken is not installed (minimal CI), falls back to char/4 proxy.
"""
from __future__ import annotations

import pytest

from agency.engine import Engine


def _count_tokens(text: str) -> int:
    # The Spec 023 budget is DEFINED in tiktoken cl100k tokens. A char/4 proxy
    # counts differently (e.g. a 521-char search = 130 by proxy vs 112 by
    # tiktoken), so validating the gate without the real tokenizer would
    # false-fail. tiktoken is pinned in [dev]; if it is genuinely absent
    # (minimal install) we SKIP rather than assert against the wrong unit.
    try:
        import tiktoken
    except ImportError:  # pragma: no cover
        import pytest
        pytest.skip("tiktoken not installed; token-budget gate needs the real "
                    "cl100k tokenizer (pinned in [dev]) — skipping vs false-fail")
    return len(tiktoken.encoding_for_model("gpt-4").encode(text))


async def _search(query: str, limit: int = 5) -> str:
    e = Engine(":memory:")
    try:
        mcp = e.build_mcp(codemode=True)
        result = await mcp.call_tool("search", {"query": query, "limit": limit})
        return result.content[0].text
    finally:
        e.memory.close()


async def test_search_reflect_note_under_budget():
    body = await _search("reflect note", limit=5)
    tokens = _count_tokens(body)
    assert tokens <= 120, (
        f"search 'reflect note' returned {tokens} tokens (budget=120). "
        f"Body ({len(body)} chars):\n{body}"
    )


async def test_search_dispatch_under_budget():
    """Another typical query — `dispatch` matches jules+delegate verbs."""
    body = await _search("dispatch", limit=5)
    tokens = _count_tokens(body)
    assert tokens <= 120, (
        f"search 'dispatch' returned {tokens} tokens (budget=120). "
        f"Body ({len(body)} chars):\n{body}"
    )


async def test_search_default_limit_under_budget():
    """Open-ended query at default limit — the worst-case discovery scan
    an agent runs when the search query is generic. Allow more room here
    since this is fundamentally a wider net."""
    body = await _search("graph", limit=8)
    tokens = _count_tokens(body)
    # Wider net allows wider budget — but still within Spec 023 chained
    # cost ≤ 250 tokens for the full discovery flow.
    assert tokens <= 200, (
        f"search 'graph' (wider) returned {tokens} tokens (budget=200). "
        f"Body ({len(body)} chars):\n{body}"
    )
