"""dogfood.clusters — cluster mixins composed into the single DogfoodCapability.

Spec 286 P3 — the ~1147-line ``dogfood`` god-class split into one mixin per
cluster. Each mixin holds the ``@verb`` methods of its cluster verbatim;
``DogfoodBase`` is the shared anchor (dogfood's cross-cluster helpers are
module-level pure functions re-exported from ``_main``). ``dogfood/_main.py``
composes the mixins (mixins first, ``CapabilityBase`` last) into ONE
registered ``dogfood`` capability — the wire contract is unchanged.
"""
from ._base import DogfoodBase
from .observe import ObserveMixin
from .portage import PortageMixin
from .session import SessionMixin
from .amendment import AmendmentMixin

__all__ = [
    "DogfoodBase",
    "ObserveMixin",
    "PortageMixin",
    "SessionMixin",
    "AmendmentMixin",
]
