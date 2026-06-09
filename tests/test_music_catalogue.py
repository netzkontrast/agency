"""music catalogue cluster — Spec 097 verb + skill coverage.

11 new effect/transform verbs + 1 composite gate verb + tweet-curation
(4-phase) and streaming-verify (3-phase) walkable skills + db_init schema
migration. The FakeDBDriver holds an in-memory indexed tweet store with
auto-incremented IDs; CI runs zero PostgreSQL.

Spec 097 Done When line 60-61: `scripts/test-cap music_catalogue` under 6s.
"""
from __future__ import annotations

import tempfile

from agency.capabilities.music.drivers import fake_drivers
from agency.capabilities.music.migrations.db_init import init_schema
from agency.engine import Engine
from agency.skill import SkillRun


def _fresh() -> Engine:
    return Engine(tempfile.mktemp(suffix=".db"), drivers=fake_drivers())


def _confirmed_iid(e: Engine, purpose: str = "catalogue") -> str:
    iid = e.intent.capture(purpose, "deliverable", "acceptance")
    e.intent.confirm(iid)
    return iid


def _invoke(e: Engine, iid: str, verb: str, **kw):
    return e.registry.invoke(e.memory, iid, "music", verb, **kw)


def test_catalogue_cluster_verbs_discover() -> None:
    e = _fresh()
    verbs = e.registry._caps["music"].verbs
    for v in ("db_create_tweet", "db_update_tweet", "db_delete_tweet",
              "db_list_tweets", "db_search_tweets", "db_get_tweet_stats",
              "db_sync_album", "update_streaming_url", "get_streaming_urls",
              "get_promo_status", "get_promo_content", "extract_links",
              "tweet_schedule_gate"):
        assert v in verbs, f"verb {v!r} not registered"
    e.memory.close()


def test_tweet_curation_skill_is_owned_and_four_phased() -> None:
    e = _fresh()
    sk = e.ontology.skill("tweet-curation")
    assert sk["kind"] == "workflow"
    assert len(sk["phases"]) == 4
    names = [p["name"] for p in sk["phases"]]
    assert names == ["draft", "schedule", "publish", "archive"]
    e.memory.close()


def test_streaming_verify_skill_is_three_phased() -> None:
    e = _fresh()
    sk = e.ontology.skill("streaming-verify")
    assert sk["kind"] == "workflow"
    assert len(sk["phases"]) == 3
    # No human gate on this routine-ops workflow
    assert not any(p.get("gate") == "hard" for p in sk["phases"])
    e.memory.close()


def test_tweet_status_enum_bites() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    e.memory.record("Tweet", {"text": "ok", "status": "draft"})
    try:
        e.memory.record("Tweet", {"text": "bad", "status": "nonsense"})
        raise AssertionError("expected enum violation")
    except ValueError:
        pass
    e.memory.close()


def test_db_create_tweet_returns_tweet_id_and_artefact() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    data, _ = _invoke(e, iid, "db_create_tweet", album="Origin",
                      body="New album out now!", scheduled_at="2026-12-01T10:00Z")
    assert data["artefact"]["kind"] == "tweet-record"
    assert "tweet_id" in data["artefact"]
    # Artefact recorded against the intent
    prov = e.memory.provenance(iid)
    assert any(a["kind"] == "tweet-record" for a in prov["artefacts"])
    e.memory.close()


def test_db_update_and_delete_tweet_round_trip() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    cap, _ = _invoke(e, iid, "db_create_tweet", album="A",
                     body="initial", scheduled_at="2026-12-01T10:00Z")
    tid = cap["artefact"]["tweet_id"]
    upd, _ = _invoke(e, iid, "db_update_tweet", tweet_id=tid,
                     fields={"status": "scheduled"})
    assert upd["fields"]["status"] == "scheduled"
    listed, _ = _invoke(e, iid, "db_list_tweets", album="A",
                       status="scheduled")
    assert listed["count"] == 1
    delete, _ = _invoke(e, iid, "db_delete_tweet", tweet_id=tid)
    assert delete["deleted"] is True
    listed_after, _ = _invoke(e, iid, "db_list_tweets", album="A")
    assert listed_after["count"] == 0
    e.memory.close()


