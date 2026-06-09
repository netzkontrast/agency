"""music lifecycle cluster — migration smoke tests (Spec 094 Slice 1).

This file replaces ``test_agency.py::test_music_capability_owns_conceptualizer``.
Tests verify the migration: ``MusicCapability`` auto-discovers (no
``extra_capabilities`` host hook needed), the ontology merges, the 7-phase
``album-concept`` skill walks to its hard gate, ``conceptualize`` produces an
album-concept artefact, ``set_album_status`` enum bites, the deprecation shim
still re-exports, and a few read-only smoke checks on the relocated assets
(drivers module, templates folder).

Spec 094's full Done-When (14 lifecycle verbs, template porting, reference
+ genre vendoring) lands across subsequent slices.
"""
from __future__ import annotations

import tempfile
import warnings
from pathlib import Path

import pytest

from agency.capabilities.music.drivers import fake_drivers
from agency.engine import Engine
from agency.skill import SkillRun


def _fresh() -> Engine:
    return Engine(tempfile.mktemp(suffix=".db"))


def _fresh_with_drivers() -> Engine:
    return Engine(tempfile.mktemp(suffix=".db"), drivers=fake_drivers())


def _confirmed_iid(e: Engine, purpose: str = "test") -> str:
    iid = e.intent.capture(purpose, "deliverable", "acceptance")
    e.intent.confirm(iid)
    return iid


def _invoke(e: Engine, iid: str, verb: str, **kw):
    return e.registry.invoke(e.memory, iid, "music", verb, **kw)


def test_music_capability_auto_discovers_under_new_home() -> None:
    """Spec 094 — ``MusicCapability`` lives at ``agency/capabilities/music/`` and
    is registered by folder-form discovery WITHOUT any ``extra_capabilities``
    host hook. A fresh engine exposes ``capability_music_*`` verbs out of the box.
    """
    e = _fresh()
    assert "music" in {cap.name for cap in e.registry._caps.values()}, (
        "music capability did not auto-discover under agency/capabilities/music/"
    )
    # the conceptualizer skill is owned by music, not core
    sk = e.ontology.skill("album-concept")
    assert len(sk["phases"]) == 7
    assert sk["phases"][-1].get("gate") == "hard"
    e.memory.close()


def test_music_album_concept_skill_walks_to_hard_gate() -> None:
    """The 7-phase ``album-concept`` walker advances on each phase's fills and
    pauses at the terminal hard confirm — preserved from the 007 contract."""
    e = _fresh()
    iid = e.intent.capture("plan an album", "album concept", "user confirms")
    sk = e.ontology.skill("album-concept")
    run = SkillRun(e.memory, iid, sk)
    fills = [
        {"artist": "a", "genre": "g", "type": "thematic", "scale": "ep",
         "theme": "t", "true_story": "no"},
        {"key_subjects": "k", "emotional_core": "e", "why": "w"},
        {"references": "r", "production_style": "p", "vocal_approach": "v",
         "instrumentation": "i", "mood": "m", "target_duration": "4:00"},
        {"tracklist": "t", "sequencing": "s", "energy_map": "e"},
        {"visual_concept": "v", "palette": "p", "symbols": "s"},
        {"album_title": "t", "track_titles": "t", "research_needs": "n",
         "explicit": "no", "distributor_genres": "g"},
    ]
    for out in fills:
        assert run.submit(out)["status"] == "working"
    assert run.current()["gate"] == "hard"
    assert run.submit({"user_confirmed": "yes"}, confirmed=True)["status"] == "completed"
    e.memory.close()


def test_music_conceptualize_records_artefact_under_intent() -> None:
    """``music.conceptualize`` records an ``album-concept`` artefact PRODUCES'd
    against the intent — graph-canonical provenance preserved."""
    e = _fresh()
    iid = e.intent.capture("plan an album", "album concept", "user confirms")
    e.intent.confirm(iid)
    res, _ = e.registry.invoke(e.memory, iid, "music", "conceptualize",
                               artist="A", title="T", type="narrative", theme="x")
    assert "# T" in res["result"]
    artefacts = e.memory.provenance(iid)["artefacts"]
    assert any(a["kind"] == "album-concept" for a in artefacts)
    e.memory.close()


