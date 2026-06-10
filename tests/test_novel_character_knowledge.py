"""Spec 131 — character-knowledge ledger.

KnownFact node + KNOWS / LEARNED_IN edges + 3 verbs. Closes Spec 127's
`_pov_card` knowledge gap when a scene declares its POV character.
"""
from __future__ import annotations

import tempfile

import pytest

from agency.engine import Engine


def _fresh() -> Engine:
    return Engine(tempfile.mktemp(suffix=".db"))


def _iid(e: Engine) -> str:
    return e.intent.capture_and_confirm(
        "spec 131 knowledge", "facts known by character",
        "anachronism flagged", owner="user")


def _invoke(e: Engine, iid: str, verb: str, cap: str = "novel", **kw):
    r, _ = e.registry.invoke(e.memory, iid, cap, verb,
                              agent_id="agent:test", **kw)
    return r


# ---------------------------------------------------------------------------
# Ontology registration.
# ---------------------------------------------------------------------------


def test_known_fact_node_declared():
    e = _fresh()
    assert "KnownFact" in e.ontology.nodes


def test_knows_and_learned_in_edges_registered():
    e = _fresh()
    edges = e.ontology.edges
    assert "KNOWS" in edges
    assert "LEARNED_IN" in edges


def test_three_verbs_registered():
    e = _fresh()
    verbs = set(e.registry.get("novel").verbs)
    expected = {"record_character_learns", "what_does_X_know_as_of",
                 "flag_anachronistic_reference"}
    assert expected <= verbs


# ---------------------------------------------------------------------------
# Fixture: 3-scene mini-novel with a POV character.
# ---------------------------------------------------------------------------


@pytest.fixture
def mini_novel():
    e = _fresh()
    iid = _iid(e)
    # Character node — minimal record (Spec 123 Slice 2 will enrich).
    nv = _invoke(e, iid, "create_novel",
                 title="K Test", author="A. Author", genre="lit")
    # No Character node ontology yet — use a graph-level record as
    # placeholder. Reuse Novel id as character_id surrogate per the
    # Spec 123 link_character_to_world pattern.
    character_id = nv["novel_id"]
    chapters = []
    scenes = []
    for n in range(1, 4):
        ch = _invoke(e, iid, "create_chapter",
                     novel_id=nv["novel_id"], number=n,
                     title=f"Ch {n}")
        chapters.append(ch["chapter_id"])
        sc = _invoke(e, iid, "create_scene",
                     chapter_id=ch["chapter_id"], slug=f"s{n}",
                     pov="third-limited")
        scenes.append(sc["scene_id"])
    return e, iid, nv["novel_id"], character_id, chapters, scenes


# ---------------------------------------------------------------------------
# record_character_learns — mints KnownFact + KNOWS + LEARNED_IN.
# ---------------------------------------------------------------------------


def test_record_character_learns_returns_fact_id(mini_novel):
    e, iid, _, character_id, _, scenes = mini_novel
    r = _invoke(e, iid, "record_character_learns",
                character_id=character_id,
                fact="The captain is bribed.",
                scene_id=scenes[1])
    assert r["fact_id"]


def test_record_character_learns_emits_knows_and_learned_in(mini_novel):
    e, iid, _, character_id, _, scenes = mini_novel
    r = _invoke(e, iid, "record_character_learns",
                character_id=character_id,
                fact="A secret.",
                scene_id=scenes[1])
    # KNOWS edge: Character → KnownFact
    rows = e.memory.g.query(
        "MATCH (c)-[r:KNOWS]->(f:KnownFact) "
        "WHERE c.id = $cid AND f.id = $fid RETURN r",
        {"cid": character_id, "fid": r["fact_id"]})
    assert len(rows) == 1
    # LEARNED_IN edge: KnownFact → Scene
    rows = e.memory.g.query(
        "MATCH (f:KnownFact)-[r:LEARNED_IN]->(s:Scene) "
        "WHERE f.id = $fid AND s.id = $sid RETURN r",
        {"fid": r["fact_id"], "sid": scenes[1]})
    assert len(rows) == 1


def test_record_character_learns_rejects_unknown_scene(mini_novel):
    e, iid, _, character_id, _, _ = mini_novel
    r = _invoke(e, iid, "record_character_learns",
                character_id=character_id,
                fact="x",
                scene_id="scene:does-not-exist")
    assert r is None  # NOT_FOUND


# ---------------------------------------------------------------------------
# what_does_X_know_as_of — narrative-time slice via chapter.number.
# ---------------------------------------------------------------------------


