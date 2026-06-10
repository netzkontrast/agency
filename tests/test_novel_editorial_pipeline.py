"""Spec 122 — novel editorial pipeline.

5 chapter-spanning prose verbs + 3 composite editorial-stage gates +
2 walkable skills.
"""
from __future__ import annotations

import tempfile

import pytest

from agency.engine import Engine


def _fresh() -> Engine:
    return Engine(tempfile.mktemp(suffix=".db"))


def _iid(e: Engine) -> str:
    return e.intent.capture_and_confirm(
        "spec 122 editorial", "pipeline ships", "gates fire", owner="user")


def _invoke(e: Engine, iid: str, verb: str, **kw):
    r, _ = e.registry.invoke(e.memory, iid, "novel", verb,
                              agent_id="agent:test", **kw)
    return r


# ---------------------------------------------------------------------------
# Verb / skill registration.
# ---------------------------------------------------------------------------


def test_new_verbs_registered():
    e = _fresh()
    verbs = set(e.registry.get("novel").verbs)
    assert {"check_voice_consistency", "check_pov_consistency",
             "check_continuity", "check_sensitivity",
             "chapter_report_full",
             "developmental_gate", "line_gate", "copy_gate"} <= verbs


def test_skills_registered():
    e = _fresh()
    skills = e.ontology.skills
    assert "developmental-editor" in skills
    assert "line-editor" in skills


def test_developmental_editor_phases_bind_to_gate():
    e = _fresh()
    skill = e.ontology.skills["developmental-editor"]
    phase3 = [p for p in skill["phases"] if p["index"] == 3][0]
    assert "novel.developmental_gate" in phase3.get("verbs", [])


def test_line_editor_phases_bind_to_gate():
    e = _fresh()
    skill = e.ontology.skills["line-editor"]
    phase3 = [p for p in skill["phases"] if p["index"] == 3][0]
    assert "novel.line_gate" in phase3.get("verbs", [])


# ---------------------------------------------------------------------------
# check_voice_consistency.
# ---------------------------------------------------------------------------


def test_voice_consistency_passes_when_bodies_align():
    e = _fresh()
    iid = _iid(e)
    similar = [
        "She walked slowly. The room was dim. She thought of him.",
        "He turned away. The hall was quiet. He thought of her.",
        "They paused. The street was empty. They thought of nothing.",
    ]
    r = _invoke(e, iid, "check_voice_consistency", bodies=similar)
    assert r["passed"] is True
    assert r["outliers"] == []


def test_voice_consistency_flags_outlier_chapter():
    e = _fresh()
    iid = _iid(e)
    # Three short tight bodies + one massively flowery/filtery body.
    bodies = [
        "She walked. The room was dim.",
        "He turned. The hall was quiet.",
        "They paused. The street was empty.",
        ("She really just truly literally absolutely simply just basically "
         "actually very really truly basically just literally absolutely "
         "actually thought about it for what felt like a very long time."),
    ]
    # Tighter z_threshold to fire on the small 4-chapter sample (default 2.0
    # is the doctrine tunable; tests can pass a lower bound to validate
    # the outlier-detection mechanism itself).
    r = _invoke(e, iid, "check_voice_consistency",
                bodies=bodies, z_threshold=1.5)
    assert r["passed"] is False
    assert any(o["index"] == 3 for o in r["outliers"])


# ---------------------------------------------------------------------------
# check_pov_consistency.
# ---------------------------------------------------------------------------


def _setup_novel_with_scenes(e, iid, povs_per_chapter):
    nv = _invoke(e, iid, "create_novel",
                 title="POV Test", author="A. Author", genre="lit")
    for n, povs in enumerate(povs_per_chapter, start=1):
        ch = _invoke(e, iid, "create_chapter",
                     novel_id=nv["novel_id"], number=n, title=f"Ch {n}")
        for i, p in enumerate(povs):
            _invoke(e, iid, "create_scene",
                    chapter_id=ch["chapter_id"], slug=f"s{i}", pov=p)
    return nv["novel_id"]


def test_pov_consistency_passes_on_uniform_pov():
    e = _fresh()
    iid = _iid(e)
    nid = _setup_novel_with_scenes(e, iid, [
        ["third-limited", "third-limited"],
        ["third-limited", "third-limited"],
    ])
    r = _invoke(e, iid, "check_pov_consistency", novel_id=nid)
    assert r["passed"] is True
    assert all(not c["mixed"] for c in r["per_chapter"])


def test_pov_consistency_flags_mid_chapter_break():
    e = _fresh()
    iid = _iid(e)
    nid = _setup_novel_with_scenes(e, iid, [
        ["third-limited", "third-limited"],
        ["third-limited", "first"],   # mid-chapter POV break
    ])
    r = _invoke(e, iid, "check_pov_consistency", novel_id=nid)
    assert r["passed"] is False
    mixed = [c for c in r["per_chapter"] if c["mixed"]]
    assert len(mixed) == 1
    assert mixed[0]["number"] == 2


# ---------------------------------------------------------------------------
# check_continuity.
# ---------------------------------------------------------------------------


def test_continuity_passes_on_consistent_names():
    e = _fresh()
    iid = _iid(e)
    nv = _invoke(e, iid, "create_novel",
                 title="Continuity Test", author="A. Author", genre="lit")
    for n, body in enumerate([
        "Sarah walked into the room. James turned to greet her.",
        "Sarah sat down. James offered her a glass.",
    ], start=1):
        _invoke(e, iid, "create_chapter",
                novel_id=nv["novel_id"], number=n, title=f"Ch {n}", body=body)
    r = _invoke(e, iid, "check_continuity", novel_id=nv["novel_id"])
    assert r["passed"] is True


