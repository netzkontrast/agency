"""prompt.clusters — cluster mixins composed into the single PromptCapability.

Spec 286 P3 — the ~932-line ``prompt`` god-class split into one mixin per
section grouping. Each mixin holds the ``@verb`` methods of its cluster
verbatim; ``PromptBase`` carries the shared (driver-less) MRO anchor, while the
token + scoring helpers live module-level in ``_base``. ``prompt/_main.py``
composes them (mixins first, ``CapabilityBase`` last) into ONE registered
``prompt`` capability — the wire contract is unchanged.
"""
from ._base import PromptBase
from .dossier import DossierMixin
from .engineering import EngineeringMixin
from .gates import GatesMixin
from .assembly import AssemblyMixin
from .fragments import FragmentsMixin

__all__ = [
    "PromptBase",
    "DossierMixin",
    "EngineeringMixin",
    "GatesMixin",
    "AssemblyMixin",
    "FragmentsMixin",
]