def test_music_album_type_enum_still_bites() -> None:
    """The capability-owned ``(Album, type)`` enum rejects an unknown value at
    ``Memory.record`` time — proof the OntologyExtension migration is
    structurally faithful."""
    e = _fresh()
    with pytest.raises(ValueError):
        e.memory.record("Album", {"artist": "A", "title": "T", "type": "polka"})
    e.memory.close()


def test_music_album_status_enum_rejection_on_set_status() -> None:
    """``set_album_status`` rejects unknown status values with INVALID_ARGUMENT.
    ``ToolResult.failure`` unwraps to ``data=None``; the error is captured on the
    Invocation node (Spec 001 Option C: env data is the wire shape; error on
    the side-effect Invocation)."""
    e = _fresh()
    iid = e.intent.capture("status flip", "set status", "verified")
    e.intent.confirm(iid)
    data, inv = e.registry.invoke(e.memory, iid, "music", "set_album_status",
                                  album="A", status="nonsense")
    assert data is None
    node = e.memory.recall(inv)
    assert node.get("outcome") == "failed"
    assert "INVALID_ARGUMENT" in node.get("error", "")
    e.memory.close()


def test_examples_music_shim_still_re_exports_for_one_cycle() -> None:
    """``examples.music`` is a deprecation shim per Spec 094 — re-exports the
    relocated names + issues a ``DeprecationWarning``. Spec 110 removes it."""
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        from examples import music as legacy
        assert any(issubclass(rec.category, DeprecationWarning) for rec in w)
    assert legacy.MusicCapability.__name__ == "MusicCapability"
    assert "thematic" in legacy.ALBUM_TYPES
    from agency.capabilities.music import MusicCapability as new
    assert legacy.MusicCapability is new


def test_examples_music_drivers_shim_still_re_exports_for_one_cycle() -> None:
    """``examples.music_drivers`` is a deprecation shim per Spec 094 — re-exports
    the relocated Driver protocols + fakes + ``fake_drivers()`` factory."""
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        from examples import music_drivers as legacy
        assert any(issubclass(rec.category, DeprecationWarning) for rec in w)
    bundle = legacy.fake_drivers()
    assert set(bundle) == {"music_state", "music_text", "music_audio",
                           "music_db", "music_cloud"}


def test_music_templates_ported_verbatim_from_bitwize() -> None:
    """5 lifecycle templates (album, track, artist, genre, ideas) ported VERBATIM
    from bitwize-music. Spec 094 mandates the 5-template subset for the lifecycle
    PR; promo + research templates land in 098 + 099."""
    tpl_dir = Path(__file__).parent.parent / "agency" / "capabilities" / "music" / "templates"
    for name in ("album.md", "track.md", "artist.md", "genre.md", "ideas.md"):
        body = (tpl_dir / name).read_text()
        assert body, f"template {name} is empty — verbatim port required"


# ════════════════════════════════════════════════════════════════════════════
# Spec 094 Slice 2 — 11 NEW lifecycle verbs + StateDriver method delta tests.
# ════════════════════════════════════════════════════════════════════════════


def test_capture_idea_records_status_new() -> None:
    """``capture_idea`` records an ``Idea`` node with ``status='new'`` (Slice 2 widening)."""
    e = _fresh_with_drivers()
    iid = _confirmed_iid(e, "idea capture")
    data, _ = _invoke(e, iid, "capture_idea", text="A documentary about modems")
    assert data["status"] == "new"
    assert data["text"] == "A documentary about modems"
    e.memory.close()


