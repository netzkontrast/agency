"""Spec 134 — POV voice profiles (per-character voice signature).

``VoiceProfile`` node + ``VOICE_OF`` edge; create/update/get; a deviation-based
0–100 ``score_voice_match``; per-scene ``check_pov_voice`` against the scene's
``pov_character_id``; a manuscript ``voice_drift_report`` + composite
``voice_drift_gate``. Voice drift is SOFT — the gate is opt-in, taboo words are
the one hard violation (OQ3).
"""
from __future__ import annotations

import tempfile

from agency.engine import Engine


def _fresh() -> Engine:
    return Engine(tempfile.mktemp(suffix=".db"))


def _iid(e: Engine) -> str:
    iid = e.intent.capture("spec 134", "voice profiles", "verified")
    e.intent.confirm(iid)
    return iid


def _invoke(e: Engine, iid: str, verb: str, **kw):
    r, _ = e.registry.invoke(e.memory, iid, "novel", verb, **kw)
    return r


def _setup(e: Engine, iid: str):
    nid = _invoke(e, iid, "create_novel", title="K", author="A")["novel_id"]
    ch = _invoke(e, iid, "create_chapter", novel_id=nid, number=1,
                 title="Ch 1")["chapter_id"]
    char = _invoke(e, iid, "create_codex_entry", novel_id=nid, slug="eliza",
                   name="Eliza", kind="minor-character", body="Eliza, POV heroine")["entry_id"]
    return nid, ch, char


def _scene_with_body(e, iid, ch, char, slug, body):
    sid = _invoke(e, iid, "create_scene", chapter_id=ch, slug=slug,
                  pov="third-limited",
                  pov_character_id=char)["scene_id"]
    _invoke(e, iid, "integrate_scene_body", scene_id=sid, body=body)
    return sid


_ELIZA = ("She could not agree. The garden lay quiet under the rain. "
          "She watched the gate and waited for the bell. "
          "The letters sat unread upon the desk.")


# ── ontology ──────────────────────────────────────────────────────────────────

def test_ontology_declares_voice_profile_and_voice_of() -> None:
    e = _fresh()
    cap = e.registry.get("novel")
    assert "VoiceProfile" in cap.ontology.nodes
    assert "VOICE_OF" in cap.ontology.edges
    e.memory.close()


# ── create / get / update ─────────────────────────────────────────────────────

def test_create_get_update_roundtrip() -> None:
    e = _fresh()
    iid = _iid(e)
    _, _, char = _setup(e, iid)
    out = _invoke(e, iid, "create_voice_profile", character_id=char,
                  sentence_avg_target=9.0, sentence_avg_stddev=3.0,
                  taboo_words="can't,gonna", formality_target="high",
                  contractions=False)
    assert out["profile_id"]
    got = _invoke(e, iid, "get_voice_profile", character_id=char)
    assert got["taboo_words"] == "can't,gonna"
    assert got["contractions"] is False
    # VOICE_OF edge → character
    linked = e.memory.neighbors(out["profile_id"], "VOICE_OF", direction="out")
    assert any(n.get("id") == char for n in linked)
    # partial update; second create overwrites, never duplicates
    _invoke(e, iid, "update_voice_profile", character_id=char,
            taboo_words="gonna")
    got2 = _invoke(e, iid, "get_voice_profile", character_id=char)
    assert got2["taboo_words"] == "gonna"
    assert got2["formality_target"] == "high"     # untouched field survives
    profiles = [p for p in e.memory.find("VoiceProfile")
                if p.get("character") == char]
    assert len(profiles) == 1


def test_get_missing_profile_is_typed_failure() -> None:
    e = _fresh()
    iid = _iid(e)
    _, _, char = _setup(e, iid)
    assert _invoke(e, iid, "get_voice_profile", character_id=char) is None


# ── scoring ───────────────────────────────────────────────────────────────────

def test_score_voice_match_high_for_matching_prose() -> None:
    e = _fresh()
    iid = _iid(e)
    _, _, char = _setup(e, iid)
    _invoke(e, iid, "create_voice_profile", character_id=char,
            sentence_avg_target=9.0, sentence_avg_stddev=4.0,
            taboo_words="gonna", contractions=False)
    out = _invoke(e, iid, "score_voice_match", character_id=char, body=_ELIZA)
    assert out["score"] >= 70
    assert isinstance(out["deviations"], list)


