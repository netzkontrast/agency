"""Spec 102 Slice 1 — novel lifecycle cluster (additive to Spec 101 Slice 1).

5 new verbs extending the MVN: capture_idea, promote_idea, list_ideas,
find_novel, set_novel_status. Plus the Idea node + IDEA_STATUS enum +
PROMOTED_TO edge that Spec 094 (music) proved.

Skill `novel-concept` extends from 5→10 phases per Spec 102 §"novel-concept
walkable skill" (premise/genre/audience/pov/setting/characters-core/
dramatica-seed/outline-shape/series-hypothesis/confirmation, hard gate).
"""
from __future__ import annotations

import tempfile

import pytest

from agency.engine import Engine
from agency.skill import SkillRun


def _fresh() -> Engine:
    return Engine(tempfile.mktemp(suffix=".db"))


def _confirmed_iid(e: Engine, purpose: str = "spec 102") -> str:
    iid = e.intent.capture(purpose, "lifecycle", "verified")
    e.intent.confirm(iid)
    return iid


def _invoke(e: Engine, iid: str, verb: str, **kw):
    return e.registry.invoke(e.memory, iid, "novel", verb, **kw)


# ─────────────────────── capability registration ───────────────────────


def test_novel_capability_registers_all_lifecycle_verbs() -> None:
    """All 8 base lifecycle verbs (101 MVN + 102 Slice-1 delta) ship."""
    e = _fresh()
    cap = e.registry._caps["novel"]
    expected = {
        # 101 Slice 1 MVN (carry-over):
        "conceptualize", "create_novel", "create_chapter",
        "chapter_report", "render_manuscript",
        # 102 Slice 1 delta:
        "capture_idea", "promote_idea", "list_ideas",
        "find_novel", "set_novel_status",
    }
    missing = expected - set(cap.verbs)
    assert not missing, f"missing verbs: {missing}"
    e.memory.close()


# ─────────────────────── ontology additions ───────────────────────


def test_idea_node_declared_with_status_enum() -> None:
    """Spec 102 adds an Idea node with the IDEA_STATUS enum (mirrors music)."""
    e = _fresh()
    cap = e.registry._caps["novel"]
    assert "Idea" in cap.ontology.nodes
    assert ("Idea", "status") in cap.ontology.enums
    # New + promoted + dropped — minimum from Spec 102 design
    status_set = cap.ontology.enums[("Idea", "status")]
    assert {"new", "promoted", "dropped"} <= status_set
    e.memory.close()


def test_promoted_to_edge_declared() -> None:
    """PROMOTED_TO ties an Idea to the Novel it became (Spec 102 design)."""
    e = _fresh()
    cap = e.registry._caps["novel"]
    assert "PROMOTED_TO" in cap.ontology.edges
    e.memory.close()


def test_idea_status_enum_bites() -> None:
    """Invalid Idea status rejected at Memory.record."""
    e = _fresh()
    with pytest.raises(ValueError):
        e.memory.record("Idea", {"text": "x", "status": "nonsense"})
    e.memory.close()


# ─────────────────────── capture_idea ───────────────────────


def test_capture_idea_records_idea_serving_intent() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    data, _ = _invoke(e, iid, "capture_idea",
                      text="A novel about time-loops in a small town")
    assert data["idea_id"].startswith("idea:")
    assert data["status"] == "new"
    # SERVES edge
    rows = e.memory.g.query(
        "MATCH (i)-[r:SERVES]->(t) WHERE i.id = $iid AND t.id = $tid RETURN r",
        {"iid": data["idea_id"], "tid": iid})
    assert rows
    e.memory.close()


# ─────────────────────── list_ideas ───────────────────────


def test_list_ideas_returns_count_and_filters_by_status() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    _invoke(e, iid, "capture_idea", text="idea-1")
    _invoke(e, iid, "capture_idea", text="idea-2")
    _invoke(e, iid, "capture_idea", text="idea-3")
    all_, _ = _invoke(e, iid, "list_ideas")
    assert all_["count"] == 3
    # status filter — all are "new" by default
    only_new, _ = _invoke(e, iid, "list_ideas", status="new")
    assert only_new["count"] == 3
    promoted, _ = _invoke(e, iid, "list_ideas", status="promoted")
    assert promoted["count"] == 0
    e.memory.close()


def test_list_ideas_rejects_invalid_status() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    data, inv = _invoke(e, iid, "list_ideas", status="bogus")
    assert data is None
    err = e.memory.recall(inv).get("error", "")
    assert "INVALID_ARGUMENT" in err
    e.memory.close()


# ─────────────────────── promote_idea ───────────────────────


