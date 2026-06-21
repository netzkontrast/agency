"""adr — architecture decision records, ported onto the substrate (Spec 354).

The enhanced WH(Y) ADR format (the `adr` repo) bound onto agency's primitives:
a strict `Decision` node, thematic-living ADRs (Documents), typed dependency
edges, and decidable WHY/MIN validation. Spec 354 lands Slice 1 (ontology +
theme + draft + validate); 355 adds the Definition-of-Done gate, 356 the
spec→decision extraction + hints.
"""
from ._main import AdrCapability

__all__ = ["AdrCapability"]
