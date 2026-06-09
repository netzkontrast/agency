"""music — clustered domain capability (Spec 093 master / Spec 094 lifecycle child).

Canonical SkillDoc (Use when / Triggers / Red flags) lives on the
`_main` module docstring — that's the single source the engine derives
from (CapabilityBase.as_capability → SkillDoc.from_module). Don't
duplicate the triple here; keeping it on ONE module avoids the drift
the Round 1 sc-analyze flagged.
"""
from ._main import MusicCapability

__all__ = ["MusicCapability"]
