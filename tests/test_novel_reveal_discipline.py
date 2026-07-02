"""Spec 139 — reveal-discipline & reader-steering.

Three independent audience tiers (reader/POV/antagonist) carry RevealRules;
premature reveals fire on the tier floor; the multiplicity-veil holds until
its chapter; deliberate Iser-Leerstellen are first-class; the composite
reveal_gate is the pre-publication discipline.
"""
from __future__ import annotations

import tempfile

from agency.engine import Engine


def _fresh() -> Engine:
    return Engine(tempfile.mktemp(suffix=".db"))


def _iid(e: Engine) -> str:
    iid = e.intent.capture("spec 139", "reveal discipline", "verified")
    e.intent.confirm(iid)
    return iid


def _invoke(e: Engine, iid: str, verb: str, **kw):
    r, _ = e.registry.invoke(e.memory, iid, "novel", verb, **kw)
    return r


def _novel(e, iid):
    return _invoke(e, iid, "create_novel", title="KP",
                   author="A")["novel_id"]


def _scene(e, iid, nid, number, body):
    ch = _invoke(e, iid, "create_chapter", novel_id=nid, number=number,
                 title=f"Ch {number}")["chapter_id"]
    sid = _invoke(e, iid, "create_scene", chapter_id=ch, slug=f"s{number}",
                  pov="first")["scene_id"]
    _invoke(e, iid, "integrate_scene_body", scene_id=sid, body=body)
    return sid


def test_nodes_edges_enums_registered() -> None:
    e = _fresh()
    cap = e.registry.get("novel")
    assert {"RevealRule", "Leerstelle"} <= set(cap.ontology.nodes)
    assert {"GOVERNS_REVEAL", "HAS_GAP"} <= cap.ontology.edges
    from agency.capabilities.novel.clusters.reveal import (
        AUDIENCE_TIER, LEERSTELLE_KIND, READER_LAYER)
    assert AUDIENCE_TIER == {"reader", "pov", "antagonist"}
    assert len(LEERSTELLE_KIND) == 4 and len(READER_LAYER) == 3
    e.memory.close()


def test_set_reveal_rule_upsert_and_enum_validation() -> None:
    e = _fresh()
    iid = _iid(e)
    nid = _novel(e, iid)
    r1 = _invoke(e, iid, "set_reveal_rule", novel_id=nid,
                 fact="kael-is-a-system", tier="reader",
                 may_know_from_chapter=13, channel="glitch")
    assert r1["was_update"] is False
    r2 = _invoke(e, iid, "set_reveal_rule", novel_id=nid,
                 fact="kael-is-a-system", tier="reader",
                 may_know_from_chapter=14)
    assert r2["was_update"] is True and r2["rule_id"] == r1["rule_id"]
    assert _invoke(e, iid, "set_reveal_rule", novel_id=nid, fact="x",
                   tier="nope", may_know_from_chapter=1) is None


def test_check_reveal_timing_premature_and_clean() -> None:
    e = _fresh()
    iid = _iid(e)
    nid = _novel(e, iid)
    _invoke(e, iid, "set_reveal_rule", novel_id=nid, fact="phoenix collapse",
            tier="reader", may_know_from_chapter=10, must_not_before=8)
    early = _scene(e, iid, nid, 3, "She whispered of the phoenix collapse.")
    out = _invoke(e, iid, "check_reveal_timing", scene_id=early,
                  fact="phoenix collapse")
    assert out["ok"] is False
    assert out["violations"][0]["verdict"] == "premature-reveal"
    late = _scene(e, iid, nid, 12, "The phoenix collapse was public now.")
    assert _invoke(e, iid, "check_reveal_timing", scene_id=late,
                   fact="phoenix collapse")["ok"] is True
    # fact absent from body → no leak, ok
    silent = _scene(e, iid, nid, 2, "Nothing of note happened.")
    assert _invoke(e, iid, "check_reveal_timing", scene_id=silent,
                   fact="phoenix collapse")["ok"] is True
    # no rule → ok with no_rule flag
    norule = _invoke(e, iid, "check_reveal_timing", scene_id=silent,
                     fact="unruled")
    assert norule["ok"] is True and norule["no_rule"] is True


def test_reveal_timeline_report_sorted_and_tier_filtered() -> None:
    e = _fresh()
    iid = _iid(e)
    nid = _novel(e, iid)
    _invoke(e, iid, "set_reveal_rule", novel_id=nid, fact="b", tier="pov",
            may_know_from_chapter=20)
    _invoke(e, iid, "set_reveal_rule", novel_id=nid, fact="a", tier="reader",
            may_know_from_chapter=5)
    rep = _invoke(e, iid, "reveal_timeline_report", novel_id=nid)
    chapters = [r["may_know_from_chapter"] for r in rep["timeline"]]
    assert chapters == sorted(chapters)
    assert rep["by_tier"] == {"reader": 1, "pov": 1}
    only = _invoke(e, iid, "reveal_timeline_report", novel_id=nid,
                   tier="pov")
    assert len(only["timeline"]) == 1


def test_check_veil_breach_and_hold() -> None:
    e = _fresh()
    iid = _iid(e)
    nid = _novel(e, iid)
    _scene(e, iid, nid, 4, "The chart said TSDP in red letters.")
    _scene(e, iid, nid, 15, "The chart said TSDP in red letters.")
    out = _invoke(e, iid, "check_veil", novel_id=nid,
                  hold_until_chapter=13)
    assert out["passed"] is False
    assert [b["chapter"] for b in out["breaches"]] == [4]   # ch15 is fine


def test_leerstelle_registration_and_report() -> None:
    e = _fresh()
    iid = _iid(e)
    nid = _novel(e, iid)
    sid = _scene(e, iid, nid, 7, "The footnote contradicted the page.")
    out = _invoke(e, iid, "record_leerstelle", scene_id=sid,
                  kind="contradictory-footnote", note="intentional")
    assert out["leerstelle_id"]
    assert _invoke(e, iid, "record_leerstelle", scene_id=sid,
                   kind="nope") is None
    rep = _invoke(e, iid, "leerstellen_report", novel_id=nid)
    assert rep["count"] == 1
    assert rep["by_kind"]["contradictory-footnote"] == 1


def test_reader_function_audit_layers() -> None:
    e = _fresh()
    iid = _iid(e)
    nid = _novel(e, iid)
    rich = _scene(e, iid, nid, 2,
                  "[log 03:14] The salt smell stung. Who had sent it? …")
    out = _invoke(e, iid, "reader_function_audit", scene_id=rich)
    assert set(out["layers"]) == {"narratological", "phenomenological",
                                  "operative"}
    flat = _scene(e, iid, nid, 3, "He walked to the door and left.")
    out2 = _invoke(e, iid, "reader_function_audit", scene_id=flat)
    assert out2["layers"] == []


def test_reveal_gate_composite() -> None:
    e = _fresh()
    iid = _iid(e)
    nid = _novel(e, iid)
    _invoke(e, iid, "set_reveal_rule", novel_id=nid, fact="phoenix",
            tier="reader", may_know_from_chapter=10)
    _scene(e, iid, nid, 2, "The phoenix waited under the ash.")
    bad = _invoke(e, iid, "reveal_gate", novel_id=nid)
    assert bad["passed"] is False
    assert bad["timing_violations"]
