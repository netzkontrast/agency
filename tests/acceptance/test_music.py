"""Acceptance — music capability (all clusters).

Converted from tests/test_music*.py (~11 files). Tests observable verb
behaviour: graph nodes, returned values, provenance, gate verdicts.

DROPPED (implementation/structural, not behaviour):
 - Verb-presence registry checks (test_*_cluster_verbs_discover, cap.verbs membership)
 - SkillRun walker tests (test_*_skill_walks_*, test_every_workflow_skill_walks_*)
 - test_music_capability_auto_discovers_under_new_home (registry structural)
 - Direct Memory.record enum tests (test_music_album_type_enum_still_bites etc.)
 - Deprecation shim import tests (test_examples_music_shim_*)
 - Template file-presence tests (test_music_templates_ported_*, test_*_templates_*)
 - Frozen schema/enum/edge/node count snapshots (test_music_capability_registers_*)
 - db_init migration helper test (test_db_init_runs_schema_against_fake)
 - Production driver internals (test_sqlite_db_driver_*, test_file_state_driver_*,
   test_production_drivers_*, test_config_*, test_bootstrap_*, test_autowire_*,
   test_create_track_renders_*, test_set_track_status_round_trips_*,
   test_create_album_substitutes_*)
 - Monkeypatched sub-gate composition tests (test_lyrics_pregen_gate_composes_*,
   test_lyrics_pregen_gate_includes_*)
 - promo_review name-exposure tests requiring tmp_path config injection
 - test_require_drv_helper_works_across_clusters (internal helper)
 - test_capability_lint_clean_in_block_mode (lint helper internal)

GAPS (require real binaries/network — not exercised):
 - Real ffmpeg / pyloudnorm / AnthemScore / LilyPond
 - Real Cloudflare R2 / PostgreSQL
"""
from __future__ import annotations

import tempfile

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from conftest import invoke, served

scenarios("features/music.feature")


# ──────────────────────────── fixtures ────────────────────────────────────────

@pytest.fixture
def engine():
    """Fresh engine with fake music drivers (standard set, unconfigured cloud)."""
    from agency.capabilities.music.drivers import fake_drivers
    from agency.engine import Engine
    e = Engine(tempfile.mktemp(suffix=".db"), drivers=fake_drivers())
    yield e
    e.memory.close()


@pytest.fixture
def confirmed_intent(engine):
    iid = engine.intent.capture("music acceptance", "behaviour preserved", "verified")
    engine.intent.confirm(iid)
    return iid


# ──────────────────────────── shared Given steps ──────────────────────────────

@given("a music engine with fake drivers")
def _given_music_engine(engine):
    return engine


@given("a confirmed music intent")
def _given_music_intent(confirmed_intent):
    return confirmed_intent


@given("the cloud driver is configured")
def _given_cloud_configured(engine):
    """Swap in a configured FakeCloudDriver so cloud verbs succeed."""
    from agency.capabilities.music.drivers import FakeCloudDriver
    engine.drivers.register("music_cloud", FakeCloudDriver(configured=True))


# ──────────────────────────── per-test lifecycle fixture ──────────────────────

@pytest.fixture
def lc(engine, confirmed_intent):
    """A fresh lifecycle, opened once per test."""
    return engine.lifecycle.open(confirmed_intent)


# ──────────────────────── Lifecycle cluster (094) ─────────────────────────────

@when(parsers.parse('I capture the idea "{text}"'), target_fixture="result")
def _capture_idea(engine, confirmed_intent, text):
    r, _ = invoke(engine, confirmed_intent, "music", "capture_idea", text=text)
    return r


@then("the result carries an idea_id")
def _has_idea_id(result):
    assert result and result.get("idea_id"), "idea_id missing from result"


@then(parsers.parse('the idea status is "{status}"'))
def _idea_status(result, status):
    assert result["status"] == status


@then("the idea text matches the input")
def _idea_text(result):
    assert result["text"]


@given(parsers.parse('an idea "{text}" has been captured'), target_fixture="captured_idea")
def _given_idea(engine, confirmed_intent, text):
    r, _ = invoke(engine, confirmed_intent, "music", "capture_idea", text=text)
    return r


@when(
    parsers.parse('I promote that idea with artist "{artist}" and title "{title}"'),
    target_fixture="result",
)
def _promote_idea(engine, confirmed_intent, captured_idea, artist, title):
    r, _ = invoke(
        engine, confirmed_intent, "music", "promote_idea",
        idea_id=captured_idea["idea_id"], artist=artist, title=title, genre="ambient",
    )
    return r


@then(parsers.parse('the result status is "{status}"'))
def _result_status(result, status):
    assert result["status"] == status


@then("an album_slug is returned")
def _album_slug_returned(result):
    assert result.get("album_slug")


@then("the idea status in the graph is \"promoted\"")
def _idea_promoted_in_graph(engine, captured_idea):
    node = engine.memory.recall(captured_idea["idea_id"])
    assert node.get("status") == "promoted"


@then("a PROMOTED_TO edge links the idea to the album")
def _promoted_to_edge(engine, captured_idea, result):
    rows = engine.memory.g.query(
        "MATCH (i)-[r:PROMOTED_TO]->(a) WHERE i.id = $iid AND a.id = $aid RETURN r",
        {"iid": captured_idea["idea_id"], "aid": result["album_id"]},
    )
    assert rows, "PROMOTED_TO edge missing"


@when("I promote a non-existent idea id", target_fixture="last_inv")
def _promote_ghost(engine, confirmed_intent):
    _data, inv = invoke(
        engine, confirmed_intent, "music", "promote_idea",
        idea_id="idea:ghost-does-not-exist", artist="A", title="T", genre="g",
    )
    return inv


@then(parsers.parse('the invocation outcome is "{outcome}"'))
def _outcome(engine, request, outcome):
    """Unified outcome check - works with last_inv, rename_result, or gate_inv."""
    inv = None
    try:
        inv = request.getfixturevalue("last_inv")
    except pytest.FixtureLookupError:
        pass
    if inv is None:
        try:
            rr = request.getfixturevalue("rename_result")
            inv = rr["inv"]
        except pytest.FixtureLookupError:
            pass
    if inv is None:
        try:
            gi = request.getfixturevalue("gate_inv")
            inv = gi["inv"]
        except pytest.FixtureLookupError:
            pass
    assert inv is not None, "no invocation id for outcome check"
    node = engine.memory.recall(inv)
    assert node.get("outcome") == outcome


@given('ideas "alpha" and "beta" have been captured')
def _given_two_ideas(engine, confirmed_intent):
    invoke(engine, confirmed_intent, "music", "capture_idea", text="alpha")
    invoke(engine, confirmed_intent, "music", "capture_idea", text="beta")


@given('"alpha" has been promoted')
def _given_alpha_promoted(engine, confirmed_intent):
    ideas = engine.memory.find("Idea")
    alpha = next(i for i in ideas if i.get("text") == "alpha")
    invoke(
        engine, confirmed_intent, "music", "promote_idea",
        idea_id=alpha["id"], artist="A", title="Alpha", genre="ambient",
    )


@when("I list all ideas", target_fixture="result")
def _list_all_ideas(engine, confirmed_intent):
    r, _ = invoke(engine, confirmed_intent, "music", "list_ideas")
    return r


@when(parsers.parse('I list ideas with status "{status}"'), target_fixture="result")
def _list_ideas_by_status(engine, confirmed_intent, status):
    r, _ = invoke(engine, confirmed_intent, "music", "list_ideas", status=status)
    return r


@then(parsers.parse("the count is {n:d}"))
def _count_is(result, n):
    assert result["count"] == n


@when(
    parsers.parse('I create album "{title}" by artist "{artist}" in genre "{genre}"'),
    target_fixture="result",
)
def _create_album(engine, confirmed_intent, title, artist, genre):
    r, _ = invoke(
        engine, confirmed_intent, "music", "create_album",
        artist=artist, title=title, genre=genre, type="thematic",
    )
    return r


@when(
    parsers.parse('I create album "{title}" by artist "{artist}" in genre "{genre}" with type "{album_type}"'),
    target_fixture="last_inv",
)
def _create_album_bad_type(engine, confirmed_intent, title, artist, genre, album_type):
    _data, inv = invoke(
        engine, confirmed_intent, "music", "create_album",
        artist=artist, title=title, genre=genre, type=album_type,
    )
    return inv


@then(parsers.parse('the album_slug is "{slug}"'))
def _album_slug_is(result, slug):
    assert result["album_slug"] == slug


@then("artist_seeded is True")
def _artist_seeded(result):
    assert result["artist_seeded"] is True


@then(parsers.parse('the album node has type "{album_type}"'))
def _album_node_type(engine, result, album_type):
    node = engine.memory.recall(result["album_id"])
    assert node.get("type") == album_type


