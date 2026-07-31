"""Spec 141 — chapter briefing & narrative-mode blocks.

ModeBlock spans with three simultaneous values (mode · storyform-status ·
bridge target) + genre accent; the load-bearing mode-≠-storyform-boundary
check; genre-bleed; the 13-section chapter briefing aggregating the whole
136–140 stack; the section-M pre-draft checklist.
"""
from __future__ import annotations

import tempfile

from agency.engine import Engine


def _fresh() -> Engine:
    return Engine(tempfile.mktemp(suffix=".db"))


def _iid(e: Engine) -> str:
    iid = e.intent.capture("spec 141", "chapter briefing", "verified")
    e.intent.confirm(iid)
    return iid


def _invoke(e: Engine, iid: str, verb: str, **kw):
    r, _ = e.registry.invoke(e.memory, iid, "novel", verb, **kw)
    return r


def _novel(e, iid):
    return _invoke(e, iid, "create_novel", title="KP",
                   author="A")["novel_id"]


def test_node_edge_enum_registered() -> None:
    e = _fresh()
    cap = e.registry.get("novel")
    assert "ModeBlock" in cap.ontology.nodes
    assert "IN_MODE_BLOCK" in cap.ontology.edges
    from agency.capabilities.novel.clusters.modeblocks import NARRATIVE_MODE
    assert "vortex-still" in NARRATIVE_MODE and len(NARRATIVE_MODE) == 6
    e.memory.close()


def test_define_block_report_and_unstaged() -> None:
    e = _fresh()
    iid = _iid(e)
    nid = _novel(e, iid)
    for n in (1, 2, 15):
        _invoke(e, iid, "create_chapter", novel_id=nid, number=n,
                title=f"Ch {n}")
    b = _invoke(e, iid, "define_mode_block", novel_id=nid,
                label="Akt I", mode="linear-introspective",
                from_chapter=1, to_chapter=12,
                bridge_frequency_target=0.10,
                genre_accent="philosophical horror")
    assert b["mode_block_id"]
    assert _invoke(e, iid, "define_mode_block", novel_id=nid, label="x",
                   mode="nope", from_chapter=1, to_chapter=2) is None
    rep = _invoke(e, iid, "mode_block_report", novel_id=nid)
    assert rep["blocks"][0]["label"] == "Akt I"
    assert rep["unstaged"] == [15]                 # ch15 in no block


def test_assign_chapter_to_block_edge() -> None:
    e = _fresh()
    iid = _iid(e)
    nid = _novel(e, iid)
    ch = _invoke(e, iid, "create_chapter", novel_id=nid, number=1,
                 title="Ch 1")["chapter_id"]
    b = _invoke(e, iid, "define_mode_block", novel_id=nid, label="Akt I",
                mode="framing", from_chapter=0,
                to_chapter=1)["mode_block_id"]
    out = _invoke(e, iid, "assign_chapter_to_block", chapter_id=ch,
                  mode_block_id=b)
    assert out["mode_block_id"] == b
    linked = e.memory.neighbors(ch, "IN_MODE_BLOCK", direction="out")
    assert any(n["id"] == b for n in linked)


def _dual_set(e, iid, nid):
    set_id = _invoke(e, iid, "create_storyform_set", novel_id=nid,
                     label="dual")["set_id"]
    a = _invoke(e, iid, "create_storyform", novel_id=nid,
                body={"dynamics": {"driver": "Decision"}})["storyform_id"]
    _invoke(e, iid, "add_storyform_to_set", storyform_id=a, set_id=set_id,
            role="primary")
    b = _invoke(e, iid, "create_storyform", novel_id=nid,
                body={"dynamics": {"driver": "Action"}},
                role="secondary")["storyform_id"]
    _invoke(e, iid, "add_storyform_to_set", storyform_id=b, set_id=set_id,
            role="secondary")
    return set_id


