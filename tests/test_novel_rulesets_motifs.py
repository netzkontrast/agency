"""Spec 140 — project rule-sets & motif discipline.

Author-authored R-rules over four decidable predicate kinds; the per-scene
self-review checklist made executable; severity-tiered manuscript gate; the
motif echo-trail (max 1 per scene) and named foreshadowing anchors.
"""
from __future__ import annotations

import tempfile

from agency.engine import Engine


def _fresh() -> Engine:
    return Engine(tempfile.mktemp(suffix=".db"))


def _iid(e: Engine) -> str:
    iid = e.intent.capture("spec 140", "rulesets motifs", "verified")
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
    assert {"ProjectRule", "Motif", "Anchor"} <= set(cap.ontology.nodes)
    assert {"ECHOES_IN", "PLANTS", "PAYS_OFF"} <= cap.ontology.edges
    from agency.capabilities.novel.clusters.rulesets import (
        DEFECT_SEVERITY, PREDICATE_KIND)
    assert DEFECT_SEVERITY == {"critical", "medium", "low"}
    assert len(PREDICATE_KIND) == 4
    e.memory.close()


def test_register_upsert_and_list() -> None:
    e = _fresh()
    iid = _iid(e)
    nid = _novel(e, iid)
    r1 = _invoke(e, iid, "register_project_rule", novel_id=nid,
                 rule_id="R-5", name="hot-polarity", severity="critical",
                 predicate_kind="mutual-exclusion",
                 params={"set_a": ["cold ozone"], "set_b": ["warm skin"]})
    assert r1["was_update"] is False
    r2 = _invoke(e, iid, "register_project_rule", novel_id=nid,
                 rule_id="R-5", name="hot-polarity-v2", severity="critical",
                 predicate_kind="mutual-exclusion",
                 params={"set_a": ["cold ozone"], "set_b": ["warm skin"]})
    assert r2["was_update"] is True
    assert _invoke(e, iid, "register_project_rule", novel_id=nid,
                   rule_id="R-X", name="x", severity="nope",
                   predicate_kind="mutual-exclusion") is None
    lst = _invoke(e, iid, "list_project_rules", novel_id=nid)
    assert lst["count"] == 1 and lst["rules"][0]["name"] == "hot-polarity-v2"


def test_mutual_exclusion_and_forbidden_verbatim() -> None:
    e = _fresh()
    iid = _iid(e)
    nid = _novel(e, iid)
    _invoke(e, iid, "register_project_rule", novel_id=nid, rule_id="R-5",
            name="hot-polarity", severity="critical",
            predicate_kind="mutual-exclusion",
            params={"set_a": ["cold ozone"], "set_b": ["warm skin"]})
    _invoke(e, iid, "register_project_rule", novel_id=nid, rule_id="R-9",
            name="genesis-verbatim", severity="medium",
            predicate_kind="forbidden-verbatim",
            params={"phrases": ["the first hum of form"]})
    bad = _scene(e, iid, nid, 1,
                 "Cold ozone drifted over her warm skin as she recalled "
                 "the first hum of form.")
    out = _invoke(e, iid, "run_project_rules", scene_id=bad)
    assert out["passed"] is False
    ids = {f["rule_id"] for f in out["findings"]}
    assert ids == {"R-5", "R-9"}
    # critical sorts first
    assert out["findings"][0]["rule_id"] == "R-5"
    clean = _scene(e, iid, nid, 2, "Cold ozone hung in the hall alone.")
    assert _invoke(e, iid, "run_project_rules",
                   scene_id=clean)["passed"] is True


