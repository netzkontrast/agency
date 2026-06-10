"""Spec 123 Slice 1 — World sub-graph (ontology + 9 verbs).

Worldbuilding nodes: World / Culture / Religion / Language / MagicSystem /
WorldAxiom; edges: PART_OF_WORLD, CONTRADICTS, BELONGS_TO / INHABITS /
WORSHIPS / SPEAKS / WIELDS.

Slice 2 (deferred): Character psychology + Conflict/Theme + foreshadowing.
"""
from __future__ import annotations

import tempfile

import pytest

from agency.engine import Engine


def _fresh() -> Engine:
    return Engine(tempfile.mktemp(suffix=".db"))


def _iid(e: Engine) -> str:
    return e.intent.capture_and_confirm(
        "spec 123 world", "world graph", "axioms + contradictions",
        owner="user")


def _invoke(e: Engine, iid: str, verb: str, **kw):
    r, _ = e.registry.invoke(e.memory, iid, "novel", verb,
                              agent_id="agent:test", **kw)
    return r


# ---------------------------------------------------------------------------
# Ontology registration.
# ---------------------------------------------------------------------------


def test_world_nodes_declared():
    e = _fresh()
    nodes = e.ontology.nodes
    for n in ("World", "Culture", "Religion", "Language",
               "MagicSystem", "WorldAxiom"):
        assert n in nodes, f"{n} missing from novel ontology"


def test_world_axiom_severity_enum():
    e = _fresh()
    assert e.ontology.enums[("WorldAxiom", "severity")] == {"hard", "soft"}


def test_part_of_world_edge_registered():
    e = _fresh()
    assert "PART_OF_WORLD" in e.ontology.edges


def test_world_verbs_registered():
    e = _fresh()
    verbs = set(e.registry.get("novel").verbs)
    expected = {"create_world", "create_culture", "create_religion",
                 "create_language", "create_magic_system",
                 "create_world_axiom", "list_world",
                 "find_axiom_contradictions", "link_character_to_world"}
    assert expected <= verbs


# ---------------------------------------------------------------------------
# create_world + create_culture / religion / language / magic_system.
# ---------------------------------------------------------------------------


def test_create_world_records_node():
    e = _fresh()
    iid = _iid(e)
    r = _invoke(e, iid, "create_world", slug="midgard", name="Midgard")
    assert r["world_id"]
    assert r["slug"] == "midgard"
    assert r["name"] == "Midgard"


def test_create_world_children_link_via_part_of_world():
    e = _fresh()
    iid = _iid(e)
    w = _invoke(e, iid, "create_world", slug="midgard", name="Midgard")
    c = _invoke(e, iid, "create_culture",
                world_id=w["world_id"], slug="vikings", name="Vikings")
    rel = _invoke(e, iid, "create_religion",
                   world_id=w["world_id"], slug="asatru", name="Ásatrú")
    lang = _invoke(e, iid, "create_language",
                    world_id=w["world_id"], slug="old-norse",
                    name="Old Norse")
    mag = _invoke(e, iid, "create_magic_system",
                   world_id=w["world_id"], slug="seidr", name="Seiðr")
    # Each child has the right return key.
    assert c["culture_id"]
    assert rel["religion_id"]
    assert lang["language_id"]
    assert mag["magic_system_id"]
    # The PART_OF_WORLD edge lands.
    rows = e.memory.g.query(
        "MATCH (x)-[r:PART_OF_WORLD]->(w:World) "
        "WHERE w.id = $wid RETURN x",
        {"wid": w["world_id"]})
    assert len(rows) == 4


def test_create_culture_rejects_unknown_world():
    e = _fresh()
    iid = _iid(e)
    r = _invoke(e, iid, "create_culture",
                world_id="world:does-not-exist",
                slug="x", name="X")
    assert r is None   # NOT_FOUND typed failure unwraps to None


# ---------------------------------------------------------------------------
# create_world_axiom — severity enum + PART_OF_WORLD.
# ---------------------------------------------------------------------------


def test_create_world_axiom_records_with_severity():
    e = _fresh()
    iid = _iid(e)
    w = _invoke(e, iid, "create_world", slug="midgard", name="Midgard")
    r = _invoke(e, iid, "create_world_axiom",
                world_id=w["world_id"],
                text="The dead never return.", severity="hard")
    assert r["axiom_id"]
    assert r["severity"] == "hard"


def test_create_world_axiom_rejects_unknown_severity():
    e = _fresh()
    iid = _iid(e)
    w = _invoke(e, iid, "create_world", slug="midgard", name="Midgard")
    r = _invoke(e, iid, "create_world_axiom",
                world_id=w["world_id"],
                text="x", severity="medium")
    assert r is None