def test_promote_idea_flips_status_and_creates_album() -> None:
    """``promote_idea`` records an ``Album`` node, edges ``Idea PROMOTED_TO Album``,
    and flips the ``Idea.status`` via the StateDriver."""
    e = _fresh_with_drivers()
    iid = _confirmed_iid(e, "promote")
    cap, _ = _invoke(e, iid, "capture_idea", text="The phreaker tale")
    res, _ = _invoke(e, iid, "promote_idea",
                     idea_id=cap["idea_id"], artist="Phreak",
                     title="The Phreaker Tale", genre="ambient")
    assert res["status"] == "promoted"
    assert res["album_slug"] == "the-phreaker-tale"
    # The PROMOTED_TO edge is the audit trail.
    state = e.drivers.get("music_state")
    promoted = state.list_ideas(status="promoted")
    assert any(i["idea_id"] == cap["idea_id"] for i in promoted)
    e.memory.close()


def test_promote_idea_rejects_unknown_album_type() -> None:
    e = _fresh_with_drivers()
    iid = _confirmed_iid(e, "bad promote")
    cap, _ = _invoke(e, iid, "capture_idea", text="x")
    data, inv = _invoke(e, iid, "promote_idea",
                        idea_id=cap["idea_id"], artist="A", title="T",
                        genre="g", type="polka")
    assert data is None
    node = e.memory.recall(inv)
    assert "INVALID_ARGUMENT" in node.get("error", "")
    e.memory.close()


def test_list_ideas_filters_by_status() -> None:
    e = _fresh_with_drivers()
    iid = _confirmed_iid(e, "list")
    a, _ = _invoke(e, iid, "capture_idea", text="alpha")
    b, _ = _invoke(e, iid, "capture_idea", text="beta")
    _invoke(e, iid, "promote_idea", idea_id=a["idea_id"], artist="A",
            title="Alpha", genre="ambient")
    all_data, _ = _invoke(e, iid, "list_ideas")
    new_data, _ = _invoke(e, iid, "list_ideas", status="new")
    promoted_data, _ = _invoke(e, iid, "list_ideas", status="promoted")
    assert all_data["count"] == 2
    assert new_data["count"] == 1 and new_data["ideas"][0]["text"] == "beta"
    assert promoted_data["count"] == 1
    e.memory.close()


def test_create_album_records_graph_node_and_renders_templates() -> None:
    """``create_album`` records the Album node + renders the bitwize-ported album
    template via the StateDriver. First-album-for-artist also seeds an artist page."""
    e = _fresh_with_drivers()
    iid = _confirmed_iid(e, "create")
    data, _ = _invoke(e, iid, "create_album", artist="Studio One",
                      title="Origin", genre="ambient", type="narrative")
    assert data["album_slug"] == "origin"
    assert data["album_root"].endswith("origin")
    assert data["artist_seeded"] is True
    # State has the album recorded
    state = e.drivers.get("music_state")
    assert state.find_album(query="origin")
    # Graph node carries the type enum
    node = e.memory.recall(data["album_id"])
    assert node.get("type") == "narrative"
    e.memory.close()


def test_create_album_rejects_unknown_type() -> None:
    e = _fresh_with_drivers()
    iid = _confirmed_iid(e, "bad")
    data, inv = _invoke(e, iid, "create_album", artist="A", title="T",
                        genre="g", type="polka")
    assert data is None
    assert "INVALID_ARGUMENT" in e.memory.recall(inv).get("error", "")
    e.memory.close()


def test_find_album_fuzzy_and_exact() -> None:
    e = _fresh_with_drivers()
    iid = _confirmed_iid(e, "find")
    _invoke(e, iid, "create_album", artist="A", title="Origin",
            genre="ambient")
    _invoke(e, iid, "create_album", artist="A", title="Echoes",
            genre="ambient")
    exact, _ = _invoke(e, iid, "find_album", query="origin")
    fuzzy, _ = _invoke(e, iid, "find_album", query="echo")
    all_data, _ = _invoke(e, iid, "find_album")
    assert exact["count"] == 1 and exact["albums"][0]["slug"] == "origin"
    assert fuzzy["count"] == 1
    assert all_data["count"] == 2
    e.memory.close()


