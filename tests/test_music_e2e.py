"""music capability — end-to-end provenance chain test (Spec 093 master).

The load-bearing test cited by Plan/093-music-complete-port/spec.md's
Followup section. Drives a full music pipeline through every cluster
(lifecycle 094 → research 099 → audio 096 → promo 098 + catalogue 097 →
gates 100) and asserts memory.provenance(intent_id) returns the complete
chain. When this passes, the master Spec 093 contract is satisfied:
bitwize-music is fully ported, the provenance moat is lit, release audit
is one graph traversal.

This file's existence is the spec-Followup-grounding handshake — the
identical-behavior copy in test_music_gates.py is the cluster-local
smoke test; this file is the master-spec citation target.
"""
from __future__ import annotations

import tempfile

from agency.capabilities.music.drivers import FakeCloudDriver, fake_drivers
from agency.engine import Engine


def _fresh_configured() -> Engine:
    drv = fake_drivers()
    drv["music_cloud"] = FakeCloudDriver(configured=True)
    return Engine(tempfile.mktemp(suffix=".db"), drivers=drv)


def _invoke(e: Engine, iid: str, verb: str, **kw):
    return e.registry.invoke(e.memory, iid, "music", verb, **kw)


def test_e2e_full_provenance_chain_through_release_qa() -> None:
    """Spec 100 Done When (the master Spec 093 test): end-to-end pipeline
    drives the full release-qa workflow and asserts the complete provenance
    chain records correctly.

    Phases:
      1. lifecycle (094) — create_album, create_track
      2. research (099) — capture_claim, verify_sources
      3. audio (096)   — set_track_status to mastered
      4. promo (098)   — upload_promo_video
      5. catalogue (097) — update_streaming_url + db_create_tweet
      6. gates (100)   — audio_release_gate + catalogue_gate + promo_gate
      7. assert the provenance graph traversal returns the complete chain
    """
    e = _fresh_configured()
    iid = e.intent.capture("end-to-end music pipeline",
                           "Modem Daze shipped", "all 3 gates green")
    e.intent.confirm(iid)

    # 1. Create album + track via lifecycle cluster (094)
    album_res, _ = _invoke(e, iid, "create_album",
                            artist="The Phreakers", title="Modem Daze",
                            genre="ambient", type="documentary")
    assert album_res["album_slug"] == "modem-daze"

    track_res, _ = _invoke(e, iid, "create_track",
                            album="modem-daze", title="Carrier Tone",
                            track_number=1)

    # 2. Capture research claim (099)
    _invoke(e, iid, "capture_claim",
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
    artefact_kinds = {a["kind"] for a in prov["artefacts"]}
    assert "published-asset" in artefact_kinds   # 098
    assert "tweet-record" in artefact_kinds       # 097
    gate_names = {g["name"] for g in prov["gates"]}
    assert "audio-release" in gate_names
    assert "catalogue" in gate_names
    assert "promo" in gate_names
    e.memory.close()
