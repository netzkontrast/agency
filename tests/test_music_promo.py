"""music promo cluster — Spec 098 verb + skill coverage.

7 new effect/transform verbs + 1 composite gate verb + PROMO_PASS_SKILL
(5-phase) and RELEASE_PUBLISH_SKILL (4-phase) walkable skills. The
FakeCloudDriver holds an in-memory object store + audit log so CI runs
zero boto3 / R2 / S3 binary.

Spec 098 Done When line 32-33: `scripts/test-cap music_promo` under 8s.
"""
from __future__ import annotations

import tempfile

from agency.capabilities.music.drivers import FakeCloudDriver, fake_drivers
from agency.engine import Engine
from agency.skill import SkillRun


def _fresh_configured() -> Engine:
    """Engine with a CONFIGURED CloudDriver so r2_put doesn't return DEPENDENCY_MISSING."""
    drv = fake_drivers()
    drv["music_cloud"] = FakeCloudDriver(configured=True)
    return Engine(tempfile.mktemp(suffix=".db"), drivers=drv)


def _confirmed_iid(e: Engine, purpose: str = "promo") -> str:
    iid = e.intent.capture(purpose, "deliverable", "acceptance")
    e.intent.confirm(iid)
    return iid


def _invoke(e: Engine, iid: str, verb: str, **kw):
    return e.registry.invoke(e.memory, iid, "music", verb, **kw)


def test_promo_cluster_verbs_discover() -> None:
    e = _fresh_configured()
    verbs = e.registry._caps["music"].verbs
    for v in ("promo_review", "publish_sheet_music", "upload_promo_video",
              "r2_delete", "r2_list", "release_package",
              "promo_review_gate"):
        assert v in verbs, f"verb {v!r} not registered"
    e.memory.close()


def test_promo_pass_skill_is_five_phased() -> None:
    e = _fresh_configured()
    sk = e.ontology.skill("promo-pass")
    assert sk["kind"] == "workflow"
    assert len(sk["phases"]) == 5
    assert sk["phases"][-1].get("gate") == "hard"
    names = [p["name"] for p in sk["phases"]]
    assert names == ["draft", "review", "asset-attach", "schedule", "publish"]
    e.memory.close()


def test_release_publish_skill_is_four_phased() -> None:
    e = _fresh_configured()
    sk = e.ontology.skill("release-publish")
    assert sk["kind"] == "workflow"
    assert len(sk["phases"]) == 4
    assert sk["phases"][-1].get("gate") == "hard"
    e.memory.close()


def test_promo_review_high_score_for_clean_cta_copy() -> None:
    e = _fresh_configured()
    iid = _confirmed_iid(e)
    data, _ = _invoke(e, iid, "promo_review",
                      body="New album out now! Stream everywhere.",
                      platform="x")
    assert data["score"] >= 80
    assert data["max_length"] == 280
    e.memory.close()


def test_promo_review_flags_over_length() -> None:
    e = _fresh_configured()
    iid = _confirmed_iid(e)
    long_body = "Listen now! " + ("x" * 280)  # > 280 limit
    data, _ = _invoke(e, iid, "promo_review", body=long_body, platform="x")
    assert any(f["kind"] == "over_length" for f in data["findings"])
    assert data["score"] < 70
    e.memory.close()


def test_promo_review_flags_no_cta() -> None:
    e = _fresh_configured()
    iid = _confirmed_iid(e)
    data, _ = _invoke(e, iid, "promo_review",
                      body="Just words, no call to action.",
                      platform="x")
    assert any(f["kind"] == "no_cta" for f in data["findings"])
    e.memory.close()


def test_promo_review_flags_explicit() -> None:
    e = _fresh_configured()
    iid = _confirmed_iid(e)
    data, _ = _invoke(e, iid, "promo_review",
                      body="This shit is fire! Stream now.",
                      platform="x")
    assert any(f["kind"] == "explicit" for f in data["findings"])
    e.memory.close()


def test_publish_sheet_music_produces_published_asset() -> None:
    e = _fresh_configured()
    iid = _confirmed_iid(e)
    data, _ = _invoke(e, iid, "publish_sheet_music", album="Origin",
                      key="origin/songbook.pdf", body=b"PDF bytes here")
    assert data["artefact"]["kind"] == "published-asset"
    assert data["artefact"]["asset_kind"] == "sheet-music"
    e.memory.close()


def test_upload_promo_video_produces_published_asset() -> None:
    e = _fresh_configured()
    iid = _confirmed_iid(e)
    data, _ = _invoke(e, iid, "upload_promo_video", album="Origin",
                      key="origin/promo.mp4", body=b"video bytes")
    assert data["artefact"]["kind"] == "published-asset"
    assert data["artefact"]["asset_kind"] == "promo-video"
    e.memory.close()


