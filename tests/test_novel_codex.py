"""Spec 132 — codex-entity-tracking (Novelcrafter-parity).

CodexEntry node + CODEX_OF edge + 5 verbs (create / list / match /
update / archive). Closes Spec 127's `_world_rules` placeholder —
`assemble_scene_brief`'s composer scans the chapter/scene text against
registered triggers and injects matched bodies.
"""
from __future__ import annotations

import tempfile

import pytest

from agency.engine import Engine


def _fresh() -> Engine:
    return Engine(tempfile.mktemp(suffix=".db"))


def _iid(e: Engine) -> str:
    return e.intent.capture_and_confirm(
        "spec 132 codex", "codex entries + matching",
        "world_rules composer reads it", owner="user")


def _invoke(e: Engine, iid: str, verb: str, cap: str = "novel", **kw):
    r, _ = e.registry.invoke(e.memory, iid, cap, verb,
                              agent_id="agent:test", **kw)
    return r


# ---------------------------------------------------------------------------
# Ontology registration.
# ---------------------------------------------------------------------------


def test_codex_entry_node_declared():
    e = _fresh()
    assert "CodexEntry" in e.ontology.nodes


def test_codex_kind_enum_present():
    e = _fresh()
    enums = e.ontology.enums
    assert ("CodexEntry", "kind") in enums
    assert {"location", "minor-character", "artefact", "concept",
             "faction"} <= enums[("CodexEntry", "kind")]


def test_codex_of_edge_registered():
    e = _fresh()
    assert "CODEX_OF" in e.ontology.edges


def test_codex_verbs_registered():
    e = _fresh()
    verbs = set(e.registry.get("novel").verbs)
    expected = {"create_codex_entry", "list_codex_entries",
                 "match_codex_entries", "update_codex_entry",
                 "archive_codex_entry"}
    assert expected <= verbs


# ---------------------------------------------------------------------------
# create_codex_entry + CODEX_OF.
# ---------------------------------------------------------------------------


@pytest.fixture
def novel(_fresh_engine=None):
    e = _fresh()
    iid = _iid(e)
    nv = _invoke(e, iid, "create_novel",
                 title="Codex Test", author="A. Author", genre="lit")
    return e, iid, nv["novel_id"]


def test_create_codex_entry_records_node(novel):
    e, iid, nid = novel
    r = _invoke(e, iid, "create_codex_entry",
                novel_id=nid, slug="iron-mask",
                name="The Iron Mask", kind="artefact",
                body="A black-iron half-mask forged in the Third Age.",
                triggers="Iron Mask, the mask")
    assert r["entry_id"]
    assert r["kind"] == "artefact"


def test_create_codex_entry_links_to_novel(novel):
    e, iid, nid = novel
    r = _invoke(e, iid, "create_codex_entry",
                novel_id=nid, slug="x", name="X",
                kind="concept", body="A concept.")
    rows = e.memory.g.query(
        "MATCH (c:CodexEntry)-[r:CODEX_OF]->(n:Novel) "
        "WHERE c.id = $cid AND n.id = $nid RETURN r",
        {"cid": r["entry_id"], "nid": nid})
    assert len(rows) == 1


def test_create_codex_entry_rejects_unknown_kind(novel):
    e, iid, nid = novel
    r = _invoke(e, iid, "create_codex_entry",
                novel_id=nid, slug="x", name="X",
                kind="hyperbole", body="x")
    assert r is None  # INVALID_ARGUMENT


def test_triggers_default_to_name_and_slug(novel):
    """When triggers is empty, the verb auto-fills with [name, slug]."""
    e, iid, nid = novel
    r = _invoke(e, iid, "create_codex_entry",
                novel_id=nid, slug="raven", name="Raven",
                kind="minor-character", body="A trickster.")
    node = e.memory.g.get_node(r["entry_id"])
    tprop = node["properties"].get("triggers", "")
    assert "raven" in tprop.lower()
    assert "Raven" in tprop


# ---------------------------------------------------------------------------
# list_codex_entries.
# ---------------------------------------------------------------------------


def test_list_codex_entries_all(novel):
    e, iid, nid = novel
    _invoke(e, iid, "create_codex_entry",
            novel_id=nid, slug="a", name="A", kind="location",
            body="x", triggers="a")
    _invoke(e, iid, "create_codex_entry",
            novel_id=nid, slug="b", name="B", kind="artefact",
            body="x", triggers="b")
    r = _invoke(e, iid, "list_codex_entries", novel_id=nid)
    slugs = {entry["slug"] for entry in r["entries"]}
    assert slugs == {"a", "b"}


