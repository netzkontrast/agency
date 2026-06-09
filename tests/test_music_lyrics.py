"""music lyrics cluster — Spec 095 verb + skill coverage.

13 new transforms + 4 composite gate verbs + the ``lyric-writing`` walkable
skill. All deterministic, driver-free in principle (TextDriver routing for
swappable backends); CI runs full coverage in milliseconds.

Skill walk asserts the 6-phase computed-gate → hard-elicit pattern from
Spec 095 Done When line 52-54.
"""
from __future__ import annotations

import tempfile

from agency.capabilities.music.drivers import fake_drivers
from agency.engine import Engine
from agency.skill import SkillRun


def _fresh() -> Engine:
    return Engine(tempfile.mktemp(suffix=".db"), drivers=fake_drivers())


def _confirmed_iid(e: Engine, purpose: str = "lyrics") -> str:
    iid = e.intent.capture(purpose, "deliverable", "acceptance")
    e.intent.confirm(iid)
    return iid


def _invoke(e: Engine, iid: str, verb: str, **kw):
    return e.registry.invoke(e.memory, iid, "music", verb, **kw)


_BLOCK_LYRICS = """[Verse 1]
The phreaker dialed a modem at night
Routing through the synth and the wire
A blue box echo in the chrome
She read the lead and made it home

[Chorus]
We're stronger than the tide
We're deeper than the night
""".strip()


def test_lyrics_cluster_verbs_discover() -> None:
    e = _fresh()
    verbs = e.registry._caps["music"].verbs
    for v in ("analyze_rhyme_scheme", "analyze_readability",
              "check_pronunciation", "check_homographs",
              "check_streaming_lyrics", "check_cross_track_repetition",
              "check_explicit_content", "extract_distinctive_phrases",
              "extract_section", "validate_section_structure",
              "scan_artist_names", "check_voice_tells",
              "check_name_exposure",
              "prosody_gate", "pronunciation_gate",
              "repetition_gate", "explicit_gate", "name_exposure_gate"):
        assert v in verbs, f"verb {v!r} not registered on music capability"
    e.memory.close()


def test_lyric_writing_skill_is_owned_and_six_phased() -> None:
    e = _fresh()
    sk = e.ontology.skill("lyric-writing")
    assert sk["kind"] == "workflow"
    assert len(sk["phases"]) == 6
    assert sk["phases"][-1].get("gate") == "hard"
    # Computed gates at 2/3/4/5; hard at 6
    for i, exp in enumerate(("draft", "prosody", "pronunciation",
                              "cross-track", "explicit", "finalize")):
        assert sk["phases"][i]["name"] == exp
    e.memory.close()


def test_analyze_rhyme_scheme_returns_groups_and_self_rhymes() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    data, _ = _invoke(e, iid, "analyze_rhyme_scheme",
                      lyrics="The cat sat\nOn the mat\nThe dog ran")
    assert "scheme" in data
    assert data["groups"] >= 1
    e.memory.close()


def test_analyze_readability_returns_grade_level() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    data, _ = _invoke(e, iid, "analyze_readability", text_=_BLOCK_LYRICS)
    assert "grade_level" in data
    assert data["avg_words_per_sentence"] > 0
    e.memory.close()


def test_check_pronunciation_flags_known_word() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    data, _ = _invoke(e, iid, "check_pronunciation",
                      lyrics="The phreaker dialed a modem at night")
    assert data["count"] >= 1
    flagged = {f["word"] for f in data["findings"]}
    assert "phreaker" in flagged
    e.memory.close()


def test_check_homographs_flags_lead() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    data, _ = _invoke(e, iid, "check_homographs",
                      lyrics="She read the lead carefully")
    flagged = {f["word"] for f in data["findings"]}
    assert flagged & {"lead", "read"}
    e.memory.close()


def test_check_explicit_content_classifies_clean() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    data, _ = _invoke(e, iid, "check_explicit_content",
                      lyrics="Sunshine and good vibes")
    assert data["rating"] == "clean"
    e.memory.close()


def test_check_explicit_content_classifies_explicit() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    data, _ = _invoke(e, iid, "check_explicit_content",
                      lyrics="What the fuck is happening")
    assert data["rating"] == "explicit"
    e.memory.close()


def test_check_cross_track_repetition_flags_duplicate_line() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    data, _ = _invoke(e, iid, "check_cross_track_repetition",
                      tracks=[
                          "The phreaker dialed at night\nLine two of track one",
                          "Different opening here\nThe phreaker dialed at night",
                      ])
    assert data["repeated_lines"] >= 1
    e.memory.close()