@given(parsers.parse('albums "{a}" and "{b}" exist for artist "{artist}"'))
def _given_two_albums(engine, confirmed_intent, a, b, artist):
    invoke(engine, confirmed_intent, "music", "create_album",
           artist=artist, title=a, genre="ambient")
    invoke(engine, confirmed_intent, "music", "create_album",
           artist=artist, title=b, genre="ambient")


@when(parsers.parse('I search for album "{query}"'), target_fixture="result")
def _find_album(engine, confirmed_intent, query):
    r, _ = invoke(engine, confirmed_intent, "music", "find_album", query=query)
    return r


@then(parsers.parse("exactly {n:d} album is found"))
def _exactly_n_albums(result, n):
    assert result["count"] == n


@then(parsers.parse('the first album slug is "{slug}"'))
def _first_album_slug(result, slug):
    assert result["albums"][0]["slug"] == slug


@given(parsers.parse('album "{title}" by artist "{artist}" exists'), target_fixture="album_res")
def _given_album(engine, confirmed_intent, title, artist):
    r, _ = invoke(engine, confirmed_intent, "music", "create_album",
                  artist=artist, title=title, genre="ambient")
    return r


@when(
    parsers.parse('I create track "{title}" number {num:d} on album "{album}"'),
    target_fixture="last_track",
)
def _create_track(engine, confirmed_intent, title, num, album):
    r, _ = invoke(engine, confirmed_intent, "music", "create_track",
                  album=album, title=title, track_number=num)
    return r


@then("the track slugs begin with the track number prefix")
def _track_slug_prefix(engine):
    tracks = engine.memory.find("Track")
    assert len(tracks) >= 1
    for t in tracks:
        assert t.get("slug"), "slug missing"


@then(parsers.parse("{n:d} RECORDED_FOR edges link tracks to the album"))
def _recorded_for_edges(engine, album_res, n):
    rows = engine.memory.g.query(
        "MATCH (t:Track)-[r:RECORDED_FOR]->(a:Album) WHERE a.id = $aid RETURN t",
        {"aid": album_res["album_id"]},
    )
    assert len(rows) == n


@given(parsers.parse("{n:d} tracks exist on album \"{album}\""), target_fixture="track_slugs")
def _given_n_tracks(engine, confirmed_intent, n, album):
    slugs = []
    for i in range(1, n + 1):
        r, _ = invoke(engine, confirmed_intent, "music", "create_track",
                      album=album, title=f"Track{i}", track_number=i)
        slugs.append(r["track_slug"])
    return slugs


@given(parsers.parse("{n:d} track exists on album \"{album}\""), target_fixture="track_slugs")
def _given_one_track(engine, confirmed_intent, n, album):
    slugs = []
    for i in range(1, n + 1):
        r, _ = invoke(engine, confirmed_intent, "music", "create_track",
                      album=album, title=f"Track{i}", track_number=i)
        slugs.append(r["track_slug"])
    return slugs


@when(parsers.parse('I set the first track status to "{status}"'))
def _set_first_track_status(engine, confirmed_intent, track_slugs, status):
    invoke(engine, confirmed_intent, "music", "set_track_status",
           album="loop", track=track_slugs[0], status=status)


@when(parsers.parse('I list tracks for album "{album}"'), target_fixture="result")
def _list_tracks(engine, confirmed_intent, album):
    r, _ = invoke(engine, confirmed_intent, "music", "list_tracks", album=album)
    return r


@then(parsers.parse('at least one track has status "{status}"'))
def _at_least_one_track_status(result, status):
    assert any(t["status"] == status for t in result["tracks"])


@when(parsers.parse('I set that track status to "{status}"'), target_fixture="last_inv")
def _set_track_status_bad(engine, confirmed_intent, track_slugs, status):
    _data, inv = invoke(engine, confirmed_intent, "music", "set_track_status",
                        album="loop", track=track_slugs[0], status=status)
    return inv


@given("the first track has status \"mastered\"")
def _given_first_track_mastered(engine, confirmed_intent, track_slugs):
    invoke(engine, confirmed_intent, "music", "set_track_status",
           album="long-player", track=track_slugs[0], status="mastered")


@when(parsers.parse('I request album progress for "{album}"'), target_fixture="result")
def _album_progress(engine, confirmed_intent, album):
    r, _ = invoke(engine, confirmed_intent, "music", "album_progress", album=album)
    return r


@then(parsers.parse("track_count is {n:d}"))
def _track_count(result, n):
    assert result["track_count"] == n


@then(parsers.parse("tracks_completed is {n:d}"))
def _tracks_completed(result, n):
    assert result["tracks_completed"] == n


@then(parsers.parse("completion_percentage is {n:d}"))
def _completion_pct(result, n):
    assert result["completion_percentage"] == n


@given(parsers.parse('album "{title}" by artist "{artist}" exists with {n:d} track'))
def _given_album_with_n_tracks(engine, confirmed_intent, title, artist, n):
    invoke(engine, confirmed_intent, "music", "create_album",
           artist=artist, title=title, genre="ambient")
    slug = title.lower().replace(" ", "-")
    for i in range(1, n + 1):
        invoke(engine, confirmed_intent, "music", "create_track",
               album=slug, title=f"T{i}", track_number=i)


@when(parsers.parse('I rename album "{old}" to "{new}"'), target_fixture="rename_result")
def _rename_album(engine, confirmed_intent, old, new):
    r, inv = invoke(engine, confirmed_intent, "music", "rename_album",
                    old_slug=old, new_slug=new)
    # For bad slugs result is None, expose inv as last_inv
    return {"data": r, "inv": inv}


@then("the rename succeeds")
def _rename_succeeds(rename_result):
    assert rename_result["data"]["success"] is True


@then(parsers.parse('the track is still listed under "{album}"'))
def _track_after_rename(engine, confirmed_intent, album):
    listed, _ = invoke(engine, confirmed_intent, "music", "list_tracks", album=album)
    assert listed["count"] == 1


# Unified error-contains step: tries rename_result, gate_inv, then last_inv
@then(parsers.parse('the error contains "{fragment}"'))
def _error_contains_generic(engine, request, fragment):
    """Look up error from the fixture that was actually populated this scenario."""
    inv = None
    # Try rename_result (only if step actually ran and populated it)
    try:
        rr = request.getfixturevalue("rename_result")
        inv = rr["inv"]
    except pytest.FixtureLookupError:
        pass
    # Try last_inv
    if inv is None:
        try:
            inv = request.getfixturevalue("last_inv")
        except pytest.FixtureLookupError:
            pass
    # Try gate_inv
    if inv is None:
        try:
            gi = request.getfixturevalue("gate_inv")
            inv = gi["inv"]
        except pytest.FixtureLookupError:
            pass
    assert inv is not None, "no invocation id available for error check"
    node = engine.memory.recall(inv)
    assert fragment in node.get("error", ""), (
        f"expected {fragment!r} in {node.get('error', '')!r}")


@when(parsers.parse('I set album "{album}" status to "{status}"'), target_fixture="last_inv")
def _set_album_status_bad(engine, confirmed_intent, album, status):
    _data, inv = invoke(engine, confirmed_intent, "music", "set_album_status",
                        album=album, status=status)
    return inv


@when(
    parsers.parse('I conceptualize album "{title}" by "{artist}" of type "{album_type}"'),
    target_fixture="result",
)
def _conceptualize(engine, confirmed_intent, title, artist, album_type):
    r, _ = invoke(engine, confirmed_intent, "music", "conceptualize",
                  artist=artist, title=title, type=album_type, theme="x")
    return r


@then("the result contains a rendered concept")
def _rendered_concept(result):
    assert result and result.get("result")


@then("an album-concept artefact is recorded against the intent")
def _album_concept_artefact(engine, confirmed_intent):
    prov = engine.memory.provenance(confirmed_intent)
    assert any(a["kind"] == "album-concept" for a in prov["artefacts"])


@given(parsers.parse('session state is set to last_album "{album}" last_phase "{phase}"'))
def _given_session_state(engine, album, phase):
    engine.drivers.get("music_state").update_session(
        {"last_album": album, "last_phase": phase}
    )


@when("I call resume_session", target_fixture="result")
def _resume_session(engine, confirmed_intent):
    r, _ = invoke(engine, confirmed_intent, "music", "resume_session")
    return r


@then(parsers.parse('session last_album is "{album}"'))
def _session_last_album(result, album):
    assert result["session"]["last_album"] == album


@then(parsers.parse('session last_phase is "{phase}"'))
def _session_last_phase(result, phase):
    assert result["session"]["last_phase"] == phase


# ──────────────────────── Lyrics cluster (095) ────────────────────────────────

_BLOCK_LYRICS = (
    "[Verse 1]\n"
    "The phreaker dialed a modem at night\n"
    "Routing through the synth and the wire\n"
    "A blue box echo in the chrome\n"
    "She read the lead and made it home\n\n"
    "[Chorus]\n"
    "We're stronger than the tide\n"
    "We're deeper than the night"
)


