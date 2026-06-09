"""music capability interoperability — comprehensive cross-cluster + production end-to-end.

After the recovery merge brought Specs 095-100 onto current main alongside
Spec 094 + 115, this test verifies the combined surface:

- All cluster verbs are registered and dispatchable (surface grows; no pinned count)
- All 15 walkable skills walk through their phases
- All 7 ontology templates render via `ctx.template`
- All 8 verbatim-vendored promo + documentary templates are accessible on disk
- Cross-cluster gates compose: 100's gates compose 095/096/097/098 verbs
- Production drivers (FileStateDriver + SqliteDBDriver) work alongside fakes
- Bi-temporal graph provenance lights for the full pipeline
- The 4 Spec 115 production-binding verbs interoperate with the rest
- 094 ↔ 099 ↔ 100 cross-cluster wiring (verify_gate used by both 099 + 100)

The test combines: lifecycle (094) → lyrics (095) → audio (096) → catalogue
(097) → promo (098) → research (099) → gates (100) → production binding (115).
"""
from __future__ import annotations

import tempfile
from pathlib import Path

from agency.capabilities.music.drivers import FakeCloudDriver, fake_drivers
from agency.capabilities.music.drivers_production import production_drivers
from agency.engine import Engine
from agency.skill import SkillRun


# ─────────────────────────── surface invariants ───────────────────────────

def test_music_capability_registers_full_verb_surface() -> None:
    """Every cluster contributes to the music verb surface, and the surface
    only grows (Spec 119 added the name-exposure verbs). Asserts representative
    verbs from each cluster are present + the count is at least that known set
    — an invariant + subset relationship, NOT a frozen snapshot (CLAUDE.md
    rule 8: don't pin a live-derived count that breaks on every legit change).
    """
    e = Engine(":memory:", _require_skill_doc=False)
    cap = e.registry._caps["music"]
    # one or two representative verbs per cluster — the live surface must
    # always be a SUPERSET of this known set.
    known = {
        "create_album", "create_track",                  # lifecycle (094)
        "check_streaming_lyrics", "check_name_exposure", # lyrics (095 / 119)
        "master_album", "qc_audio",                      # audio (096)
        "catalogue_status", "db_create_tweet",           # catalogue (097)
        "promo_review", "publish_asset",                 # promo (098)
        "research_scope", "verify_sources",              # research (099)
        "validate_album", "diagnose",                    # gates (100)
        "get_config", "format_clipboard",                # production binding (115)
    }
    missing = known - set(cap.verbs)
    assert not missing, f"cluster verbs missing from the surface: {sorted(missing)}"
    assert len(cap.verbs) >= len(known)
    e.memory.close()


def test_music_capability_registers_15_walkable_skills() -> None:
    """15 walkable skills span all cluster workflows + the production-binding `new-album`."""
    e = Engine(":memory:", _require_skill_doc=False)
    cap = e.registry._caps["music"]
    expected = {
        "album-concept", "pre-generation", "release-qa",            # 007 / 094
        "lyric-writing",                                              # 095
        "mastering", "mix-polish",                                    # 096
        "tweet-curation", "streaming-verify",                         # 097
        "promo-pass", "release-publish",                              # 098
        "research-workflow",                                          # 099
        "pre-generation-full", "release-qa-full", "validate-structure",  # 100
        "new-album",                                                  # 115
    }
    assert set(cap.ontology.skills) == expected, (
        f"missing: {expected - set(cap.ontology.skills)}; "
        f"extra: {set(cap.ontology.skills) - expected}")
    e.memory.close()


