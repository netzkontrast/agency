"""Spec 163 Slice 2 — derive-status of every live capability's SkillDoc.

Slice 1 shipped the typed `DeriveStatus` shape but nothing populated it
(dormant). This is the deriver: for every capability it renders the SkillDoc
TWO ways — once from the live `skill_doc` the capability presents, once from the
SkillDoc DERIVED from its module docstring (`Use when:` / `Triggers:` /
`Red flags:`) — and compares the rendered SKILL.md **byte-for-byte**.

The invariant (CLAUDE.md rule 2 + the "derivability audit" field-test): a
capability must NOT hand-author a literal SkillDoc that diverges from what its
docstring would derive — the docstring is the single source. `byte_equal` =
derivable (the healthy state); `drift` = a literal diverged; `missing` = no
`Use when:` marker to derive from.

Composes the existing `SkillDoc.from_module` + `emit_skill` (rule 2) — no second
render path, so the derive-status and the committed SKILL.md cannot disagree.
"""
from __future__ import annotations

import importlib

from ._typed_shapes_wave1_part2 import DeriveStatus


def _module_of(cap):
    mod = cap.module
    if isinstance(mod, str):
        mod = importlib.import_module(mod)
    return mod


def derive_skilldoc_status(registry) -> "tuple[DeriveStatus, ...]":
    """One :class:`DeriveStatus` per live capability, comparing the rendered
    SKILL.md from the live `skill_doc` against the one derived from the module
    docstring. `bytes_drift` is the byte-length delta of the two renders when they
    differ (0 when byte-equal)."""
    from .capability import SkillDoc
    from .skill_emit import emit_skill

    out = []
    for name in sorted(registry.names()):
        cap = registry.get(name)
        derived = SkillDoc.from_module(_module_of(cap), name, list(cap.verbs))
        if derived is None:
            out.append(DeriveStatus(skill_name=name, result="missing"))
            continue
        try:
            ren_derived = emit_skill(name, derived, cap.verbs, cap.walker_skills)
            ren_actual = emit_skill(name, cap.skill_doc, cap.verbs, cap.walker_skills)
        except ValueError:
            # a lint failure on either render means we can't certify byte-equality
            out.append(DeriveStatus(skill_name=name, result="missing"))
            continue
        if ren_derived == ren_actual:
            out.append(DeriveStatus(skill_name=name, result="byte_equal"))
        else:
            drift = abs(len(str(ren_derived)) - len(str(ren_actual)))
            out.append(DeriveStatus(skill_name=name, result="drift",
                                    bytes_drift=drift))
    return tuple(out)


def skilldoc_derive_summary(registry) -> dict:
    """A doctor-friendly roll-up of :func:`derive_skilldoc_status`. `ready` iff
    every capability's SkillDoc is `byte_equal` to its derived render (zero drift,
    zero missing — the derivability invariant holds across the live registry)."""
    statuses = derive_skilldoc_status(registry)
    byte_equal = [s.skill_name for s in statuses if s.result == "byte_equal"]
    drift = [s.skill_name for s in statuses if s.result == "drift"]
    missing = [s.skill_name for s in statuses if s.result == "missing"]
    return {"skills": len(statuses),
            "byte_equal": len(byte_equal),
            "drift": drift,
            "missing": missing,
            "ready": not drift and not missing}