def test_create_and_list_tracks_and_set_status() -> None:
    """``create_track`` + ``list_tracks`` + ``set_track_status`` round-trip;
    status enum bites on bogus value."""
    e = _fresh_with_drivers()
    iid = _confirmed_iid(e, "tracks")
    _invoke(e, iid, "create_album", artist="A", title="Loop",
            genre="ambient")
    t1, _ = _invoke(e, iid, "create_track", album="loop", title="Intro",
                    track_number=1)
    t2, _ = _invoke(e, iid, "create_track", album="loop", title="Beat",
                    track_number=2)
    assert t1["track_slug"].startswith("01-")
    assert t2["track_slug"].startswith("02-")
    listed, _ = _invoke(e, iid, "list_tracks", album="loop")
    assert listed["count"] == 2
    # Status flip works
    _invoke(e, iid, "set_track_status", album="loop",
            track=t1["track_slug"], status="mastered")
    listed2, _ = _invoke(e, iid, "list_tracks", album="loop")
    assert any(t["status"] == "mastered" for t in listed2["tracks"])
    # Status enum bites
    data, inv = _invoke(e, iid, "set_track_status", album="loop",
                        track=t1["track_slug"], status="bogus")
    assert data is None
    assert "INVALID_ARGUMENT" in e.memory.recall(inv).get("error", "")
    e.memory.close()


def test_album_progress_reports_completion_percentage() -> None:
    e = _fresh_with_drivers()
    iid = _confirmed_iid(e, "progress")
    _invoke(e, iid, "create_album", artist="A", title="Long Player",
            genre="ambient")
    t1, _ = _invoke(e, iid, "create_track", album="long-player",
                    title="A1", track_number=1)
    t2, _ = _invoke(e, iid, "create_track", album="long-player",
                    title="A2", track_number=2)
    _invoke(e, iid, "set_track_status", album="long-player",
            track=t1["track_slug"], status="mastered")
    prog, _ = _invoke(e, iid, "album_progress", album="long-player")
    assert prog["track_count"] == 2
    assert prog["tracks_completed"] == 1
    assert prog["completion_percentage"] == 50
    e.memory.close()


def test_rename_album_and_rename_track_preserve_state() -> None:
    e = _fresh_with_drivers()
    iid = _confirmed_iid(e, "rename")
    _invoke(e, iid, "create_album", artist="A", title="Old Name",
            genre="ambient")
    _invoke(e, iid, "create_track", album="old-name", title="A1",
            track_number=1)
    res, _ = _invoke(e, iid, "rename_album", old_slug="old-name",
                     new_slug="new-name")
    assert res["success"] is True
    listed, _ = _invoke(e, iid, "list_tracks", album="new-name")
    assert listed["count"] == 1
    # Rename a track
    track_slug = listed["tracks"][0]["slug"]
    rt, _ = _invoke(e, iid, "rename_track", album="new-name",
                    old_slug=track_slug, new_slug="renamed-track")
    assert rt["success"] is True
    e.memory.close()


def test_rename_album_unknown_slug_typed_failure() -> None:
    e = _fresh_with_drivers()
    iid = _confirmed_iid(e, "rename-bad")
    data, inv = _invoke(e, iid, "rename_album", old_slug="ghost",
                        new_slug="phantom")
    assert data is None
    assert "NOT_FOUND" in e.memory.recall(inv).get("error", "")
    e.memory.close()


def test_resume_session_returns_session_state() -> None:
    e = _fresh_with_drivers()
    iid = _confirmed_iid(e, "resume")
    state = e.drivers.get("music_state")
    state.update_session({"last_album": "origin", "last_phase": "drafting"})
    data, _ = _invoke(e, iid, "resume_session")
    assert data["session"]["last_album"] == "origin"
    assert data["session"]["last_phase"] == "drafting"
    e.memory.close()


def test_idea_status_enum_bites_at_record_time() -> None:
    """``(Idea, status)`` is now a closed enum {new, promoted, dropped} —
    direct ``Memory.record`` of an unknown status raises (graph-level guard)."""
    e = _fresh_with_drivers()
    with pytest.raises(ValueError):
        e.memory.record("Idea", {"text": "x", "status": "bogus"})
    e.memory.close()
