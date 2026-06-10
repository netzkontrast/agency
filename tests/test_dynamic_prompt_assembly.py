"""Spec 127 — `prompt.assemble_scene_brief`.

Walks Scene → Chapter → Novel → Storyform; composes a bounded prompt
from 7 sections (storyform / pov_card / scene_cast / world_rules /
continuity / foreshadowing / voice_constraints) with full per-source
provenance. Pure transform; no driver, no LLM, no filesystem.
"""
from __future__ import annotations

import json
import tempfile

import pytest

from agency.engine import Engine


@pytest.fixture
def engine():
    return Engine(tempfile.mktemp(suffix=".db"))


@pytest.fixture
def iid(engine):
    return engine.intent.capture_and_confirm(
        "spec 127 assembly",
        "scene brief composed",
        "all sections present",
        owner="user")


def _call(engine, iid, cap, verb, **kw):
    r, _ = engine.registry.invoke(
        engine.memory, iid, cap, verb,
        agent_id="agent:test", **kw)
    return r


@pytest.fixture
def scene_id(engine, iid):
    """Mint Novel → Chapter → Scene to give the brief something to walk."""
    nv = _call(engine, iid, "novel", "create_novel",
               title="Test Novel", author="A. Author", genre="literary")
    ch = _call(engine, iid, "novel", "create_chapter",
               novel_id=nv["novel_id"], number=3, title="The Crossing")
    sc = _call(engine, iid, "novel", "create_scene",
               chapter_id=ch["chapter_id"], slug="bridge", pov="third-limited")
    return sc["scene_id"]


@pytest.fixture
def scene_id_with_storyform(engine, iid, scene_id):
    """Same setup as scene_id but ALSO records a Storyform with NCP body."""
    # Walk back to the novel.
    scene = engine.memory.recall(scene_id)
    chapter = engine.memory.recall(scene["chapter"])
    novel_id = chapter["novel"]
    # Mint a Storyform node carrying a good-fixture-shaped NCP body.
    ncp = {
        "storyform": {
            "crucial_element_id": "el.self-interest",
            "throughlines": {
                "mc": {
                    "class_id": "class.universe",
                    "concern_id": "t.past",
                    "problem_id": "el.self-interest",
                    "solution_id": "el.morality",
                    "signposts": ["t.past", "t.progress", "t.future", "t.present"],
                },
            },
        },
    }
    sf_id = engine.memory.record("Storyform", {
        "novel": novel_id, "body": json.dumps(ncp),
    })
    engine.memory.link(sf_id, novel_id, "SERVES")
    return scene_id


# ---------------------------------------------------------------------------
# Verb registration + smoke.
# ---------------------------------------------------------------------------


def test_verb_registered(engine):
    verbs = set(engine.registry.get("prompt").verbs)
    assert "assemble_scene_brief" in verbs


def test_assemble_returns_brief_shape(engine, iid, scene_id):
    r = _call(engine, iid, "prompt", "assemble_scene_brief",
              scene_id=scene_id)
    assert "prompt" in r
    assert "sections" in r
    assert "token_count" in r
    assert "sources" in r
    assert "brief_id" in r
    assert r["token_count"] > 0


def test_assemble_unknown_scene_returns_error(engine, iid):
    r = _call(engine, iid, "prompt", "assemble_scene_brief",
              scene_id="scene:does-not-exist")
    assert r.get("error") == "NOT_FOUND"


# ---------------------------------------------------------------------------
# Section coverage — every section that the spec lists is present.
# ---------------------------------------------------------------------------


def test_all_seven_sections_present(engine, iid, scene_id):
    r = _call(engine, iid, "prompt", "assemble_scene_brief",
              scene_id=scene_id, max_tokens=10000, section_budget=2000)
    expected = {"storyform", "pov_card", "scene_cast", "world_rules",
                "continuity", "foreshadowing", "voice_constraints"}
    assert expected <= set(r["sections"].keys())


def test_pov_card_carries_scene_pov(engine, iid, scene_id):
    r = _call(engine, iid, "prompt", "assemble_scene_brief",
              scene_id=scene_id)
    assert "third-limited" in r["sections"]["pov_card"]


def test_voice_constraint_matches_pov(engine, iid, scene_id):
    r = _call(engine, iid, "prompt", "assemble_scene_brief",
              scene_id=scene_id)
    assert "third-limited" in r["sections"]["voice_constraints"].lower()


def test_continuity_anchors_to_chapter_number(engine, iid, scene_id):
    r = _call(engine, iid, "prompt", "assemble_scene_brief",
              scene_id=scene_id)
    assert "chapter 3" in r["sections"]["continuity"]