def test_mode_vs_storyform_boundary_distinction() -> None:
    e = _fresh()
    iid = _iid(e)
    nid = _novel(e, iid)
    set_id = _dual_set(e, iid, nid)
    _invoke(e, iid, "define_mode_block", novel_id=nid, label="Akt I",
            mode="linear-introspective", from_chapter=1, to_chapter=13)
    _invoke(e, iid, "define_mode_block", novel_id=nid, label="Vortex",
            mode="vortex-still", from_chapter=35, to_chapter=36)
    # the REAL turn at the vortex edge — fine
    _invoke(e, iid, "record_storyform_transition", storyform_set_id=set_id,
            from_role="secondary", to_role="primary", at_chapter=35,
            kind="operative")
    ok = _invoke(e, iid, "check_mode_vs_storyform_boundary", novel_id=nid)
    assert ok["passed"] is True
    # a transition mislabeled onto the Akt-I mode edge — violation
    _invoke(e, iid, "record_storyform_transition", storyform_set_id=set_id,
            from_role="primary", to_role="secondary", at_chapter=13,
            kind="ontological")
    bad = _invoke(e, iid, "check_mode_vs_storyform_boundary", novel_id=nid)
    assert bad["passed"] is False
    assert bad["violations"][0]["at_chapter"] == 13


def test_genre_bleed_flagged() -> None:
    e = _fresh()
    iid = _iid(e)
    nid = _novel(e, iid)
    ch = _invoke(e, iid, "create_chapter", novel_id=nid, number=3,
                 title="Ch 3")["chapter_id"]
    _invoke(e, iid, "define_mode_block", novel_id=nid, label="Akt I",
            mode="linear-introspective", from_chapter=1, to_chapter=12,
            genre_accent="philosophical horror")
    e.memory.update(ch, {"genre_accent": "technothriller"})
    out = _invoke(e, iid, "check_genre_bleed", novel_id=nid)
    assert out["passed"] is False
    assert out["bleeds"][0]["chapter_number"] == 3


def test_render_chapter_briefing_aggregates_stack() -> None:
    e = _fresh()
    iid = _iid(e)
    nid = _novel(e, iid)
    ch = _invoke(e, iid, "create_chapter", novel_id=nid, number=2,
                 title="Signal")["chapter_id"]
    _invoke(e, iid, "define_mode_block", novel_id=nid, label="Akt I",
            mode="linear-introspective", from_chapter=1, to_chapter=12,
            bridge_frequency_target=0.10, genre_accent="philosophical horror")
    sid = _invoke(e, iid, "create_scene", chapter_id=ch, slug="s",
                  pov="first")["scene_id"]
    _invoke(e, iid, "plant_anchor", scene_id=sid, name="734")
    out = _invoke(e, iid, "render_chapter_briefing", chapter_id=ch)
    assert out["artefact_id"]
    content = out["content"]
    assert "Akt I" in content
    assert "734" in content
    assert e.memory.recall(out["artefact_id"]).get("kind") == \
        "chapter-briefing"


def test_briefing_checklist_missing_then_ready() -> None:
    e = _fresh()
    iid = _iid(e)
    nid = _novel(e, iid)
    ch = _invoke(e, iid, "create_chapter", novel_id=nid, number=5,
                 title="Ch 5")["chapter_id"]
    out = _invoke(e, iid, "briefing_checklist", chapter_id=ch)
    assert out["ready"] is False
    assert any("mode-block" in m for m in out["missing"])
    # stage the chapter + minimum stack
    _invoke(e, iid, "define_mode_block", novel_id=nid, label="Akt I",
            mode="linear-introspective", from_chapter=1, to_chapter=12)
    _invoke(e, iid, "create_storyform", novel_id=nid, body={"slots": {}})
    entry = _invoke(e, iid, "create_codex_entry", novel_id=nid, slug="k",
                    name="K", kind="minor-character", body="b")["entry_id"]
    _invoke(e, iid, "create_voice_profile", character_id=entry,
            sentence_avg_target=8.0, sentence_avg_stddev=3.0)
    _invoke(e, iid, "register_project_rule", novel_id=nid, rule_id="R-5",
            name="polarity", severity="critical",
            predicate_kind="mutual-exclusion",
            params={"set_a": ["a"], "set_b": ["b"]})
    _invoke(e, iid, "set_reveal_rule", novel_id=nid, fact="f",
            tier="reader", may_know_from_chapter=10)
    out2 = _invoke(e, iid, "briefing_checklist", chapter_id=ch)
    assert out2["ready"] is True and out2["missing"] == []