def test_taboo_word_is_a_hard_violation() -> None:
    e = _fresh()
    iid = _iid(e)
    _, _, char = _setup(e, iid)
    _invoke(e, iid, "create_voice_profile", character_id=char,
            sentence_avg_target=9.0, sentence_avg_stddev=4.0,
            taboo_words="gonna", contractions=False)
    bad = _ELIZA + " I'm gonna leave now."
    out = _invoke(e, iid, "score_voice_match", character_id=char, body=bad)
    clean = _invoke(e, iid, "score_voice_match", character_id=char,
                    body=_ELIZA)
    assert out["score"] < clean["score"]
    assert any(d["field"] == "taboo_words" for d in out["deviations"])
    assert any(d["field"] == "contractions" for d in out["deviations"])


# ── per-scene gate + manuscript report ────────────────────────────────────────

def test_check_pov_voice_passes_matching_scene() -> None:
    e = _fresh()
    iid = _iid(e)
    _, ch, char = _setup(e, iid)
    _invoke(e, iid, "create_voice_profile", character_id=char,
            sentence_avg_target=9.0, sentence_avg_stddev=4.0)
    sid = _scene_with_body(e, iid, ch, char, "s1", _ELIZA)
    out = _invoke(e, iid, "check_pov_voice", scene_id=sid)
    assert out["passed"] is True and out["score"] >= 70


def test_check_pov_voice_without_profile_is_typed_failure() -> None:
    e = _fresh()
    iid = _iid(e)
    _, ch, char = _setup(e, iid)
    sid = _scene_with_body(e, iid, ch, char, "s1", _ELIZA)
    assert _invoke(e, iid, "check_pov_voice", scene_id=sid) is None


def test_voice_drift_gate_and_report() -> None:
    e = _fresh()
    iid = _iid(e)
    nid, ch, char = _setup(e, iid)
    _invoke(e, iid, "create_voice_profile", character_id=char,
            sentence_avg_target=9.0, sentence_avg_stddev=4.0,
            taboo_words="gonna", contractions=False)
    _scene_with_body(e, iid, ch, char, "good", _ELIZA)
    gate = _invoke(e, iid, "voice_drift_gate", novel_id=nid)
    assert gate["passed"] is True
    bad = _scene_with_body(e, iid, ch, char, "bad",
                           "I'm gonna go. Gonna run, gonna hide, y'know.")
    gate2 = _invoke(e, iid, "voice_drift_gate", novel_id=nid)
    assert gate2["passed"] is False
    assert any(f["scene_id"] == bad for f in gate2["failing"])
    rep = _invoke(e, iid, "voice_drift_report", novel_id=nid)
    assert char in rep["by_character"]
    assert len(rep["by_character"][char]) == 2
    scores = [s["score"] for s in rep["by_character"][char]]
    assert scores == sorted(scores)               # worst-first ordering


# ── auto-derivation (rule 8: computed defaults, not snapshots) ────────────────

def test_sentence_target_auto_derived_from_five_scenes() -> None:
    e = _fresh()
    iid = _iid(e)
    _, ch, char = _setup(e, iid)
    for i in range(5):
        _scene_with_body(e, iid, ch, char, f"s{i}", _ELIZA)
    out = _invoke(e, iid, "create_voice_profile", character_id=char)
    got = _invoke(e, iid, "get_voice_profile", character_id=char)
    assert out["derived_from_scenes"] == 5
    assert float(got["sentence_avg_target"]) > 0


def test_no_auto_derivation_below_five_scenes() -> None:
    e = _fresh()
    iid = _iid(e)
    _, ch, char = _setup(e, iid)
    _scene_with_body(e, iid, ch, char, "s0", _ELIZA)
    out = _invoke(e, iid, "create_voice_profile", character_id=char)
    assert out["derived_from_scenes"] == 0


# ── skill extension ───────────────────────────────────────────────────────────

def test_scene_writer_check_phase_includes_pov_voice() -> None:
    from agency.capabilities.novel._main import SCENE_WRITER_SKILL
    check = next(p for p in SCENE_WRITER_SKILL["phases"]
                 if p["name"] == "check")
    assert "novel.check_pov_voice" in check["verbs"]
