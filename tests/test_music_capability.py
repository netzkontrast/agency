"""Spec 007 — the music capability proves the clustered Capability + Driver contract
end-to-end with deterministic fake drivers, and the provenance moat (a release audit
is one traversal — the net-new vs bitwize).

Spec 094 migration: imports updated from ``examples.music*`` → ``agency.capabilities.
music*`` (music graduated from examples/ into a first-class folder-form capability).
The legacy ``examples.music*`` modules remain as deprecation shims for one cycle;
``test_music_lifecycle.py`` covers the shim contract separately. Auto-discovery means
no ``extra_capabilities=[…]`` host hook is needed.
"""
import tempfile

import pytest

from agency.capabilities.music.drivers import FakeCloudDriver, fake_drivers
from agency.engine import Engine


def _engine(drivers=None):
    return Engine(tempfile.mktemp(suffix=".db"),
                  drivers=fake_drivers() if drivers is None else drivers)


@pytest.fixture
def engine():
    e = _engine()
    try:
        yield e
    finally:
        e.memory.close()


@pytest.fixture
def iid(engine):
    i = engine.intent.capture("album", "produce an album", "mastered + released")
    engine.intent.confirm(i)
    return i


def _data(e, iid, verb, **kw):
    res, _inv = e.registry.invoke(e.memory, iid, "music", verb, **kw)
    return res


def _invoke(e, iid, verb, **kw):
    return e.registry.invoke(e.memory, iid, "music", verb, **kw)


def test_capability_registers_and_ontology_merges(engine):
    # (a)+(f) loading + ontology merge onto core with no strict-schema collision
    cap = engine.registry.get("music")
    for v in ("conceptualize", "count_syllables", "lyric_report", "master_album",
              "catalogue_status", "promo_copy", "set_album_status", "publish_asset"):
        assert v in cap.verbs, f"missing representative verb {v}"


def test_count_syllables_is_deterministic_and_driver_free(engine, iid):
    # (c) a transform with no driver — deterministic
    out = _data(engine, iid, "count_syllables", word="mastering")
    assert out["syllables"] == 3                       # mas-ter-ing
    assert _data(engine, iid, "count_syllables", word="mastering") == out


def test_master_album_routes_through_audio_driver_and_records_provenance(engine, iid):
    # (d) + the provenance moat
    out = _data(engine, iid, "master_album", album="Nightshift", path="a.wav", target_lufs=-14.0)
    assert out["artefact"]["kind"] == "mastering-report"
    assert out["artefact"]["measured_lufs"] == -14.0   # the fake AudioDriver's reading
    # the driver's ffmpeg method actually fired (no direct ffmpeg)
    assert engine.drivers.get("music_audio").ffmpeg_calls
    # the moat: the run is in provenance — a mastering-report Artefact exists + an Invocation
    arts = engine.memory.find("Artefact")
    assert any(a.get("kind") == "mastering-report" for a in arts)
    assert any(i.get("verb") == "master_album" for i in engine.memory.find("Invocation"))


def test_db_cluster_reads_through_dbdriver(engine, iid):
    out = _data(engine, iid, "catalogue_status", album="Nightshift")
    slugs = {t["slug"] for t in out["tracks"]}
    assert slugs == {"track-1", "track-2"}             # the FakeDBDriver's rows


def test_lyric_report_uses_text_driver_and_produces_artefact(engine, iid):
    out = _data(engine, iid, "lyric_report", album="X", lyrics="hello darkness\nmy old friend")
    assert out["artefact"]["kind"] == "lyric-report" and out["artefact"]["lines"] == 2
    assert any(a.get("kind") == "lyric-report" for a in engine.memory.find("Artefact"))


def test_state_and_promo_clusters(engine, iid):
    st = _data(engine, iid, "set_album_status", album="X", status="mastered")
    assert st["status"] == "mastered"
    assert engine.drivers.get("music_state").get("album:X")["status"] == "mastered"
    promo = _data(engine, iid, "promo_copy", album="X", angle="debut")
    assert promo["artefact"]["kind"] == "promo-copy"


def test_invalid_status_is_a_typed_failure(engine, iid):
    data, inv = _invoke(engine, iid, "set_album_status", album="X", status="bogus")
    assert data is None                                # failure unwraps to None
    node = engine.memory.recall(inv)
    assert node.get("outcome") == "failed" and "INVALID_ARGUMENT" in node.get("error", "")