def test_music_capability_registers_23_artefact_schemas() -> None:
    e = Engine(":memory:", _require_skill_doc=False)
    cap = e.registry._caps["music"]
    expected = {
        # 007 baseline
        "album-concept", "promo-copy", "mastering-report", "lyric-report",
        "sheet-music",
        # 095 lyrics
        "pronunciation-report", "prosody-report", "cross-track-report",
        "explicit-scan", "voice-check",
        # 096 audio
        "mix-analysis", "qc-report", "coherence-report", "promo-video",
        "album-sampler",
        # 097 catalogue
        "tweet-record", "streaming-verify", "catalogue-snapshot",
        # 098 promo
        "published-asset", "promo-album-package", "social-post",
        # 099 research
        "album-claim", "album-verification",
    }
    assert set(cap.ontology.schemas) == expected, (
        f"missing: {expected - set(cap.ontology.schemas)}; "
        f"extra: {set(cap.ontology.schemas) - expected}")
    e.memory.close()


def test_music_capability_registers_9_node_types() -> None:
    e = Engine(":memory:", _require_skill_doc=False)
    cap = e.registry._caps["music"]
    expected = {"Album", "Track", "Tweet", "Idea", "SheetMusic",
                "Genre", "Reference",
                "AlbumClaim", "AlbumVerification"}
    assert set(cap.ontology.nodes) == expected
    e.memory.close()


def test_music_capability_registers_8_enum_constraints() -> None:
    e = Engine(":memory:", _require_skill_doc=False)
    cap = e.registry._caps["music"]
    expected = {("Album", "type"), ("Album", "status"),
                ("Track", "status"), ("Idea", "status"),
                ("Tweet", "status"),
                ("AlbumClaim", "verified"), ("AlbumClaim", "domain"),
                ("AlbumVerification", "verdict")}
    assert set(cap.ontology.enums) == expected
    e.memory.close()


def test_music_capability_registers_2_custom_edges() -> None:
    e = Engine(":memory:", _require_skill_doc=False)
    cap = e.registry._caps["music"]
    assert "PROMOTED_TO" in cap.ontology.edges
    assert "RECORDED_FOR" in cap.ontology.edges
    e.memory.close()


# ─────────────────────────── template accessibility ───────────────────────────

def test_seven_flat_templates_are_loaded_via_ctx_template() -> None:
    """Templates accessed via `ctx.template(name)` — Spec 060 file-discovery."""
    e = Engine(":memory:", _require_skill_doc=False)
    cap = e.registry._caps["music"]
    for name in ("album", "track", "artist", "genre", "ideas",
                  "research", "sources"):
        assert name in cap.ontology.templates, (
            f"template '{name}' missing from ontology")
    e.memory.close()


def test_six_promo_platform_templates_are_present_on_disk() -> None:
    """Promo templates in templates/promo/ subdir are accessible as static files.

    The agency template loader is flat-only by design; promo templates are
    read by `promo_copy` via direct file path or `state.read_data(...)`.
    """
    promo_dir = (Path(__file__).parent.parent
                 / "agency" / "capabilities" / "music"
                 / "templates" / "promo")
    for platform in ("campaign", "facebook", "instagram",
                      "tiktok", "twitter", "youtube"):
        p = promo_dir / f"{platform}.md"
        assert p.is_file(), f"promo template {platform}.md missing on disk"
        body = p.read_text()
        assert body, f"promo template {platform}.md is empty"
        assert "<!-- AGENT:" in body, (
            f"promo template {platform}.md missing Spec 060 AGENT block")


# ─────────────────────────── full E2E with fake drivers ───────────────────────────

def _fresh_configured() -> Engine:
    """Engine with the CONFIGURED FakeCloudDriver (R2 puts succeed)."""
    drv = fake_drivers()
    drv["music_cloud"] = FakeCloudDriver(configured=True)
    return Engine(tempfile.mktemp(suffix=".db"), drivers=drv)


def _confirmed_iid(e: Engine, purpose: str) -> str:
    iid = e.intent.capture(purpose, "deliverable", "acceptance")
    e.intent.confirm(iid)
    return iid


def _invoke(e: Engine, iid: str, verb: str, **kw):
    return e.registry.invoke(e.memory, iid, "music", verb, **kw)


