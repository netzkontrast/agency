"""Spec 082 — the token-count boundary.

ONE place to count tokens, with tiers (best first):
  1. **count_tokens** — Anthropic `messages.count_tokens` (model-specific, the
     authoritative count; the `claude-api` skill warns tiktoken undercounts Claude
     tokens ~15–20%). Used when `ANTHROPIC_API_KEY` + the `anthropic` SDK are present.
  2. **tiktoken** — cl100k approximation (close for English; off on code).
  3. **proxy** — `len(text)//4` (zero-dep, hermetic).

Replaces the SAME `tiktoken-else-char//4` proxy that was DUPLICATED across
document/dogfood/plugin (a derivability-audit catch). `agency_doctor` reports the
live `backend` so the active tier is visible. `AGENCY_TOKENS=proxy|tiktoken` pins a
tier (hermetic CI / offline).
"""
from __future__ import annotations

import os

_CHARS_PER_TOKEN = 4
_DEFAULT_MODEL = "claude-opus-4-8"


class TokenCounter:
    """A resolved counter: `backend` names the tier; `count(text, model)` measures.
    Never raises — any backend failure degrades to the char proxy."""

    def __init__(self, backend: str, fn):
        self.backend = backend                 # "count_tokens" | "tiktoken" | "proxy"
        self._fn = fn

    def count(self, text: str, model: str | None = None) -> int:
        if not text:
            return 0
        try:
            return int(self._fn(text, model or _DEFAULT_MODEL))
        except Exception:
            return max(1, len(text) // _CHARS_PER_TOKEN)


def _proxy(text: str, model: str) -> int:
    return max(1, len(text) // _CHARS_PER_TOKEN)


def _tiktoken_fn():
    import tiktoken
    enc = tiktoken.get_encoding("cl100k_base")
    return lambda text, model: len(enc.encode(text))


def _anthropic_fn():
    import anthropic
    client = anthropic.Anthropic()             # reads ANTHROPIC_API_KEY from env

    def fn(text: str, model: str) -> int:
        r = client.messages.count_tokens(
            model=model, messages=[{"role": "user", "content": text}])
        return r.input_tokens
    return fn


def resolve_token_counter() -> TokenCounter:
    """Pick the best available backend. `AGENCY_TOKENS=proxy|tiktoken` forces a tier;
    else count_tokens (key + SDK) → tiktoken → proxy."""
    forced = os.environ.get("AGENCY_TOKENS", "").strip().lower()
    if forced == "proxy":
        return TokenCounter("proxy", _proxy)
    if forced != "tiktoken" and os.environ.get("ANTHROPIC_API_KEY"):
        try:
            return TokenCounter("count_tokens", _anthropic_fn())
        except Exception:
            pass
    try:
        return TokenCounter("tiktoken", _tiktoken_fn())
    except Exception:
        return TokenCounter("proxy", _proxy)


_DEFAULT: TokenCounter | None = None


def count_tokens(text: str, model: str | None = None) -> int:
    """Module-level convenience over a cached default counter (the migration target
    for the previously-scattered inline tiktoken helpers)."""
    global _DEFAULT
    if _DEFAULT is None:
        _DEFAULT = resolve_token_counter()
    return _DEFAULT.count(text, model)
