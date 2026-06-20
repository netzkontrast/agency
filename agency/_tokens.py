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

import hashlib
import os
import time
from collections import OrderedDict
from dataclasses import dataclass

_CHARS_PER_TOKEN = 4
_DEFAULT_MODEL = "claude-opus-4-8"

# Spec 201 — named band tunables (rule 8; OQ3: widen via PR with a claude-api
# citation, never silently). The authoritative API count and the tiktoken
# approximation should agree to within this band; outside it signals a
# tokenizer-family mismatch (e.g. an OpenAI-family delta on code).
TOKEN_BAND_LOW = 0.80
TOKEN_BAND_HIGH = 1.30
# Documented LRU size cap (OQ1) — counts are derivable, never persisted to the
# graph (CLAUDE.md rule 2); the in-process cache is per-counter-lifetime.
_CACHE_MAX = 4096


@dataclass(frozen=True)
class CountResult:
    """Spec 201 — the typed token-count return. Callers branch on `backend` for
    diagnostics; `tokens` is always usable. `cached`/`latency_ms` expose the
    per-(content, model) cache; `error_code` is set when the preferred backend
    fell back (empty on the happy path)."""
    tokens: int
    backend: str            # "count_tokens" (the Anthropic API) | "tiktoken" | "proxy"
    model: str
    cached: bool
    latency_ms: int
    error_code: str = ""


def band_ok(a: int, b: int, *, low: float = TOKEN_BAND_LOW,
            high: float = TOKEN_BAND_HIGH) -> bool:
    """True iff `a / b` sits within `[low, high]` — the two backends agree to
    within the band. `b == 0` is vacuously True (nothing to compare against)."""
    if b == 0:
        return True
    ratio = a / b
    return low <= ratio <= high


class TokenCounter:
    """A resolved counter: `backend` names the tier; `count(text, model)` measures.
    Never raises — any backend failure degrades to the char proxy.

    Spec 201 — `count_result` returns the typed :class:`CountResult` and both it
    and `count` read through a per-(content, model) LRU cache, so Spec 146's
    `prefix_size_tokens` is cheap to recompute every call."""

    def __init__(self, backend: str, fn):
        self.backend = backend                 # "count_tokens" | "tiktoken" | "proxy"
        self._fn = fn
        self._cache: "OrderedDict[tuple[str, str], int]" = OrderedDict()

    def _cached_count(self, text: str, model: str) -> tuple[int, bool]:
        """Return `(tokens, cached)`. Deterministic per (content, model): a hit
        returns the prior count (cache-idempotence invariant). A backend failure
        degrades to the char proxy, exactly as the bare `count` did."""
        key = (hashlib.sha256(text.encode("utf-8")).hexdigest()[:32], model)
        if key in self._cache:
            self._cache.move_to_end(key)
            return self._cache[key], True
        try:
            n = int(self._fn(text, model))
        except Exception:
            n = max(1, len(text) // _CHARS_PER_TOKEN)
        self._cache[key] = n
        if len(self._cache) > _CACHE_MAX:
            self._cache.popitem(last=False)     # evict the least-recently-used
        return n, False

    def count(self, text: str, model: str | None = None) -> int:
        if not text:
            return 0
        return self._cached_count(text, model or _DEFAULT_MODEL)[0]

    def count_result(self, text: str, model: str | None = None) -> CountResult:
        """Spec 201 — the typed count: tokens + backend + model + cache state +
        wall-clock. Empty text is a zero-cost, uncached result."""
        m = model or _DEFAULT_MODEL
        if not text:
            return CountResult(tokens=0, backend=self.backend, model=m,
                               cached=False, latency_ms=0)
        t0 = time.perf_counter()
        n, cached = self._cached_count(text, m)
        return CountResult(tokens=n, backend=self.backend, model=m, cached=cached,
                           latency_ms=int((time.perf_counter() - t0) * 1000))


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
