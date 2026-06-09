"""music gates cluster — Spec 100 verb + skill coverage.

4 new top-level verbs + 5 composite gate verbs + pre-generation-full +
release-qa-full + validate-structure walkable skills. NO new drivers —
gates compose existing cluster verbs + StateDriver reads + gate.check.

Spec 100 Done When: end-to-end test asserts the full provenance chain
records through the release-qa-full walk.
"""
from __future__ import annotations

import tempfile

from agency.capabilities.music.drivers import FakeCloudDriver, fake_drivers
from agency.engine import Engine
from agency.skill import SkillRun


def _fresh_configured() -> Engine:
    drv = fake_drivers()
    drv["music_cloud"] = FakeCloudDriver(configured=True)
    return Engine(tempfile.mktemp(suffix=".db"), drivers=drv)


def _confirmed_iid(e: Engine, purpose: str = "gates") -> str:
    iid = e.intent.capture(purpose, "deliverable", "acceptance")
    e.intent.confirm(iid)
    return iid


def _invoke(e: Engine, iid: str, verb: str, **kw):
    return e.registry.invoke(e.memory, iid, "music", verb, **kw)


def test_gates_cluster_verbs_discover() -> None:
    e = _fresh_configured()
    verbs = e.registry._caps["music"].verbs
    for v in ("validate_album", "validate_sections", "diagnose",
              "concept_gate", "lyrics_pregen_gate", "audio_release_gate",
              "catalogue_gate", "promo_gate"):
        assert v in verbs, f"verb {v!r} not registered"
    e.memory.close()


def test_pre_generation_full_skill_is_four_phased() -> None:
    e = _fresh_configured()
    sk = e.ontology.skill("pre-generation-full")
    assert sk["kind"] == "workflow"
    assert len(sk["phases"]) == 4
    assert sk["phases"][-1].get("gate") == "hard"
    names = [p["name"] for p in sk["phases"]]
    assert names == ["concept-ready", "research-verified",
                     "lyrics-clean", "ready-to-generate"]
    e.memory.close()


def test_release_qa_full_skill_is_four_phased() -> None:
    e = _fresh_configured()
    sk = e.ontology.skill("release-qa-full")
    assert len(sk["phases"]) == 4
    assert sk["phases"][-1].get("gate") == "hard"
    e.memory.close()


def test_validate_structure_skill_is_three_phased() -> None:
    e = _fresh_configured()
    sk = e.ontology.skill("validate-structure")
    assert len(sk["phases"]) == 3
    e.memory.close()


def test_validate_album_flags_missing_album() -> None:
    e = _fresh_configured()
    iid = _confirmed_iid(e)
    data, _ = _invoke(e, iid, "validate_album", album="nonexistent")
    assert data["files_present"] is False
    assert data["track_count"] == 0
    assert len(data["issues"]) >= 1
    e.memory.close()


def test_validate_album_passes_for_existing_album() -> None:
    e = _fresh_configured()
    iid = _confirmed_iid(e)
    _invoke(e, iid, "create_album", artist="A", title="Origin",
            genre="ambient")
    _invoke(e, iid, "create_track", album="origin", title="A1",
            track_number=1)
    data, _ = _invoke(e, iid, "validate_album", album="origin")
    assert data["files_present"] is True
    assert data["track_count"] == 1
    assert data["mirror_paths_ok"] is True
    e.memory.close()


def test_diagnose_returns_driver_inventory() -> None:
    e = _fresh_configured()
    iid = _confirmed_iid(e)
    data, _ = _invoke(e, iid, "diagnose")
    assert data["ok"] is True
    assert set(data["drivers_wired"]) == {"music_state", "music_text",
                                          "music_audio", "music_db",
                                          "music_cloud"}
    assert data["verbs_count"] > 90
    assert data["skills_count"] > 10
    e.memory.close()


def test_concept_gate_passes_when_album_exists() -> None:
    e = _fresh_configured()
    iid = _confirmed_iid(e)
    _invoke(e, iid, "create_album", artist="A", title="Origin",
            genre="ambient")
    lc = e.lifecycle.open(iid)
    data, _ = _invoke(e, iid, "concept_gate", lifecycle_id=lc,
                      album="origin")
    assert data["passed"] is True
    e.memory.close()


