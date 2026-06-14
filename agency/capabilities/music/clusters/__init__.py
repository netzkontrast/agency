# agency-scaffold: v1
"""music clusters — per-cluster verb mixin modules (Spec 094 / Spec 286 P3).

The ``MusicCapability`` god-class splits into one mixin class per domain
cluster, composed into the single registered capability via multiple
inheritance (``_main.py``). Each mixin holds the ``@verb`` methods of its
section verbatim; the shared driver-wiring + helpers live on ``_base``.

The verb-name set, ontology, skill_doc, and wire contract are unchanged — the
split is a pure behaviour-frozen relocation.
"""
from .audio import AudioCluster
from .catalogue import CatalogueCluster
from .cloud import CloudCluster
from .gates import GatesCluster
from .lifecycle import LifecycleCluster
from .lyrics import LyricsCluster
from .promo import PromoCluster
from .research import ResearchCluster
from .state import StateCluster

__all__ = [
    "AudioCluster",
    "CatalogueCluster",
    "CloudCluster",
    "GatesCluster",
    "LifecycleCluster",
    "LyricsCluster",
    "PromoCluster",
    "ResearchCluster",
    "StateCluster",
]