def test_publish_sheet_music_fails_when_cloud_unconfigured() -> None:
    """Unconfigured FakeCloudDriver (the default) returns DEPENDENCY_MISSING."""
    e = Engine(tempfile.mktemp(suffix=".db"), drivers=fake_drivers())
    iid = _confirmed_iid(e)
    data, inv = _invoke(e, iid, "publish_sheet_music", album="A",
                        key="k.pdf", body=b"x")
    assert data is None
    err = e.memory.recall(inv).get("error", "")
    assert "DEPENDENCY_MISSING" in err
    e.memory.close()


def test_r2_delete_and_list_round_trip() -> None:
    e = _fresh_configured()
    iid = _confirmed_iid(e)
    # Upload 3 assets
    _invoke(e, iid, "upload_promo_video", album="A",
            key="a/promo1.mp4", body=b"v1")
    _invoke(e, iid, "upload_promo_video", album="A",
            key="a/promo2.mp4", body=b"v2")
    _invoke(e, iid, "publish_sheet_music", album="A",
            key="a/book.pdf", body=b"p")
    # List
    listed, _ = _invoke(e, iid, "r2_list", prefix="a/")
    assert listed["count"] == 3
    # Delete one
    del_res, _ = _invoke(e, iid, "r2_delete", key="a/promo1.mp4")
    assert del_res["deleted"] is True
    # List after delete
    after, _ = _invoke(e, iid, "r2_list", prefix="a/")
    assert after["count"] == 2
    e.memory.close()


def test_release_package_records_artefact() -> None:
    e = _fresh_configured()
    iid = _confirmed_iid(e)
    data, _ = _invoke(e, iid, "release_package", album="Origin",
                      assets=["origin/master.wav", "origin/cover.jpg",
                              "origin/promo.mp4"])
    assert data["artefact"]["kind"] == "promo-album-package"
    assert len(data["artefact"]["assets"]) == 3
    # Artefact PRODUCES'd against the intent
    prov = e.memory.provenance(iid)
    assert any(a["kind"] == "promo-album-package" for a in prov["artefacts"])
    e.memory.close()


def test_promo_review_gate_passes_quality_copy() -> None:
    e = _fresh_configured()
    iid = _confirmed_iid(e)
    lc = e.lifecycle.open(iid)
    data, _ = _invoke(e, iid, "promo_review_gate", lifecycle_id=lc,
                      body="New album out now! Stream everywhere.",
                      platform="x", min_score=70)
    assert data["passed"] is True
    assert data["score"] >= 70
    e.memory.close()


def test_promo_review_gate_blocks_low_quality() -> None:
    e = _fresh_configured()
    iid = _confirmed_iid(e)
    lc = e.lifecycle.open(iid)
    # Body is empty → score 0, gate blocks
    data, inv = _invoke(e, iid, "promo_review_gate", lifecycle_id=lc,
                        body="   ", platform="x", min_score=70)
    assert data is None
    assert "GATE_FAILED" in e.memory.recall(inv).get("error", "")
    assert e.memory.recall(lc).get("state") == "input-required"
    e.memory.close()


def test_streaming_verify_artefact_now_produced() -> None:
    """Spec 097 review-driven: verify_streaming now PRODUCES'd a streaming-verify artefact."""
    e = _fresh_configured()
    iid = _confirmed_iid(e)
    data, _ = _invoke(e, iid, "verify_streaming", album="A",
                      urls="https://x.com/a, https://x.com/b")
    assert data["artefact"]["kind"] == "streaming-verify"
    assert data["artefact"]["album"] == "A"
    prov = e.memory.provenance(iid)
    assert any(a["kind"] == "streaming-verify" for a in prov["artefacts"])
    e.memory.close()


def test_promo_pass_skill_walks_through_publish() -> None:
    e = _fresh_configured()
    iid = _confirmed_iid(e)
    sk = e.ontology.skill("promo-pass")
    run = SkillRun(e.memory, iid, sk)
    fills = [
        {"promo_body": "Stream now", "promo_platform": "x"},
        {"review_score": "85", "review_passed": "yes"},
        {"assets_attached": "yes"},
        {"scheduled_at_set": "2026-12-01"},
    ]
    for out in fills:
        assert run.submit(out)["status"] == "working"
    assert run.current()["gate"] == "hard"
    assert run.submit({"published": "yes"},
                      confirmed=True)["status"] == "completed"
    e.memory.close()


def test_release_publish_skill_walks_through_announce() -> None:
    e = _fresh_configured()
    iid = _confirmed_iid(e)
    sk = e.ontology.skill("release-publish")
    run = SkillRun(e.memory, iid, sk)
    fills = [
        {"release_assets_collected": "yes"},
        {"assets_uploaded": "yes"},
        {"catalogue_synced": "yes"},
    ]
    for out in fills:
        assert run.submit(out)["status"] == "working"
    assert run.current()["gate"] == "hard"
    assert run.submit({"announcement_posted": "yes"},
                      confirmed=True)["status"] == "completed"
    e.memory.close()