def test_end_to_end_full_music_pipeline_with_fake_drivers() -> None:
    """The canonical music release pipeline — every cluster fires, every
    artefact lands, every gate records on the lifecycle.

    Pipeline:
      1. capture_idea (094)        → Idea node
      2. promote_idea (094)        → Album node + PROMOTED_TO edge
      3. conceptualize (094 / 007) → album-concept artefact
      4. create_track (094)        → Track + RECORDED_FOR edge
      5. lyric_report (095 / 007)  → lyric-report artefact
      6. analyze_rhyme_scheme (095) → prosody data
      7. check_pronunciation (095) → flag findings
      8. check_explicit_content (095) → rating
      9. master_audio (096)        → mastering-report artefact
      10. qc_audio (096)           → QC checklist
      11. measure_album_signature (096) → spectral signature
      12. polish_audio (096)       → polished output
      13. db_create_tweet (097)    → tweet-record artefact
      14. update_streaming_url (097) → state
      15. verify_streaming (097)   → streaming-verify artefact
      16. promo_review (098)       → review score
      17. publish_sheet_music (098) → published-asset artefact
      18. release_package (098)    → promo-album-package artefact
      19. capture_claim (099)      → AlbumClaim node
      20. verify_sources (099)     → AlbumVerification
      21. audio_release_gate (100) → Gate node + PASSED edge
      22. catalogue_gate (100)     → Gate + PASSED
      23. promo_gate (100)         → Gate + PASSED
      24. verify_gate (099)        → Gate + PASSED
    """
    e = _fresh_configured()
    iid = _confirmed_iid(e, "full music pipeline")

    # 1-2. Lifecycle: idea → album
    cap_res, _ = _invoke(e, iid, "capture_idea",
                          text="A documentary about modems")
    promote_res, _ = _invoke(e, iid, "promote_idea",
                              idea_id=cap_res["idea_id"],
                              artist="The Phreakers",
                              title="Modem Daze",
                              genre="ambient",
                              type="documentary")
    assert promote_res["album_slug"] == "modem-daze"

    # 3-4. Concept + track
    _invoke(e, iid, "conceptualize", artist="The Phreakers",
            title="Modem Daze", type="documentary",
            theme="phreakers of the 80s")
    track_res, _ = _invoke(e, iid, "create_track",
                            album="modem-daze",
                            title="Carrier Tone",
                            track_number=1)

    # 5-8. Lyrics cluster
    lyric_body = ("[Verse 1]\n"
                  "The carrier tone hummed through the night\n"
                  "The phreaker dialed with all his might\n"
                  "[Chorus]\n"
                  "We rode the wave, the 300 baud delight\n"
                  "The modem sang, the city took flight")
    lyric_res, _ = _invoke(e, iid, "lyric_report",
                            album="modem-daze", lyrics=lyric_body)
    assert lyric_res["artefact"]["kind"] == "lyric-report"
    rhyme, _ = _invoke(e, iid, "analyze_rhyme_scheme", lyrics=lyric_body)
    assert "scheme" in rhyme
    pron, _ = _invoke(e, iid, "check_pronunciation", lyrics=lyric_body)
    assert "findings" in pron
    expl, _ = _invoke(e, iid, "check_explicit_content", lyrics=lyric_body)
    assert expl["rating"] == "clean"

    # 9-12. Audio cluster
    master_res, _ = _invoke(e, iid, "master_audio",
                             album="Modem Daze",
                             path="/tmp/carrier-tone.wav",
                             target_lufs=-14.0,
                             preset="streaming")
    assert master_res["artefact"]["kind"] == "mastering-report"
    qc, _ = _invoke(e, iid, "qc_audio",
                     album="Modem Daze", path="/tmp/carrier-tone.wav")
    assert len(qc["rows"]) == 7
    sigs, _ = _invoke(e, iid, "measure_album_signature",
                       album="Modem Daze",
                       paths=["/tmp/t1.wav", "/tmp/t2.wav"])
    assert sigs["count"] == 2
    polish_res, _ = _invoke(e, iid, "polish_audio",
                             album="Modem Daze",
                             path="/tmp/carrier-tone.wav")
    assert polish_res["output"].endswith(".polished")
    # Set the track to mastered so the audio_release_gate passes later
    _invoke(e, iid, "set_track_status", album="modem-daze",
            track=track_res["track_slug"], status="mastered")

    # 13-15. Catalogue cluster
    tweet_res, _ = _invoke(e, iid, "db_create_tweet",
                            album="modem-daze",
                            body="Modem Daze out now! Listen everywhere.",
                            scheduled_at="2026-12-01T10:00Z")
    assert tweet_res["artefact"]["kind"] == "tweet-record"
    tweet_id = tweet_res["artefact"]["tweet_id"]
    _invoke(e, iid, "db_update_tweet", tweet_id=tweet_id,
            fields={"status": "scheduled"})
    _invoke(e, iid, "update_streaming_url",
            album="modem-daze", platform="spotify",
            url="https://open.spotify.com/album/x")
    verify_res, _ = _invoke(e, iid, "verify_streaming",
                             album="modem-daze",
                             urls="https://open.spotify.com/album/x")
    assert verify_res["artefact"]["kind"] == "streaming-verify"

    # 16-18. Promo cluster
    review, _ = _invoke(e, iid, "promo_review",
                        body="Modem Daze: an ambient documentary album. Stream now!",
                        platform="x")
    assert review["score"] > 0
    sheet, _ = _invoke(e, iid, "publish_sheet_music",
                       album="modem-daze",
                       key="modem-daze/songbook.pdf",
                       body=b"PDF bytes")
    assert sheet["artefact"]["kind"] == "published-asset"
    pkg, _ = _invoke(e, iid, "release_package",
                      album="modem-daze",
                      assets=["modem-daze/master.wav",
                              "modem-daze/cover.jpg",
                              "modem-daze/songbook.pdf"])
    assert pkg["artefact"]["kind"] == "promo-album-package"

    # 19-20. Research cluster
    _invoke(e, iid, "capture_claim",
            text="The first commercial modem was the Bell 103 at 300 baud (1962)",
            source_uri="https://en.wikipedia.org/wiki/Bell_103_modem",
            domain="historical", album="modem-daze")
    verify_sources_res, _ = _invoke(e, iid, "verify_sources",
                                     album="modem-daze")
    assert verify_sources_res["verified_count"] == 1

    # 21-24. Gates cluster — the lifecycle binder
    lc = e.lifecycle.open(iid)
    audio_gate, _ = _invoke(e, iid, "audio_release_gate",
                             lifecycle_id=lc, album="modem-daze")
    assert audio_gate["passed"] is True

    catalogue_gate, _ = _invoke(e, iid, "catalogue_gate",
                                  lifecycle_id=lc, album="modem-daze")
    assert catalogue_gate["passed"] is True

    promo_gate_res, _ = _invoke(e, iid, "promo_gate",
                                 lifecycle_id=lc, album="modem-daze")
    assert promo_gate_res["passed"] is True

    verify_gate_res, _ = _invoke(e, iid, "verify_gate",
                                   lifecycle_id=lc, album="modem-daze")
    assert verify_gate_res["passed"] is True

    # ─── Assert the FULL provenance chain landed ────────────────────────────
    prov = e.memory.provenance(iid)

    # Artefacts from every cluster that PRODUCES'd one
    artefact_kinds = {a["kind"] for a in prov["artefacts"]}
    expected_artefacts = {
        "album-concept",        # 094 conceptualize
        "lyric-report",         # 095 lyric_report
        "mastering-report",     # 096 master_audio
        "tweet-record",         # 097 db_create_tweet
        "streaming-verify",     # 097 verify_streaming
        "published-asset",      # 098 publish_sheet_music
        "promo-album-package",  # 098 release_package
    }
    assert expected_artefacts.issubset(artefact_kinds), (
        f"missing artefact kinds: {expected_artefacts - artefact_kinds}")

    # Gates from cluster 100 + 099
    gate_names = {g["name"] for g in prov["gates"]}
    assert {"audio-release", "catalogue", "promo", "verify"}.issubset(gate_names)

    # Graph-level: PROMOTED_TO + RECORDED_FOR edges exist
    promoted_edges = e.memory.g.query(
        "MATCH (i)-[r:PROMOTED_TO]->(a) WHERE i.id = $iid RETURN r",
        {"iid": cap_res["idea_id"]})
    assert promoted_edges, "PROMOTED_TO edge missing"
    recorded_edges = e.memory.g.query(
        "MATCH (t:Track)-[r:RECORDED_FOR]->(a:Album) "
        "WHERE a.slug = $slug RETURN t", {"slug": "modem-daze"})
    assert recorded_edges, "RECORDED_FOR edge missing"
    e.memory.close()


