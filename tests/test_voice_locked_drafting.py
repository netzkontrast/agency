"""Spec 144 — voice-locked drafting prompt.

One composer bakes an alter's Sprach-DNA into a §-structured drafting brief;
the co-front guard refuses max-phobia pairs; exemplars rotate deterministically;
the post-draft drift audit closes the loop (leaked-other-alter defensive check).
"""
from __future__ import annotations

import tempfile

from agency.engine import Engine


def _fresh() -> Engine:
    return Engine(tempfile.mktemp(suffix=".db"))


def _iid(e: Engine) -> str:
    iid = e.intent.capture("spec 144", "voice lock", "verified")
    e.intent.confirm(iid)
    return iid


def _invoke(e, iid, cap, verb, **kw):
    r, _ = e.registry.invoke(e.memory, iid, cap, verb, **kw)
    return r


def _stack(e, iid):
    nid = _invoke(e, iid, "novel", "create_novel", title="KP",
                  author="A")["novel_id"]
    sys_id = _invoke(e, iid, "novel", "create_character_system",
                     novel_id=nid, name="Kael")["system_id"]
    lex = _invoke(e, iid, "novel", "add_alter", system_id=sys_id,
                  name="Lex", category="anp", layer="layer-1",
                  function="Rationalist",
                  taboo_rules="gonna")["alter_id"]
    nyx = _invoke(e, iid, "novel", "add_alter", system_id=sys_id,
                  name="Nyx", category="ep", layer="layer-2",
                  function="Fight")["alter_id"]
    _invoke(e, iid, "novel", "create_voice_profile", character_id=lex,
            sentence_avg_target=12.0, sentence_avg_stddev=2.0,
            signature_phrases="in all consequence")
    _invoke(e, iid, "novel", "update_voice_profile", character_id=lex,
            sentence_shape="long, subordinate-clause chains",
            vocabulary_preferred="protocol, verify, consequence",
            vocabulary_forbidden="vibe, gut-feeling",
            example_sentences="In all consequence, the ledger holds; "
                              "Verification precedes belief; "
                              "The protocol answers before I do; "
                              "Numbers do not tremble")
    ch = _invoke(e, iid, "novel", "create_chapter", novel_id=nid, number=2,
                 title="Ch 2")["chapter_id"]
    sid = _invoke(e, iid, "novel", "create_scene", chapter_id=ch, slug="s",
                  pov="first", pov_character_id=lex)["scene_id"]
    return nid, sys_id, lex, nyx, sid


def test_compose_brief_structure_and_taboo_block() -> None:
    e = _fresh()
    iid = _iid(e)
    _, _, lex, _, sid = _stack(e, iid)
    out = _invoke(e, iid, "prompt", "compose_voice_locked_brief",
                  scene_id=sid, alter_id=lex)
    brief = out["brief"]
    for marker in ("§VOICE-LOCK: Lex", "§SYNTAX:", "§TABOO (HARD): gonna",
                   "§EXAMPLES:", "§INSTRUCTION:"):
        assert marker in brief, marker
    assert "long, subordinate-clause chains" in brief
    assert out["artefact_id"]
    assert e.memory.recall(out["artefact_id"]).get("kind") == \
        "voice-locked-brief"


def test_cofront_guard_refuses_max_pair() -> None:
    e = _fresh()
    iid = _iid(e)
    _, _, lex, nyx, sid = _stack(e, iid)
    _invoke(e, iid, "novel", "record_alter_conflict", alter_a=lex,
            alter_b=nyx, vector="anp-ep", intensity="max")
    e.memory.update(sid, {"cast": f"{lex},{nyx}"})
    out = _invoke(e, iid, "prompt", "compose_voice_locked_brief",
                  scene_id=sid, alter_id=lex)
    assert out["refused"] is True and out["reason"] == "max-pair-cofront"
    assert sorted(out["pair"]) == sorted([lex, nyx])
    forced = _invoke(e, iid, "prompt", "compose_voice_locked_brief",
                     scene_id=sid, alter_id=lex, allow_max_pair=True)
    assert "brief" in forced                      # explicit override works


def test_exemplar_pool_rotates_deterministically() -> None:
    e = _fresh()
    iid = _iid(e)
    _, _, lex, _, _ = _stack(e, iid)
    a = _invoke(e, iid, "prompt", "exemplar_pool", alter_id=lex, n=3)
    b = _invoke(e, iid, "prompt", "exemplar_pool", alter_id=lex, n=3)
    assert a["pool_size"] == 4 and len(a["examples"]) == 3
    assert a["examples"] == b["examples"]         # same intent → same slice
    iid2 = _iid(e)
    c = _invoke(e, iid2, "prompt", "exemplar_pool", alter_id=lex, n=3)
    assert c["pool_size"] == 4                    # rotation varies by intent


def test_truncation_drops_examples_never_taboo() -> None:
    e = _fresh()
    iid = _iid(e)
    _, _, lex, _, sid = _stack(e, iid)
    out = _invoke(e, iid, "prompt", "compose_voice_locked_brief",
                  scene_id=sid, alter_id=lex, max_tokens=60)
    assert "examples" not in out["sections"]
    assert "taboo" in out["sections"]             # never truncated


def test_voice_drift_audit_verdicts() -> None:
    e = _fresh()
    iid = _iid(e)
    _, _, lex, nyx, sid = _stack(e, iid)
    good = ("In all consequence, the committee reached a considered "
            "verdict at last. The protocol had answered the question "
            "before any of us spoke. Verification, as always in this "
            "house, preceded every stated belief.")
    _invoke(e, iid, "novel", "integrate_scene_body", scene_id=sid, body=good)
    ok = _invoke(e, iid, "prompt", "voice_drift_audit", scene_id=sid)
    assert ok["verdict"] == "in-voice" and ok["passed"] is True
    assert ok["signature_phrase_presence"] is True
    bad = "Gut-feeling says run. I'm gonna trust the vibe."
    _invoke(e, iid, "novel", "integrate_scene_body", scene_id=sid, body=bad)
    drift = _invoke(e, iid, "prompt", "voice_drift_audit", scene_id=sid)
    assert drift["verdict"] in ("drifted", "leaked-other-alter")
    assert "vibe" in drift["forbidden_lexicon_hits"]
    assert any(v["rule"] == "gonna" for v in drift["taboo_violations"])