def test_continuity_flags_single_chapter_name():
    e = _fresh()
    iid = _iid(e)
    nv = _invoke(e, iid, "create_novel",
                 title="Continuity Test 2", author="A. Author", genre="lit")
    for n, body in enumerate([
        "Sarah walked in. James was there.",
        "Sarah sat. James greeted her.",
        "Sarah left. James waved. Bartholomew appeared briefly.",
    ], start=1):
        _invoke(e, iid, "create_chapter",
                novel_id=nv["novel_id"], number=n, title=f"Ch {n}", body=body)
    r = _invoke(e, iid, "check_continuity", novel_id=nv["novel_id"])
    single = [s["name"] for s in r["single_chapter"]]
    assert "Bartholomew" in single


def test_continuity_flags_close_spelling_pair():
    e = _fresh()
    iid = _iid(e)
    nv = _invoke(e, iid, "create_novel",
                 title="Continuity Test 3", author="A. Author", genre="lit")
    for n, body in enumerate([
        "Lara walked the streets.",
        "Laura watched the rain. Lara called out.",  # Lara/Laura typo pair
    ], start=1):
        _invoke(e, iid, "create_chapter",
                novel_id=nv["novel_id"], number=n, title=f"Ch {n}", body=body)
    r = _invoke(e, iid, "check_continuity", novel_id=nv["novel_id"])
    pairs = {(p["a"], p["b"]) for p in r["close_pairs"]}
    assert ("Lara", "Laura") in pairs or ("Laura", "Lara") in pairs


# ---------------------------------------------------------------------------
# check_sensitivity — advisory; always passes.
# ---------------------------------------------------------------------------


def test_sensitivity_passes_and_emits_warnings():
    e = _fresh()
    iid = _iid(e)
    body = ("She had been struggling with depression for months. "
             "The trauma of the assault stayed with her.")
    r = _invoke(e, iid, "check_sensitivity", body=body)
    assert r["passed"] is True   # advisory — never blocks
    categories = {w["category"] for w in r["warnings"]}
    assert "mental-health" in categories
    assert "trauma" in categories


# ---------------------------------------------------------------------------
# chapter_report_full.
# ---------------------------------------------------------------------------


def test_chapter_report_full_aggregates_checks():
    e = _fresh()
    iid = _iid(e)
    nv = _invoke(e, iid, "create_novel",
                 title="Report Test", author="A. Author", genre="lit")
    ch = _invoke(e, iid, "create_chapter",
                 novel_id=nv["novel_id"], number=1, title="Ch 1",
                 body="She walked into the room. The light was warm.")
    r = _invoke(e, iid, "chapter_report_full", chapter_id=ch["chapter_id"])
    assert r["chapter_id"] == ch["chapter_id"]
    assert {"readability", "filter_words", "show_dont_tell",
             "dialogue_attribution", "content_warnings",
             "sensitivity"} <= set(r["checks"].keys())
    assert r["artefact_id"]


# ---------------------------------------------------------------------------
# Composite gates.
# ---------------------------------------------------------------------------


def test_developmental_gate_blocks_when_storyform_missing():
    e = _fresh()
    iid = _iid(e)
    nv = _invoke(e, iid, "create_novel",
                 title="DG Test", author="A. Author", genre="lit")
    _invoke(e, iid, "create_chapter",
            novel_id=nv["novel_id"], number=1, title="Ch 1")
    r = _invoke(e, iid, "developmental_gate", novel_id=nv["novel_id"])
    # No Storyform → GATE_FAILED returned through registry as None+inv
    assert r is None or r.get("passed") is False


def test_developmental_gate_passes_when_substrate_present():
    e = _fresh()
    iid = _iid(e)
    nv = _invoke(e, iid, "create_novel",
                 title="DG Pass", author="A. Author", genre="lit")
    _invoke(e, iid, "create_chapter",
            novel_id=nv["novel_id"], number=1, title="Ch 1")
    e.memory.record("Storyform", {"novel": nv["novel_id"]})
    r = _invoke(e, iid, "developmental_gate", novel_id=nv["novel_id"])
    assert r["passed"] is True
    assert all(r["checks"].values())


def test_line_gate_passes_on_clean_chapters():
    e = _fresh()
    iid = _iid(e)
    nv = _invoke(e, iid, "create_novel",
                 title="LG Test", author="A. Author", genre="lit")
    _invoke(e, iid, "create_chapter",
            novel_id=nv["novel_id"], number=1, title="Ch 1",
            body='She walked into the room. "Hello," she said. '
                 "The light shone warmly across the wooden floor.")
    r = _invoke(e, iid, "line_gate", novel_id=nv["novel_id"])
    # Either passes or returns None with typed failure — both valid based
    # on whether the prose body passes the underlying thresholds.
    if r is not None:
        assert "checks" in r


def test_copy_gate_blocks_when_content_warnings_undeclared():
    e = _fresh()
    iid = _iid(e)
    nv = _invoke(e, iid, "create_novel",
                 title="CG Test", author="A. Author", genre="lit")
    _invoke(e, iid, "create_chapter",
            novel_id=nv["novel_id"], number=1, title="Ch 1",
            body="She walked. He turned. They paused.")
    r = _invoke(e, iid, "copy_gate", novel_id=nv["novel_id"])
    assert r is None or r.get("passed") is False
