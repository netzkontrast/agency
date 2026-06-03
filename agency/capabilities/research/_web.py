"""Web-search boundary driver (Spec 044 + Spec 052).

Two shipped backends:
  DuckDuckGoClient — zero-config default. POSTs to DuckDuckGo Instant
                     Answer API (no key required). Parses AbstractText
                     + RelatedTopics. Spec 052 §"DuckDuckGo as default".
  resolve_web_search() — env-driven resolution
                     (AGENCY_WEB_BACKEND); matches Spec 045
                     resolve_embedder pattern. Unknown name falls back
                     to DuckDuckGo silently.

A future SerpAPI / Tavily backend slots in next to DuckDuckGoClient —
add to the resolution table, keep the protocol.
"""
from __future__ import annotations

import os
from typing import Protocol


_DDG_API = "https://api.duckduckgo.com/"
_HTTP_TIMEOUT = 10.0


class WebSearchClient(Protocol):
    """Pluggable web-search backend boundary.

    Implementations return a list of `{url, title, text}` dicts.
    Citations record the URL + a text snippet; confidence rules per
    Spec 044 §"confidence computation rule".
    """

    name: str

    def search(self, query: str, k: int = 5) -> list[dict]: ...


class DuckDuckGoClient:
    """Zero-config web search via DuckDuckGo Instant Answer API.

    Returns up to k hits combining AbstractText + RelatedTopics.
    Network failures degrade to empty list (no exceptions cross the
    boundary). v1 doesn't paginate; v2 may.
    """

    name = "duckduckgo"

    def search(self, query: str, k: int = 5) -> list[dict]:
        """Return [{url, title, text}, ...] hits for ``query``."""
        try:
            import httpx
            with httpx.Client(timeout=_HTTP_TIMEOUT) as client:
                resp = client.get(_DDG_API, params={
                    "q": query, "format": "json", "no_html": "1",
                    "skip_disambig": "1",
                })
                resp.raise_for_status()
                data = resp.json()
        except Exception:
            return []
        results: list[dict] = []
        abstract = data.get("AbstractText", "") or ""
        abstract_url = data.get("AbstractURL", "") or ""
        if abstract and abstract_url:
            results.append({
                "url": abstract_url,
                "title": data.get("Heading", "") or "",
                "text": abstract,
            })
        for topic in data.get("RelatedTopics", []) or []:
            if len(results) >= k:
                break
            if not isinstance(topic, dict):
                continue
            url = topic.get("FirstURL", "") or ""
            text = topic.get("Text", "") or ""
            if not url or not text:
                continue
            results.append({"url": url, "title": text[:80], "text": text})
        return results[:k]


# ---------------------------------------------------------------------------
# Resolution — env > unknown-fallback > default.
# ---------------------------------------------------------------------------


KNOWN_BACKENDS: frozenset[str] = frozenset({"duckduckgo"})


def resolve_web_search() -> WebSearchClient:
    """Spec 052 §"Engine wiring": env-driven default; matches Spec 045
    resolve_embedder pattern (env > known-backend > silent-default)."""
    target = (os.environ.get("AGENCY_WEB_BACKEND", "duckduckgo")
              or "duckduckgo").strip()
    if target == "duckduckgo" or target not in KNOWN_BACKENDS:
        return DuckDuckGoClient()
    return DuckDuckGoClient()    # only one backend in v1