def test_db_search_tweets_finds_substring() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    _invoke(e, iid, "db_create_tweet", album="A",
            body="The phreaker tale begins",
            scheduled_at="2026-12-01T10:00Z")
    _invoke(e, iid, "db_create_tweet", album="A",
            body="Listen now",
            scheduled_at="2026-12-02T10:00Z")
    data, _ = _invoke(e, iid, "db_search_tweets", query="phreaker")
    assert data["count"] == 1
    assert "phreaker" in data["tweets"][0]["body"].lower()
    e.memory.close()


def test_db_get_tweet_stats_aggregates_by_status() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    a, _ = _invoke(e, iid, "db_create_tweet", album="A",
                   body="one", scheduled_at="2026-12-01T10:00Z")
    b, _ = _invoke(e, iid, "db_create_tweet", album="A",
                   body="two", scheduled_at="2026-12-02T10:00Z")
    _invoke(e, iid, "db_update_tweet",
            tweet_id=a["artefact"]["tweet_id"],
            fields={"status": "scheduled"})
    stats, _ = _invoke(e, iid, "db_get_tweet_stats", album="A")
    assert stats["total"] == 2
    assert stats["by_status"].get("draft") == 1
    assert stats["by_status"].get("scheduled") == 1
    e.memory.close()


def test_db_sync_album_replaces_existing_tweets() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    _invoke(e, iid, "db_create_tweet", album="A",
            body="will be replaced", scheduled_at="2026-12-01T10:00Z")
    sync, _ = _invoke(e, iid, "db_sync_album", album="A",
                      tweets=[
                          {"body": "new tweet 1", "scheduled_at": "2026-12-02"},
                          {"body": "new tweet 2", "scheduled_at": "2026-12-03"},
                          {"body": "new tweet 3", "scheduled_at": "2026-12-04"},
                      ])
    assert sync["removed"] == 1
    assert sync["created"] == 3
    listed, _ = _invoke(e, iid, "db_list_tweets", album="A")
    assert listed["count"] == 3
    e.memory.close()


def test_update_and_get_streaming_urls_round_trip() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    _invoke(e, iid, "update_streaming_url", album="A",
            platform="spotify", url="https://open.spotify.com/album/123")
    _invoke(e, iid, "update_streaming_url", album="A",
            platform="apple", url="https://music.apple.com/album/456")
    data, _ = _invoke(e, iid, "get_streaming_urls", album="A")
    platforms = {u["platform"] for u in data["urls"]}
    assert platforms == {"spotify", "apple"}
    e.memory.close()


def test_get_promo_status_combines_tweets_and_streaming() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    _invoke(e, iid, "db_create_tweet", album="A",
            body="x", scheduled_at="2026-12-01T10:00Z")
    _invoke(e, iid, "update_streaming_url", album="A",
            platform="spotify", url="https://example.com/x")
    data, _ = _invoke(e, iid, "get_promo_status", album="A")
    assert data["tweets"]["total"] == 1
    assert data["streaming_urls"] == 1
    e.memory.close()


def test_get_promo_content_splits_drafts_and_scheduled() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    a, _ = _invoke(e, iid, "db_create_tweet", album="A",
                   body="draft tweet", scheduled_at="2026-12-01T10:00Z")
    b, _ = _invoke(e, iid, "db_create_tweet", album="A",
                   body="scheduled tweet", scheduled_at="2026-12-02T10:00Z")
    _invoke(e, iid, "db_update_tweet",
            tweet_id=b["artefact"]["tweet_id"],
            fields={"status": "scheduled"})
    data, _ = _invoke(e, iid, "get_promo_content", album="A")
    assert data["total"] == 2
    assert len(data["drafts"]) == 1
    assert len(data["scheduled"]) == 1
    e.memory.close()


