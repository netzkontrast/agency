"""Shared spec-tree walker — the ONE place that knows where spec files live.

Spec 357 moved every spec into a physical STATE folder
(``Plan/<state>/<NNN-slug>/spec.md``). Before this helper, four spec-walking
scripts (``check_vision_goals``, ``derive_docs``, ``followup_derive``,
``vision_matrix``) each globbed ``Plan/*/spec.md`` — a ONE-LEVEL pattern that
matched ZERO specs post-migration, silently turning their CI gates into no-ops.

``spec_files`` globs RECURSIVELY (``**/spec.md``) and excludes any path under an
underscore-prefixed directory (``Plan/_research/…``, ``Plan/_planning/…``) — those
are research/planning artefacts, not lifecycle specs. One source, so the next
layout change is a one-line edit here, not a four-script hunt.
"""
from __future__ import annotations

from pathlib import Path


def spec_files(root: "Path | str") -> "list[Path]":
    """Every lifecycle ``spec.md`` under ``root``, sorted, excluding
    underscore-prefixed (research/planning) directories."""
    root = Path(root)
    out = []
    for sp in root.glob("**/spec.md"):
        rel = sp.relative_to(root)
        if any(part.startswith("_") for part in rel.parts):
            continue
        out.append(sp)
    return sorted(out)