def test_cloud_unconfigured_returns_typed_dependency_missing(engine, iid):
    # (g) r2_put on an unconfigured CloudDriver → typed DEPENDENCY_MISSING, not a raise
    data, inv = _invoke(engine, iid, "publish_asset", album="X", key="k", body="hi")
    assert data is None
    node = engine.memory.recall(inv)
    assert node.get("outcome") == "failed" and "DEPENDENCY_MISSING" in node.get("error", "")


def test_release_check_computed_gate_fails_and_pauses_lifecycle(engine, iid):
    # (e) a failed COMPUTED gate → ToolResult(GATE_FAILED) + the lifecycle pauses via gate.check
    lc = engine.lifecycle.open(iid)
    data, inv = _invoke(engine, iid, "release_check", lifecycle_id=lc, album="X")
    assert data is None                                # ok=False → unwrapped to None
    assert "GATE_FAILED" in engine.memory.recall(inv).get("error", "")
    assert engine.memory.recall(lc).get("state") == "input-required"   # gate.check paused it
    assert any(g.get("name") == "release-qa" and not g.get("passed")
               for g in engine.memory.find("Gate"))


def test_release_check_passes_when_all_tracks_mastered(iid):
    from agency.capabilities.music.drivers import FakeDBDriver, fake_drivers
    drivers = fake_drivers()
    drivers["music_db"] = FakeDBDriver(rows=[("t1", "mastered"), ("t2", "mastered")])
    e = _engine(drivers=drivers)
    try:
        i = e.intent.capture("a", "b", "c")
        e.intent.confirm(i)
        lc = e.lifecycle.open(i)
        data, _inv = e.registry.invoke(e.memory, i, "music", "release_check",
                                       lifecycle_id=lc, album="X")
        assert data["passed"] is True
        assert e.memory.recall(lc).get("state") != "input-required"
    finally:
        e.memory.close()


def test_pregen_gate_blocks_then_passes(engine, iid):
    lc = engine.lifecycle.open(iid)
    data, inv = _invoke(engine, iid, "pregen_check", lifecycle_id=lc,
                        concept_ready=True, rights_clear=False)
    assert data is None and "GATE_FAILED" in engine.memory.recall(inv).get("error", "")
    assert engine.memory.recall(lc).get("state") == "input-required"
    lc2 = engine.lifecycle.open(iid)
    ok, _ = _invoke(engine, iid, "pregen_check", lifecycle_id=lc2,
                    concept_ready=True, rights_clear=True)
    assert ok["passed"] is True


def test_longtail_clusters_route_through_their_drivers(engine, iid):
    # sheet-music (AudioDriver, produces an artefact)
    sheet = _data(engine, iid, "transcribe_sheet", album="X", path="a.wav")
    assert sheet["artefact"]["kind"] == "sheet-music"
    assert engine.drivers.get("music_audio").ffmpeg_calls          # transcription ran via the driver
    assert any(a.get("kind") == "sheet-music" for a in engine.memory.find("Artefact"))
    # mixing (AudioDriver) — deterministic findings from the fake's -14 LUFS
    mix = _data(engine, iid, "analyze_mix", album="X", path="a.wav")
    assert mix["measured_lufs"] == -14.0 and mix["findings"] == ["within target"]
    # streaming (CloudDriver) — the fake returns 200 → all live
    stream = _data(engine, iid, "verify_streaming", album="X", urls="https://a, https://b")
    assert stream["live"] == ["https://a", "https://b"] and stream["dead"] == []


def test_capture_idea_records_an_idea_node(engine, iid):
    out = _data(engine, iid, "capture_idea", text="a concept album about lighthouses")
    assert out["idea_id"] and out["text"].startswith("a concept")
    ideas = engine.memory.find("Idea")
    assert any(i.get("text", "").startswith("a concept") for i in ideas)
    # persisted via the StateDriver too
    assert engine.drivers.get("music_state").get(f"idea:{out['idea_id']}")["text"]


def test_music_health_reports_wired_drivers(engine, iid):
    out = _data(engine, iid, "music_health")
    assert out["ok"] is True
    assert set(out["drivers_wired"]) == {"music_state", "music_text", "music_audio",
                                         "music_db", "music_cloud"}
    assert out["drivers_missing"] == []


def test_missing_driver_degrades_to_typed_failure(iid_factory=None):
    # a driver-backed verb with NO driver registered returns DEPENDENCY_MISSING
    e = _engine(drivers={})                            # no music drivers at all
    try:
        iid = e.intent.capture("a", "b", "c")
        e.intent.confirm(iid)
        data, inv = e.registry.invoke(e.memory, iid, "music", "master_album",
                                      album="X", path="a.wav")
        assert data is None
        assert "DEPENDENCY_MISSING" in e.memory.recall(inv).get("error", "")
    finally:
        e.memory.close()
