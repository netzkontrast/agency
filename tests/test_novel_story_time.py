"""Spec 128 — story-time / narrative-time graph.

Adds StoryTimeEvent + NarrativeBeat nodes + HAPPENS_AT / REVEALED_IN /
PRECEDES edges + 6 verbs. Closes Spec 127's `_continuity` placeholder —
`assemble_scene_brief`'s _compose_continuity composer reads the event
list from the graph instead of returning a placeholder.
"""
from __future__ import annotations

import tempfile

import pytest

from agency.engine import Engine


def _fresh() -> Engine:
    return Engine(tempfile.mktemp(suffix=".db"))


def _iid(e: Engine) -> str:
    return e.intent.capture_and_confirm(
        "spec 128 story time", "events + reveals graph",
        "continuity composer reads it", owner="user")


def _invoke(e: Engine, iid: str, verb: str, cap: str = "novel", **kw):
    r, _ = e.registry.invoke(e.memory, iid, cap, verb,
                              agent_id="agent:test", **kw)
    return r


# ---------------------------------------------------------------------------
# Ontology registration.
# ---------------------------------------------------------------------------


def test_story_time_event_node_declared():
    e = _fresh()
    assert "StoryTimeEvent" in e.ontology.nodes


def test_narrative_beat_node_declared():
    e = _fresh()
    assert "NarrativeBeat" in e.ontology.nodes


def test_new_edges_registered():
    e = _fresh()
    edges = e.ontology.edges
    for edge in ("HAPPENS_AT", "REVEALED_IN", "PRECEDES"):
        assert edge in edges, f"{edge} missing"


def test_six_new_verbs_registered():
    e = _fresh()
    verbs = set(e.registry.get("novel").verbs)
    expected = {"record_story_event", "reveal_in_scene",
                 "list_story_events_up_to", "list_reveals_in",
                 "mark_narrative_beat", "narrative_order"}
    assert expected <= verbs


# ---------------------------------------------------------------------------
# Fixture: a 3-chapter novel with scenes anchored to story-time.
# ---------------------------------------------------------------------------


@pytest.fixture
def novel_with_scenes(_fresh_engine=None):
    e = _fresh()
    iid = _iid(e)
    nv = _invoke(e, iid, "create_novel",
                 title="Time Test", author="A. Author", genre="lit")
    chapters = []
    scenes = []
    for n in range(1, 4):
        ch = _invoke(e, iid, "create_chapter",
                     novel_id=nv["novel_id"], number=n, title=f"Ch {n}")
        chapters.append(ch["chapter_id"])
        sc = _invoke(e, iid, "create_scene",
                     chapter_id=ch["chapter_id"], slug=f"s{n}",
                     pov="third-limited")
        scenes.append(sc["scene_id"])
    return e, iid, nv["novel_id"], chapters, scenes


# ---------------------------------------------------------------------------
# record_story_event — mints + optional HAPPENS_AT to scene.
# ---------------------------------------------------------------------------


def test_record_story_event_creates_node(novel_with_scenes):
    e, iid, nid, _, scenes = novel_with_scenes
    r = _invoke(e, iid, "record_story_event",
                novel_id=nid, label="King dies",
                when_story="Y2391.04")
    assert r["event_id"]
    assert r["when_story"] == "Y2391.04"
    assert r["label"] == "King dies"


def test_record_story_event_anchors_to_scene_via_happens_at(novel_with_scenes):
    e, iid, nid, _, scenes = novel_with_scenes
    scene_id = scenes[1]
    r = _invoke(e, iid, "record_story_event",
                novel_id=nid, label="Coronation",
                when_story="Y2391.05", scene_id=scene_id)
    # HAPPENS_AT edge: Scene → StoryTimeEvent (the scene depicts the event).
    rows = e.memory.g.query(
        "MATCH (s:Scene)-[r:HAPPENS_AT]->(ev:StoryTimeEvent) "
        "WHERE s.id = $sid AND ev.id = $eid RETURN r",
        {"sid": scene_id, "eid": r["event_id"]})
    assert len(rows) == 1


def test_record_story_event_without_scene_no_edge(novel_with_scenes):
    e, iid, nid, _, _ = novel_with_scenes
    r = _invoke(e, iid, "record_story_event",
                novel_id=nid, label="Backstory",
                when_story="Y2380.01")
    rows = e.memory.g.query(
        "MATCH (s:Scene)-[r:HAPPENS_AT]->(ev:StoryTimeEvent) "
        "WHERE ev.id = $eid RETURN r",
        {"eid": r["event_id"]})
    assert len(rows) == 0


# ---------------------------------------------------------------------------
# reveal_in_scene — adds REVEALED_IN edge for foreshadow/payoff.
# ---------------------------------------------------------------------------


def test_reveal_in_scene_adds_edge(novel_with_scenes):
    e, iid, nid, _, scenes = novel_with_scenes
    ev = _invoke(e, iid, "record_story_event",
                  novel_id=nid, label="Past murder",
                  when_story="Y2390.01")
    revealer_scene = scenes[2]   # chapter 3 reveals the chapter-1 event
    r = _invoke(e, iid, "reveal_in_scene",
                event_id=ev["event_id"], scene_id=revealer_scene)
    rows = e.memory.g.query(
        "MATCH (ev:StoryTimeEvent)-[r:REVEALED_IN]->(s:Scene) "
        "WHERE ev.id = $eid AND s.id = $sid RETURN r",
        {"eid": ev["event_id"], "sid": revealer_scene})
    assert len(rows) == 1


