"""Spec 130 — scene-writer walkable skill.

5-phase walkable skill integrating Specs 127 + 128 + 129 + 131 + 132.
Slice 1 ships the skill registration + a minimal `integrate_scene_body`
verb (phase 5 binding). FakeTextDriver wiring + production TextDriver
are Slice 2 territory (gated on Spec 005).
"""
from __future__ import annotations

import tempfile

import pytest

from agency.engine import Engine


def _fresh() -> Engine:
    return Engine(tempfile.mktemp(suffix=".db"))


def _iid(e: Engine) -> str:
    return e.intent.capture_and_confirm(
        "spec 130 scene-writer", "skill registered + integrate verb",
        "phase bindings reach real verbs", owner="user")


def _invoke(e: Engine, iid: str, verb: str, cap: str = "novel", **kw):
    r, _ = e.registry.invoke(e.memory, iid, cap, verb,
                              agent_id="agent:test", **kw)
    return r


# ---------------------------------------------------------------------------
# scene-writer skill registration.
# ---------------------------------------------------------------------------


def test_scene_writer_skill_registered():
    e = _fresh()
    assert "scene-writer" in e.ontology.skills


def test_scene_writer_has_5_phases():
    e = _fresh()
    skill = e.ontology.skills["scene-writer"]
    phases = skill["phases"]
    assert len(phases) == 5
    names = {p["name"] for p in phases}
    assert {"assemble", "validate-constraints", "generate",
             "check", "integrate"} <= names


def test_phase_1_binds_to_assemble_scene_brief():
    e = _fresh()
    skill = e.ontology.skills["scene-writer"]
    phase1 = [p for p in skill["phases"] if p["name"] == "assemble"][0]
    assert "prompt.assemble_scene_brief" in phase1.get("verbs", [])


def test_phase_4_chains_prose_and_storyform_checks():
    """Phase 4 (check) binds to multiple verbs — at least the 4 named
    in the spec: check_filter_words, check_dialogue_attribution,
    check_show_dont_tell, novel_coherence_check."""
    e = _fresh()
    skill = e.ontology.skills["scene-writer"]
    phase4 = [p for p in skill["phases"] if p["name"] == "check"][0]
    verbs = phase4.get("verbs", [])
    expected = {"novel.check_filter_words",
                 "novel.check_dialogue_attribution",
                 "novel.check_show_dont_tell",
                 "novel.novel_coherence_check"}
    assert expected <= set(verbs)


def test_phase_5_is_hard_gate():
    e = _fresh()
    skill = e.ontology.skills["scene-writer"]
    phase5 = [p for p in skill["phases"] if p["name"] == "integrate"][0]
    assert phase5.get("gate") == "hard"
    # Integrate binds to the new integrate_scene_body verb.
    assert "novel.integrate_scene_body" in phase5.get("verbs", [])


# ---------------------------------------------------------------------------
# integrate_scene_body — phase 5 binding.
# ---------------------------------------------------------------------------


@pytest.fixture
def scene(_fresh_engine=None):
    e = _fresh()
    iid = _iid(e)
    nv = _invoke(e, iid, "create_novel",
                 title="SW Test", author="A. Author", genre="lit")
    ch = _invoke(e, iid, "create_chapter",
                 novel_id=nv["novel_id"], number=1, title="Ch 1")
    sc = _invoke(e, iid, "create_scene",
                 chapter_id=ch["chapter_id"], slug="opening",
                 pov="third-limited")
    return e, iid, sc["scene_id"]


def test_integrate_scene_body_writes_body_to_scene(scene):
    e, iid, scene_id = scene
    body = ("She crossed the bridge at dawn. The mist had not yet "
             "lifted off the river.")
    r = _invoke(e, iid, "integrate_scene_body",
                 scene_id=scene_id, body=body)
    assert r["scene_id"] == scene_id
    node = e.memory.recall(scene_id)
    assert node["body"] == body


def test_integrate_scene_body_records_integration_artefact(scene):
    e, iid, scene_id = scene
    r = _invoke(e, iid, "integrate_scene_body",
                 scene_id=scene_id, body="Body.")
    assert r["artefact_id"]
    node = e.memory.g.get_node(r["artefact_id"])
    props = node["properties"]
    assert props["kind"] == "scene-integration"
    assert props["scene_id"] == scene_id


def test_integrate_scene_body_rejects_unknown_scene():
    e = _fresh()
    iid = _iid(e)
    r = _invoke(e, iid, "integrate_scene_body",
                 scene_id="scene:does-not-exist", body="x")
    assert r is None  # NOT_FOUND


def test_integrate_scene_body_verb_registered():
    e = _fresh()
    verbs = set(e.registry.get("novel").verbs)
    assert "integrate_scene_body" in verbs