# ---------------------------------------------------------------------------
# list_world — tree of children grouped by label.
# ---------------------------------------------------------------------------


def test_list_world_groups_children_by_label():
    e = _fresh()
    iid = _iid(e)
    w = _invoke(e, iid, "create_world", slug="midgard", name="Midgard")
    _invoke(e, iid, "create_culture",
            world_id=w["world_id"], slug="vikings", name="Vikings")
    _invoke(e, iid, "create_culture",
            world_id=w["world_id"], slug="saxons", name="Saxons")
    _invoke(e, iid, "create_religion",
            world_id=w["world_id"], slug="asatru", name="Ásatrú")
    _invoke(e, iid, "create_world_axiom",
            world_id=w["world_id"], text="The Allfather watches all.",
            severity="hard")
    r = _invoke(e, iid, "list_world", world_id=w["world_id"])
    assert len(r["cultures"]) == 2
    assert len(r["religions"]) == 1
    assert len(r["axioms"]) == 1
    assert r["world"]["name"] == "Midgard"


# ---------------------------------------------------------------------------
# find_axiom_contradictions — decidable scan.
# ---------------------------------------------------------------------------


def test_find_axiom_contradictions_flags_negation_pair():
    e = _fresh()
    iid = _iid(e)
    w = _invoke(e, iid, "create_world", slug="midgard", name="Midgard")
    a1 = _invoke(e, iid, "create_world_axiom",
                  world_id=w["world_id"],
                  text="The dead can return through ritual.",
                  severity="hard")
    a2 = _invoke(e, iid, "create_world_axiom",
                  world_id=w["world_id"],
                  text="The dead can not return through ritual.",
                  severity="hard")
    r = _invoke(e, iid, "find_axiom_contradictions",
                 world_id=w["world_id"])
    assert r["passed"] is False
    ids = {(c["a_id"], c["b_id"]) for c in r["contradictions"]}
    assert (a1["axiom_id"], a2["axiom_id"]) in ids


def test_find_axiom_contradictions_passes_on_independent_rules():
    e = _fresh()
    iid = _iid(e)
    w = _invoke(e, iid, "create_world", slug="midgard", name="Midgard")
    _invoke(e, iid, "create_world_axiom",
            world_id=w["world_id"],
            text="Gravity pulls down always.", severity="hard")
    _invoke(e, iid, "create_world_axiom",
            world_id=w["world_id"],
            text="Magic costs blood to wield.", severity="hard")
    r = _invoke(e, iid, "find_axiom_contradictions",
                 world_id=w["world_id"])
    assert r["passed"] is True
    assert r["contradictions"] == []


# ---------------------------------------------------------------------------
# link_character_to_world — edge-kind whitelist.
# ---------------------------------------------------------------------------


def test_link_character_to_world_rejects_unknown_edge():
    e = _fresh()
    iid = _iid(e)
    w = _invoke(e, iid, "create_world", slug="midgard", name="Midgard")
    rel = _invoke(e, iid, "create_religion",
                   world_id=w["world_id"], slug="asatru", name="Ásatrú")
    # Use a Novel node as the placeholder character (Character ontology
    # lands in Slice 2).
    nv = _invoke(e, iid, "create_novel",
                  title="Saga", author="A", genre="lit")
    r = _invoke(e, iid, "link_character_to_world",
                 character_id=nv["novel_id"],
                 target_id=rel["religion_id"],
                 edge_kind="SHOPS_AT")
    assert r is None  # INVALID_ARGUMENT


def test_link_character_to_world_records_edge():
    e = _fresh()
    iid = _iid(e)
    w = _invoke(e, iid, "create_world", slug="midgard", name="Midgard")
    rel = _invoke(e, iid, "create_religion",
                   world_id=w["world_id"], slug="asatru", name="Ásatrú")
    nv = _invoke(e, iid, "create_novel",
                  title="Saga", author="A", genre="lit")
    r = _invoke(e, iid, "link_character_to_world",
                 character_id=nv["novel_id"],
                 target_id=rel["religion_id"],
                 edge_kind="WORSHIPS")
    assert r["edge_kind"] == "WORSHIPS"
    rows = e.memory.g.query(
        "MATCH (c)-[r:WORSHIPS]->(rel:Religion) "
        "WHERE c.id = $cid AND rel.id = $rid RETURN r",
        {"cid": nv["novel_id"], "rid": rel["religion_id"]})
    assert rows