def test_reveal_in_scene_unknown_event_returns_error(novel_with_scenes):
    e, iid, _, _, scenes = novel_with_scenes
    r = _invoke(e, iid, "reveal_in_scene",
                event_id="event:does-not-exist", scene_id=scenes[0])
    assert r is None   # NOT_FOUND


# ---------------------------------------------------------------------------
# list_story_events_up_to — sortable string slice.
# ---------------------------------------------------------------------------


def test_list_story_events_up_to_returns_anchored_only(novel_with_scenes):
    e, iid, nid, _, scenes = novel_with_scenes
    s1, s2, s3 = scenes
    # Three events anchored to scenes in story-time order.
    _invoke(e, iid, "record_story_event",
            novel_id=nid, label="Birth", when_story="A001",
            scene_id=s1)
    _invoke(e, iid, "record_story_event",
            novel_id=nid, label="Marriage", when_story="A015",
            scene_id=s2)
    _invoke(e, iid, "record_story_event",
            novel_id=nid, label="Death", when_story="A050",
            scene_id=s3)
    # Looking up at scene 2 (its event has when_story=A015), include events
    # ≤ "A015".
    r = _invoke(e, iid, "list_story_events_up_to", scene_id=s2)
    labels = [ev["label"] for ev in r["events"]]
    assert "Birth" in labels
    assert "Marriage" in labels
    assert "Death" not in labels


def test_list_story_events_up_to_handles_scene_without_anchor(
        novel_with_scenes):
    """When the queried scene has no HAPPENS_AT, return all events the
    scene's narrative position can know — for v1, none (no anchor → no
    story-time reference frame)."""
    e, iid, _, _, scenes = novel_with_scenes
    r = _invoke(e, iid, "list_story_events_up_to", scene_id=scenes[0])
    assert r["events"] == []
    assert r["anchor_when"] is None


# ---------------------------------------------------------------------------
# list_reveals_in — events the scene discloses.
# ---------------------------------------------------------------------------


def test_list_reveals_in_returns_revealed_events(novel_with_scenes):
    e, iid, nid, _, scenes = novel_with_scenes
    ev = _invoke(e, iid, "record_story_event",
                  novel_id=nid, label="Lost will",
                  when_story="A001")
    _invoke(e, iid, "reveal_in_scene",
            event_id=ev["event_id"], scene_id=scenes[2])
    r = _invoke(e, iid, "list_reveals_in", scene_id=scenes[2])
    assert len(r["reveals"]) == 1
    assert r["reveals"][0]["label"] == "Lost will"


# ---------------------------------------------------------------------------
# mark_narrative_beat — beats + PRECEDES edge.
# ---------------------------------------------------------------------------


def test_mark_narrative_beat_records_node(novel_with_scenes):
    e, iid, _, _, scenes = novel_with_scenes
    r = _invoke(e, iid, "mark_narrative_beat",
                scene_id=scenes[0], beat_label="opening-image")
    assert r["beat_id"]


def test_mark_narrative_beat_chains_precedes(novel_with_scenes):
    e, iid, _, _, scenes = novel_with_scenes
    b1 = _invoke(e, iid, "mark_narrative_beat",
                  scene_id=scenes[0], beat_label="opening-image")
    b2 = _invoke(e, iid, "mark_narrative_beat",
                  scene_id=scenes[1], beat_label="inciting-incident",
                  predecessor_id=b1["beat_id"])
    rows = e.memory.g.query(
        "MATCH (a:NarrativeBeat)-[r:PRECEDES]->(b:NarrativeBeat) "
        "WHERE a.id = $aid AND b.id = $bid RETURN r",
        {"aid": b1["beat_id"], "bid": b2["beat_id"]})
    assert len(rows) == 1


# ---------------------------------------------------------------------------
# narrative_order — topo-sort over PRECEDES.
# ---------------------------------------------------------------------------


def test_narrative_order_returns_topo_sort(novel_with_scenes):
    e, iid, nid, _, scenes = novel_with_scenes
    b1 = _invoke(e, iid, "mark_narrative_beat",
                  scene_id=scenes[0], beat_label="b1")
    b2 = _invoke(e, iid, "mark_narrative_beat",
                  scene_id=scenes[1], beat_label="b2",
                  predecessor_id=b1["beat_id"])
    b3 = _invoke(e, iid, "mark_narrative_beat",
                  scene_id=scenes[2], beat_label="b3",
                  predecessor_id=b2["beat_id"])
    r = _invoke(e, iid, "narrative_order", novel_id=nid)
    ids = [b["beat_id"] for b in r["beats"]]
    # b1 before b2 before b3 in topo-sort.
    assert ids.index(b1["beat_id"]) < ids.index(b2["beat_id"])
    assert ids.index(b2["beat_id"]) < ids.index(b3["beat_id"])


# ---------------------------------------------------------------------------
# prompt.assemble_scene_brief upgrade — _continuity composer reads the graph.
# ---------------------------------------------------------------------------


def test_assemble_scene_brief_continuity_lists_recorded_events(
        novel_with_scenes):
    e, iid, nid, _, scenes = novel_with_scenes
    s1, s2, s3 = scenes
    _invoke(e, iid, "record_story_event",
            novel_id=nid, label="The crown is forged",
            when_story="A001", scene_id=s1)
    _invoke(e, iid, "record_story_event",
            novel_id=nid, label="The king is poisoned",
            when_story="A015", scene_id=s2)
    r = _invoke(e, iid, "assemble_scene_brief", cap="prompt",
                scene_id=s2, max_tokens=10000, section_budget=3000)
    cont = r["sections"]["continuity"]
    assert "The crown is forged" in cont
    assert "The king is poisoned" in cont
    # The placeholder text MUST be gone — graph-backed now.
    assert "pending" not in cont.lower()
