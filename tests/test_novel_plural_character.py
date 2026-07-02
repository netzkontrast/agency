"""Spec 138 — plural-character system (dissociative-system model).

``CharacterSystem`` + ``Alter`` roster (ANP/EP/special/mirror × trauma layers),
the typed ``PHOBIA_OF`` conflict matrix with max-pair co-front warnings, per-
alter voice binding (``VOICED_BY`` → Spec 134), the "recognized, never labeled"
scene discipline incl. the Akt-I veil, a switching log inferred from voice
signatures, and the no-fusion resolution invariant (the end-state is a plural
"Wir", never a merged self).
"""
from __future__ import annotations

import tempfile

from agency.engine import Engine


def _fresh() -> Engine:
    return Engine(tempfile.mktemp(suffix=".db"))


def _iid(e: Engine) -> str:
    iid = e.intent.capture("spec 138", "plural system", "verified")
    e.intent.confirm(iid)
    return iid


def _invoke(e: Engine, iid: str, verb: str, **kw):
    r, _ = e.registry.invoke(e.memory, iid, "novel", verb, **kw)
    return r


def _system(e, iid):
    nid = _invoke(e, iid, "create_novel", title="KP", author="A")["novel_id"]
    sys_id = _invoke(e, iid, "create_character_system", novel_id=nid,
                     name="Kael", model="TSDP")["system_id"]
    lex = _invoke(e, iid, "add_alter", system_id=sys_id, name="Lex",
                  category="anp", layer="layer-1",
                  function="Rationalist")["alter_id"]
    nyx = _invoke(e, iid, "add_alter", system_id=sys_id, name="Nyx",
                  category="ep", layer="layer-2", function="Fight",
                  taboo_rules="cutesy,uwu")["alter_id"]
    return nid, sys_id, lex, nyx


def test_nodes_edges_enums_registered() -> None:
    e = _fresh()
    cap = e.registry.get("novel")
    assert {"CharacterSystem", "Alter"} <= set(cap.ontology.nodes)
    assert {"ALTER_OF", "PHOBIA_OF", "VOICED_BY", "MIRRORS"} \
        <= cap.ontology.edges
    from agency.capabilities.novel.clusters.plural import (
        ALTER_CATEGORY, PHOBIA_INTENSITY, PHOBIA_VECTOR, TRAUMA_LAYER)
    assert ALTER_CATEGORY == {"anp", "ep", "special", "mirror"}
    assert TRAUMA_LAYER == {"layer-1", "layer-2", "cross-layer"}
    assert PHOBIA_VECTOR == {"anp-ep", "anp-anp", "ep-ep", "mirror"}
    assert PHOBIA_INTENSITY == {"max", "phobic-avoidance", "friction",
                                "ambivalent"}
    e.memory.close()


def test_roster_with_enum_validation_and_duplicate_name() -> None:
    e = _fresh()
    iid = _iid(e)
    _, sys_id, lex, _ = _system(e, iid)
    assert e.memory.recall(lex).get("category") == "anp"
    members = e.memory.neighbors(sys_id, "ALTER_OF", direction="in")
    assert len(members) == 2
    assert _invoke(e, iid, "add_alter", system_id=sys_id, name="X",
                   category="nope", layer="layer-1") is None
    assert _invoke(e, iid, "add_alter", system_id=sys_id, name="Lex",
                   category="ep", layer="layer-2") is None   # duplicate


def test_conflict_matrix_and_max_pairs() -> None:
    e = _fresh()
    iid = _iid(e)
    _, sys_id, lex, nyx = _system(e, iid)
    out = _invoke(e, iid, "record_alter_conflict", alter_a=lex, alter_b=nyx,
                  vector="anp-ep", intensity="max",
                  rationale="Nyx destabilizes Lex's control")
    assert out["vector"] == "anp-ep"
    assert _invoke(e, iid, "record_alter_conflict", alter_a=lex, alter_b=lex,
                   vector="anp-anp", intensity="friction") is None  # a==b
    rep = _invoke(e, iid, "conflict_matrix_report", system_id=sys_id)
    assert rep["by_vector"]["anp-ep"] == 1
    assert (lex, nyx) in [tuple(p) for p in rep["max_pairs"]]
    assert len(rep["alters"]) == 2


def test_assign_voice_rebind_replaces() -> None:
    e = _fresh()
    iid = _iid(e)
    _, _, lex, _ = _system(e, iid)
    v1 = _invoke(e, iid, "create_voice_profile", character_id=lex,
                 sentence_avg_target=8.0,
                 sentence_avg_stddev=3.0)["profile_id"]
    out = _invoke(e, iid, "assign_voice_to_alter", alter_id=lex,
                  voice_profile_id=v1)
    assert out["replaced_voice"] == ""
    # a second profile node for the rebind case
    v2 = e.memory.record("VoiceProfile", {"character": "other"})
    out2 = _invoke(e, iid, "assign_voice_to_alter", alter_id=lex,
                   voice_profile_id=v2)
    assert out2["replaced_voice"] == v1
    # keep-both: the property carries the CURRENT binding; edges are history
    assert e.memory.recall(lex).get("voice_profile_id") == v2
    voiced = e.memory.neighbors(lex, "VOICED_BY", direction="out")
    assert v2 in [n["id"] for n in voiced]