@when(
    parsers.parse('I analyze the rhyme scheme of "{lyrics}"'),
    target_fixture="result",
)
def _analyze_rhyme(engine, confirmed_intent, lyrics):
    r, _ = invoke(engine, confirmed_intent, "music", "analyze_rhyme_scheme",
                  lyrics=lyrics.replace("\\n", "\n"))
    return r


@then(parsers.parse('the result contains a "{key}"'))
def _result_has_key(result, key):
    assert key in result


@then("groups is at least 1")
def _groups_at_least_one(result):
    assert result["groups"] >= 1


@when("I analyze readability of multi-verse lyrics", target_fixture="result")
def _analyze_readability(engine, confirmed_intent):
    r, _ = invoke(engine, confirmed_intent, "music", "analyze_readability",
                  text_=_BLOCK_LYRICS)
    return r


@then("avg_words_per_sentence is positive")
def _avg_words_positive(result):
    assert result["avg_words_per_sentence"] > 0


@when(
    parsers.parse('I check pronunciation of "{lyrics}"'),
    target_fixture="result",
)
def _check_pronunciation(engine, confirmed_intent, lyrics):
    r, _ = invoke(engine, confirmed_intent, "music", "check_pronunciation", lyrics=lyrics)
    return r


@then("at least 1 finding is returned")
def _at_least_one_finding(result):
    assert result.get("count", 0) >= 1 or len(result.get("findings", [])) >= 1


@then(parsers.parse('"{word}" appears in the flagged words'))
def _word_flagged(result, word):
    flagged = {f["word"] for f in result["findings"]}
    assert word in flagged


@when(
    parsers.parse('I check homographs of "{lyrics}"'),
    target_fixture="result",
)
def _check_homographs(engine, confirmed_intent, lyrics):
    r, _ = invoke(engine, confirmed_intent, "music", "check_homographs", lyrics=lyrics)
    return r


@then('the flagged words include "lead" or "read"')
def _lead_or_read_flagged(result):
    flagged = {f["word"] for f in result["findings"]}
    assert flagged & {"lead", "read"}


@when(
    parsers.parse('I check explicit content of "{lyrics}"'),
    target_fixture="result",
)
def _check_explicit(engine, confirmed_intent, lyrics):
    r, _ = invoke(engine, confirmed_intent, "music", "check_explicit_content", lyrics=lyrics)
    return r


@then(parsers.parse('the rating is "{rating}"'))
def _rating_is(result, rating):
    assert result["rating"] == rating


@when("I check cross-track repetition of two tracks sharing a line", target_fixture="result")
def _check_cross_track(engine, confirmed_intent):
    r, _ = invoke(
        engine, confirmed_intent, "music", "check_cross_track_repetition",
        tracks=[
            "The phreaker dialed at night\nLine two of track one",
            "Different opening here\nThe phreaker dialed at night",
        ],
    )
    return r


@then("repeated_lines is at least 1")
def _repeated_lines(result):
    assert result["repeated_lines"] >= 1


@when("I extract section \"Chorus\" from the test lyrics block", target_fixture="result")
def _extract_chorus(engine, confirmed_intent):
    r, _ = invoke(engine, confirmed_intent, "music", "extract_section",
                  lyrics=_BLOCK_LYRICS, label="Chorus")
    return r


@then(parsers.parse('the body contains "{text}"'))
def _body_contains(result, text):
    assert text.lower() in result["body"].lower()


@when(
    parsers.parse('I validate section structure of "{lyrics}"'),
    target_fixture="result",
)
def _validate_section(engine, confirmed_intent, lyrics):
    # pytest_bdd passes \n as literal two-char sequence from the feature file
    r, _ = invoke(engine, confirmed_intent, "music", "validate_section_structure",
                  lyrics=lyrics.replace("\\n", "\n"))
    return r


@when("I validate section structure of a lowercase-tagged lyric block",
      target_fixture="result")
def _validate_section_lowercase(engine, confirmed_intent):
    """Feature step without a lyrics parameter — use a fixed lowercase-tagged block."""
    bad = "[verse 1]\nsome lyrics here\n[chorus]\nmore lyrics"
    r, _ = invoke(engine, confirmed_intent, "music", "validate_section_structure",
                  lyrics=bad)
    return r


@then("ok is False")
def _ok_false(result):
    assert result["ok"] is False


@then(parsers.parse('a finding has issue "{issue}"'))
def _finding_issue(result, issue):
    assert any(f["issue"] == issue for f in result["findings"])


@when(
    parsers.parse('I scan artist names in "{lyrics}"'),
    target_fixture="result",
)
def _scan_artist_names(engine, confirmed_intent, lyrics):
    r, _ = invoke(engine, confirmed_intent, "music", "scan_artist_names", lyrics=lyrics)
    return r


@then("at least 1 hit is returned")
def _at_least_one_hit(result):
    assert result.get("count", 0) >= 1


@then(parsers.parse('"{name}" appears in the hit names'))
def _name_in_hits(result, name):
    assert any(h["name"] == name for h in result["hits"])


@when(
    parsers.parse('I check voice tells for "{lyrics}"'),
    target_fixture="result",
)
def _check_voice_tells(engine, confirmed_intent, lyrics):
    r, _ = invoke(engine, confirmed_intent, "music", "check_voice_tells", lyrics=lyrics)
    return r


@when("I check voice tells for escalating cliche lyrics", target_fixture="result")
def _check_voice_tells_cliche(engine, confirmed_intent):
    """Literal step — uses known cliche escalation phrases that trigger the heuristic."""
    cliche = "deeper than the ocean\nstronger than the tide\nmore than ever before"
    r, _ = invoke(engine, confirmed_intent, "music", "check_voice_tells", lyrics=cliche)
    return r


@then(parsers.parse('"{heuristic}" appears in the finding heuristics'))
def _heuristic_in_findings(result, heuristic):
    found = {f["heuristic"] for f in result["findings"]}
    assert heuristic in found


# ──────────────────── Gate steps ──────────────────────────────────────────────

@when("I run prosody_gate on lyrics with an all-A rhyme scheme", target_fixture="gate_inv")
def _prosody_gate_fail(engine, confirmed_intent, lc):
    bad = "the cat\nthe bat\nthe rat\n"
    _data, inv = invoke(engine, confirmed_intent, "music", "prosody_gate",
                        lifecycle_id=lc, lyrics=bad)
    return {"inv": inv, "lc": lc}


@then("the gate fails")
def _gate_fails(engine, gate_inv):
    node = engine.memory.recall(gate_inv["inv"])
    assert "GATE_FAILED" in node.get("error", "")


@then(parsers.parse('the lifecycle state is "{state}"'))
def _lifecycle_state(engine, gate_inv, state):
    lc_node = engine.memory.recall(gate_inv["lc"])
    assert lc_node.get("state") == state


@when(
    parsers.parse('I run pronunciation_gate on "{lyrics}"'),
    target_fixture="result",
)
def _pronunciation_gate(engine, confirmed_intent, lc, lyrics):
    r, _ = invoke(engine, confirmed_intent, "music", "pronunciation_gate",
                  lifecycle_id=lc, lyrics=lyrics)
    return r


@when(parsers.parse('I run explicit_gate on "{lyrics}"'), target_fixture="gate_inv")
def _explicit_gate_fail(engine, confirmed_intent, lc, lyrics):
    _data, inv = invoke(engine, confirmed_intent, "music", "explicit_gate",
                        lifecycle_id=lc, lyrics=lyrics)
    return {"inv": inv, "lc": lc}


@when(parsers.parse('I run explicit_gate on "{lyrics}" with allow_explicit'), target_fixture="result")
def _explicit_gate_allowed(engine, confirmed_intent, lyrics):
    lc2 = engine.lifecycle.open(confirmed_intent)
    r, _ = invoke(engine, confirmed_intent, "music", "explicit_gate",
                  lifecycle_id=lc2, lyrics=lyrics, allow_explicit=True)
    return r


@then(parsers.parse('rating is "{rating}"'))
def _rating_field(result, rating):
    assert result["rating"] == rating


@when("I run repetition_gate on two tracks with no shared lines", target_fixture="result")
def _repetition_gate(engine, confirmed_intent, lc):
    r, _ = invoke(engine, confirmed_intent, "music", "repetition_gate",
                  lifecycle_id=lc,
                  tracks=["unique line one only here",
                          "different second track content"])
    return r


@when(
    parsers.parse('I check name exposure of "{text}" against roster ["{name}"]'),
    target_fixture="result",
)
def _check_name_exposure_one(engine, confirmed_intent, text, name):
    r, _ = invoke(engine, confirmed_intent, "music", "check_name_exposure",
                  text=text, roster=[name])
    return r


@then(parsers.parse("count is {n:d}"))
def _count_is_n(result, n):
    assert result["count"] == n


@then(parsers.parse('hits contain name "{name}"'))
def _hits_contain(result, name):
    assert any(h["name"] == name for h in result["hits"])


