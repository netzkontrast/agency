"""Spec 133 — story structure templates (pacing layer).

Vendored beat-sheet templates (Save the Cat, Three-Act, Hero's Journey, Story
Circle, Snowflake) as data under ``novel/data/structures/``; ``BeatExpectation``
nodes minted per applied template; scene→beat anchoring via ``FULFILS``; a
coverage checklist + a position report that flags out-of-position beats.
"""
from __future__ import annotations

import tempfile

from agency.engine import Engine


def _fresh() -> Engine:
    return Engine(tempfile.mktemp(suffix=".db"))


def _iid(e: Engine) -> str:
    iid = e.intent.capture("spec 133", "structure templates", "verified")
    e.intent.confirm(iid)
    return iid


def _invoke(e: Engine, iid: str, verb: str, **kw):
    r, _ = e.registry.invoke(e.memory, iid, "novel", verb, **kw)
    return r


def _novel(e: Engine, iid: str) -> str:
    return _invoke(e, iid, "create_novel", title="K", author="A")["novel_id"]


def _scene(e: Engine, iid: str, novel_id: str, number: int, slug: str) -> str:
    ch = _invoke(e, iid, "create_chapter", novel_id=novel_id, number=number,
                 title=f"Ch {number}")
    return _invoke(e, iid, "create_scene", chapter_id=ch["chapter_id"],
                   slug=slug, pov="third-limited")["scene_id"]


# ── ontology ──────────────────────────────────────────────────────────────────

def test_ontology_declares_beat_expectation_and_fulfils() -> None:
    e = _fresh()
    cap = e.registry.get("novel")
    assert "BeatExpectation" in cap.ontology.nodes
    assert "FULFILS" in cap.ontology.edges
    e.memory.close()


# ── template discovery ────────────────────────────────────────────────────────

def test_list_structure_templates_ships_the_five_builtins() -> None:
    e = _fresh()
    out = _invoke(e, _iid(e), "list_structure_templates")
    ids = {t["template_id"] for t in out["templates"]}
    assert {"save-the-cat", "three-act", "heros-journey", "story-circle",
            "snowflake"} <= ids
    for t in out["templates"]:
        assert t["name"] and t["source"] and t["beat_count"] >= 5


def test_get_structure_template_full_body() -> None:
    e = _fresh()
    out = _invoke(e, _iid(e), "get_structure_template",
                  template_id="save-the-cat")
    beats = out["beats"]
    assert len(beats) == 15                      # the canonical STC beat sheet
    positions = [b["position"] for b in beats]
    assert all(0.0 <= p <= 1.0 for p in positions)
    assert positions == sorted(positions)        # beats in manuscript order
    assert all(b["slug"] and b["name"] and b["prompt"] for b in beats)


def test_get_unknown_template_is_typed_failure() -> None:
    e = _fresh()
    out = _invoke(e, _iid(e), "get_structure_template", template_id="nope")
    assert out is None                            # typed NOT_FOUND failure


# ── apply / anchor / coverage ─────────────────────────────────────────────────

def test_apply_structure_mints_expectations_idempotently() -> None:
    e = _fresh()
    iid = _iid(e)
    nid = _novel(e, iid)
    out = _invoke(e, iid, "apply_structure", novel_id=nid,
                  template_id="three-act")
    assert out["minted"] == out["beat_count"] > 0
    again = _invoke(e, iid, "apply_structure", novel_id=nid,
                    template_id="three-act")
    exps = [b for b in e.memory.find("BeatExpectation")
            if b.get("novel") == nid]
    assert len(exps) == out["beat_count"]        # no duplicates
    assert again["beat_count"] == out["beat_count"]


def test_anchor_beat_links_scene_and_coverage_reports_it() -> None:
    e = _fresh()
    iid = _iid(e)
    nid = _novel(e, iid)
    _invoke(e, iid, "apply_structure", novel_id=nid, template_id="three-act")
    sid = _scene(e, iid, nid, 1, "opening")
    out = _invoke(e, iid, "anchor_beat", novel_id=nid, beat_slug="hook",
                  scene_id=sid)
    assert out["anchored"] is True
    cov = _invoke(e, iid, "check_structure_coverage", novel_id=nid)
    assert cov["anchored"] == 1
    assert all(u["beat_slug"] != "hook" for u in cov["unanchored"])
    # FULFILS edge: Scene → BeatExpectation
    exp = next(b for b in e.memory.find("BeatExpectation")
               if b.get("novel") == nid and b.get("beat_slug") == "hook")
    linked = e.memory.neighbors(sid, "FULFILS", direction="out")
    assert any(n.get("id") == exp["id"] for n in linked)