def test_concept_gate_blocks_when_album_missing() -> None:
    e = _fresh_configured()
    iid = _confirmed_iid(e)
    lc = e.lifecycle.open(iid)
    data, inv = _invoke(e, iid, "concept_gate", lifecycle_id=lc,
                        album="ghost")
    assert data is None
    assert "GATE_FAILED" in e.memory.recall(inv).get("error", "")
    assert e.memory.recall(lc).get("state") == "input-required"
    e.memory.close()


def test_audio_release_gate_passes_when_all_mastered() -> None:
    e = _fresh_configured()
    iid = _confirmed_iid(e)
    _invoke(e, iid, "create_album", artist="A", title="Origin",
            genre="ambient")
    t1, _ = _invoke(e, iid, "create_track", album="origin",
                    title="A1", track_number=1)
    _invoke(e, iid, "set_track_status", album="origin",
            track=t1["track_slug"], status="mastered")
    lc = e.lifecycle.open(iid)
    data, _ = _invoke(e, iid, "audio_release_gate", lifecycle_id=lc,
                      album="origin")
    assert data["passed"] is True
    e.memory.close()


def test_audio_release_gate_blocks_on_unmastered_tracks() -> None:
    e = _fresh_configured()
    iid = _confirmed_iid(e)
    _invoke(e, iid, "create_album", artist="A", title="Origin",
            genre="ambient")
    _invoke(e, iid, "create_track", album="origin",
            title="A1", track_number=1)
    lc = e.lifecycle.open(iid)
    data, inv = _invoke(e, iid, "audio_release_gate",
                        lifecycle_id=lc, album="origin")
    assert data is None
    assert "GATE_FAILED" in e.memory.recall(inv).get("error", "")
    e.memory.close()


def test_catalogue_gate_blocks_on_empty_state() -> None:
    e = _fresh_configured()
    iid = _confirmed_iid(e)
    lc = e.lifecycle.open(iid)
    data, inv = _invoke(e, iid, "catalogue_gate", lifecycle_id=lc,
                        album="A")
    assert data is None
    assert "GATE_FAILED" in e.memory.recall(inv).get("error", "")
    e.memory.close()


def test_catalogue_gate_passes_with_urls_and_scheduled_tweets() -> None:
    e = _fresh_configured()
    iid = _confirmed_iid(e)
    _invoke(e, iid, "update_streaming_url", album="A",
            platform="spotify", url="https://x/a")
    cap, _ = _invoke(e, iid, "db_create_tweet", album="A",
                     body="x", scheduled_at="2026-12-01T10:00Z")
    _invoke(e, iid, "db_update_tweet",
            tweet_id=cap["artefact"]["tweet_id"],
            fields={"status": "scheduled"})
    lc = e.lifecycle.open(iid)
    data, _ = _invoke(e, iid, "catalogue_gate", lifecycle_id=lc,
                      album="A")
    assert data["passed"] is True
    e.memory.close()


def test_promo_gate_passes_with_published_asset() -> None:
    e = _fresh_configured()
    iid = _confirmed_iid(e)
    _invoke(e, iid, "upload_promo_video", album="A",
            key="A/promo.mp4", body=b"video")
    lc = e.lifecycle.open(iid)
    data, _ = _invoke(e, iid, "promo_gate", lifecycle_id=lc, album="A")
    assert data["passed"] is True
    e.memory.close()


def test_promo_gate_blocks_with_no_assets() -> None:
    e = _fresh_configured()
    iid = _confirmed_iid(e)
    lc = e.lifecycle.open(iid)
    data, inv = _invoke(e, iid, "promo_gate", lifecycle_id=lc, album="A")
    assert data is None
    assert "GATE_FAILED" in e.memory.recall(inv).get("error", "")
    e.memory.close()


def test_lyrics_pregen_gate_blocks_on_empty_lyrics() -> None:
    e = _fresh_configured()
    iid = _confirmed_iid(e)
    lc = e.lifecycle.open(iid)
    data, inv = _invoke(e, iid, "lyrics_pregen_gate", lifecycle_id=lc,
                        album="A", lyrics="")
    assert data is None
    e.memory.close()