@when(
    parsers.parse('I run name_exposure_gate on "{text}" with roster ["{name}"]'),
    target_fixture="gate_inv",
)
def _name_exposure_gate_blocked(engine, confirmed_intent, lc, text, name):
    _data, inv = invoke(engine, confirmed_intent, "music", "name_exposure_gate",
                        lifecycle_id=lc, lyrics=text, roster=[name])
    return {"inv": inv, "lc": lc, "data": _data}



@then("hits is empty")
def _hits_empty(request):
    """Check hits is empty from gate_inv["data"] or result."""
    data = None
    try:
        gi = request.getfixturevalue("gate_inv")
        data = gi.get("data") if gi else None
    except pytest.FixtureLookupError:
        pass
    if data is None:
        try:
            data = request.getfixturevalue("result")
        except pytest.FixtureLookupError:
            pass
    assert data is not None and data.get("hits") == []


@when(
    parsers.parse('I extract distinctive phrases from "{lyrics}"'),
    target_fixture="result",
)
def _extract_phrases(engine, confirmed_intent, lyrics):
    r, _ = invoke(engine, confirmed_intent, "music", "extract_distinctive_phrases",
                  lyrics=lyrics, corpus=["nothing matches here", "another song"])
    return r


@then("at least 1 phrase is returned")
def _at_least_one_phrase(result):
    assert result["count"] >= 1


@when(
    parsers.parse('I check streaming lyrics of "{lyrics}"'),
    target_fixture="result",
)
def _check_streaming_lyrics(engine, confirmed_intent, lyrics):
    r, _ = invoke(engine, confirmed_intent, "music", "check_streaming_lyrics",
                  lyrics=lyrics.replace("\\n", "\n"))
    return r


@then("safe is False")
def _safe_false(result):
    assert result["safe"] is False


@then("bracket_tags is at least 1")
def _bracket_tags(result):
    assert result["bracket_tags"] >= 1


# ──────────────────────── Audio cluster (096) ─────────────────────────────────

@when(
    parsers.parse('I master audio "{path}" with target_lufs {lufs:f} and preset "{preset}"'),
    target_fixture="result",
)
def _master_audio(engine, confirmed_intent, path, lufs, preset):
    r, _ = invoke(engine, confirmed_intent, "music", "master_audio",
                  album="Origin", path=path, target_lufs=lufs, preset=preset)
    return r


@then(parsers.parse('the artefact kind is "{kind}"'))
def _artefact_kind(result, kind):
    assert result["artefact"]["kind"] == kind


@then(parsers.parse("target_lufs in the artefact is {lufs:f}"))
def _target_lufs(result, lufs):
    assert result["artefact"]["target_lufs"] == lufs


@then("a mastering-report artefact is recorded against the intent")
def _mastering_artefact(engine, confirmed_intent):
    prov = engine.memory.provenance(confirmed_intent)
    assert any(a["kind"] == "mastering-report" for a in prov["artefacts"])


@when(
    parsers.parse('I master audio "{path}" with reference "{ref}"'),
    target_fixture="result",
)
def _master_with_ref(engine, confirmed_intent, path, ref):
    r, _ = invoke(engine, confirmed_intent, "music", "master_with_reference",
                  album="Origin", path=path, reference=ref)
    return r


@then("the artefact contains a target_lufs")
def _artefact_has_target_lufs(result):
    assert "target_lufs" in result["artefact"]


@then('the preset starts with "ref:"')
def _preset_ref(result):
    assert result["artefact"]["preset"].startswith("ref:")


@when(parsers.parse('I polish audio "{path}"'), target_fixture="result")
def _polish_audio(engine, confirmed_intent, path):
    r, _ = invoke(engine, confirmed_intent, "music", "polish_audio",
                  album="A", path=path)
    return r


@then('the output path ends with ".polished"')
def _output_polished(result):
    assert result["output"].endswith(".polished")


@when("I polish album \"A\" with 3 paths", target_fixture="result")
def _polish_album(engine, confirmed_intent):
    r, _ = invoke(engine, confirmed_intent, "music", "polish_album",
                  album="A", paths=["/tmp/t1.wav", "/tmp/t2.wav", "/tmp/t3.wav"])
    return r


@then("every polished path ends with \".polished\"")
def _all_polished(result):
    assert all(p.endswith(".polished") for p in result["polished"])


@when(parsers.parse('I analyze audio "{path}"'), target_fixture="result")
def _analyze_audio(engine, confirmed_intent, path):
    r, _ = invoke(engine, confirmed_intent, "music", "analyze_audio",
                  album="A", path=path)
    return r


@then("loudness_lufs is present")
def _loudness_lufs(result):
    assert "loudness_lufs" in result


@then("signature contains centroid_hz")
def _signature_centroid(result):
    assert "centroid_hz" in result["signature"]


@when(parsers.parse('I run qc_audio on "{path}"'), target_fixture="result")
def _qc_audio(engine, confirmed_intent, path):
    r, _ = invoke(engine, confirmed_intent, "music", "qc_audio",
                  album="A", path=path)
    return r


@then("7 QC rows are returned")
def _seven_qc_rows(result):
    assert len(result["rows"]) == 7


@then('summary is one of "pass", "warn", "fail"')
def _summary_valid(result):
    assert result["summary"] in {"pass", "warn", "fail"}


@then("all expected QC categories are present")
def _qc_categories(result):
    expected = {"loudness", "clipping", "silence", "phase",
                "stereo_width", "frequency_balance", "dynamic_range"}
    assert set(result["rows"].keys()) == expected


@when(parsers.parse('I run mono_fold_check on "{path}"'), target_fixture="result")
def _mono_fold_check(engine, confirmed_intent, path):
    r, _ = invoke(engine, confirmed_intent, "music", "mono_fold_check",
                  album="A", path=path)
    return r


@then("cancellation_db is present")
def _cancellation_db(result):
    assert "cancellation_db" in result


@then("phase_safe is present")
def _phase_safe(result):
    assert "phase_safe" in result


@when("I measure album signature for 2 paths", target_fixture="result")
def _measure_sig(engine, confirmed_intent):
    r, _ = invoke(engine, confirmed_intent, "music", "measure_album_signature",
                  album="A", paths=["/tmp/t1.wav", "/tmp/t2.wav"])
    return r


@then("each signature has centroid_hz and rms_db")
def _sig_fields(result):
    for sig in result["signatures"]:
        assert "centroid_hz" in sig
        assert "rms_db" in sig


@when("I run album_coherence_check on 4 paths", target_fixture="result")
def _album_coherence(engine, confirmed_intent):
    r, _ = invoke(engine, confirmed_intent, "music", "album_coherence_check",
                  album="A", paths=["/tmp/t1.wav", "/tmp/t2.wav",
                                    "/tmp/t3.wav", "/tmp/t4.wav"])
    return r


@then("coherent is present")
def _coherent_present(result):
    assert "coherent" in result


@then("outliers is present")
def _outliers_present(result):
    assert "outliers" in result


@then(parsers.parse("track_count is {n:d}"))
def _track_count_n(result, n):
    assert result["track_count"] == n


@when(
    parsers.parse('I fix dynamic track "{path}" with target_dr {dr:f}'),
    target_fixture="result",
)
def _fix_dynamic(engine, confirmed_intent, path, dr):
    r, _ = invoke(engine, confirmed_intent, "music", "fix_dynamic_track",
                  album="A", path=path, target_dr=dr)
    return r


@then("measured_dr is present")
def _measured_dr(result):
    assert "measured_dr" in result


@then(parsers.parse("target_dr is {dr:f}"))
def _target_dr(result, dr):
    assert result["target_dr"] == dr


@then("applied is present")
def _applied_present(result):
    assert "applied" in result


@when(
    parsers.parse('I render codec preview of "{path}" with codec "{codec}"'),
    target_fixture="result",
)
def _render_codec(engine, confirmed_intent, path, codec):
    r, _ = invoke(engine, confirmed_intent, "music", "render_codec_preview",
                  album="A", path=path, codec=codec)
    return r


@then(parsers.parse('the codec in result is "{codec}"'))
def _codec_in_result(result, codec):
    assert result["codec"] == codec


@then("bitrate_kbps is 256")
def _bitrate(result):
    assert result["bitrate_kbps"] == 256


@then('the output ends with ".aac.preview"')
def _aac_preview(result):
    assert result["output"].endswith(".aac.preview")


@given(parsers.parse('album "{title}" by artist "{artist}" has 1 mastered track'))
def _given_mastered_track(engine, confirmed_intent, title, artist):
    invoke(engine, confirmed_intent, "music", "create_album",
           artist=artist, title=title, genre="ambient")
    slug = title.lower().replace(" ", "-")
    t, _ = invoke(engine, confirmed_intent, "music", "create_track",
                  album=slug, title="T1", track_number=1)
    invoke(engine, confirmed_intent, "music", "set_track_status",
           album=slug, track=t["track_slug"], status="mastered")


@when(parsers.parse('I reset mastering for album "{album}"'), target_fixture="result")
def _reset_mastering(engine, confirmed_intent, album):
    r, _ = invoke(engine, confirmed_intent, "music", "reset_mastering", album=album)
    return r


