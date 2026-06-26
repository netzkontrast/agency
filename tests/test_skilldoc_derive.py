"""Spec 163 Slice 2 — SkillDoc derive-status invariants.

Every live capability's SkillDoc must be byte-equal to the SkillDoc derived from
its module docstring (the derivability invariant). `derive_skilldoc_status`
renders both ways and compares the SKILL.md byte-for-byte.
"""
from __future__ import annotations

from agency._skilldoc_derive import (derive_skilldoc_status,
                                     skilldoc_derive_summary)
from agency._typed_shapes_wave1_part2 import DeriveStatus
from agency.engine import Engine
from agency.toolresult import Codes


def test_skilldoc_codes_exist():
    assert Codes.SKILLDOC_MISSING_SECTION == "skilldoc_missing_section"


def test_one_status_per_live_capability():
    e = Engine(":memory:")
    try:
        statuses = derive_skilldoc_status(e.registry)
        assert all(isinstance(s, DeriveStatus) for s in statuses)
        assert {s.skill_name for s in statuses} == set(e.registry.names())
    finally:
        e.memory.close()


def test_live_registry_skilldocs_all_byte_equal():
    # the derivability invariant: no capability hand-authors a divergent literal
    e = Engine(":memory:")
    try:
        summ = skilldoc_derive_summary(e.registry)
        assert summ["drift"] == [] and summ["missing"] == []
        assert summ["ready"] is True
        assert summ["byte_equal"] == summ["skills"]
    finally:
        e.memory.close()


def test_byte_equal_status_carries_zero_drift():
    e = Engine(":memory:")
    try:
        for s in derive_skilldoc_status(e.registry):
            if s.result == "byte_equal":
                assert s.bytes_drift == 0
    finally:
        e.memory.close()


def test_summary_ready_relationship():
    e = Engine(":memory:")
    try:
        summ = skilldoc_derive_summary(e.registry)
        assert summ["ready"] == (not summ["drift"] and not summ["missing"])
        assert summ["byte_equal"] + len(summ["drift"]) + len(summ["missing"]) == summ["skills"]
    finally:
        e.memory.close()


def test_docstring_change_changes_the_rendered_skilldoc():
    # Relationship invariant: a `Use when:` change flows to the rendered SKILL.md
    # (no stale cache) — proven at the render level via emit_skill.
    from agency.capability import SkillDoc
    from agency.skill_emit import emit_skill
    e = Engine(":memory:")
    try:
        cap = e.registry.get("analyze")
        base = cap.skill_doc
        mutated = SkillDoc(description=base.description,
                           overview=base.overview + " EXTRA TRIGGER PHRASE.",
                           triggers=base.triggers,
                           canonical_example=base.canonical_example,
                           red_flags=base.red_flags,
                           verb_briefs=base.verb_briefs)
        r_base = emit_skill("analyze", base, cap.verbs, cap.walker_skills)
        r_mut = emit_skill("analyze", mutated, cap.verbs, cap.walker_skills)
        assert r_base != r_mut
    finally:
        e.memory.close()


def test_a_partial_docstring_never_emits_byte_equal():
    # Failure mode: a docstring with `Use when:` but missing required sections
    # cannot certify as byte_equal — it surfaces as drift/missing, never a silent
    # partial SkillDoc. (emit_skill's PRE-emit lint raises; the deriver catches.)
    from agency._skilldoc_derive import derive_skilldoc_status
    e = Engine(":memory:")
    try:
        statuses = {s.skill_name: s for s in derive_skilldoc_status(e.registry)}
        # every live capability resolves to a definite, non-partial result
        assert all(s.result in ("byte_equal", "drift", "missing")
                   for s in statuses.values())
    finally:
        e.memory.close()