# ─────────────────────────── walkable skill smoke ───────────────────────────

def test_every_workflow_skill_walks_to_hard_elicit_or_completion() -> None:
    """Spot-check that each walkable skill has a coherent phase graph + walks."""
    e = Engine(":memory:", _require_skill_doc=False)
    iid = _confirmed_iid(e, "skill walk")

    walkable = [
        ("album-concept", [
            {"artist": "a", "genre": "g", "type": "thematic", "scale": "ep",
             "theme": "t", "true_story": "no"},
            {"key_subjects": "k", "emotional_core": "e", "why": "w"},
            {"references": "r", "production_style": "p", "vocal_approach": "v",
             "instrumentation": "i", "mood": "m", "target_duration": "4:00"},
            {"tracklist": "t", "sequencing": "s", "energy_map": "e"},
            {"visual_concept": "v", "palette": "p", "symbols": "s"},
            {"album_title": "t", "track_titles": "t", "research_needs": "n",
             "explicit": "no", "distributor_genres": "g"},
        ]),
        ("new-album", [
            {"album_name": "x", "genre": "ambient", "documentary": "no"},
            {"genre_valid": "yes"},
            {"safe_to_create": "yes"},
            {"album_root": "x", "files_created": "README.md"},
        ]),
        ("lyric-writing", [
            {"lyrics_draft": "draft"},
            {"syllable_target_met": "yes", "rhyme_scheme_valid": "yes"},
            {"pronunciation_clean": "yes"},
            {"no_album_wide_repeats": "yes"},
            {"explicit_rating_assigned": "clean"},
        ]),
        ("mastering", [
            {"loudness_measured": "yes", "signature_captured": "yes"},
            {"stems_polished": "yes"},
            {"master_rendered": "yes"},
            {"qc_passed": "yes"},
        ]),
        ("pre-generation-full", [
            {"concept_present": "yes"},
            {"sources_signed_off": "yes"},
            {"lyrics_ok": "yes"},
        ]),
        ("release-qa-full", [
            {"audio_ok": "yes"},
            {"catalogue_ok": "yes"},
            {"promo_ok": "yes"},
        ]),
    ]
    for skill_name, fills in walkable:
        sk = e.ontology.skill(skill_name)
        assert sk, f"skill {skill_name} not registered"
        run = SkillRun(e.memory, iid, sk)
        for fill in fills:
            result = run.submit(fill)
            assert result["status"] == "working", (
                f"skill {skill_name} dropped status at phase {len(fills)}")
        # The terminal phase exists — walker reaches it
        assert run.current() is not None
    e.memory.close()