def test_extract_links_finds_urls() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    data, _ = _invoke(e, iid, "extract_links",
                      text="Stream now at https://open.spotify.com/album/1 or "
                           "https://music.apple.com/album/2")
    assert data["count"] == 2
    assert any("spotify" in u for u in data["urls"])
    assert any("apple" in u for u in data["urls"])
    e.memory.close()


def test_tweet_schedule_gate_passes_valid_body() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    lc = e.lifecycle.open(iid)
    data, _ = _invoke(e, iid, "tweet_schedule_gate", lifecycle_id=lc,
                      body="New album out now! Stream it everywhere.",
                      scheduled_at="2026-12-01T10:00Z",
                      platform="x", max_length=280)
    assert data["passed"] is True
    assert data["length"] > 0
    e.memory.close()


def test_tweet_schedule_gate_fails_empty_body() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    lc = e.lifecycle.open(iid)
    data, inv = _invoke(e, iid, "tweet_schedule_gate", lifecycle_id=lc,
                        body="   ", scheduled_at="2026-12-01T10:00Z")
    assert data is None
    assert "GATE_FAILED" in e.memory.recall(inv).get("error", "")
    assert "body is empty" in e.memory.recall(inv).get("error", "")
    e.memory.close()


def test_tweet_schedule_gate_fails_over_max_length() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    lc = e.lifecycle.open(iid)
    body = "x" * 281        # 281 chars, exceeds default 280
    data, inv = _invoke(e, iid, "tweet_schedule_gate", lifecycle_id=lc,
                        body=body, scheduled_at="2026-12-01T10:00Z")
    assert data is None
    assert "length 281 > 280" in e.memory.recall(inv).get("error", "")
    e.memory.close()


def test_tweet_schedule_gate_fails_missing_scheduled_at() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    lc = e.lifecycle.open(iid)
    data, inv = _invoke(e, iid, "tweet_schedule_gate", lifecycle_id=lc,
                        body="Valid body", scheduled_at="")
    assert data is None
    assert "scheduled_at is required" in e.memory.recall(inv).get("error", "")
    e.memory.close()


def test_db_init_runs_schema_against_fake() -> None:
    """db_init.init_schema executes all CREATE TABLE / INDEX statements
    via the DBDriver cursor — verifies the migration is well-formed Python
    even though the FakeDBDriver cursor is a SQL-string echo."""
    e = _fresh()
    db = e.drivers.get("music_db")
    result = init_schema(db)
    assert result["ok"] is True
    assert result["statements_executed"] >= 5     # 2 tables + 3+ indexes
    e.memory.close()


def test_tweet_curation_skill_walks_through_archive() -> None:
    """Walk the 4-phase tweet-curation skill."""
    e = _fresh()
    iid = _confirmed_iid(e)
    sk = e.ontology.skill("tweet-curation")
    run = SkillRun(e.memory, iid, sk)
    fills = [
        {"tweet_body": "new album out", "tweet_platform": "x"},
        {"scheduled_at_set": "2026-12-01T10:00Z"},
        {"posted": "yes"},
    ]
    for out in fills:
        assert run.submit(out)["status"] == "working"
    assert run.submit({"archived": "yes"})["status"] == "completed"
    e.memory.close()


def test_streaming_verify_skill_walks_through_record() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    sk = e.ontology.skill("streaming-verify")
    run = SkillRun(e.memory, iid, sk)
    fills = [
        {"urls_to_check": "['https://x.com/a']"},
        {"live_urls": "['https://x.com/a']", "dead_urls": "[]"},
    ]
    for out in fills:
        assert run.submit(out)["status"] == "working"
    assert run.submit({"verification_recorded": "yes"})["status"] == "completed"
    e.memory.close()
