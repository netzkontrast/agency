"""plugin — develop the agency Claude Code plugin from inside the engine.

Folder-form per Spec 060 §Phase 3. Re-exports the symbols tests +
substrate consumers depended on from the pre-migration single-file form.
"""
from ._main import (  # noqa: F401
    PluginCapability,
    author_command,
    author_skill,
    help_map,
    lint_capability,
    lint_skill,
    lint_skill_doc,
    marketplace_entry,
    scaffold,
    step_doc,
)