def _scene(e, iid, nid, number, body):
    ch = _invoke(e, iid, "create_chapter", novel_id=nid, number=number,
                 title=f"Ch {number}")["chapter_id"]
    sid = _invoke(e, iid, "create_scene", chapter_id=ch, slug=f"s{number}",
                  pov="first")["scene_id"]
    _invoke(e, iid, "integrate_scene_body", scene_id=sid, body=body)
    return sid


def test_alter_recognition_headers_and_veil() -> None:
    e = _fresh()
    iid = _iid(e)
    nid, sys_id, _, _ = _system(e, iid)
    bad = _scene(e, iid, nid, 3, "[Nyx]: the walls breathe.\n"
                                 "Lex spricht: no, they do not.")
    out = _invoke(e, iid, "check_alter_recognition", scene_id=bad)
    assert out["passed"] is False
    assert any(v["kind"] == "header" for v in out["violations"])
    veil = _scene(e, iid, nid, 5, "The clinician wrote DID on the chart.")
    out2 = _invoke(e, iid, "check_alter_recognition", scene_id=veil,
                   veil_chapter=13)
    assert out2["veil_active"] is True
    assert any(v["kind"] == "veil" for v in out2["violations"])
    # after the veil chapter, the same term is allowed
    late = _scene(e, iid, nid, 20, "The clinician wrote DID on the chart.")
    out3 = _invoke(e, iid, "check_alter_recognition", scene_id=late,
                   veil_chapter=13)
    assert out3["passed"] is True and out3["veil_active"] is False


def test_switching_log_infers_fronting_alter() -> None:
    e = _fresh()
    iid = _iid(e)
    nid, sys_id, lex, nyx = _system(e, iid)
    vlex = _invoke(e, iid, "create_voice_profile", character_id=lex,
                   sentence_avg_target=12.0, sentence_avg_stddev=2.0,
                   signature_phrases="in all consequence")["profile_id"]
    vnyx = _invoke(e, iid, "create_voice_profile", character_id=nyx,
                   sentence_avg_target=3.0, sentence_avg_stddev=1.0,
                   signature_phrases="burn it")["profile_id"]
    _invoke(e, iid, "assign_voice_to_alter", alter_id=lex,
            voice_profile_id=vlex)
    _invoke(e, iid, "assign_voice_to_alter", alter_id=nyx,
            voice_profile_id=vnyx)
    _scene(e, iid, nid, 1,
           "In all consequence the committee deliberated through the long "
           "afternoon and reached in the end a considered verdict of note.")
    log = _invoke(e, iid, "switching_log", system_id=sys_id, novel_id=nid)
    assert log["summary"]["total_scenes"] == 1
    assert log["scenes"][0]["inferred_alter"] == lex


def test_validate_no_fusion() -> None:
    e = _fresh()
    iid = _iid(e)
    _, sys_id, lex, nyx = _system(e, iid)
    ok = _invoke(e, iid, "validate_no_fusion", system_id=sys_id)
    assert ok["passed"] is True
    e.memory.update(nyx, {"status": "fused"})
    bad = _invoke(e, iid, "validate_no_fusion", system_id=sys_id)
    assert bad["passed"] is False
    assert any(v["alter_id"] == nyx for v in bad["violations"])


def test_alter_taboo_rules_extend_pov_voice_check() -> None:
    """Spec 138 anti-cliché layer: Alter.taboo_rules matches are HARD
    violations in Spec 134's check_pov_voice."""
    e = _fresh()
    iid = _iid(e)
    nid, sys_id, lex, nyx = _system(e, iid)   # nyx taboo: cutesy,uwu
    v = _invoke(e, iid, "create_voice_profile", character_id=nyx,
                sentence_avg_target=6.0, sentence_avg_stddev=3.0)
    ch = _invoke(e, iid, "create_chapter", novel_id=nid, number=1,
                 title="Ch")["chapter_id"]
    sid = _invoke(e, iid, "create_scene", chapter_id=ch, slug="s",
                  pov="first", pov_character_id=nyx)["scene_id"]
    _invoke(e, iid, "integrate_scene_body", scene_id=sid,
            body="That is so cutesy. She smiled uwu at the wreckage.")
    out = _invoke(e, iid, "check_pov_voice", scene_id=sid)
    assert any(d["field"] == "alter_taboo_rules" and d["severity"] == "hard"
               for d in out["deviations"])