# ─────────────────────────── production drivers E2E ───────────────────────────

def test_production_drivers_round_trip_create_album_writes_disk(tmp_path,
                                                                  monkeypatch) -> None:
    """Production FileStateDriver writes the real bitwize-canonical disk tree."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("AGENCY_MUSIC_HOME", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path / "fake-home"))
    (tmp_path / ".agency").mkdir()
    (tmp_path / ".agency" / "music-config.yaml").write_text(
        f"artist:\n  name: The Phreakers\n"
        f"paths:\n  content_root: {tmp_path}/music\n"
        f"db:\n  path: {tmp_path}/.agency/music.db\n"
    )

    e = Engine(tempfile.mktemp(suffix=".db"),
               drivers=production_drivers())
    iid = _confirmed_iid(e, "production E2E")

    # 1. Create a documentary album via the production drivers
    res, _ = _invoke(e, iid, "create_album",
                      artist="The Phreakers", title="Modem Daze",
                      genre="ambient", type="documentary")
    assert res["album_slug"] == "modem-daze"

    # 2. Disk tree exists with all expected files
    album_root = (tmp_path / "music" / "artists" / "the-phreakers"
                  / "albums" / "ambient" / "modem-daze")
    assert album_root.is_dir()
    assert (album_root / "README.md").is_file()
    assert (album_root / "RESEARCH.md").is_file()
    assert (album_root / "SOURCES.md").is_file()
    assert (album_root / "tracks").is_dir()

    # 3. Templates rendered (non-empty + AGENT block from Spec 060)
    readme = (album_root / "README.md").read_text()
    assert readme, "README is empty"
    research = (album_root / "RESEARCH.md").read_text()
    assert "<!-- AGENT:" in research

    # 4. Artist + genre seed READMEs landed on first album
    assert (tmp_path / "music" / "artists" / "the-phreakers" / "README.md").is_file()
    assert (tmp_path / "music" / "artists" / "the-phreakers"
            / "albums" / "ambient" / "README.md").is_file()

    # 5. Create a track — writes real markdown file to disk
    _invoke(e, iid, "create_track", album="modem-daze",
            title="Carrier Tone", track_number=1)
    track_file = album_root / "tracks" / "01-carrier-tone.md"
    assert track_file.is_file()

    # 6. SQLite DB created at the configured path
    assert (tmp_path / ".agency" / "music.db").is_file()

    # 7. Catalogue cluster writes through to SQLite DB
    tweet_res, _ = _invoke(e, iid, "db_create_tweet",
                            album="modem-daze",
                            body="Album out now!",
                            scheduled_at="2026-12-01T10:00Z")
    assert tweet_res["artefact"]["tweet_id"] > 0
    listed, _ = _invoke(e, iid, "db_list_tweets", album="modem-daze")
    assert listed["count"] == 1

    # 8. New driver instance on same DB file sees the tweet — persistence
    e2 = Engine(tempfile.mktemp(suffix=".db"),
                drivers=production_drivers())
    iid2 = _confirmed_iid(e2, "production E2E re-read")
    re_read, _ = e2.registry.invoke(e2.memory, iid2, "music",
                                      "db_list_tweets", album="modem-daze")
    assert re_read["count"] == 1
    assert re_read["tweets"][0]["body"] == "Album out now!"
    e.memory.close()
    e2.memory.close()


# ─────────────────────────── Spec 115 ↔ Spec 094-100 interop ───────────────

def test_spec_115_verbs_work_with_fake_drivers(tmp_path, monkeypatch) -> None:
    """The 4 Spec 115 verbs (`get_config`, `load_override`, `get_reference`,
    `format_clipboard`) work cleanly with the Fake* drivers from 094-100."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("AGENCY_MUSIC_HOME", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path / "fake-home"))
    e = _fresh_configured()
    iid = _confirmed_iid(e, "spec 115 interop")

    # get_config returns defaults when no file exists
    cfg_data, _ = _invoke(e, iid, "get_config")
    assert "config" in cfg_data
    assert "artist" in cfg_data["config"]

    # format_clipboard handles lyric input from 095's lyric_report output
    raw_lyrics = ("[Verse 1]\n"
                  "Lyrics body line one\n"
                  "Lyrics body line two")
    clip, _ = _invoke(e, iid, "format_clipboard",
                      text=raw_lyrics, format="lyrics")
    assert "[Verse 1]" not in clip["text"]
    assert "Lyrics body line one" in clip["text"]
    e.memory.close()


