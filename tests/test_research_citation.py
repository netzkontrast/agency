"""Spec 168 Slice 1 — typed Citation shape + backend-selection invariants."""
from __future__ import annotations

import hashlib

import pytest

from agency._research_citation import (
    Citation,
    CitationBackend,
    compute_citation_hash,
    select_backend,
)


def test_citation_typed_shape():
    c = Citation(
        url="https://example.com/x",
        title="Example",
        snippet="A snippet.",
        retrieved_at="2026-06-12T10:00:00Z",
        backend="duckduckgo",
        hash=compute_citation_hash("https://example.com/x", "A snippet."),
    )
    assert c.url == "https://example.com/x"
    assert c.backend == "duckduckgo"


def test_citation_rejects_empty_url():
    with pytest.raises(ValueError):
        Citation(url="", title="t", snippet="s", retrieved_at="t",
                  backend="duckduckgo", hash="x")


def test_citation_rejects_invalid_backend():
    with pytest.raises(ValueError):
        Citation(url="x", title="t", snippet="s", retrieved_at="t",
                  backend="bogus", hash="x")                          # type: ignore[arg-type]


def test_citation_rejects_empty_hash():
    """A citation MUST carry a content hash so dedup + provenance are
    deterministic across backends."""
    with pytest.raises(ValueError):
        Citation(url="x", title="t", snippet="s", retrieved_at="t",
                  backend="duckduckgo", hash="")


def test_compute_citation_hash_is_deterministic():
    """Same (url, snippet) yields the same hash across calls."""
    a = compute_citation_hash("https://x.com", "snippet")
    b = compute_citation_hash("https://x.com", "snippet")
    assert a == b
    assert len(a) == 16   # 16-char hex prefix (per the impl contract)


def test_compute_citation_hash_differs_on_different_snippet():
    a = compute_citation_hash("https://x.com", "alpha")
    b = compute_citation_hash("https://x.com", "beta")
    assert a != b


def test_select_backend_uses_anthropic_when_key_set():
    env = {"ANTHROPIC_API_KEY": "sk-...", "AGENCY_RESEARCH_ANTHROPIC": "1"}
    assert select_backend(env) == "anthropic_web"


def test_select_backend_falls_back_to_duckduckgo_without_key():
    env = {}
    assert select_backend(env) == "duckduckgo"


def test_select_backend_anthropic_disabled_by_env_override():
    """`AGENCY_RESEARCH_ANTHROPIC=0` opts OUT of anthropic_web even
    when the key is present — the invariant: backend selection is
    deterministic per the env (no silent fallback)."""
    env = {"ANTHROPIC_API_KEY": "sk-...", "AGENCY_RESEARCH_ANTHROPIC": "0"}
    assert select_backend(env) == "duckduckgo"


def test_backend_set_equals_documented():
    """The valid backends are exactly {anthropic_web, duckduckgo}."""
    assert set(CitationBackend.__args__) == {"anthropic_web", "duckduckgo"}
