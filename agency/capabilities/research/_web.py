"""Web-search boundary driver (Spec 044 §"Web-search boundary driver").

v1 ships ONLY the protocol; the default is None. The host (the engine
caller or a downstream skill) injects a concrete client when web
research is wanted. Tests stub the protocol.

When the running session has access to the host's `WebSearch` MCP tool
(e.g. Claude Code's built-in), a future thin wrapper exposes it as a
WebSearchClient. This is deferred to a follow-up — v1 doesn't ship
the wrapper.
"""
from __future__ import annotations

from typing import Protocol


class WebSearchClient(Protocol):
    """Pluggable web-search backend boundary.

    Implementations return a list of `{url, title, text}` dicts.
    Citations record the URL + a text snippet; confidence rules per
    spec §"confidence computation rule".
    """

    name: str

    def search(self, query: str, k: int = 5) -> list[dict]: ...