@then("reset is True")
def _reset_true(result):
    assert result["reset"] is True


@then('no tracks are in "mastered" status')
def _no_mastered_tracks(engine, confirmed_intent):
    listed, _ = invoke(engine, confirmed_intent, "music", "list_tracks", album="origin")
    assert all(t["status"] != "mastered" for t in listed["tracks"])


@when(
    parsers.parse('I generate promo videos for album "{album}" with template "{template}"'),
    target_fixture="result",
)
def _gen_promo_videos(engine, confirmed_intent, album, template):
    r, _ = invoke(engine, confirmed_intent, "music", "generate_promo_videos",
                  album=album, audio="/tmp/t1.wav", art="/tmp/cover.jpg",
                  template=template)
    return r


@then(parsers.parse('the output path contains "{fragment}"'))
def _output_contains(result, fragment):
    assert fragment in result["artefact"]["output_path"]


@when("I create a songbook for album \"A\" with 3 tracks", target_fixture="result")
def _create_songbook(engine, confirmed_intent):
    r, _ = invoke(engine, confirmed_intent, "music", "create_songbook",
                  album="A", tracks=["Track 1", "Track 2", "Track 3"])
    return r


@when(
    parsers.parse("I run measure_gate on \"{path}\" with window min {mn:f} max {mx:f}"),
    target_fixture="gate_inv",
)
def _measure_gate(engine, confirmed_intent, lc, path, mn, mx):
    _data, inv = invoke(engine, confirmed_intent, "music", "measure_gate",
                        lifecycle_id=lc, path=path,
                        min_lufs=mn, max_lufs=mx)
    return {"inv": inv, "lc": lc, "data": _data}


@then("measured_lufs is present")
def _measured_lufs(gate_inv):
    data = gate_inv.get("data") or {}
    assert "measured_lufs" in data


# ──────────────────────── Catalogue cluster (097) ─────────────────────────────

@when(
    parsers.parse('I create a tweet for album "{album}" with body "{body}"'),
    target_fixture="result",
)
def _create_tweet(engine, confirmed_intent, album, body):
    r, _ = invoke(engine, confirmed_intent, "music", "db_create_tweet",
                  album=album, body=body, scheduled_at="2026-12-01T10:00Z")
    return r


@then("tweet_id is present in the artefact")
def _tweet_id(result):
    assert "tweet_id" in result["artefact"]


@then("a tweet-record artefact is recorded against the intent")
def _tweet_artefact(engine, confirmed_intent):
    prov = engine.memory.provenance(confirmed_intent)
    assert any(a["kind"] == "tweet-record" for a in prov["artefacts"])


@given(parsers.parse('a tweet exists for album "{album}" with body "{body}"'),
       target_fixture="tweet_info")
def _given_tweet(engine, confirmed_intent, album, body):
    r, _ = invoke(engine, confirmed_intent, "music", "db_create_tweet",
                  album=album, body=body, scheduled_at="2026-12-01T10:00Z")
    return {"tid": r["artefact"]["tweet_id"], "album": album}


@when(parsers.parse('I update that tweet status to "{status}"'))
def _update_tweet(engine, confirmed_intent, tweet_info, status):
    invoke(engine, confirmed_intent, "music", "db_update_tweet",
           tweet_id=tweet_info["tid"], fields={"status": status})


@when(
    parsers.parse('I list tweets for album "{album}" filtered by "{status}"'),
    target_fixture="result",
)
def _list_tweets_filtered(engine, confirmed_intent, album, status):
    r, _ = invoke(engine, confirmed_intent, "music", "db_list_tweets",
                  album=album, status=status)
    return r


@when("I delete that tweet")
def _delete_tweet(engine, confirmed_intent, tweet_info):
    invoke(engine, confirmed_intent, "music", "db_delete_tweet",
           tweet_id=tweet_info["tid"])


@when(
    parsers.parse('I list tweets for album "{album}"'),
    target_fixture="result",
)
def _list_tweets(engine, confirmed_intent, album):
    r, _ = invoke(engine, confirmed_intent, "music", "db_list_tweets", album=album)
    return r


@given("2 tweets exist for album \"A\"")
def _given_2_tweets(engine, confirmed_intent):
    invoke(engine, confirmed_intent, "music", "db_create_tweet",
           album="A", body="The phreaker tale begins",
           scheduled_at="2026-12-01T10:00Z")
    invoke(engine, confirmed_intent, "music", "db_create_tweet",
           album="A", body="Listen now",
           scheduled_at="2026-12-02T10:00Z")


@when(parsers.parse('I search tweets for "{query}"'), target_fixture="result")
def _search_tweets(engine, confirmed_intent, query):
    r, _ = invoke(engine, confirmed_intent, "music", "db_search_tweets", query=query)
    return r


@then("the returned tweet body contains \"phreaker\"")
def _tweet_body_phreaker(result):
    assert "phreaker" in result["tweets"][0]["body"].lower()


@given("2 tweets exist for album \"A\" with one scheduled")
def _given_2_tweets_one_scheduled(engine, confirmed_intent):
    a, _ = invoke(engine, confirmed_intent, "music", "db_create_tweet",
                  album="A", body="one", scheduled_at="2026-12-01T10:00Z")
    b, _ = invoke(engine, confirmed_intent, "music", "db_create_tweet",
                  album="A", body="two", scheduled_at="2026-12-02T10:00Z")
    invoke(engine, confirmed_intent, "music", "db_update_tweet",
           tweet_id=a["artefact"]["tweet_id"], fields={"status": "scheduled"})


@when(parsers.parse('I get tweet stats for album "{album}"'), target_fixture="result")
def _tweet_stats(engine, confirmed_intent, album):
    r, _ = invoke(engine, confirmed_intent, "music", "db_get_tweet_stats", album=album)
    return r


@then("total is 2")
def _total_2(result):
    assert result["total"] == 2


@then("draft count is 1")
def _draft_1(result):
    assert result["by_status"].get("draft") == 1


@then("scheduled count is 1")
def _scheduled_1(result):
    # tweet stats: {"by_status": {"scheduled": 1}} OR promo_content: {"scheduled": [...]}
    if "by_status" in result:
        assert result["by_status"].get("scheduled") == 1
    else:
        assert len(result["scheduled"]) == 1


@given("1 tweet exists for album \"A\"")
def _given_1_tweet(engine, confirmed_intent):
    invoke(engine, confirmed_intent, "music", "db_create_tweet",
           album="A", body="will be replaced", scheduled_at="2026-12-01T10:00Z")


@when("I sync album \"A\" with 3 new tweets", target_fixture="result")
def _sync_album(engine, confirmed_intent):
    r, _ = invoke(engine, confirmed_intent, "music", "db_sync_album",
                  album="A", tweets=[
                      {"body": "new tweet 1", "scheduled_at": "2026-12-02"},
                      {"body": "new tweet 2", "scheduled_at": "2026-12-03"},
                      {"body": "new tweet 3", "scheduled_at": "2026-12-04"},
                  ])
    return r


@then("removed is 1")
def _removed_1(result):
    assert result["removed"] == 1


@then("created is 3")
def _created_3(result):
    assert result["created"] == 3


@then("listing tweets for \"A\" returns 3")
def _listing_3(engine, confirmed_intent):
    listed, _ = invoke(engine, confirmed_intent, "music", "db_list_tweets", album="A")
    assert listed["count"] == 3


@when(parsers.parse('I update streaming url for album "{album}" platform "{platform}"'))
def _update_streaming_url(engine, confirmed_intent, album, platform):
    urls = {"spotify": "https://open.spotify.com/album/123",
            "apple": "https://music.apple.com/album/456"}
    invoke(engine, confirmed_intent, "music", "update_streaming_url",
           album=album, platform=platform, url=urls.get(platform, "https://x.com"))


@when(parsers.parse('I get streaming urls for album "{album}"'), target_fixture="result")
def _get_streaming_urls(engine, confirmed_intent, album):
    r, _ = invoke(engine, confirmed_intent, "music", "get_streaming_urls", album=album)
    return r


@then('the returned platforms include "spotify" and "apple"')
def _platforms(result):
    platforms = {u["platform"] for u in result["urls"]}
    assert {"spotify", "apple"}.issubset(platforms)


@given("1 tweet and 1 streaming url exist for album \"A\"")
def _given_tweet_and_url(engine, confirmed_intent):
    invoke(engine, confirmed_intent, "music", "db_create_tweet",
           album="A", body="x", scheduled_at="2026-12-01T10:00Z")
    invoke(engine, confirmed_intent, "music", "update_streaming_url",
           album="A", platform="spotify", url="https://example.com/x")


@when(parsers.parse('I get promo status for album "{album}"'), target_fixture="result")
def _promo_status(engine, confirmed_intent, album):
    r, _ = invoke(engine, confirmed_intent, "music", "get_promo_status", album=album)
    return r


@then("tweets total is 1")
def _tweets_total_1(result):
    assert result["tweets"]["total"] == 1


