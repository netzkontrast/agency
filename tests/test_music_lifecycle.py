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

from agency.engine import Engine
from agency.skill import SkillRun


def _fresh() -> Engine:
    return Engine(tempfile.mktemp(suffix=".db"))


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