def test_what_does_X_know_as_of_returns_facts_learned_before(mini_novel):
    e, iid, _, character_id, _, scenes = mini_novel
    s1, s2, s3 = scenes
    # Character learns in scene 1 and scene 2.
    _invoke(e, iid, "record_character_learns",
            character_id=character_id,
            fact="Fact A", scene_id=s1)
    _invoke(e, iid, "record_character_learns",
            character_id=character_id,
            fact="Fact B", scene_id=s2)
    # As-of scene 2: facts from s1 + s2.
    r = _invoke(e, iid, "what_does_X_know_as_of",
                 character_id=character_id, scene_id=s2)
    facts = [f["fact"] for f in r["facts"]]
    assert "Fact A" in facts
    assert "Fact B" in facts


def test_what_does_X_know_as_of_excludes_future_facts(mini_novel):
    e, iid, _, character_id, _, scenes = mini_novel
    s1, s2, s3 = scenes
    _invoke(e, iid, "record_character_learns",
            character_id=character_id,
            fact="Fact A", scene_id=s1)
    _invoke(e, iid, "record_character_learns",
            character_id=character_id,
            fact="Future Fact", scene_id=s3)
    # As-of scene 2: only A; the s3 fact hasn't been learned yet.
    r = _invoke(e, iid, "what_does_X_know_as_of",
                 character_id=character_id, scene_id=s2)
    facts = [f["fact"] for f in r["facts"]]
    assert "Fact A" in facts
    assert "Future Fact" not in facts


def test_what_does_X_know_as_of_empty_when_no_facts(mini_novel):
    e, iid, _, character_id, _, scenes = mini_novel
    r = _invoke(e, iid, "what_does_X_know_as_of",
                 character_id=character_id, scene_id=scenes[0])
    assert r["facts"] == []


# ---------------------------------------------------------------------------
# flag_anachronistic_reference — narrative-position check.
# ---------------------------------------------------------------------------


def test_flag_anachronism_passes_for_known_fact(mini_novel):
    e, iid, _, character_id, _, scenes = mini_novel
    s1, s2, _ = scenes
    _invoke(e, iid, "record_character_learns",
            character_id=character_id,
            fact="The captain is bribed.", scene_id=s1)
    # Referenced in scene 2 — character learned it in scene 1 → no anachronism.
    r = _invoke(e, iid, "flag_anachronistic_reference",
                 scene_id=s2, character_id=character_id,
                 fact_text="The captain is bribed.")
    assert r["anachronism"] is False


def test_flag_anachronism_fires_when_learned_after(mini_novel):
    e, iid, _, character_id, _, scenes = mini_novel
    s1, _, s3 = scenes
    _invoke(e, iid, "record_character_learns",
            character_id=character_id,
            fact="The captain is bribed.", scene_id=s3)
    # Referenced in scene 1 but only learned in scene 3 → anachronism.
    r = _invoke(e, iid, "flag_anachronistic_reference",
                 scene_id=s1, character_id=character_id,
                 fact_text="The captain is bribed.")
    assert r["anachronism"] is True
    assert "Ch 3" in r.get("expected_learned_in", "") or \
           "scene" in r.get("expected_learned_in", "").lower()


def test_flag_anachronism_returns_no_record_for_unknown_fact(mini_novel):
    """If the character has never learned the fact, the verb returns
    no_record=True — the author hasn't authored the disclosure yet."""
    e, iid, _, character_id, _, scenes = mini_novel
    r = _invoke(e, iid, "flag_anachronistic_reference",
                 scene_id=scenes[0], character_id=character_id,
                 fact_text="Never recorded.")
    assert r["anachronism"] is False
    assert r.get("no_record") is True


# ---------------------------------------------------------------------------
# Spec 127 _compose_pov_card upgrade — when scene has pov_character_id.
# ---------------------------------------------------------------------------


def test_compose_pov_card_lists_knowledge_for_pov_character(mini_novel):
    e, iid, nid, character_id, _, scenes = mini_novel
    s1, s2, _ = scenes
    # Stamp scene 2 with a POV character (Scene gets an optional
    # pov_character_id property the upgrade reads).
    e.memory.update(s2, {"pov_character_id": character_id})
    _invoke(e, iid, "record_character_learns",
            character_id=character_id,
            fact="The captain is bribed.", scene_id=s1)
    r = _invoke(e, iid, "assemble_scene_brief", cap="prompt",
                 scene_id=s2, max_tokens=10000, section_budget=3000)
    pov_card = r["sections"]["pov_card"]
    assert "captain is bribed" in pov_card or "POV knows" in pov_card