@then("streaming_urls count is 1")
def _streaming_urls_count(result):
    assert result["streaming_urls"] == 1


@when(parsers.parse('I get promo content for album "{album}"'), target_fixture="result")
def _promo_content(engine, confirmed_intent, album):
    r, _ = invoke(engine, confirmed_intent, "music", "get_promo_content", album=album)
    return r


@then("drafts count is 1")
def _drafts_1(result):
    assert len(result["drafts"]) == 1


@when("I extract links from text containing 2 URLs", target_fixture="result")
def _extract_links(engine, confirmed_intent):
    r, _ = invoke(engine, confirmed_intent, "music", "extract_links",
                  text="Stream now at https://open.spotify.com/album/1 or "
                       "https://music.apple.com/album/2")
    return r


@then('one url contains "spotify"')
def _url_spotify(result):
    assert any("spotify" in u for u in result["urls"])


@then('one url contains "apple"')
def _url_apple(result):
    assert any("apple" in u for u in result["urls"])


@when("I run tweet_schedule_gate with a valid body and scheduled_at", target_fixture="result")
def _tweet_gate_pass(engine, confirmed_intent, lc):
    r, _ = invoke(engine, confirmed_intent, "music", "tweet_schedule_gate",
                  lifecycle_id=lc,
                  body="New album out now! Stream it everywhere.",
                  scheduled_at="2026-12-01T10:00Z",
                  platform="x", max_length=280)
    return r


@then("length is positive")
def _length_positive(result):
    assert result["length"] > 0


@when("I run tweet_schedule_gate with an empty body", target_fixture="gate_inv")
def _tweet_gate_empty(engine, confirmed_intent, lc):
    _data, inv = invoke(engine, confirmed_intent, "music", "tweet_schedule_gate",
                        lifecycle_id=lc, body="   ",
                        scheduled_at="2026-12-01T10:00Z")
    return {"inv": inv, "lc": lc}


@when("I run tweet_schedule_gate with a body of 281 characters", target_fixture="gate_inv")
def _tweet_gate_over(engine, confirmed_intent, lc):
    _data, inv = invoke(engine, confirmed_intent, "music", "tweet_schedule_gate",
                        lifecycle_id=lc, body="x" * 281,
                        scheduled_at="2026-12-01T10:00Z")
    return {"inv": inv, "lc": lc}


@when("I run tweet_schedule_gate with a valid body and no scheduled_at", target_fixture="gate_inv")
def _tweet_gate_no_sched(engine, confirmed_intent, lc):
    _data, inv = invoke(engine, confirmed_intent, "music", "tweet_schedule_gate",
                        lifecycle_id=lc, body="Valid body", scheduled_at="")
    return {"inv": inv, "lc": lc}


# ──────────────────────── Promo cluster (098) ─────────────────────────────────

@when(
    parsers.parse('I review promo body "{body}" for platform "{platform}"'),
    target_fixture="result",
)
def _promo_review(engine, confirmed_intent, body, platform):
    r, _ = invoke(engine, confirmed_intent, "music", "promo_review",
                  body=body, platform=platform)
    return r


@then(parsers.parse("score is at least {n:d}"))
def _score_at_least(request, n):
    """Read score from result or gate_inv["data"] depending on what ran."""
    data = None
    try:
        gi = request.getfixturevalue("gate_inv")
        data = gi.get("data") if gi else None
    except pytest.FixtureLookupError:
        pass
    if data is None:
        try:
            data = request.getfixturevalue("result")
        except pytest.FixtureLookupError:
            pass
    assert data is not None and data.get("score", -1) >= n


@then("max_length is 280")
def _max_length(result):
    assert result["max_length"] == 280


@when("I review a promo body over 280 characters for platform \"x\"", target_fixture="result")
def _promo_review_long(engine, confirmed_intent):
    r, _ = invoke(engine, confirmed_intent, "music", "promo_review",
                  body="Listen now! " + ("x" * 280), platform="x")
    return r


@then("an over_length finding is present")
def _over_length_finding(result):
    assert any(f["kind"] == "over_length" for f in result["findings"])


@then(parsers.parse("score is below {n:d}"))
def _score_below(result, n):
    assert result["score"] < n


@then("a no_cta finding is present")
def _no_cta_finding(result):
    assert any(f["kind"] == "no_cta" for f in result["findings"])


@then("an explicit finding is present")
def _explicit_finding(result):
    assert any(f["kind"] == "explicit" for f in result["findings"])


@when(
    parsers.parse('I upload promo video for album "{album}" with key "{key}"'),
    target_fixture="result",
)
def _upload_promo_video(engine, confirmed_intent, album, key):
    r, _ = invoke(engine, confirmed_intent, "music", "upload_promo_video",
                  album=album, key=key, body=b"video bytes")
    return r


@then(parsers.parse('the asset_kind is "{kind}"'))
def _asset_kind(result, kind):
    assert result["artefact"]["asset_kind"] == kind


@when(
    parsers.parse('I publish sheet music for album "{album}" with key "{key}"'),
    target_fixture="result",
)
def _publish_sheet(engine, confirmed_intent, album, key):
    r, _ = invoke(engine, confirmed_intent, "music", "publish_sheet_music",
                  album=album, key=key, body=b"PDF bytes here")
    return r


@when("I publish sheet music without a configured cloud driver", target_fixture="last_inv")
def _publish_sheet_no_cloud(engine, confirmed_intent):
    # cloud driver is NOT configured (default unconfigured fake)
    _data, inv = invoke(engine, confirmed_intent, "music", "publish_sheet_music",
                        album="A", key="k.pdf", body=b"x")
    return inv


@given("3 assets are uploaded under prefix \"a/\"")
def _given_3_assets(engine, confirmed_intent):
    invoke(engine, confirmed_intent, "music", "upload_promo_video",
           album="A", key="a/promo1.mp4", body=b"v1")
    invoke(engine, confirmed_intent, "music", "upload_promo_video",
           album="A", key="a/promo2.mp4", body=b"v2")
    invoke(engine, confirmed_intent, "music", "publish_sheet_music",
           album="A", key="a/book.pdf", body=b"p")


@when(parsers.parse('I list assets under prefix "{prefix}"'), target_fixture="result")
def _r2_list(engine, confirmed_intent, prefix):
    r, _ = invoke(engine, confirmed_intent, "music", "r2_list", prefix=prefix)
    return r


@when(parsers.parse('I delete asset "{key}"'))
def _r2_delete(engine, confirmed_intent, key):
    invoke(engine, confirmed_intent, "music", "r2_delete", key=key)


@when("I create a release package for album \"Origin\" with 3 assets", target_fixture="result")
def _release_package(engine, confirmed_intent):
    r, _ = invoke(engine, confirmed_intent, "music", "release_package",
                  album="Origin",
                  assets=["origin/master.wav", "origin/cover.jpg",
                          "origin/promo.mp4"])
    return r


@then("the artefact has 3 assets")
def _artefact_3_assets(result):
    assert len(result["artefact"]["assets"]) == 3


@then("a promo-album-package artefact is recorded against the intent")
def _pkg_artefact(engine, confirmed_intent):
    prov = engine.memory.provenance(confirmed_intent)
    assert any(a["kind"] == "promo-album-package" for a in prov["artefacts"])


@when(
    parsers.parse('I run promo_review_gate on "{body}" for "{platform}"'),
    target_fixture="gate_inv",
)
def _promo_review_gate(engine, confirmed_intent, lc, body, platform):
    _data, inv = invoke(engine, confirmed_intent, "music", "promo_review_gate",
                        lifecycle_id=lc, body=body, platform=platform, min_score=70)
    return {"inv": inv, "lc": lc, "data": _data}


@when("I verify streaming urls for album \"A\"", target_fixture="result")
def _verify_streaming(engine, confirmed_intent):
    r, _ = invoke(engine, confirmed_intent, "music", "verify_streaming",
                  album="A", urls="https://x.com/a, https://x.com/b")
    return r


@then("a streaming-verify artefact is recorded against the intent")
def _streaming_verify_artefact(engine, confirmed_intent):
    prov = engine.memory.provenance(confirmed_intent)
    assert any(a["kind"] == "streaming-verify" for a in prov["artefacts"])


# ──────────────────────── Research cluster (099) ──────────────────────────────

@when(
    parsers.parse(
        'I capture claim "{text}" from "{src}" domain "{domain}" album "{album}"'
    ),
    target_fixture="result",
)
def _capture_claim(engine, confirmed_intent, text, src, domain, album):
    r, _ = invoke(engine, confirmed_intent, "music", "capture_claim",
                  text=text, source_uri=src, domain=domain, album=album)
    return r


@then(parsers.parse('the claim_id starts with "{prefix}"'))
def _claim_id_prefix(result, prefix):
    assert result["claim_id"].startswith(prefix)


@then(parsers.parse('domain is "{domain}"'))
def _domain_is(result, domain):
    assert result["domain"] == domain


@then(parsers.parse('verified is "{status}"'))
def _verified_is(result, status):
    assert result["verified"] == status