def test_anchor_unknown_beat_is_typed_failure() -> None:
    e = _fresh()
    iid = _iid(e)
    nid = _novel(e, iid)
    _invoke(e, iid, "apply_structure", novel_id=nid, template_id="three-act")
    sid = _scene(e, iid, nid, 1, "s")
    out = _invoke(e, iid, "anchor_beat", novel_id=nid, beat_slug="nope",
                  scene_id=sid)
    assert out is None                            # typed NOT_FOUND failure


def test_switching_templates_preserves_shared_slug_anchors() -> None:
    """`apply_structure` is idempotent so switching templates preserves
    manuscript anchors that share beat slugs (spec §Design notes)."""
    e = _fresh()
    iid = _iid(e)
    nid = _novel(e, iid)
    _invoke(e, iid, "apply_structure", novel_id=nid, template_id="three-act")
    sid = _scene(e, iid, nid, 5, "mid")
    _invoke(e, iid, "anchor_beat", novel_id=nid, beat_slug="midpoint",
            scene_id=sid)
    out = _invoke(e, iid, "apply_structure", novel_id=nid,
                  template_id="save-the-cat")     # STC also has `midpoint`
    exps = [b for b in e.memory.find("BeatExpectation")
            if b.get("novel") == nid]
    assert len(exps) == out["beat_count"]         # one template's worth only
    mid = next(b for b in exps if b.get("beat_slug") == "midpoint")
    assert mid.get("scene_id") == sid             # anchor survived the switch
    assert mid.get("template_id") == "save-the-cat"


# ── position report ───────────────────────────────────────────────────────────

def test_structure_position_report_flags_out_of_position() -> None:
    e = _fresh()
    iid = _iid(e)
    nid = _novel(e, iid)
    for n in range(1, 11):                        # 10 body-less chapters
        _invoke(e, iid, "create_chapter", novel_id=nid, number=n,
                title=f"Ch {n}")
    _invoke(e, iid, "apply_structure", novel_id=nid, template_id="three-act")
    ch5_scene = _scene(e, iid, nid, 5, "mid")     # reuses chapter 5
    ch9_scene = _scene(e, iid, nid, 9, "late")
    _invoke(e, iid, "anchor_beat", novel_id=nid, beat_slug="midpoint",
            scene_id=ch5_scene)                   # target 0.5, actual ~0.45
    _invoke(e, iid, "anchor_beat", novel_id=nid,
            beat_slug="inciting-incident", scene_id=ch9_scene)  # target ~0.12
    rep = _invoke(e, iid, "structure_position_report", novel_id=nid)
    by_slug = {b["beat_slug"]: b for b in rep["beats"]}
    assert by_slug["midpoint"]["out_of_position"] is False
    assert by_slug["inciting-incident"]["out_of_position"] is True
    assert 0.0 <= by_slug["midpoint"]["actual_position"] <= 1.0


# ── coherence-check soft warning ──────────────────────────────────────────────

def test_drafting_without_structure_warns_softly() -> None:
    e = _fresh()
    iid = _iid(e)
    nid = _novel(e, iid)
    _invoke(e, iid, "create_chapter", novel_id=nid, number=1, title="Ch 1")
    _invoke(e, iid, "set_novel_status", novel_id=nid, status="drafting")
    out = _invoke(e, iid, "manuscript_coherence_check", novel_id=nid)
    assert out["passed"] is True                  # soft: never blocks
    assert any("structure" in w for w in out.get("warnings", []))
    _invoke(e, iid, "apply_structure", novel_id=nid, template_id="three-act")
    out2 = _invoke(e, iid, "manuscript_coherence_check", novel_id=nid)
    assert not out2.get("warnings")


# ── skill extension ───────────────────────────────────────────────────────────

def test_storyform_build_skill_gains_optional_template_pick_phase() -> None:
    from agency.capabilities.novel._main import STORYFORM_BUILD_SKILL
    last = STORYFORM_BUILD_SKILL["phases"][-1]
    assert "apply_structure" in " ".join(last.get("verbs", []))
    assert last.get("gate") != "hard"             # optional — never blocks


# ── overlay ───────────────────────────────────────────────────────────────────

def test_overlay_yaml_adds_a_custom_template(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".agency").mkdir()
    (tmp_path / ".agency" / "structure-templates-overlay.yaml").write_text(
        "templates:\n"
        "  - template_id: my-custom\n"
        "    name: My Custom\n"
        "    source: me\n"
        "    beats:\n"
        "      - {slug: start, name: Start, position: 0.0, prompt: 'Open?'}\n"
        "      - {slug: end, name: End, position: 0.9, prompt: 'Close?'}\n")
    e = Engine(str(tmp_path / "a.db"))
    out = _invoke(e, _iid(e), "list_structure_templates")
    ids = {t["template_id"] for t in out["templates"]}
    assert "my-custom" in ids
    e.memory.close()
