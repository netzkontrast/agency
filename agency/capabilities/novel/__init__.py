# agency-scaffold: v1
"""novel — long-form prose authoring capability (Spec 101 master).

Canonical SkillDoc (Use when / Triggers / Red flags) lives on the
`_main` module docstring — that's the single source the engine derives
from (CapabilityBase.as_capability → SkillDoc.from_module). Don't
duplicate the triple here; keeping it on ONE module avoids the drift
the Round 1 sc-analyze flagged.
"""
from ._main import NovelCapability

__all__ = ["NovelCapability"]
