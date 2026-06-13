"""skills — the first-class registry over every capability's walkable skills (Spec 026).

Folder-form per Spec 060 §Phase 3 / Spec 286 Goal 4. Re-exports the public
surface other modules + tests reach for (`MatcherResult`, `_all_skills`) so
existing `from agency.capabilities.skills import …` keeps working.
"""
from ._main import (  # noqa: F401
    MatcherResult,
    SkillsCapability,
    _all_skills,
)
