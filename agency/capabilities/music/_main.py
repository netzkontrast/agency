# agency-scaffold: v1
"""music — clustered domain capability (Spec 093 master + Specs 094-100 + 115).

Music graduates from ``examples/music.py`` into a first-class folder-form
capability under ``agency/capabilities/music/`` (Spec 094). The CLAUDE.md +
docs/vision/CAPABILITY-CLUSTERS.md doctrine exception is documented in those
files; music remains the **reference clustered domain capability** but is no
longer "third-party example" — it's the substrate's first creative-production
domain.

This module composes the migrated Spec-007 verb surface PLUS every cluster verb
from Specs 094-100 (lifecycle, lyrics, audio, catalogue, promo, research,
gates) PLUS Spec 115 production-binding extras. The live ``@verb``
decorators are the authoritative count — `agency.registry._caps['music'].verbs`
enumerates them — per CLAUDE.md §"Derivability audit" (authored numerals
in docstrings drift; the live surface is the single source of truth).
Spec 286 Phase 3 SHIPS the per-cluster file split (Spec 094 design §"Module
layout") that earlier slices intentionally deferred: each cluster's verbs now
live on a mixin class in ``clusters/<name>.py``; ``MusicCapability`` composes
them via multiple inheritance. The split is a pure behaviour-frozen relocation
— verb names, signatures, bodies, ontology, skill_doc, and the wire contract
are unchanged. ``cls.__module__`` stays ``…music._main`` so this docstring
remains the single SkillDoc source (CapabilityBase.as_capability →
SkillDoc.from_module).

Use when: conceptualizing or producing an album — turning an idea into a gated concept, mastering to a target loudness, drafting promo copy, or auditing a release — as the reference for how a first-class clustered domain capability extends agency.
Triggers:
- An album idea that needs a structured, gated concept before production
- A music production step (master, promo, lyric analysis) that should be recorded as provenance
- A reference for how a clustered domain capability reaches external tools via Drivers
Red flags:
- Shelling out to ffmpeg/Postgres/R2 directly → route through a Spec-002 Driver via ctx.get_driver
- Producing a document without an artefact → set data['artefact'] so the Registry records PRODUCES
"""
from __future__ import annotations

from agency.capability import CapabilityBase, RenderTemplates

from .ontology import music_ontology

# Backward-compat re-exports (Spec 286 P3): the module-level constants, helpers,
# and standalone ``conceptualize`` moved to ``clusters._base`` as the single
# source the cluster mixins share. Re-exported here so existing call sites that
# import them from ``music._main`` keep working unchanged.
from .clusters._base import (  # noqa: F401
    DEFAULT_CLAIM_CONFIDENCE,
    STREAMING_TARGET_LUFS,
    _MIN_RHYME_GROUPS,
    _SYLLABLE_TOLERANCE,
    _VOWELS,
    _fill_album_body,
    _fill_track_body,
    _slugify,
    _syllables,
    _validate_album_type,
    conceptualize,
)
from .clusters import (
    AudioCluster,
    CatalogueCluster,
    CloudCluster,
    GatesCluster,
    LifecycleCluster,
    LyricsCluster,
    PromoCluster,
    ResearchCluster,
    StateCluster,
)


class MusicCapability(LifecycleCluster, LyricsCluster, AudioCluster,
                      CatalogueCluster, PromoCluster, ResearchCluster,
                      GatesCluster, StateCluster, CloudCluster,
                      CapabilityBase):
    """The single registered ``music`` capability (Spec 286 Phase 3).

    Composed from the per-cluster verb mixins; the registration surface
    (name / home / ontology / render_templates / docstring-derived skill_doc)
    is identical to the prior single-class form. Verb discovery walks the MRO
    (``CapabilityBase.as_capability`` → ``inspect.getmembers``) so every mixin's
    ``@verb`` methods register under the one ``music`` capability. The shared
    driver-wiring (``_require_drv`` override + lazy autowire) + the Spec-119
    name-exposure scan live on ``clusters._base._MusicBase`` — the common base
    of every mixin.
    """
    name = "music"
    home = "capability"
    ontology = music_ontology
    render_templates = RenderTemplates.from_module(__file__)
