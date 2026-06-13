"""memory pillar — the bi-temporal graph store (`_core`) + its capabilities
(reflect · document · dogfood). Spec 291: `agency/memory.py` was absorbed into
`agency/memory/_core.py`; this package re-exports its surface so
`from agency.memory import Memory` is unchanged."""
from ._core import OPEN, Memory

__all__ = ["Memory", "OPEN"]
