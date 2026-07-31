"""Spec 142 — novel-craft walkable skills (per-cluster authoring).

Six walks turn the scattered 136–141 verbs into ordered, gated operations:
each registers on novel.ontology.skills, pauses at its hard gate via
develop.skill_walk, and previews via the new dry_run flag (no side effects).
"""
from __future__ import annotations

import tempfile

from agency.engine import Engine

_SIX = {"dual-storyform-author": ("verify-inversion", 5),
        "canon-lock-author": ("audit-review", 4),
        "alter-roster-builder": ("discipline-verify", 6),
        "reveal-rule-author": ("gate-verify", 4),
        "r-rule-author": ("gate-attach", 5),
        "chapter-briefing-author": ("checklist-run", 5)}


def _fresh() -> Engine:
    return Engine(tempfile.mktemp(suffix=".db"))


def _iid(e: Engine) -> str:
    iid = e.intent.capture("spec 142", "skill walks", "verified")
    e.intent.confirm(iid)
    return iid


def _walk(e, iid, **kw):
    r, _ = e.registry.invoke(e.memory, iid, "develop", "skill_walk", **kw)
    return r


def test_six_skills_registered_with_gates() -> None:
    e = _fresh()
    skills = e.registry.get("novel").ontology.skills
    for name, (gate_phase, n_phases) in _SIX.items():
        assert name in skills, f"{name} not registered"
        phases = skills[name]["phases"]
        assert len(phases) == n_phases, (name, len(phases))
        gates = [p["name"] for p in phases if p.get("gate") == "hard"]
        assert gates == [gate_phase], (name, gates)
        # indexes are contiguous and ordered
        assert [p["index"] for p in phases] == list(range(1, n_phases + 1))
    e.memory.close()


def test_dry_run_previews_without_side_effects() -> None:
    e = _fresh()
    iid = _iid(e)
    nodes_before = len(e.memory.find("StoryformSet"))
    out = _walk(e, iid, name="dual-storyform-author", inputs={},
                dry_run=True)
    assert out["status"] == "dry-run"
    by_phase = {p["phase"]: p for p in out["phases"]}
    assert "novel.check_klein_c_inversion" in \
        by_phase["verify-inversion"]["would_invoke"]
    assert by_phase["verify-inversion"]["gate"] == "hard"
    # nothing touched the graph
    assert len(e.memory.find("StoryformSet")) == nodes_before


def test_walk_pauses_at_hard_gate() -> None:
    e = _fresh()
    iid = _iid(e)
    out = _walk(e, iid, name="dual-storyform-author",
                inputs={"set_defined": "set:x", "primary_added": "sf:a",
                        "secondary_added": "sf:b"})
    assert out["status"] == "input-required"
    assert out["phase"] == "verify-inversion"
    assert "inversion_verified" in out["resume_with"]
    # resume past the gate completes the remaining phase
    done = _walk(e, iid, name="dual-storyform-author",
                 inputs={"inversion_verified": "true",
                         "opening_routed": "ch1-3"},
                 resume_from=out["skill_id"])
    assert done["status"] == "completed"


def test_unknown_skill_still_fails_typed() -> None:
    e = _fresh()
    iid = _iid(e)
    out = _walk(e, iid, name="nope", inputs={})
    assert out["status"] == "failed"
    assert "dual-storyform-author" in out["available"]