def test_unimplemented_sections_flag_their_dependency(engine, iid, scene_id):
    """world_rules / foreshadowing must explicitly name their future spec
    so a reader knows it's a placeholder, not a silent gap."""
    r = _call(engine, iid, "prompt", "assemble_scene_brief",
              scene_id=scene_id)
    assert "Spec" in r["sections"]["world_rules"]
    assert "Spec" in r["sections"]["foreshadowing"]


# ---------------------------------------------------------------------------
# Storyform composition — when a Storyform body is on the graph,
# storyform section pulls Dramatica fragments.
# ---------------------------------------------------------------------------


def test_storyform_section_pulls_fragments(engine, iid, scene_id_with_storyform):
    r = _call(engine, iid, "prompt", "assemble_scene_brief",
              scene_id=scene_id_with_storyform,
              max_tokens=10000, section_budget=3000)
    body = r["sections"]["storyform"]
    # The good-fixture-shaped NCP routes to throughline.main + class.universe
    # + type.past + var.self-interest + var.morality, all of which have
    # bootstrap fragments per Spec 129.
    assert "throughline.main" in body
    assert "class.universe" in body
    assert "type.past" in body


def test_storyform_section_has_sources(engine, iid, scene_id_with_storyform):
    r = _call(engine, iid, "prompt", "assemble_scene_brief",
              scene_id=scene_id_with_storyform,
              max_tokens=10000, section_budget=3000)
    storyform_sources = [s for s in r["sources"]
                         if s["contributed"] == "storyform"]
    assert len(storyform_sources) >= 3
    node_ids = {s["node_id"] for s in storyform_sources}
    assert "throughline.main" in node_ids


def test_no_storyform_falls_back_gracefully(engine, iid, scene_id):
    """When the novel has no Storyform body, the storyform section flags
    it instead of failing."""
    r = _call(engine, iid, "prompt", "assemble_scene_brief",
              scene_id=scene_id)
    assert r["sections"]["storyform"]   # non-empty placeholder


# ---------------------------------------------------------------------------
# Budgeting — section + total caps work.
# ---------------------------------------------------------------------------


def test_section_budget_truncates_long_sections(engine, iid,
                                                 scene_id_with_storyform):
    r = _call(engine, iid, "prompt", "assemble_scene_brief",
              scene_id=scene_id_with_storyform,
              max_tokens=10000, section_budget=20)
    assert "storyform" in r["truncated"]
    assert "..." in r["sections"]["storyform"]


def test_total_budget_drops_lowest_priority(engine, iid, scene_id):
    """When max_tokens binds, lowest-priority sections drop; storyform
    (highest priority) is preserved. With the placeholder-only sections
    summing to ~127 tok on a fresh scene, a tight cap (110) forces the
    tail to drop while the head fits."""
    r = _call(engine, iid, "prompt", "assemble_scene_brief",
              scene_id=scene_id, max_tokens=110, section_budget=80)
    assert "storyform" in r["sections"]  # highest priority kept
    assert r["truncated"], "expected tail-section drops at max_tokens=110"


# ---------------------------------------------------------------------------
# Provenance — Artefact + SERVES edge recorded.
# ---------------------------------------------------------------------------


def test_brief_artefact_recorded(engine, iid, scene_id):
    r = _call(engine, iid, "prompt", "assemble_scene_brief",
              scene_id=scene_id)
    aid = r["brief_id"]
    node = engine.memory.g.get_node(aid)
    assert node is not None
    props = node["properties"]
    assert props["kind"] == "scene-brief"
    assert props["scene_id"] == scene_id


def test_brief_serves_intent(engine, iid, scene_id):
    r = _call(engine, iid, "prompt", "assemble_scene_brief",
              scene_id=scene_id)
    rows = engine.memory.g.query(
        "MATCH (a:Artefact)-[:SERVES]->(i:Intent) "
        "WHERE a.id = $aid AND i.id = $iid RETURN a",
        {"aid": r["brief_id"], "iid": iid})
    assert len(rows) == 1


# ---------------------------------------------------------------------------
# Rendered prompt — structured markdown shape.
# ---------------------------------------------------------------------------


def test_rendered_prompt_is_markdown_with_sections(engine, iid, scene_id):
    r = _call(engine, iid, "prompt", "assemble_scene_brief",
              scene_id=scene_id)
    prompt = r["prompt"]
    assert prompt.startswith("# Scene brief")
    assert "## Storyform position" in prompt
    assert "## POV card" in prompt
    assert "## Voice + craft constraints" in prompt