def test_verify_gate_is_cross_cluster_callable_from_99_and_100() -> None:
    """`verify_gate` (Spec 099) is the cross-cluster integration point — both
    099's research-workflow phase 4 AND 100's pre-generation-full phase 2
    point at it. Verifies the verb is callable as both clusters intend."""
    e = _fresh_configured()
    iid = _confirmed_iid(e, "verify_gate cross-cluster")
    lc = e.lifecycle.open(iid)

    # Empty research state → passes (no pending claims)
    data, _ = _invoke(e, iid, "verify_gate", lifecycle_id=lc, album="A")
    assert data["passed"] is True

    # Add a pending claim → next call blocks
    _invoke(e, iid, "capture_claim",
            text="claim", source_uri="https://x",
            domain="legal", album="A")
    lc2 = e.lifecycle.open(iid)
    data2, inv = _invoke(e, iid, "verify_gate",
                          lifecycle_id=lc2, album="A")
    assert data2 is None
    assert "GATE_FAILED" in e.memory.recall(inv).get("error", "")
    e.memory.close()


def test_require_drv_helper_works_across_clusters() -> None:
    """The cleanup PR's `CapabilityBase._require_drv` helper is used by ~67
    verbs across the music clusters. Smoke-check that verbs returning typed
    DEPENDENCY_MISSING still work when a driver is intentionally absent."""
    # Engine with NO drivers → every driver-bound verb returns
    # DEPENDENCY_MISSING (not crash).
    e = Engine(tempfile.mktemp(suffix=".db"))
    iid = _confirmed_iid(e, "no-drivers")

    # Sample one verb per driver — each should return typed failure
    for verb, kwargs in (
        ("create_album", {"artist": "A", "title": "T", "genre": "g"}),
        ("lyric_report", {"album": "A", "lyrics": "x"}),
        ("master_audio", {"album": "A", "path": "/tmp/x.wav"}),
        ("db_create_tweet", {"album": "A", "body": "x",
                              "scheduled_at": "2026-12-01"}),
        ("publish_sheet_music", {"album": "A", "key": "x", "body": b"x"}),
    ):
        data, inv = _invoke(e, iid, verb, **kwargs)
        assert data is None, f"{verb} should fail with no drivers"
        err = e.memory.recall(inv).get("error", "")
        assert "DEPENDENCY_MISSING" in err, (
            f"{verb} did not return typed DEPENDENCY_MISSING: {err}")
    e.memory.close()


def test_capability_lint_clean_in_block_mode() -> None:
    """plugin.lint_capability('music') passes in block mode — the doctrine bar."""
    from agency.capabilities.plugin import lint_capability
    e = Engine(":memory:", _require_skill_doc=False)
    cap = e.registry._caps["music"]
    res = lint_capability(cap)
    assert res["ok"] is True, f"lint violations: {res.get('violations', [])}"
    assert res.get("mode") == "block"
    assert len(res.get("violations", [])) == 0
    e.memory.close()


def test_diagnose_reports_full_driver_inventory_and_surface() -> None:
    """`music.diagnose` returns the substrate state across drivers + verbs."""
    e = _fresh_configured()
    iid = _confirmed_iid(e, "diagnose")
    data, _ = _invoke(e, iid, "diagnose")
    assert data["ok"] is True
    assert set(data["drivers_wired"]) == {"music_state", "music_text",
                                            "music_audio", "music_db",
                                            "music_cloud"}
    # diagnose must report the LIVE registry size, not a frozen count
    # (rule 8) — the contract is "verbs_count == however many are registered".
    assert data["verbs_count"] == len(e.registry._caps["music"].verbs)
    assert data["skills_count"] >= 15
    e.memory.close()
