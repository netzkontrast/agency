"""Spec 168 Slice 1 — typed Citation shape + backend-selection invariant.

Research today supports two web backends: the Anthropic-hosted
`web_search` tool (Spec 044) and the zero-config DuckDuckGo client.
Spec 168 lifts the shared output shape (`Citation`) into a typed
frozen dataclass + commits to a deterministic backend-selection
invariant so the verify path is backend-agnostic.

Slice 1 ships the typed shape + the selector + the hashing helper.
Slice 2 wires the anthropic_web backend through Spec 147; Slice 3
adds Spec 154 overflow capture for long result lists.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Literal


CitationBackend = Literal["anthropic_web", "duckduckgo"]
_VALID_BACKENDS = ("anthropic_web", "duckduckgo")


@dataclass(frozen=True)
class Citation:
    """One web-search result. The shape is identical across backends so
    downstream consumers (research.fetch, the verify path, the brief
    builder) don't branch on backend internals."""

    url:          str
    title:        str
    snippet:      str
    retrieved_at: str
    backend:      CitationBackend
    hash:         str

    def __post_init__(self) -> None:
        if not self.url:
            raise ValueError("Citation.url must be non-empty")
        if self.backend not in _VALID_BACKENDS:
            raise ValueError(
                f"Citation.backend must be one of {_VALID_BACKENDS}; "
                f"got {self.backend!r}")
        if not self.hash:
            raise ValueError(
                "Citation.hash must be non-empty (dedup + provenance "
                "discipline; compute via compute_citation_hash(url, snippet))")


def compute_citation_hash(url: str, snippet: str) -> str:
    """Deterministic 16-char hex hash over (url, snippet). Two backends
    returning the same content for the same URL produce the same hash —
    dedup + cross-backend provenance becomes trivial.

    The snippet is included (not just the URL) so a page that updates
    its content surfaces as a NEW citation, not a duplicate."""
    payload = "|".join([url, snippet]).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:16]


def select_backend(env: dict) -> CitationBackend:
    """Pure backend selector. Invariant:
      - `ANTHROPIC_API_KEY` present AND `AGENCY_RESEARCH_ANTHROPIC` != "0"
        ⇒ `"anthropic_web"`
      - else `"duckduckgo"`

    No silent fallback at runtime — the selection is fixed per the env
    at the boundary so the verify path is reproducible.
    """
    has_key = bool((env or {}).get("ANTHROPIC_API_KEY", "").strip())
    opt_out = str((env or {}).get("AGENCY_RESEARCH_ANTHROPIC", "")).strip()
    if has_key and opt_out != "0":
        return "anthropic_web"
    return "duckduckgo"