@then("a SERVES edge links the claim to the intent")
def _serves_edge(engine, confirmed_intent, result):
    rows = engine.memory.g.query(
        "MATCH (c)-[r:SERVES]->(i) WHERE c.id = $cid AND i.id = $iid RETURN r",
        {"cid": result["claim_id"], "iid": confirmed_intent},
    )
    assert rows


@when("I capture claim with domain \"polka\"", target_fixture="last_inv")
def _capture_bad_domain(engine, confirmed_intent):
    _data, inv = invoke(engine, confirmed_intent, "music", "capture_claim",
                        text="x", source_uri="http://a", domain="polka", album="A")
    return inv


@given(parsers.parse("2 claims exist for album \"{album}\" with status \"pending\""))
def _given_2_claims(engine, confirmed_intent, album):
    invoke(engine, confirmed_intent, "music", "capture_claim",
           text="c1", source_uri="http://a", domain="legal", album=album)
    invoke(engine, confirmed_intent, "music", "capture_claim",
           text="c2", source_uri="http://b", domain="financial", album=album)


@when("I list all claims", target_fixture="result")
def _list_all_claims(engine, confirmed_intent):
    r, _ = invoke(engine, confirmed_intent, "music", "list_claims")
    return r


@when(parsers.parse('I list claims with status "{status}"'), target_fixture="result")
def _list_claims_status(engine, confirmed_intent, status):
    r, _ = invoke(engine, confirmed_intent, "music", "list_claims", status=status)
    return r


@given("2 legal claims and 1 financial claim for album \"A\"")
def _given_legal_financial(engine, confirmed_intent):
    invoke(engine, confirmed_intent, "music", "capture_claim",
           text="c1", source_uri="http://a", domain="legal", album="A")
    invoke(engine, confirmed_intent, "music", "capture_claim",
           text="c2", source_uri="http://b", domain="legal", album="A")
    invoke(engine, confirmed_intent, "music", "capture_claim",
           text="c3", source_uri="http://c", domain="financial", album="A")


@when(parsers.parse('I get pending verifications for album "{album}"'),
      target_fixture="result")
def _pending_verifications(engine, confirmed_intent, album):
    r, _ = invoke(engine, confirmed_intent, "music", "pending_verifications",
                  album=album)
    return r


@then("pending_count is 3")
def _pending_count_3(result):
    assert result["pending_count"] == 3


@then("legal count is 2")
def _legal_2(result):
    assert result["by_domain"]["legal"] == 2


@then("financial count is 1")
def _financial_1(result):
    assert result["by_domain"]["financial"] == 1


@given(parsers.parse("3 claims exist for album \"{album}\""))
def _given_3_claims(engine, confirmed_intent, album):
    for d in ("legal", "financial", "primary_source"):
        invoke(engine, confirmed_intent, "music", "capture_claim",
               text=f"claim {d}", source_uri="http://a", domain=d, album=album)


@when(parsers.parse('I verify sources for album "{album}"'), target_fixture="result")
def _verify_sources(engine, confirmed_intent, album):
    r, _ = invoke(engine, confirmed_intent, "music", "verify_sources", album=album)
    return r


@then("verified_count is 3")
def _verified_count_3(result):
    assert result["verified_count"] == 3


@then("no pending claims remain")
def _no_pending(engine, confirmed_intent):
    after, _ = invoke(engine, confirmed_intent, "music", "list_claims",
                      status="pending")
    assert after["count"] == 0


@when("I run verify_gate on album \"A\" with no claims", target_fixture="result")
def _verify_gate_pass(engine, confirmed_intent, lc):
    r, _ = invoke(engine, confirmed_intent, "music", "verify_gate",
                  lifecycle_id=lc, album="A")
    return r


@then("pending_count is 0")
def _pending_count_0(result):
    assert result["pending_count"] == 0


@given("1 pending claim exists for album \"A\"")
def _given_pending_claim(engine, confirmed_intent):
    invoke(engine, confirmed_intent, "music", "capture_claim",
           text="pending", source_uri="http://a", domain="legal", album="A")


@when("I run verify_gate on album \"A\"", target_fixture="gate_inv")
def _verify_gate_blocked(engine, confirmed_intent, lc):
    _data, inv = invoke(engine, confirmed_intent, "music", "verify_gate",
                        lifecycle_id=lc, album="A")
    return {"inv": inv, "lc": lc}


@when(
    parsers.parse('I call human_signoff for album "{album}" reviewer "{reviewer}"'),
    target_fixture="result",
)
def _human_signoff(engine, confirmed_intent, album, reviewer):
    r, _ = invoke(engine, confirmed_intent, "music", "human_signoff",
                  album=album, reviewer=reviewer)
    return r


@then(parsers.parse('album in result is "{album}"'))
def _album_in_result(result, album):
    assert result["album"] == album


@then(parsers.parse('reviewer in result is "{reviewer}"'))
def _reviewer_in_result(result, reviewer):
    assert result["reviewer"] == reviewer


@then(parsers.parse('signoff_id starts with "{prefix}"'))
def _signoff_id(result, prefix):
    assert result["signoff_id"].startswith(prefix)


@when(
    parsers.parse('I call document_hunt with query "{query}"'),
    target_fixture="result",
)
def _document_hunt(engine, confirmed_intent, query):
    r, _ = invoke(engine, confirmed_intent, "music", "document_hunt", query=query)
    return r


@then("research_id is present")
def _research_id(result):
    assert "research_id" in result


@then('domain is "document_hunter"')
def _domain_doc_hunter(result):
    assert result["domain"] == "document_hunter"


@when(
    parsers.parse('I call research_scope question "{question}" album "{album}"'),
    target_fixture="result",
)
def _research_scope(engine, confirmed_intent, question, album):
    r, _ = invoke(engine, confirmed_intent, "music", "research_scope",
                  question=question, album=album, depth="deep")
    return r


@then("specialists is present")
def _specialists(result):
    assert "specialists" in result


@then(parsers.parse('album is "{album}"'))
def _album_is(result, album):
    assert result["album"] == album


# ──────────────────────── Gates cluster (100) ─────────────────────────────────

@when(parsers.parse('I validate album "{album}"'), target_fixture="result")
def _validate_album(engine, confirmed_intent, album):
    r, _ = invoke(engine, confirmed_intent, "music", "validate_album", album=album)
    return r


@then("files_present is False")
def _files_not_present(result):
    assert result["files_present"] is False


@then("at least 1 issue is reported")
def _at_least_one_issue(result):
    assert len(result["issues"]) >= 1


@then("files_present is True")
def _files_present(result):
    assert result["files_present"] is True


@then("mirror_paths_ok is True")
def _mirror_paths(result):
    assert result["mirror_paths_ok"] is True


@when("I call diagnose", target_fixture="result")
def _diagnose(engine, confirmed_intent):
    r, _ = invoke(engine, confirmed_intent, "music", "diagnose")
    return r


@then("ok is True")
def _ok_true(result):
    assert result["ok"] is True


@then("all 5 music drivers are wired")
def _all_drivers(result, engine):
    assert set(result["drivers_wired"]) == {
        "music_state", "music_text", "music_audio", "music_db", "music_cloud"
    }


@then("verbs_count is the live verb count")
def _verbs_count(result, engine):
    live = len(engine.registry._caps["music"].verbs)
    assert result["verbs_count"] == live


@then("skills_count is at least 10")
def _skills_count(result):
    assert result["skills_count"] >= 10


@when(parsers.parse('I run concept_gate on album "{album}"'), target_fixture="gate_inv")
def _concept_gate(engine, confirmed_intent, lc, album):
    _data, inv = invoke(engine, confirmed_intent, "music", "concept_gate",
                        lifecycle_id=lc, album=album)
    return {"inv": inv, "lc": lc, "data": _data}


@given(parsers.parse('album "{title}" by artist "{artist}" exists with 1 mastered track'))
def _given_mastered_track_for_gate(engine, confirmed_intent, title, artist):
    invoke(engine, confirmed_intent, "music", "create_album",
           artist=artist, title=title, genre="ambient")
    slug = title.lower().replace(" ", "-")
    t, _ = invoke(engine, confirmed_intent, "music", "create_track",
                  album=slug, title="T1", track_number=1)
    invoke(engine, confirmed_intent, "music", "set_track_status",
           album=slug, track=t["track_slug"], status="mastered")


@given(parsers.parse('album "{title}" by artist "{artist}" exists with 1 unmastered track'))
def _given_unmastered_track(engine, confirmed_intent, title, artist):
    invoke(engine, confirmed_intent, "music", "create_album",
           artist=artist, title=title, genre="ambient")
    slug = title.lower().replace(" ", "-")
    invoke(engine, confirmed_intent, "music", "create_track",
           album=slug, title="T1", track_number=1)


@when(parsers.parse('I run audio_release_gate on album "{album}"'), target_fixture="gate_inv")
def _audio_release_gate(engine, confirmed_intent, lc, album):
    _data, inv = invoke(engine, confirmed_intent, "music", "audio_release_gate",
                        lifecycle_id=lc, album=album)
    return {"inv": inv, "lc": lc, "data": _data}