def test_pre_generation_full_skill_walks_through_ready() -> None:
    e = _fresh_configured()
    iid = _confirmed_iid(e)
    sk = e.ontology.skill("pre-generation-full")
    run = SkillRun(e.memory, iid, sk)
    fills = [
        {"concept_present": "yes"},
        {"sources_signed_off": "yes"},
        {"lyrics_ok": "yes"},
    ]
    for out in fills:
        assert run.submit(out)["status"] == "working"
    assert run.current()["gate"] == "hard"
    assert run.submit({"ready": "yes"}, confirmed=True)["status"] == "completed"
    e.memory.close()


def test_release_qa_full_skill_walks_through_ship() -> None:
    e = _fresh_configured()
    iid = _confirmed_iid(e)
    sk = e.ontology.skill("release-qa-full")
    run = SkillRun(e.memory, iid, sk)
    fills = [
        {"audio_ok": "yes"},
        {"catalogue_ok": "yes"},
        {"promo_ok": "yes"},
    ]
    for out in fills:
        assert run.submit(out)["status"] == "working"
    assert run.current()["gate"] == "hard"
    assert run.submit({"shipped": "yes"}, confirmed=True)["status"] == "completed"
    e.memory.close()


def test_e2e_full_provenance_chain_through_release_qa() -> None:
    """Spec 100 Done When: end-to-end pipeline drives the full release-qa
    workflow and asserts the complete provenance chain records correctly.

    This is the master Spec 093 end-to-end test — when this passes, the
    music capability is the substrate's proven creative-production
    domain.
    """
    e = _fresh_configured()
    iid = _confirmed_iid(e, "end-to-end music pipeline")

    # 1. Create album + track via lifecycle cluster (094)
    album_res, _ = _invoke(e, iid, "create_album",
                            artist="The Phreakers", title="Modem Daze",
                            genre="ambient", type="documentary")
    assert album_res["album_slug"] == "modem-daze"

    track_res, _ = _invoke(e, iid, "create_track",
                            album="modem-daze", title="Carrier Tone",
                            track_number=1)

    # 2. Capture research claim (099)
    claim_res, _ = _invoke(e, iid, "capture_claim",
                            text="The first modems used 300 baud",
                            source_uri="https://example.com",
                            domain="historical", album="modem-daze")

    # 3. Verify sources (099)
    verify_res, _ = _invoke(e, iid, "verify_sources",
                             album="modem-daze")
    assert verify_res["verified_count"] == 1

    # 4. Master + status flip (096)
    _invoke(e, iid, "set_track_status", album="modem-daze",
            track=track_res["track_slug"], status="mastered")

    # 5. Upload promo + streaming URL (098 + 097)
    _invoke(e, iid, "upload_promo_video", album="modem-daze",
            key="modem-daze/promo.mp4", body=b"video")
    _invoke(e, iid, "update_streaming_url", album="modem-daze",
            platform="spotify", url="https://open.spotify.com/album/x")
    cap, _ = _invoke(e, iid, "db_create_tweet", album="modem-daze",
                     body="Out now!", scheduled_at="2026-12-01T10:00Z")
    _invoke(e, iid, "db_update_tweet",
            tweet_id=cap["artefact"]["tweet_id"],
            fields={"status": "scheduled"})

    # 6. Drive the release-qa gates (100)
    lc = e.lifecycle.open(iid)
    audio, _ = _invoke(e, iid, "audio_release_gate", lifecycle_id=lc,
                       album="modem-daze")
    assert audio["passed"] is True

    catalogue, _ = _invoke(e, iid, "catalogue_gate", lifecycle_id=lc,
                            album="modem-daze")
    assert catalogue["passed"] is True

    promo, _ = _invoke(e, iid, "promo_gate", lifecycle_id=lc,
                       album="modem-daze")
    assert promo["passed"] is True

    # 7. Assert the provenance chain — every cluster's work landed.
    prov = e.memory.provenance(iid)
    # Artefacts from across clusters
    artefact_kinds = {a["kind"] for a in prov["artefacts"]}
    assert "published-asset" in artefact_kinds   # 098
    assert "tweet-record" in artefact_kinds       # 097
    # Gates from 100
    gate_names = {g["name"] for g in prov["gates"]}
    assert "audio-release" in gate_names
    assert "catalogue" in gate_names
    assert "promo" in gate_names
    e.memory.close()
