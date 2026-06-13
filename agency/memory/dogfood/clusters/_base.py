"""dogfood.clusters._base — shared DogfoodCapability infrastructure (Spec 286 P3).

Dogfood's verbs lean on module-level helper functions (the amendment
classifier rules, the observation-header parser, the export version
constant) rather than instance-level driver wiring. Those helpers live in
their owning cluster modules and are re-exported from ``dogfood/_main.py``
for back-compat. ``DogfoodBase`` is the shared mixin anchor every cluster
mixin and the composed ``DogfoodCapability`` inherit; it currently carries
no shared instance state but keeps the composition shape identical to the
music / novel / plugin splits (Spec 286 P3). Behaviour-frozen relocation.
"""
from __future__ import annotations


class DogfoodBase:
    """Shared anchor for the dogfood cluster mixins.

    No shared instance helpers today — dogfood's cross-cluster helpers are
    module-level pure functions (re-exported from ``_main`` for back-compat).
    Present for parity with the other Spec 286 P3 splits and as the seam for
    any future shared guard / resolver.
    """
