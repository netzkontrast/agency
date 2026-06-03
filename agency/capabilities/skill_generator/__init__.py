"""skill_generator — generate a deploy-ready skill in one call.

Folder-form per Spec 060 §Phase 3 — composition capability (no own
templates/schemas; delegates to plugin.author_skill + plugin.lint_skill).
"""
from ._main import SkillGeneratorCapability  # noqa: F401