def test_register_forbidden_speaker_lines() -> None:
    e = _fresh()
    iid = _iid(e)
    nid = _novel(e, iid)
    _invoke(e, iid, "register_project_rule", novel_id=nid, rule_id="R-8",
            name="aegis-register", severity="critical",
            predicate_kind="register-forbidden",
            params={"speaker_tag": "AEGIS",
                    "forbidden_classes": ["ich-pronoun", "affect-word"],
                    "class_terms": {"ich-pronoun": ["ich"],
                                    "affect-word": ["fühlte"]}})
    bad = _scene(e, iid, nid, 1,
                 "AEGIS: Ich fühlte den Fehler kommen.\n"
                 "Kael: das war nie deine Sprache.")
    out = _invoke(e, iid, "run_project_rules", scene_id=bad)
    assert out["passed"] is False
    assert "AEGIS" in out["findings"][0]["message"]
    ok = _scene(e, iid, nid, 2,
                "AEGIS: Abweichung registriert. Korrektur folgt.\n"
                "Kael: Ich fühlte es trotzdem.")   # Kael may feel
    assert _invoke(e, iid, "run_project_rules", scene_id=ok)["passed"] is True


def test_project_rule_gate_severity_tiers() -> None:
    e = _fresh()
    iid = _iid(e)
    nid = _novel(e, iid)
    _invoke(e, iid, "register_project_rule", novel_id=nid, rule_id="R-9",
            name="verbatim", severity="medium",
            predicate_kind="forbidden-verbatim",
            params={"phrases": ["marker"]})
    _scene(e, iid, nid, 1, "the marker was visible")
    gate = _invoke(e, iid, "project_rule_gate", novel_id=nid)
    assert gate["passed"] is True                # medium only warns
    assert gate["warnings"]
    gate2 = _invoke(e, iid, "project_rule_gate", novel_id=nid,
                    block_at="medium")
    assert gate2["passed"] is False              # threshold lowered


def test_motif_echo_budget_and_trail() -> None:
    e = _fresh()
    iid = _iid(e)
    nid = _novel(e, iid)
    s1 = _scene(e, iid, nid, 2, "the noise rose")
    s2 = _scene(e, iid, nid, 9, "the noise returned")
    _invoke(e, iid, "record_motif_echo", scene_id=s1, motif_slug="rauschen")
    _invoke(e, iid, "record_motif_echo", scene_id=s2, motif_slug="rauschen")
    _invoke(e, iid, "record_motif_echo", scene_id=s2, motif_slug="klick")
    rep = _invoke(e, iid, "motif_echo_report", novel_id=nid)
    assert rep["trails"]["rauschen"] == [2, 9]
    assert any(o["scene_id"] == s2 and o["count"] == 2
               for o in rep["over_cap"])         # 2 echoes in s2 > cap 1
    # motif-edge budget rule composes with the tracker
    _invoke(e, iid, "register_project_rule", novel_id=nid, rule_id="R-7",
            name="genesis-echo-budget", severity="medium",
            predicate_kind="per-scene-budget",
            params={"tag": "genesis-echo", "cap": 1,
                    "count_kind": "motif-edge"})
    out = _invoke(e, iid, "run_project_rules", scene_id=s2)
    assert any(f["rule_id"] == "R-7" for f in out["findings"])


def test_anchor_plant_payoff_audit() -> None:
    e = _fresh()
    iid = _iid(e)
    nid = _novel(e, iid)
    s2 = _scene(e, iid, nid, 2, "the number 734 on the door")
    s25 = _scene(e, iid, nid, 25, "room 734 opened at last")
    _invoke(e, iid, "plant_anchor", scene_id=s2, name="734")
    _invoke(e, iid, "plant_anchor", scene_id=s2, name="Telefon-Stille")
    rep = _invoke(e, iid, "anchor_status_report", novel_id=nid)
    assert rep["open_count"] == 2
    _invoke(e, iid, "pay_off_anchor", scene_id=s25, name="734")
    rep2 = _invoke(e, iid, "anchor_status_report", novel_id=nid)
    assert rep2["open_count"] == 1
    paid = next(a for a in rep2["anchors"] if a["name"] == "734")
    assert paid["payoff_chapter"] == 25 and paid["open"] is False
    assert _invoke(e, iid, "pay_off_anchor", scene_id=s25,
                   name="never-planted") is None
