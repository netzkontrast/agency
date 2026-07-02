"""Spec 238 — story-time graph queries.

narrative_order derived as a PRECEDES topological path (cycle = typed
TEMPORAL_CYCLE); story_time_query SURFACES temporal contradictions instead of
sorting around them (empty scope = coverage 1.0, vacuous truth);
events_pov_witnessed intersects the POV horizon with the when_story ceiling.
"""
from __future__ import annotations

import tempfile

from agency.engine import Engine


def _fresh() -> Engine:
    return Engine(tempfile.mktemp(suffix=".db"))


def _iid(e: Engine) -> str:
    iid = e.intent.capture("spec 238", "story-time query", "verified")
    e.intent.confirm(iid)
    return iid


def _invoke(e, iid, verb, **kw):
    r, _ = e.registry.invoke(e.memory, iid, "novel", verb, **kw)
    return r


def _novel(e, iid):
    return _invoke(e, iid, "create_novel", title="K",
                   author="A")["novel_id"]


def _beat(e, iid, nid, label, scene=""):
    return e.memory.record("NarrativeBeat",
                           {"novel": nid, "label": label,
                            "scene": scene or f"scene:stub-{label}"})


def test_narrative_order_topological_and_cycle_typed() -> None:
    e = _fresh()
    iid = _iid(e)
    nid = _novel(e, iid)
    b1, b2, b3 = (_beat(e, iid, nid, f"b{i}") for i in (1, 2, 3))
    e.memory.link(b1, b2, "PRECEDES")
    e.memory.link(b2, b3, "PRECEDES")
    out = _invoke(e, iid, "narrative_order", novel_id=nid)
    assert out["order"].index(b1) < out["order"].index(b2) \
        < out["order"].index(b3)
    assert out["edges_traversed"] == 2
    e.memory.link(b3, b1, "PRECEDES")             # close the cycle
    assert _invoke(e, iid, "narrative_order", novel_id=nid) is None  # typed


def test_story_time_query_surfaces_contradiction() -> None:
    e = _fresh()
    iid = _iid(e)
    nid = _novel(e, iid)
    ch1 = _invoke(e, iid, "create_chapter", novel_id=nid, number=1,
                  title="I")["chapter_id"]
    ch9 = _invoke(e, iid, "create_chapter", novel_id=nid, number=9,
                  title="IX")["chapter_id"]
    s1 = _invoke(e, iid, "create_scene", chapter_id=ch1, slug="a",
                 pov="first")["scene_id"]
    s9 = _invoke(e, iid, "create_scene", chapter_id=ch9, slug="b",
                 pov="first")["scene_id"]
    # LATER story-time event shown in the EARLIER chapter and vice versa
    _invoke(e, iid, "record_story_event", novel_id=nid, label="late",
            when_story="2044-09", scene_id=s1)
    _invoke(e, iid, "record_story_event", novel_id=nid, label="early",
            when_story="2044-01", scene_id=s9)
    out = _invoke(e, iid, "story_time_query", novel_id=nid)
    assert len(out["contradictions"]) == 1
    assert "when_story" in out["contradictions"][0]["reason"]
    assert out["coverage"] == 1.0                 # both events anchored


def test_story_time_query_empty_scope_vacuous_truth() -> None:
    e = _fresh()
    iid = _iid(e)
    nid = _novel(e, iid)
    out = _invoke(e, iid, "story_time_query", novel_id=nid)
    assert out["events"] == [] and out["coverage"] == 1.0


def test_events_pov_witnessed_intersection() -> None:
    e = _fresh()
    iid = _iid(e)
    nid = _novel(e, iid)
    char = _invoke(e, iid, "create_codex_entry", novel_id=nid, slug="c",
                   name="C", kind="minor-character", body="pov")["entry_id"]
    ch = _invoke(e, iid, "create_chapter", novel_id=nid, number=1,
                 title="I")["chapter_id"]
    mine = _invoke(e, iid, "create_scene", chapter_id=ch, slug="mine",
                   pov="first", pov_character_id=char)["scene_id"]
    other = _invoke(e, iid, "create_scene", chapter_id=ch, slug="other",
                    pov="first")["scene_id"]
    e1 = _invoke(e, iid, "record_story_event", novel_id=nid, label="E1",
                 when_story="2044-01")["event_id"]
    e3 = _invoke(e, iid, "record_story_event", novel_id=nid, label="E3",
                 when_story="2044-03")["event_id"]
    e5 = _invoke(e, iid, "record_story_event", novel_id=nid, label="E5",
                 when_story="2044-05")["event_id"]
    for ev in (e1, e3):
        _invoke(e, iid, "reveal_in_scene", event_id=ev, scene_id=mine)
    _invoke(e, iid, "reveal_in_scene", event_id=e5, scene_id=other)
    out = _invoke(e, iid, "events_pov_witnessed", character_id=char)
    ids = [x["event_id"] for x in out["events"]]
    assert ids == [e1, e3]                        # e5 seen by another POV
    assert len(ids) <= out["total_events"]
    cut = _invoke(e, iid, "events_pov_witnessed", character_id=char,
                  before_when="2044-02")
    assert [x["event_id"] for x in cut["events"]] == [e1]
    assert _invoke(e, iid, "events_pov_witnessed",
                   character_id="nope") is None   # UNKNOWN_CHARACTER