def test_extract_section_returns_named_block() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    data, _ = _invoke(e, iid, "extract_section",
                      lyrics=_BLOCK_LYRICS, label="Chorus")
    assert "stronger than the tide" in data["body"].lower()
    e.memory.close()


def test_validate_section_structure_rejects_lowercase() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    bad = "[verse 1]\nthe lyric body here\n"  # lowercase tag
    data, _ = _invoke(e, iid, "validate_section_structure", lyrics=bad)
    assert data["ok"] is False
    assert any(f["issue"] == "title-case required" for f in data["findings"])
    e.memory.close()


def test_scan_artist_names_flags_blocklist() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    data, _ = _invoke(e, iid, "scan_artist_names",
                      lyrics="Like Drake said, the city's mine")
    assert data["count"] >= 1
    assert any(h["name"] == "drake" for h in data["hits"])
    e.memory.close()


def test_check_voice_tells_flags_cliche_escalation() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    data, _ = _invoke(e, iid, "check_voice_tells",
                      lyrics="We're deeper than the ocean\nWe're stronger than the tide")
    found = {f["heuristic"] for f in data["findings"]}
    assert "cliche_escalation" in found
    e.memory.close()


def test_prosody_gate_fails_on_no_rhyme() -> None:
    """Prosody fails when the rhyme scheme has < 2 groups (no real rhyming)."""
    e = _fresh()
    iid = _confirmed_iid(e)
    lc = e.lifecycle.open(iid)
    # All lines ending on same syllable → all-A scheme → 1 group → fail
    bad = "the cat\nthe bat\nthe rat\n"
    data, inv = _invoke(e, iid, "prosody_gate",
                        lifecycle_id=lc, lyrics=bad)
    assert data is None
    assert "GATE_FAILED" in e.memory.recall(inv).get("error", "")
    # Lifecycle paused on the failed gate
    assert e.memory.recall(lc).get("state") == "input-required"
    e.memory.close()


def test_pronunciation_gate_passes_on_clean_text() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    lc = e.lifecycle.open(iid)
    clean = "Sunshine warms the morning fields\nBirds wheel above the bay"
    data, _ = _invoke(e, iid, "pronunciation_gate",
                      lifecycle_id=lc, lyrics=clean)
    assert data["passed"] is True
    e.memory.close()


def test_explicit_gate_blocks_unless_allowed() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    lc = e.lifecycle.open(iid)
    # Default: explicit blocks
    bad, _ = _invoke(e, iid, "explicit_gate",
                     lifecycle_id=lc, lyrics="we yelled fuck and ran")
    assert bad is None
    # With allow_explicit, passes
    lc2 = e.lifecycle.open(iid)
    ok, _ = _invoke(e, iid, "explicit_gate",
                    lifecycle_id=lc2, lyrics="we yelled fuck and ran",
                    allow_explicit=True)
    assert ok["passed"] is True and ok["rating"] == "explicit"
    e.memory.close()


def test_repetition_gate_passes_on_unique_tracks() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    lc = e.lifecycle.open(iid)
    data, _ = _invoke(e, iid, "repetition_gate",
                      lifecycle_id=lc,
                      tracks=["unique line one only here",
                              "different second track content"])
    assert data["passed"] is True
    e.memory.close()


# ─────────────────────── Spec 119 — name-exposure ───────────────────────


def test_check_name_exposure_finds_rostered_name() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    data, _ = _invoke(e, iid, "check_name_exposure",
                      text="Lex stood there in the rain", roster=["Lex"])
    assert data["count"] == 1
    assert data["roster_size"] == 1
    assert data["hits"] == [{"name": "Lex", "count": 1}]
    e.memory.close()


def test_check_name_exposure_respects_word_boundary() -> None:
    """CRITICAL: 'Lex' must NOT match inside 'lexicon'."""
    e = _fresh()
    iid = _confirmed_iid(e)
    data, _ = _invoke(e, iid, "check_name_exposure",
                      text="it is in my lexicon", roster=["Lex"])
    assert data["count"] == 0
    assert data["hits"] == []
    e.memory.close()


def test_check_name_exposure_is_case_insensitive() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    data, _ = _invoke(e, iid, "check_name_exposure",
                      text="lex walked home alone", roster=["Lex"])
    assert data["count"] == 1
    assert data["hits"][0]["name"] == "Lex"
    e.memory.close()


