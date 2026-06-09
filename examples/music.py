"""DEPRECATED — re-export shim for one spec cycle (Spec 094).

Music graduated from ``examples/`` into ``agency/capabilities/music/`` as a
first-class folder-form capability. This shim preserves third-party imports
during the migration cycle and is removed in Spec 110 (or when no external
import survives a grep — whichever first).

Migrate imports::

    # before
    from examples.music import MusicCapability, ALBUM_TYPES

    # after
    from agency.capabilities.music import MusicCapability
    from agency.capabilities.music.ontology import ALBUM_TYPES
"""
from __future__ import annotations

import warnings

from agency.capabilities.music import MusicCapability
from agency.capabilities.music._main import _syllables, conceptualize
from agency.capabilities.music.ontology import (
    ALBUM_CONCEPT_SKILL,
    ALBUM_STATUS,
    ALBUM_TYPES,
    PRE_GENERATION_SKILL,
    RELEASE_QA_SKILL,
    TRACK_STATUS,
    music_ontology,
)

warnings.warn(
    "examples.music is deprecated since Spec 094 — import from "
    "agency.capabilities.music instead. This shim is removed in Spec 110.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = [
    "ALBUM_CONCEPT_SKILL",
    "ALBUM_STATUS",
    "ALBUM_TYPES",
    "MusicCapability",
    "PRE_GENERATION_SKILL",
    "RELEASE_QA_SKILL",
    "TRACK_STATUS",
    "_syllables",
    "conceptualize",
    "music_ontology",
]