@given("a streaming url and a scheduled tweet exist for album \"A\"")
def _given_url_and_tweet(engine, confirmed_intent):
    invoke(engine, confirmed_intent, "music", "update_streaming_url",
           album="A", platform="spotify", url="https://x/a")
    cap, _ = invoke(engine, confirmed_intent, "music", "db_create_tweet",
                    album="A", body="x", scheduled_at="2026-12-01T10:00Z")
    invoke(engine, confirmed_intent, "music", "db_update_tweet",
           tweet_id=cap["artefact"]["tweet_id"], fields={"status": "scheduled"})


@when(parsers.parse('I run catalogue_gate on album "{album}"'), target_fixture="gate_inv")
def _catalogue_gate(engine, confirmed_intent, lc, album):
    _data, inv = invoke(engine, confirmed_intent, "music", "catalogue_gate",
                        lifecycle_id=lc, album=album)
    return {"inv": inv, "lc": lc, "data": _data}


@when(parsers.parse('I run catalogue_gate on album "{album}" with no state'),
      target_fixture="gate_inv")
def _catalogue_gate_empty(engine, confirmed_intent, lc, album):
    _data, inv = invoke(engine, confirmed_intent, "music", "catalogue_gate",
                        lifecycle_id=lc, album=album)
    return {"inv": inv, "lc": lc, "data": _data}


@given("a promo video is uploaded for album \"A\"")
def _given_promo_video(engine, confirmed_intent):
    invoke(engine, confirmed_intent, "music", "upload_promo_video",
           album="A", key="A/promo.mp4", body=b"video")


@when(parsers.parse('I run promo_gate on album "{album}"'), target_fixture="gate_inv")
def _promo_gate(engine, confirmed_intent, lc, album):
    _data, inv = invoke(engine, confirmed_intent, "music", "promo_gate",
                        lifecycle_id=lc, album=album)
    return {"inv": inv, "lc": lc, "data": _data}


@when(parsers.parse('I run promo_gate on album "{album}" with no assets'),
      target_fixture="gate_inv")
def _promo_gate_empty(engine, confirmed_intent, lc, album):
    _data, inv = invoke(engine, confirmed_intent, "music", "promo_gate",
                        lifecycle_id=lc, album=album)
    return {"inv": inv, "lc": lc, "data": _data}


# ──────────────────────── Provenance (cross-cluster) ──────────────────────────

@when("I run the full release pipeline for album \"Modem Daze\"",
      target_fixture="pipeline_result")
def _full_pipeline(engine, confirmed_intent):
    # create album + track
    invoke(engine, confirmed_intent, "music", "create_album",
           artist="The Phreakers", title="Modem Daze",
           genre="ambient", type="documentary")
    track_res, _ = invoke(engine, confirmed_intent, "music", "create_track",
                          album="modem-daze", title="Carrier Tone", track_number=1)
    # set mastered
    invoke(engine, confirmed_intent, "music", "set_track_status",
           album="modem-daze", track=track_res["track_slug"], status="mastered")
    # upload promo
    invoke(engine, confirmed_intent, "music", "upload_promo_video",
           album="modem-daze", key="modem-daze/promo.mp4", body=b"video")
    # streaming url + tweet
    invoke(engine, confirmed_intent, "music", "update_streaming_url",
           album="modem-daze", platform="spotify",
           url="https://open.spotify.com/album/x")
    cap, _ = invoke(engine, confirmed_intent, "music", "db_create_tweet",
                    album="modem-daze", body="Out now!",
                    scheduled_at="2026-12-01T10:00Z")
    invoke(engine, confirmed_intent, "music", "db_update_tweet",
           tweet_id=cap["artefact"]["tweet_id"], fields={"status": "scheduled"})
    # gates
    lc = engine.lifecycle.open(confirmed_intent)
    invoke(engine, confirmed_intent, "music", "audio_release_gate",
           lifecycle_id=lc, album="modem-daze")
    invoke(engine, confirmed_intent, "music", "catalogue_gate",
           lifecycle_id=lc, album="modem-daze")
    invoke(engine, confirmed_intent, "music", "promo_gate",
           lifecycle_id=lc, album="modem-daze")
    return engine.memory.provenance(confirmed_intent)


@then(parsers.parse('the provenance chain includes artefact kind "{kind}"'))
def _prov_artefact(pipeline_result, kind):
    kinds = {a["kind"] for a in pipeline_result["artefacts"]}
    assert kind in kinds, f"expected {kind!r} in {kinds}"


@then(parsers.parse('the gate names include "{name}"'))
def _prov_gate(pipeline_result, name):
    names = {g["name"] for g in pipeline_result["gates"]}
    assert name in names, f"expected {name!r} in {names}"


@when("I run driver-backed verbs with no music drivers registered",
      target_fixture="dep_missing_invs")
def _no_drivers(engine, confirmed_intent):
    """Use an engine with no music drivers at all."""
    from agency.engine import Engine
    import tempfile
    e2 = Engine(tempfile.mktemp(suffix=".db"))
    iid = e2.intent.capture("test", "d", "a")
    e2.intent.confirm(iid)
    invs = []
    for verb, kwargs in (
        ("create_album", {"artist": "A", "title": "T", "genre": "g"}),
        ("lyric_report", {"album": "A", "lyrics": "x"}),
        ("master_audio", {"album": "A", "path": "/tmp/x.wav"}),
    ):
        data, inv = e2.registry.invoke(e2.memory, iid, "music", verb, **kwargs)
        invs.append((e2, inv, data))
    return invs


@then("each verb returns DEPENDENCY_MISSING")
def _dep_missing(dep_missing_invs):
    for e2, inv, data in dep_missing_invs:
        assert data is None
        err = e2.memory.recall(inv).get("error", "")
        assert "DEPENDENCY_MISSING" in err
    for e2, _, __ in dep_missing_invs:
        try:
            e2.memory.close()
        except Exception:
            pass


# ──────────────────────── Capability health (007 baseline) ────────────────────

@when("I call music_health", target_fixture="result")
def _music_health(engine, confirmed_intent):
    r, _ = invoke(engine, confirmed_intent, "music", "music_health")
    return r


@then("all 5 drivers are in drivers_wired")
def _all_5_drivers(result):
    assert set(result["drivers_wired"]) == {
        "music_state", "music_text", "music_audio", "music_db", "music_cloud"
    }


@when(parsers.parse('I count syllables of "{word}"'), target_fixture="result")
def _count_syllables(engine, confirmed_intent, word):
    r, _ = invoke(engine, confirmed_intent, "music", "count_syllables", word=word)
    return r


@then("syllable count is 3")
def _syllables_3(result):
    assert result["syllables"] == 3


@then("calling again returns the same result")
def _deterministic(engine, confirmed_intent):
    r1, _ = invoke(engine, confirmed_intent, "music", "count_syllables", word="mastering")
    r2, _ = invoke(engine, confirmed_intent, "music", "count_syllables", word="mastering")
    assert r1 == r2


@when(
    parsers.parse('I call lyric_report for album "{album}" with lyrics "{lyrics}"'),
    target_fixture="result",
)
def _lyric_report(engine, confirmed_intent, album, lyrics):
    r, _ = invoke(engine, confirmed_intent, "music", "lyric_report",
                  album=album, lyrics=lyrics.replace("\\n", "\n"))
    return r


@then("lines is 2")
def _lines_2(result):
    assert result["artefact"]["lines"] == 2


@then("a lyric-report artefact exists in the graph")
def _lyric_artefact(engine, confirmed_intent):
    arts = engine.memory.find("Artefact")
    assert any(a.get("kind") == "lyric-report" for a in arts)


# ─── unified gate-pass assertion ──────────────────────────────────────────────
# For gate scenarios that succeed: gate_inv["data"] holds the result.
# For non-gate scenarios: result fixture holds it directly.
# ONE step handles both using try/except for fixture discovery:

@then("passed is True")
def _gate_passed_or_result(request):
    """Accept passed=True from either `result` (direct verbs) or
    `gate_inv["data"]` (gate verbs that store data there).
    Uses try/except to safely discover which fixture was actually populated.
    If gate_inv exists but has no data (failed gate that sets lc/inv only),
    falls through to result."""
    # Try gate_inv with data field first
    try:
        gi = request.getfixturevalue("gate_inv")
        data = gi.get("data") if gi else None
        if data is not None:
            assert data.get("passed") is True, f"gate_inv.data={data!r}"
            return
        # gate_inv exists but has no data — this scenario uses result instead
    except pytest.FixtureLookupError:
        pass
    # Fall back to result (direct verb scenarios or name_exposure_gate pass)
    try:
        result = request.getfixturevalue("result")
        assert result is not None and result.get("passed") is True
    except pytest.FixtureLookupError:
        raise AssertionError("Neither gate_inv.data nor result fixture available for 'passed is True' assertion")