def test_promote_idea_flips_status_and_creates_novel() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    idea, _ = _invoke(e, iid, "capture_idea",
                      text="A premise for a novel")
    data, _ = _invoke(e, iid, "promote_idea",
                      idea_id=idea["idea_id"],
                      title="The Promoted Novel",
                      author="An Author")
    assert data["novel_id"].startswith("novel:")
    assert data["idea_id"] == idea["idea_id"]
    # Idea status flipped
    node = e.memory.recall(idea["idea_id"])
    assert node["status"] == "promoted"
    # PROMOTED_TO edge from Idea → Novel
    rows = e.memory.g.query(
        "MATCH (i)-[r:PROMOTED_TO]->(n) WHERE i.id = $iid AND n.id = $nid "
        "RETURN r",
        {"iid": idea["idea_id"], "nid": data["novel_id"]})
    assert rows
    e.memory.close()


def test_promote_idea_not_found() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    data, inv = _invoke(e, iid, "promote_idea",
                        idea_id="idea:does-not-exist",
                        title="x", author="y")
    assert data is None
    err = e.memory.recall(inv).get("error", "")
    assert "NOT_FOUND" in err
    e.memory.close()


# ─────────────────────── find_novel ───────────────────────


def test_find_novel_returns_matches_by_substring() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    _invoke(e, iid, "create_novel",
            title="The Great Modem", author="A")
    _invoke(e, iid, "create_novel",
            title="Quantum Dawn", author="B")
    _invoke(e, iid, "create_novel",
            title="Modem Mysteries", author="C")
    data, _ = _invoke(e, iid, "find_novel", query="modem")
    assert data["count"] == 2
    titles = {n["title"] for n in data["novels"]}
    assert titles == {"The Great Modem", "Modem Mysteries"}
    e.memory.close()


def test_find_novel_empty_query_returns_all() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    _invoke(e, iid, "create_novel", title="A", author="x")
    _invoke(e, iid, "create_novel", title="B", author="y")
    data, _ = _invoke(e, iid, "find_novel", query="")
    assert data["count"] == 2
    e.memory.close()


# ─────────────────────── set_novel_status ───────────────────────


def test_set_novel_status_flips_and_returns_new_status() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    novel, _ = _invoke(e, iid, "create_novel",
                        title="X", author="Y")
    data, _ = _invoke(e, iid, "set_novel_status",
                      novel_id=novel["novel_id"],
                      status="drafting")
    assert data["status"] == "drafting"
    node = e.memory.recall(novel["novel_id"])
    assert node["status"] == "drafting"
    e.memory.close()


def test_set_novel_status_rejects_invalid_status() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    novel, _ = _invoke(e, iid, "create_novel",
                        title="X", author="Y")
    data, inv = _invoke(e, iid, "set_novel_status",
                        novel_id=novel["novel_id"],
                        status="not-a-real-status")
    assert data is None
    err = e.memory.recall(inv).get("error", "")
    assert "INVALID_ARGUMENT" in err
    e.memory.close()


def test_set_novel_status_not_found() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    data, inv = _invoke(e, iid, "set_novel_status",
                        novel_id="novel:nope", status="drafting")
    assert data is None
    err = e.memory.recall(inv).get("error", "")
    assert "NOT_FOUND" in err
    e.memory.close()


# ─────────────────────── skill extension (5 → 10 phases) ───────────────────────


def test_novel_concept_skill_extended_to_ten_phases() -> None:
    """Spec 102 §"novel-concept walkable skill (10 phases)" — extends
    Slice 1's 5-phase skill with genre/audience/setting/characters-core/
    dramatica-seed/outline-shape/series-hypothesis blocks.
    """
    e = _fresh()
    sk = e.ontology.skill("novel-concept")
    assert sk["kind"] == "conceptualizer"
    assert len(sk["phases"]) == 10
    names = [p["name"] for p in sk["phases"]]
    assert names == [
        "premise", "genre", "audience", "pov", "setting",
        "characters-core", "dramatica-seed", "outline-shape",
        "series-hypothesis", "confirmation",
    ]
    assert sk["phases"][-1].get("gate") == "hard"
    e.memory.close()


def test_novel_concept_skill_walks_through_all_ten_phases() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    sk = e.ontology.skill("novel-concept")
    run = SkillRun(e.memory, iid, sk)
    fills = [
        {"logline": "x", "central_question": "y"},
        {"genre": "scifi", "subgenre": "cyberpunk", "tone": "noir"},
        {"target_reader": "adults", "comp_titles": "Neuromancer, Snow Crash"},
        {"pov_choice": "third-limited", "narrator_voice": "wry"},
        {"world": "futuristic-LA", "time_period": "2089",
         "geography": "urban-sprawl"},
        {"protagonist_seed": "Case-like hacker",
         "antagonist_seed": "Corporate AI",
         "supporting_seeds": "Molly-like sidekick"},
        {"resolve_intent": "change", "growth_intent": "start",
         "approach_intent": "do-er", "mental_sex_intent": "linear"},
        {"act_structure": "3-act", "midpoint_intent": "betrayal",
         "ending_intent": "ambiguous"},
        {"standalone_or_series": "standalone", "series_arc": "n/a"},
    ]
    for out in fills:
        assert run.submit(out)["status"] == "working"
    assert run.current()["gate"] == "hard"
    assert run.submit({"user_confirmed": "yes"},
                      confirmed=True)["status"] == "completed"
    e.memory.close()