def test_check_name_exposure_empty_roster_is_noop() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    data, _ = _invoke(e, iid, "check_name_exposure",
                      text="Lex and Kael and Nyx", roster=[])
    assert data["count"] == 0
    assert data["roster_size"] == 0
    e.memory.close()


def test_name_exposure_gate_blocks_on_rostered_name() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    lc = e.lifecycle.open(iid)
    data, inv = _invoke(e, iid, "name_exposure_gate",
                        lifecycle_id=lc,
                        lyrics="and then Lex spoke softly",
                        roster=["Lex"])
    assert data is None
    assert "GATE_FAILED" in e.memory.recall(inv).get("error", "")
    assert e.memory.recall(lc).get("state") == "input-required"
    e.memory.close()


def test_name_exposure_gate_passes_when_clean() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    lc = e.lifecycle.open(iid)
    data, _ = _invoke(e, iid, "name_exposure_gate",
                      lifecycle_id=lc,
                      lyrics="the host watched the witness leave",
                      roster=["Lex", "Kael"])
    assert data["passed"] is True
    assert data["hits"] == []
    e.memory.close()


def test_name_exposure_gate_empty_roster_passes() -> None:
    """No-op pass when the roster is empty — rosterless projects unaffected."""
    e = _fresh()
    iid = _confirmed_iid(e)
    lc = e.lifecycle.open(iid)
    data, _ = _invoke(e, iid, "name_exposure_gate",
                      lifecycle_id=lc,
                      lyrics="Lex and Kael appear here freely",
                      roster=[])
    assert data["passed"] is True
    e.memory.close()


def test_lyrics_pregen_gate_includes_name_exposure_subgate() -> None:
    """Spec 119 — the composite carries a 5th `name_exposure` sub-gate and
    still passes overall with an empty (default) roster.

    The other sub-gates are stubbed (mirrors test_music_gates' compose test) so
    the only live sub-gate under test is the real `name_exposure_gate`; with the
    default empty blocklist it is a no-op pass, keeping the composite green for
    rosterless projects.
    """
    from agency.toolresult import ToolResult
    e = _fresh()
    iid = _confirmed_iid(e)
    lc = e.lifecycle.open(iid)
    music_cap = e.registry._caps["music"]
    originals = {}
    for sub in ("prosody_gate", "pronunciation_gate",
                "repetition_gate", "explicit_gate"):
        originals[sub] = music_cap.verbs[sub]["fn"]
        music_cap.verbs[sub]["fn"] = (
            lambda ctx, **kw: ToolResult.success(data={"passed": True}))
    try:
        data, _ = _invoke(e, iid, "lyrics_pregen_gate",
                          lifecycle_id=lc, album="demo",
                          lyrics="non-empty clean body")
        assert data is not None, "composite should pass with a clean rosterless run"
        assert "name_exposure" in data["sub_gates"]
        assert data["sub_gates"]["name_exposure"] is True
        assert data["passed"] is True
    finally:
        for sub, fn in originals.items():
            music_cap.verbs[sub]["fn"] = fn
        e.memory.close()


def test_lyric_writing_skill_walks_through_finalize() -> None:
    """Walk the 6-phase skill; the terminal phase is a hard elicit."""
    e = _fresh()
    iid = _confirmed_iid(e)
    sk = e.ontology.skill("lyric-writing")
    run = SkillRun(e.memory, iid, sk)
    fills = [
        {"lyrics_draft": "draft v1"},
        {"syllable_target_met": "yes", "rhyme_scheme_valid": "yes"},
        {"pronunciation_clean": "yes"},
        {"no_album_wide_repeats": "yes"},
        {"explicit_rating_assigned": "clean"},
    ]
    for out in fills:
        assert run.submit(out)["status"] == "working"
    assert run.current()["gate"] == "hard"
    assert run.submit({"lyrics_locked": "yes"}, confirmed=True)["status"] == "completed"
    e.memory.close()


def test_extract_distinctive_phrases_returns_novel_trigrams() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    data, _ = _invoke(e, iid, "extract_distinctive_phrases",
                      lyrics="The blue box echoes through the night",
                      corpus=["nothing matches here", "another song"])
    assert data["count"] >= 1
    # All returned trigrams should be present in the lyrics
    for tg in data["phrases"]:
        assert tg in "the blue box echoes through the night"


def test_check_streaming_lyrics_flags_brackets() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    data, _ = _invoke(e, iid, "check_streaming_lyrics",
                      lyrics="[Verse 1]\nbody here")
    assert data["safe"] is False
    assert data["bracket_tags"] >= 1
    e.memory.close()
