"""novel slug — single source of truth for the novel capability's slug shape.

Mirrors `agency/capabilities/music/_slug.py`. Both `_main.py` (verbs that
record `slug` on graph nodes) and `drivers_production.py` (FileNovelStateDriver
disk layout) read from here.
"""
from __future__ import annotations

_SLUG_BAD = (" ", "/", "\\", ".", ",", "!", "?", "'", "\"",
             "(", ")", "[", "]")


def slugify(text: str) -> str:
    """Deterministic slugifier — lowercase, non-alnum → hyphen, collapse.

    Examples::

        slugify("The Heist!")     == "the-heist"
        slugify("Brave New World") == "brave-new-world"
    """
    s = text.lower().strip()
    for ch in _SLUG_BAD:
        s = s.replace(ch, "-")
    while "--" in s:
        s = s.replace("--", "-")
    return s.strip("-")
