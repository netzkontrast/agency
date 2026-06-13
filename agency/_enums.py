"""Spec 284 — projected-enum substrate.

A *projected enum* is a field whose graph value is a closed enum, but whose
caller-facing parameter accepts free text and is PROJECTED onto a canonical
member — keeping the original rich text in a paired ``<field>_detail`` prop so
nothing is lost (the non-lossy contract). The discovery half (surfacing the
members in ``get_schema``) lives in ``engine._wire`` via the verb spec's
``param_enums``; this module is the pure projection primitive.

The capability supplies the domain alias map (``novel._POV_ALIASES``); the
engine owns the primitive. On no signal, projection returns ``(None, original)``
so the caller raises a PERMANENT typed error (Spec 282) rather than silently
mis-filing — forgiving on signal, strict on noise.
"""
from __future__ import annotations

from typing import Iterable, Mapping, Optional, Tuple


def project_enum(
    value: str,
    members: Iterable[str],
    *,
    aliases: Optional[Mapping[str, str]] = None,
    default: Optional[str] = None,
) -> Tuple[Optional[str], str]:
    """Project free-text ``value`` onto one canonical ``members`` entry.

    Returns ``(canonical, detail)``:
      - ``canonical`` ∈ ``members`` (or ``default``), or ``None`` when nothing
        matches and no default is given.
      - ``detail`` is the original ``value`` when it differs from the canonical
        (the rich text to preserve), else ``""``.

    Match order (first wins):
      1. exact member (case-sensitive) → ``(value, "")`` — already canonical.
      2. exact member (case-insensitive, whitespace-trimmed) → ``(member, value)``.
      3. alias keyword: any ``aliases`` key that is a substring of the
         normalized value → its canonical member. Keys are tried **longest
         first**, so a specific signal wins over a generic one
         (``third-omniscient`` before ``third``).
      4. ``default`` when supplied.
      5. ``(None, value)`` — no signal; caller raises a permanent error.
    """
    members = list(members)
    if value in set(members):
        return value, ""
    norm = " ".join(value.split()).strip().lower()
    lower_map = {m.lower(): m for m in members}
    if norm in lower_map:
        return lower_map[norm], value
    if aliases:
        for key in sorted(aliases, key=len, reverse=True):
            if key and key.lower() in norm:
                return aliases[key], value
    if default is not None:
        return default, value
    return None, value