def test_list_codex_entries_filters_by_kind(novel):
    e, iid, nid = novel
    _invoke(e, iid, "create_codex_entry",
            novel_id=nid, slug="a", name="A", kind="location",
            body="x", triggers="a")
    _invoke(e, iid, "create_codex_entry",
            novel_id=nid, slug="b", name="B", kind="artefact",
            body="x", triggers="b")
    r = _invoke(e, iid, "list_codex_entries",
                 novel_id=nid, kind="location")
    slugs = {entry["slug"] for entry in r["entries"]}
    assert slugs == {"a"}


# ---------------------------------------------------------------------------
# match_codex_entries — trigger-word scanner.
# ---------------------------------------------------------------------------


def test_match_codex_entries_finds_by_trigger(novel):
    e, iid, nid = novel
    _invoke(e, iid, "create_codex_entry",
            novel_id=nid, slug="iron-mask", name="Iron Mask",
            kind="artefact", body="A black-iron half-mask.",
            triggers="Iron Mask, the mask")
    text = "She lifted the mask and saw her own face."
    r = _invoke(e, iid, "match_codex_entries",
                 novel_id=nid, text=text)
    slugs = {entry["slug"] for entry in r["matches"]}
    assert "iron-mask" in slugs


def test_match_codex_entries_case_insensitive(novel):
    e, iid, nid = novel
    _invoke(e, iid, "create_codex_entry",
            novel_id=nid, slug="raven", name="Raven",
            kind="minor-character", body="A trickster.",
            triggers="Raven")
    text = "raven appeared in the rafters."
    r = _invoke(e, iid, "match_codex_entries",
                 novel_id=nid, text=text)
    assert any(m["slug"] == "raven" for m in r["matches"])


def test_match_codex_entries_no_match(novel):
    e, iid, nid = novel
    _invoke(e, iid, "create_codex_entry",
            novel_id=nid, slug="x", name="X",
            kind="concept", body="x", triggers="X")
    r = _invoke(e, iid, "match_codex_entries",
                 novel_id=nid, text="nothing relevant here.")
    assert r["matches"] == []


def test_match_codex_entries_skips_archived(novel):
    e, iid, nid = novel
    ent = _invoke(e, iid, "create_codex_entry",
                   novel_id=nid, slug="cult", name="The Cult",
                   kind="faction", body="A faction.",
                   triggers="cult")
    _invoke(e, iid, "archive_codex_entry",
            entry_id=ent["entry_id"], reason="superseded by Spec 132 test")
    r = _invoke(e, iid, "match_codex_entries",
                 novel_id=nid, text="The cult gathered at dusk.")
    assert r["matches"] == []


# ---------------------------------------------------------------------------
# update_codex_entry.
# ---------------------------------------------------------------------------


def test_update_codex_entry_changes_body(novel):
    e, iid, nid = novel
    ent = _invoke(e, iid, "create_codex_entry",
                   novel_id=nid, slug="x", name="X",
                   kind="concept", body="old body", triggers="X")
    _invoke(e, iid, "update_codex_entry",
            entry_id=ent["entry_id"], body="new body")
    node = e.memory.recall(ent["entry_id"])
    assert node["body"] == "new body"


# ---------------------------------------------------------------------------
# archive_codex_entry.
# ---------------------------------------------------------------------------


def test_archive_codex_entry_flags_archived(novel):
    e, iid, nid = novel
    ent = _invoke(e, iid, "create_codex_entry",
                   novel_id=nid, slug="x", name="X",
                   kind="concept", body="x", triggers="X")
    r = _invoke(e, iid, "archive_codex_entry",
                 entry_id=ent["entry_id"], reason="deprecated")
    assert r["entry_id"] == ent["entry_id"]
    node = e.memory.recall(ent["entry_id"])
    assert node.get("archived") == "yes"


# ---------------------------------------------------------------------------
# Spec 127 _compose_world_rules upgrade — composer scans + injects.
# ---------------------------------------------------------------------------


def test_compose_world_rules_injects_matched_codex(novel):
    e, iid, nid = novel
    # Codex entry author has registered.
    _invoke(e, iid, "create_codex_entry",
            novel_id=nid, slug="iron-mask", name="Iron Mask",
            kind="artefact",
            body=("A black-iron half-mask forged in the Third Age; "
                  "wearing it summons the lost name of its bearer."),
            triggers="Iron Mask, the mask")
    # Build a scene with body mentioning the trigger.
    ch = _invoke(e, iid, "create_chapter",
                 novel_id=nid, number=1, title="Awakening",
                 body="She found the mask on the altar.")
    sc = _invoke(e, iid, "create_scene",
                 chapter_id=ch["chapter_id"], slug="opening",
                 pov="third-limited")
    r = _invoke(e, iid, "assemble_scene_brief", cap="prompt",
                 scene_id=sc["scene_id"],
                 max_tokens=10000, section_budget=3000)
    wr = r["sections"]["world_rules"]
    # The Iron Mask body should now be injected, replacing the placeholder.
    assert "Iron Mask" in wr or "half-mask" in wr
    assert "pending" not in wr.lower()
