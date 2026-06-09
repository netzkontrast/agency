# agency-scaffold: v1
"""music slug — single source of truth for the music capability's slug shape.

Both ``_main.py`` (verbs) and ``drivers_production.py`` (FileStateDriver disk
layout) need slugs. Keeping two copies of the slugifier risks silent drift
(track written under slug A, looked up under slug B → "track not found" bugs
that pass tests because both sides use the same code path).

This module is the canonical home.
"""
from __future__ import annotations

_SLUG_BAD = (" ", "/", "\\", ".", ",", "!", "?", "'", "\"",
             "(", ")", "[", "]")


def slugify(text: str) -> str:
    """Deterministic slugifier — lowercase, replace non-alnum with hyphen, collapse.

    Examples::

        slugify("Modem Daze")     == "modem-daze"
        slugify("The Heist!")      == "the-heist"
        slugify("Carrier (Tone)") == "carrier-tone"
    """
    s = text.lower().strip()
    for ch in _SLUG_BAD:
        s = s.replace(ch, "-")
    while "--" in s:
        s = s.replace("--", "-")
    return s.strip("-")
